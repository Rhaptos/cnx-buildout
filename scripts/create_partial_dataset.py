from cStringIO import StringIO
import logging
import os
import re
import sys
import time
import traceback

import transaction
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
from Acquisition import aq_inner
from Acquisition import aq_parent
from Products.Archetypes.utils import shasattr
from Products.CMFCore.tests.base.security import PermissiveSecurityPolicy
from Products.CMFCore.tests.base.security import OmnipotentUser
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.Extensions.Install import activatePluginInterfaces
from Testing.makerequest import makerequest
from psycopg import IntegrityError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('rhaptos_cleanout')
logger.setLevel(logging.INFO)

contentid_regx = re.compile(r'^((?:(?:m)|(?:col))\d+)')

class EvenMoreOmnipotentUser(OmnipotentUser):

    def has_permission(self, permission, obj):
        return True

    def getRoles(self):
        return OmnipotentUser.getRoles(self) + ('Owner',)

    def getRolesInContext(self, obj):
        return OmnipotentUser.getRolesInContext(self, obj) + ('Owner',)

    def has_role(self, role, object=None):
        return True

    def hasRole(self, *args, **kw):
        return True

    def allowed(self, object, object_roles=None):
        return True


def _getObjectIds(filename, _dict):
    ifile = open(filename, 'rb')
    for line in ifile:
        line = line.strip()
        if line:
            _dict[line] = True
    ifile.close()

def _findObjects(context, meta_type):
    objids = [id for id in context.objectIds()]
    for id in objids:
        obj = context[id]
        if (shasattr(obj, 'objectIds') and not (
                meta_type == 'Plone Site' and obj.meta_type == 'Plone Site')):
            for o in _findObjects(obj, meta_type):
                yield o
        if obj.meta_type == meta_type:
            yield obj

PARENT_SQL = """SELECT moduleid FROM modules WHERE
module_ident IN (SELECT parent FROM modules WHERE moduleid = '%s'
        AND parent IS NOT NULL);
"""

def _getModuleParents(self, modules):
    psqlda = self.devrep
    done = False
    while not done:
        done = True
        for moduleid in modules.keys():
            results = psqlda.manage_test(PARENT_SQL % moduleid)
            for result in results:
                parentid = result.moduleid
                if parentid not in modules:
                    done = False
                    modules[parentid] = True


def generateCollectionsList(self, data_dir):
    collections = dict()
    _getObjectIds(os.path.join(data_dir, 'collections.txt'), collections)
    repository = self.content
    done = False
    while not done:
        done = True
        for collectionid in collections.keys():
            obj = repository.getRhaptosObject(collectionid)
            parentid = obj.latest.getParentId()
            if parentid and parentid not in collections:
                done = False
                collections[parentid] = True
    ofile = open(os.path.join(data_dir, 'allcollections.txt'), 'wb')
    for collection in collections:
        print >> ofile, collection
    ofile.flush()
    ofile.close()
    return 'Fin.'


def generateModulesList(self, data_dir):
    modules = dict()
    collections = dict()
    for filename, _dict in (('modules.txt', modules),
            ('allcollections.txt', collections)):
        _getObjectIds(os.path.join(data_dir, filename), _dict)

    catalog = self.content.catalog
    brains = catalog(objectId = collections.keys(), portal_type='Collection')
    for b in brains:
        obj = b.getObject()
        if obj is not None:
            moduleids = obj.containedModuleIds()
            for moduleid in moduleids:
                modules[moduleid] = True

    _getModuleParents(self, modules)

    ofile = open(os.path.join(data_dir, 'allmodules.txt'), 'wb')
    for moduleid in modules:
        print >> ofile, moduleid
    ofile.flush()
    ofile.close()
    return 'Fin.'


DELETE_SQL = """DELETE FROM similarities WHERE objectid = '%(objectId)s';
DELETE FROM files WHERE fileid in 
    (SELECT fileid FROM module_files WHERE module_ident IN
        (SELECT module_ident FROM modules WHERE moduleid = '%(objectId)s'));
DELETE FROM module_files WHERE module_ident IN 
    (SELECT module_ident FROM modules WHERE moduleid = '%(objectId)s');
DELETE FROM moduletags WHERE module_ident IN
    (SELECT module_ident FROM modules WHERE moduleid = '%(objectId)s');
DELETE FROM modules WHERE moduleid = '%(objectId)s';
"""

CHECK_SQL = """SELECT module_ident FROM modules WHERE
parent IN (SELECT module_ident FROM modules WHERE moduleid = '%s');
"""

def _generateModuleDeleteSQL(objectId):
    return DELETE_SQL % dict(objectId=objectId)

HEADER_SQL = """
ALTER TABLE ONLY modules
    DROP CONSTRAINT "$3";
"""

FOOTER_SQL = """
DELETE FROM abstracts WHERE abstractid NOT IN
    (SELECT abstractid FROM modules);
ALTER TABLE ONLY modules
    ADD CONSTRAINT "$3" FOREIGN KEY (parent) REFERENCES modules(module_ident) DEFERRABLE;
"""

def cleanoutRhaptosContent(self, data_dir):
    def write(msg):
        self.REQUEST.RESPONSE.write('%s\n' % msg)
    repository = self.content
    portal_linkmap = getToolByName(self, 'portal_linkmap')
    print_tool = getToolByName(self, 'rhaptos_print')
    pdf_folder = print_tool._getContainer()
    modules = dict()
    collections = dict()
    def testId(id):
        return (contentid_regx.match(id) and id not in modules 
                and id not in collections)
    _getObjectIds(os.path.join(data_dir, 'allmodules.txt'), modules)
    _getObjectIds(os.path.join(data_dir, 'allcollections.txt'), collections)
    delete_sql = open(os.path.join(data_dir, 'module_delete.sql'), 'wb')
    delete_sql.write(HEADER_SQL)
    todelete = [id for id in repository.objectIds() if testId(id)]
    count = 0
    total = len(todelete)
    for objectId in todelete:
        try:
            write('Deleting %s' % objectId)
            if objectId.startswith('m'):
                delete_sql.write(DELETE_SQL % {'objectId': objectId})
            repository.manage_delObjects(objectId)
            portal_linkmap.deleteLinks(objectId)
            count = count + 1
        except:
            write(traceback.format_exc())
            raise
        if count and (count % 500) == 0:
            transaction.savepoint(optimistic=True)
            write('Deleted %s/%s objects' % (count, total))
    delete_sql.write(FOOTER_SQL)
    delete_sql.flush()
    delete_sql.close()
    repository.catalog.refreshCatalog(clear=1)
    pdfids = [id for id in pdf_folder.objectIds()]
    total = len(pdfids)
    count = 0
    for pdfid in pdfids:
        try:
            match = contentid_regx.search(pdfid)
            if not match:
                continue
            contentid = match.group(1)
            if contentid in todelete:
                write('Deleting %s.' % pdfid)
                pdf_folder.manage_delObjects(pdfid)
                count = count + 1
        except:
            write(traceback.format_exc())
            raise
        if count and (count % 500) == 0:
            transaction.savepoint(optimistic=True)
            write('Deleted %s/%s files' % (count, total))
    write('Fin.')


def cleanoutLenses(self, data_dir):
    ifile = open(os.path.join(data_dir, 'lenses.txt'), 'rb')
    LENSES_TO_KEEP = dict()
    for line in ifile:
        parts = line.split('/')
        if len(parts) == 2:
            folder = parts[0].strip()
            lens = parts[1].strip()
            if folder not in LENSES_TO_KEEP:
                LENSES_TO_KEEP[folder] = list()
            LENSES_TO_KEEP[folder].append(lens)
    ifile.close()
    lensfolder = self.lenses
    folderids = [x for x in lensfolder.objectIds()]
    for folderId in folderids:
        if folderId not in LENSES_TO_KEEP:
            lensfolder.manage_delObjects(folderId)
        else:
            folder = lensfolder[folderId]
            lensids = [x for x in folder.objectIds()]
            for lensId in lensids:
                if lensId not in LENSES_TO_KEEP[folderId]:
                    folder.manage_delObjects(lensId)
    return 'Fin.'

DELETE_USER_SQL = """DELETE FROM persons WHERE personid='%s';
"""

def cleanoutUsers(self, data_dir):
    portal_membership = getToolByName(self, 'portal_membership')
    portal_memberdata = getToolByName(self, 'portal_memberdata')
    portal_registration = getToolByName(self, 'portal_registration')
    portal_types = getToolByName(self, 'portal_types')
    portal_groups = getToolByName(self, 'portal_groups')
    acl_users = getToolByName(self, 'acl_users')
    def write(msg):
        logger.info(msg)
    delete_sql = open(os.path.join(data_dir, 'users_delete.sql'), 'wb')
    creators = dict()
    catalog = self.content.catalog
    brains = catalog(portal_type=['Module', 'Collection'])
    for b in brains:
        obj = b.getObject()
        write('Getting users for %s.' % obj.objectId)
        if obj.portal_type == 'Collection':
            for attr in ('getAuthors', 'getMaintainers', 'getLicensors',
                    'getPub_maintainers', 'getPub_authors',
                    'getPub_licensors', 'getCollaborators'):
                if shasattr(obj, attr):
                    func = getattr(obj, attr)
                    try:
                        users = func()
                    except AttributeError:
                        write('Failed %s call  for %s' % (attr, obj.objectId))
                        users = list()
                    if users:
                        for user in users:
                            creators[user] = 1
        else:
            for prop in ('authors', 'maintainers', 'licensors',
                    'pub_authors', 'pub_maintainers', 'pub_licensors',
                    'collaborators'):
                if shasattr(obj, prop):
                    users = getattr(obj, prop)
                    if users:
                        for user in users:
                            creators[user] = 1
    for userid in acl_users.source_users.getUserIds():
        if userid not in creators:
            delete_sql.write(DELETE_USER_SQL % userid)
    delete_sql.close()
    memberdata_properties = portal_memberdata.propdict()
    portal_role_manager = acl_users.portal_role_manager
    for user in creators:
        user_obj = acl_users.getUserById(user)
        userdata = portal_membership.getMemberById(user)
        creators[user] = props = dict()
        for prop in memberdata_properties:
            props[prop] = userdata.getProperty(prop)
            props['roles'] = portal_role_manager.getRolesForPrincipal(user_obj)
            props['groups'] = portal_groups.getGroupsForPrincipal(user_obj)
    members_propdict = self.Members.propdict()
    members_properties = dict()
    for prop in members_propdict:
        members_properties[prop] = self.Members.getProperty(prop)
    self.manage_delObjects('Members')
    self.portal_catalog.refreshCatalog(clear=1)
    del portal_role_manager
    acl_users.manage_delObjects(['portal_role_manager', 'mutable_properties',
        'source_users'])
    large_folder = portal_types['Large Plone Folder']
    large_folder.manage_changeProperties(global_allow=True)
    self.invokeFactory('Large Plone Folder', 'Members')
    large_folder.manage_changeProperties(global_allow=False)
    for prop in members_propdict:
        if self.Members.hasProperty(prop):
            self.Members._updateProperty(prop, members_properties[prop])
        else:
            self.Members._setProperty(prop, members_properties[prop],
                    type=members_propdict[prop]['type'])
    self.Members.manage_permission('Add Annotation Servers', 
            roles=['Owner'], acquire=1)
    plone_pas = acl_users.manage_addProduct['PlonePAS']
    plone_pas.manage_addUserManager('source_users')
    out = StringIO()
    activatePluginInterfaces(self, 'source_users', out)
    plone_pas.manage_addGroupAwareRoleManager('portal_role_manager')
    activatePluginInterfaces(self, 'portal_role_manager', out)
    plone_pas.manage_addZODBMutablePropertyProvider('mutable_properties')
    activatePluginInterfaces(self, "mutable_properties", out)
    portal_role_manager = acl_users.portal_role_manager
    for user in creators:
        props = creators[user]
        roles = props['roles']
        groups = props['groups']
        del props['roles']
        del props['groups']
        for role in roles:
            if role not in portal_role_manager.listRoleIds():
                portal_role_manager.addRole(role)
        portal_membership.addMember(user, user, roles, '', props)
        for group in groups:
            portal_groups.addPrincipalToGroup(user, group)
        portal_membership.createMemberarea(user)
    for role in ['Author', 'Endorser', 'Licensor', 'Maintainer']:
        if role not in portal_role_manager.listRoleIds():
            portal_role_manager.addRole(role)
    portal_role_manager.assignRoleToPrincipal('Manager', 'Administrators')
    portal_role_manager.assignRoleToPrincipal('Reviewer', 'Reviewers')
    self.member_catalog.refreshCatalog(clear=1)
    portal_memberdata.pruneMemberDataContents()
    write('fin.')

def cleanoutGroups(self, data_dir):
    tosave = {'Administrators':1, 'Reviewers':1, 'index_html':1}
    ifile = open(os.path.join(data_dir, 'groups.txt'), 'rb')
    for line in ifile:
        group = line.strip()
        if group:
            tosave[group] = 1
    ifile.close()
    portal_groups = getToolByName(self, 'portal_groups')
    def write(msg):
        logger.info(msg)
    folder = portal_groups.getGroupWorkspacesFolder()
    groupids = [id for id in folder.objectIds() if id not in tosave]
    count = 0
    total = len(groupids)
    for groupid in groupids:
        try:
            portal_groups.removeGroup(groupid)
            write('Removed group %s' % groupid)
            count = count + 1
        except:
            write(traceback.format_exc())
            raise
        if count and (count % 250) == 0:
            transaction.savepoint(optimistic=True)
            write('Removed %s/%s groups' % (count,total))
    write('fin.')

def uninstallProducts(portal):
    portal_quickinstaller = getToolByName(portal, 'portal_quickinstaller')
    for product in ['CacheSetup', ]:
        if portal_quickinstaller.isProductInstalled(product):
            logger.info('unistalling %s' % product)
            portal_quickinstaller.uninstallProducts(products=[product])
    if 'portal_squid' in portal.objectIds():
        portal.manage_delObjects('portal_squid')

def postCleanoutPopularity(portal, data_dir):

    # XXX can not working see getHitCount() Too many internal structs
    ##import sets
    ##
    ### At this point the content catalog has been cleaned up alread5Dy
    ##catalog = portal.content.catalog
    ##brains = catalog(portal_type=['Module'])
    ##mids = [o.objectId for o in brains]
    ##
    ##hd = portal.portal_hitcount._hits
    ##hids = hd.keys()
    ##deleteIds = sets.Set(hids).difference(sets.Set(mids))
    ##for m in deleteIds:
    ##    m = m.strip()
    ##    if hd.has_key(m):
    ##        hd.pop(m)
    ##portal.portal_hitcount._hits = hd
    portal.portal_hitcount.resetHitCounts()

def main(app, data_dir):
    _policy=PermissiveSecurityPolicy()
    _oldpolicy=setSecurityPolicy(_policy)
    newSecurityManager(None, EvenMoreOmnipotentUser().__of__(app.acl_users))
    app = makerequest(app)
    #uninstallProducts(app.plone)
    logger.info('Generating collections list')
    generateCollectionsList(app.plone, data_dir)
    logger.info('Generating modules list')
    generateModulesList(app.plone, data_dir)
    logger.info('Deleting groups')
    cleanoutGroups(app.plone, data_dir)
    transaction.savepoint(optimistic=True)
    logger.info('Deleting lenses')
    cleanoutLenses(app.plone, data_dir)
    transaction.savepoint(optimistic=True)
    logger.info('Deleting content')
    cleanoutRhaptosContent(app.plone, data_dir)
    transaction.savepoint(optimistic=True)
    logger.info('Deleting users')
    cleanoutUsers(app.plone, data_dir)
    transaction.savepoint(optimistic=True)
    postCleanoutPopularity(app.plone, data_dir)
    transaction.savepoint(optimistic=True)
    app.plone.portal_catalog.refreshCatalog(clear=1)
    transaction.commit()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise ValueError('Requires exactly 1 argument')
    start = time.time()
    main(app, sys.argv[1])
    delta = time.time() - start
    logger.info('Took %1.2d seconds.' % delta)



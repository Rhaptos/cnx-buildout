
import logging
import re
import os
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
from Testing.makerequest import makerequest
from psycopg import IntegrityError
from Products.RhaptosSite import product_globals
from Globals import package_home
from Products.RhaptosSite.setup.RhaptosSetup import createHelpSection

logger = logging.getLogger('deCNX')

directory_views = ('CNXPloneSite', 'cnx_overrides', 'FeatureArticle',
        'CNXContent', 'userProvidedStylesheets',
        'LensOrganizer', 'rhaptosforums', 'simpleattachment', 
        'simpleattachment_widgets', 'ploneboard_images', 'ploneboard_scripts',
        'ploneboard_templates',)

types = ('Paper', 'Presentation', 'Blog Item', 'Blog Folder', 'FeatureArticle',
        'FeedbackFolder', 'UserFeedback',
        'LensOrganizer', 'PloneboardForum', 'FileAttachment',
        'ImageAttachment',)

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

def _cleanoutSkins(self):
    def write(msg):
        logger.info(msg)
    write('Cleaning out skins')
    portal_skins = getToolByName(self, 'portal_skins')
    contents = portal_skins.objectIds()
    for todelete in directory_views:
        if todelete in contents:
            write('Deleting %s directory view' % todelete)
            portal_skins.manage_delObjects(todelete)
    def found(layer):
        return portal_skins.unrestrictedTraverse(layer, None) is not None
    for skin, path in portal_skins.getSkinPaths():
        write('Cleaning out %s skin' % skin)
        path = [p.strip() for p in path.split(',') if found(p.strip())]
        path = ','.join(path)
        portal_skins.addSkinSelection(skin, path)
        if skin == 'Connexions':
            write('Adding Rhaptos skin')
            portal_skins.addSkinSelection('Rhaptos', path)
    write('Setting Rhaptos skin to default')
    portal_skins.default_skin = 'Rhaptos'
    sels = portal_skins._getSelections()
    if 'Connexions' in sels:
        write('Deleting Connexions skin')
        del sels['Connexions']

def _cleanoutTypes(self):
    def write(msg):
        logger.info(msg)
    portal_factory = getToolByName(self, 'portal_factory')
    portal_catalog = getToolByName(self, 'portal_catalog')
    portal_types = getToolByName(self, 'portal_types')
    factory_types = portal_factory.getFactoryTypes()
    count = 0
    for typename in types:
        if typename in factory_types:
            del factory_types[typename]
        paths = [b.getPath() for b in portal_catalog(portal_type=typename) 
                if b.getObject() is not None]
        for path in paths:
            obj = self.unrestrictedTraverse(path, default=None)
            if obj is None:
                write('Failed to lookup %s' % path)
                continue
            parent = aq_parent(aq_inner(obj))
            parent.manage_delObjects(obj.getId())
            write('Deleted %s' % path)
            count = count + 1
            if count and count % 500 == 0:
                write('Deleted %s objects' % count)
                transaction.savepoint(optimistic=True)
        if typename in portal_types.objectIds():
            portal_types.manage_delObjects(typename)
    portal_factory.manage_setPortalFactoryTypes(
            listOfTypeIds=factory_types.keys())

def _customizeFrontPage(self):
    portal = self
    # borrowing heavily from customizeFrontPage in
    # rhaptos/src/Products.RhaptosSite/Products/RhaptosSite/setup/RhaptosSetup.py
    try:
        portal.manage_delObjects('index_html')
    except AttributeError:
        pass
    portal.invokeFactory('Document', 'index_html')
    frontpage = portal.index_html
    frontpage.title = 'Welcome to Rhaptos'
    path = os.path.join(package_home(product_globals), 'www/index_html')
    f = open(path)
    content = f.read()
    f.close()
    frontpage.edit('html',content)

def _emptyNewsFolder(self):
    portal = self
    news = portal.news
    for newsItem in news.listFolderContents():
        news.manage_delObjects(newsItem.getId())

def _setPortalTitle(self):
    portal = self
    portal.setTitle('Rhaptos')

def _replaceAboutUsFolder(self):
    portal = self
    aboutus = portal.aboutus
    # the following deletes will require a portal_catalog re-index (blame 'schema2schemas' Access Rule)
    # and will throw a bunch of handled exceptions
    for usItem in aboutus.listFolderContents():
        aboutus.manage_delObjects(usItem.getId())
    # borrowing heavily from creataAboutUSSection in
    # rhaptos/src/Products.RhaptosSite/Products/RhaptosSite/setup/RhaptosSetup.py
    folder = portal.aboutus
    folder.invokeFactory('Document', 'placeholder')
    placeholder = folder.placeholder
    placeholder.setTitle('Placeholder')
    text = ('<p>This is a placeholder for the default about us page. '
            'To replace it create a new Document and use the display '
            'dropdown on the aboutus folder to change the default view.'
            '</p>')
    placeholder.edit('html', text)
    folder.setDefaultPage('placeholder')

def _recreateHelp(self):
    portal = self
    portal.manage_delObjects('help')
    createHelpSection(portal, portal)

def deCNX(self):
    portal_quickinstaller = getToolByName(self, 'portal_quickinstaller')
    portal_actions = getToolByName(self, 'portal_actions')
    re_mycnx = re.compile('mycnx')
    def write(msg):
        logger.info(msg)
    try:
        actions = portal_actions._cloneActions()
        for a in actions:
            if a.title == 'MyCNX':
                a.title = 'MyRhaptos'
            if re_mycnx.search(a.action.text):
                a.action.text = re_mycnx.sub('mydashboard',a.action.text)
        portal_actions._actions = tuple(actions)

        if portal_quickinstaller.isProductInstalled('Ploneboard'):
            write('Uninstalling Ploneboard')
            portal_quickinstaller.uninstallProducts(['Ploneboard'])
            transaction.savepoint(optimistic=True)

        _cleanoutSkins(self)
        if 'templates' in self.objectIds():
            write('Deleting templates folder')
            self.manage_delObjects('templates')
            transaction.savepoint(optimistic=True)
        _cleanoutTypes(self)
        _customizeFrontPage(self)
        _emptyNewsFolder(self)
        _setPortalTitle(self)
        _recreateHelp(self)
        # recreating aboutus requires that we re-index the portal catalog
        _replaceAboutUsFolder(self)
        self.portal_catalog.refreshCatalog(clear=1)
    except:
        write(traceback.format_exc())
        raise
    write('Fin')

def main(app):
    _policy=PermissiveSecurityPolicy()
    _oldpolicy=setSecurityPolicy(_policy)
    newSecurityManager(None, EvenMoreOmnipotentUser().__of__(app.acl_users))
    app = makerequest(app)
    deCNX(app.plone)
    transaction.commit()

if __name__ == '__main__':
    main(app)


import sys
import transaction

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
from Testing.makerequest import makerequest
from Products.CMFCore.tests.base.security import PermissiveSecurityPolicy
from Products.CMFCore.tests.base.security import OmnipotentUser

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

def main(app):
    _policy=PermissiveSecurityPolicy()
    _oldpolicy=setSecurityPolicy(_policy)
    newSecurityManager(None, EvenMoreOmnipotentUser().__of__(app.acl_users))
    app = makerequest(app)

    # Reindex content catalog
    catalog = app.plone.content.catalog
    catalog.refreshCatalog(clear=1)

    # Reindex lenses catalog
    catalog = app.plone.lens_catalog
    catalog.refreshCatalog(clear=1)

    # clear hit count
    htool=app.plone.portal_hitcount
    htool.resetHitCounts()
    ###FIXME resetHitCounts is currently broken: remove this when fixed
    objs = app.plone.content.objectValues(['Version Folder','Module Version Folder'])
    for ob in objs:
        try:
            htool.registerObject(ob.id,ob.latest.created)
        except IndexError:
            # Bad object in content
            pass

    transaction.commit()

if __name__ == '__main__':
    main(app)

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


def main(app, license_url, workspaces=None):
    _policy = PermissiveSecurityPolicy()
    _oldpolicy = setSecurityPolicy(_policy)
    newSecurityManager(None, EvenMoreOmnipotentUser().__of__(app.acl_users))
    app = makerequest(app)

    for wgname in workspaces:
        wg = app.plone.GroupWorkspaces[wgname]
        print wgname
        for m in wg.objectValues():
            if m.state == 'published':
                print 'Skipping published: ', m.id
            else:
                print '  ', m.id
                m.license = license_url

    transaction.commit()

if __name__ == '__main__':

    if len(sys.argv) < 3:
        raise ValueError('Needs at least two arguments: license URL and workgroup ID(s)')
    main(app, sys.argv[1], sys.argv[2:])

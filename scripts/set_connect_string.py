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

def main(app, connection_string):
    _policy=PermissiveSecurityPolicy()
    _oldpolicy=setSecurityPolicy(_policy)
    newSecurityManager(None, EvenMoreOmnipotentUser().__of__(app.acl_users))
    app = makerequest(app)
    try:
        da = app.devrep
    except:  # If server is down, try again, only throws one error
        da = app.devrep

    da.connection_string = connection_string
    transaction.commit()
    print "Connected %s to '%s'" % (da.connected(), da.connection_string)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise ValueError('Requires exactly 1 argument')
    main(app, sys.argv[1])

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

def main(app, id, title, dbauser, dbuser, dbname, dbserver, dbport):
    _policy=PermissiveSecurityPolicy()
    _oldpolicy=setSecurityPolicy(_policy)
    newSecurityManager(None, EvenMoreOmnipotentUser().__of__(app.acl_users))
    app = makerequest(app)

    # Add Rhaptos Site
    factory = app.manage_addProduct['RhaptosSite']
    factory.manage_addRhaptosSite(id,
        title=title, description='',
        dbauser=dbauser,
        dbapass=None,
        dbuser=dbuser,
        dbpass=None,
        dbname=dbname,
        dbserver=dbserver,
        dbport=dbport and int(dbport) or None)

    # Add Virtual Host Entry
    app.virtual_hosting.set_map('http://*.cnx.rice.edu/ /'+id+'\nhttp://localhost/ /'+id)
    transaction.commit()

if __name__ == '__main__':
    if len(sys.argv) != 8:
        raise ValueError('Requires exactly 7 arguments')
    main(app, sys.argv[1], sys.argv[2], sys.argv[3],
        sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])



transaction.commit()

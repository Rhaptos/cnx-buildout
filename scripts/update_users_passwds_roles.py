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

    # Grab connection to db
    db = app.plone.objectValues('Z Psycopg 2 Database Connection')[0]()

    # Get all users who have extended roles
    updates = 0
    passwds = app.plone.acl_users.source_users._user_passwords
    for mid in passwds.keys():
        mem = app.plone.portal_membership.getMemberById(mid)
        roles = [role for role in mem.getRoles()
                 if role not in ['Member','Authenticated']]
        if roles != []:
            passwd = passwds[mid]
            db.query("update persons set passwd = %s, groups = %s"
                     " where personid = %s",
                     query_data=(passwd, roles, mid))
            print mid, roles
            updates += 1
            if updates % 10 == 0:
                transaction.commit()

    transaction.commit()

if __name__ == '__main__':
    main(app)

from Products.CMFCore.utils import getToolByName
import transaction


def main(site):
    if hasattr(site, 'pdfs'):
        site._delObject('pdfs')
    # Store pdfs in /var/www/files
    site.manage_addProduct['LocalFS'].manage_addLocalFS(
        id='pdfs', title='pdf-storage', basepath='/var/www/files')
    # Use the local fs object in print tool
    ptool = getToolByName(site, 'rhaptos_print')
    ptool.storagePaths = ptool.DEFAULT_STORAGE_PATHS
    ptool.storagePath = ptool.storagePaths[0]
    transaction.commit()


if __name__ == '__main__':
    main(app.plone)

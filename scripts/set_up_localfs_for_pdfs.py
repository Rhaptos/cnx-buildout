import sys

from Products.CMFCore.utils import getToolByName
import transaction


def main(site, paths):
    # paths should be in the format
    #  ["pdfs:/var/www/files", "pdfs2:/var/www/files2", ...]
    storage_paths = []
    for path in paths:
        obj_name, file_path = path.split(':', 1)
        if hasattr(site, obj_name):
            site._delObject(obj_name)
        site.manage_addProduct['LocalFS'].manage_addLocalFS(
            id=obj_name, title='pdf-storage', basepath=file_path)
        storage_paths.append(obj_name)

    # Use the local fs object in print tool
    ptool = getToolByName(site, 'rhaptos_print')
    ptool.storagePaths = storage_paths
    ptool.storagePath = ptool.storagePaths[0]
    transaction.commit()


def print_help_and_exit():
    sys.stderr.write("""\
Usage: %s <object_name>:<path_to_local_dir> ...

Example: %s pdfs:/var/www/files
""" % (sys.argv[0], sys.argv[0]))
    sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print_help_and_exit()
    paths = sys.argv[1:]
    for path in paths:
        if ':' not in path:
            sys.stderr.write('Error: ":" missing in %s\n' % path)
            print_help_and_exit()
    main(app.plone, paths)

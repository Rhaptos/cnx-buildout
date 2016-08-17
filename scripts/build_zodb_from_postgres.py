"""Create ZODB collections and modules from data in the postgres database.  By
default, this script forks and runs the main program in the child process."""


import logging
from optparse import OptionParser
import os
import sys
import urllib2

import transaction


# __file__ doesn't work in ``./bin/instance run``... so using sys.argv[0]
# instead
here = os.path.dirname(sys.argv[0])
logger = logging.getLogger('build-zodb')
handler = logging.FileHandler(os.path.join(here, 'build-zodb.log'))
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def build_zodb(root_url, db_conn):
    logger.debug('build_zodb started with db_conn: %s' % (db_conn,))
    cursor = db_conn().getcursor()
    cursor.execute('SELECT DISTINCT(moduleid) FROM modules')
    for result in cursor.fetchall():
        moduleid = result[0]
        try:
            urllib2.urlopen('%s/content/%s' % (root_url, moduleid))
            logger.info('Created content or content exists: %s' % (moduleid,))
        except urllib2.HTTPError, e:
            logger.error('Failed to create content: %s (%s)' % (moduleid, e))
        except:
            logger.exception('Failed to create content: %s' % (moduleid,))
    cursor.close()


def main(root_url, fork=True):
    db_conn = app.plone.objectValues('Z Psycopg 2 Database Connection')
    if len(db_conn) == 0:
        sys.stderr.write('No database connection object found')
        sys.exit(1)
    if fork:
        pid = os.fork()
        if pid:
            # parent process
            return

    build_zodb(root_url, db_conn[0])
    transaction.commit()


if __name__ == '__main__':
    usage = 'Usage: %prog [options] root_url'
    parser = OptionParser(usage=usage)
    parser.add_option('--no-fork', dest='to_fork',
                      action='store_false', default=True,
                      help='Not fork the process (default false)')
    options, args = parser.parse_args()

    if len(args) != 1:
        sys.stderr.write('Error: Wrong number of arguments.')
        parser.print_help()
        sys.exit(1)

    main(args[0], fork=options.to_fork)

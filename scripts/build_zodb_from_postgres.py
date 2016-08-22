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


def main(root_url, daemonize=False):
    db_conn = app.plone.objectValues('Z Psycopg 2 Database Connection')
    if len(db_conn) == 0:
        sys.stderr.write('No database connection object found')
        sys.exit(1)

    if daemonize:
        pid = os.fork()
        if pid:
            # Parent process exits.
            sys.exit(0)

        # Decouple from parent environment.
        os.setsid()
        os.umask(0)

        # Do second fork.
        pid = os.fork()
        if pid:
            # Second parent process exits.
            sys.exit(0)

        # Redirect standard file descriptors.
        stdin = file('/dev/null', 'r')
        stdout = file('/dev/null', 'a+')
        stderr = file('/dev/null', 'a+', 0)
        os.dup2(stdin.fileno(), sys.stdin.fileno())
        os.dup2(stdout.fileno(), sys.stdout.fileno())
        os.dup2(stderr.fileno(), sys.stderr.fileno())

    build_zodb(root_url, db_conn[0])
    transaction.commit()


if __name__ == '__main__':
    usage = 'Usage: %prog [options] root_url'
    parser = OptionParser(usage=usage)
    parser.add_option('-d', dest='daemonize',
                      action='store_true', default=False,
                      help='Run this script as a background job (daemonize)')
    options, args = parser.parse_args()

    if len(args) != 1:
        sys.stderr.write('Error: Wrong number of arguments.')
        parser.print_help()
        sys.exit(1)

    main(args[0], daemonize=options.daemonize)

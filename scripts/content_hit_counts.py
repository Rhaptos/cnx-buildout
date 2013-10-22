#!/usr/bin/env python
import os
import sys
import gzip
import re
import transaction
import time
import psycopg2
from DateTime import DateTime
from mx.DateTime.DateTime import DateTimeFrom


# Not used, only here for usage guidance.
CRON_WEEKLY_STATEMENT = """\
#!/bin/bash
# use 'touch' to set a stamp older than the first log you want to process,
# or this will process all logfiles
LOGDIR=/var/local/varnish


if [ ${LOGDIR}/varnishncsa.log.1 -nt /var/lib/varnish_import_stamp ] ;
then
    i=2
    while [ ${LOGDIR}/varnishncsa.log.$i.gz -nt /var/lib/varnish_import_stamp ]
    do str="$i,$str" ; i=$((i+1))
    done
    tmpfile=$(tempfile -m 640)
    chgrp www-data $tmpfile
    eval zcat -f  ${LOGDIR}/varnishncsa.log.{{${str::${#str}-1}}.gz,1} > $tmpfile
    /opt/instances/buildout/bin/instance run /opt/instances/buildout/scripts/content_hit_counts.py $tmpfile
    if [ ! $? ]
        then
            echo "Log import failed! Data at: " $tmpfile
        exit 1
    else
        rm $tmpfile
        touch /var/lib/varnish_import_stamp ;
        if [ ! $? ]  ;
           then echo "Can't touch timestamp file /var/lib/varnish_import_stamp"
        fi
    fi
fi
"""


# FIXME: don't hardcode this
MODULE_PATTERN = re.compile('^http://cnx\.org/(?:VirtualHostBase.*VirtualHostRoot/)?content/(m|col)([0-9]+)/[^/]*/$')

def parse_log(name):
    """Parses a varnish gzip'ed log file to capture module hit counts."""
    f = gzip.open(name)
    try:
        f.readline()
        f.seek(0)
    except IOError: # Handle 'Not a gzipped file' case
        f.close()
        f=open(name)
    counts = {}
    start_time = None
    for line in f:
        data = line.split()
        if not start_time:
            start_time = DateTimeFrom('Z'.join(data[3:5])[1:-1].replace(':',' ',1).replace('/','-')).ticks()
        match = MODULE_PATTERN.match(data[6])
        if match:
            objectId = ''.join(match.groups()[0:2])
            if objectId:
                counts[objectId] = counts.get(objectId, 0) + 1
    else:
        end_time = DateTimeFrom('Z'.join(data[3:5])[1:-1].replace(':',' ',1).replace('/','-')).ticks()

    f.close()
    return counts, start_time, end_time

if __name__ == '__main__':
    db_connection_string = os.environ['DB_CONNECTION_STRING']
    for fname in sys.argv[1:]:

        increment, s_time, e_time = parse_log(fname)

        # Filter out hits for objects that don't actually exist
        for objectId in increment.keys():
            if not app.plone.content.hasRhaptosObject(objectId):
                del increment[objectId]
        objids=app.plone.content.objectIds(['Version Folder','Module Version Folder'])
        for objid in objids:
            if not increment.has_key(objid):
                increment[objid]=0

        app.plone.portal_hitcount.incrementCounts(increment, DateTime(s_time), DateTime(e_time))
        transaction.commit()
        print "Updated logs for %s - %s in the ZODB" % (time.ctime(s_time), time.ctime(e_time))

        # Now, also put the records in SQL.
        db_connection = psycopg2.connect(db_connection_string)
        cursor = db_connection.cursor()
        start = time.ctime(s_time)
        end = time.ctime(e_time)
        for moduleid, hits in increment.items():
            cursor.execute("WITH module_ident AS "
                           "  (SELECT module_ident "
                           "   FROM latest_modules "
                           "   WHERE moduleid = %s) "
                           "INSERT INTO document_hits "
                           "  VALUES (module_ident, %s, %s, %s)",
                           (moduleid, start, end, hits,)
                           )
        cursor.close()
        db_connection.close()

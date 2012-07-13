#!/usr/bin/env python
import sys

try:
    import uno
    from unohelper import Base,systemPathToFileUrl, absolutize
except ImportError, e:
    # this is workaround for how buildout sets up the system PATH environment.
    # we need to run most of our site using python 2.4, except
    # uno is python 2.5 only module; thus, we  need a workaround here.
    (major, minor) = sys.version_info[:2] # likely (2, 5) is returned
    sys.path.append('/usr/lib/python%d.%d/site-packages' % (major,minor))
    import uno
    from unohelper import Base,systemPathToFileUrl, absolutize

from os import getcwd
import getopt
# import pdb

from com.sun.star.beans import PropertyValue
from com.sun.star.beans.PropertyState import DIRECT_VALUE
from com.sun.star.uno import Exception as UnoException
from com.sun.star.io import IOException,XInputStream, XOutputStream

class OutputStream( Base, XOutputStream ):
      def __init__( self ):
          self.closed = 0

      def closeOutput(self):
          self.closed = 1

      def writeBytes( self, seq ):
          sys.stdout.write( seq.value )

      def flush( self ):
          pass

def main(host, port, path, pagecountlimit):
    retVal = 0
    pagecountlimit = '50'
    doc = None

    url = "uno:socket,host=%s,port=%d;urp;StarOffice.ComponentContext" % (host, port)

    ctxLocal = uno.getComponentContext()
    smgrLocal = ctxLocal.ServiceManager

    resolver = smgrLocal.createInstanceWithContext(
             "com.sun.star.bridge.UnoUrlResolver", ctxLocal )
    ctx = resolver.resolve( url )
    smgr = ctx.ServiceManager

    desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx )

    cwd = systemPathToFileUrl( getcwd() )

    outProps = (
        #PropertyValue( "FilterName" , 0, "StarOffice XML (Writer)" , 0 ),
        PropertyValue( "OutputStream",0, OutputStream(),0),)
    inProps = (PropertyValue( "Hidden" , 0 , True, 0 ),)
    try:
        fileUrl = uno.absolutize( cwd, systemPathToFileUrl(path) )
        doc = desktop.loadComponentFromURL( fileUrl, "_blank", 0, inProps)

        if not doc:
            raise UnoException( "Couldn't open stream for unknown reason", None )

        # pdb.set_trace()

        try:
            cursor = doc.getCurrentController().getViewCursor()
            cursor.jumpToLastPage()
            pagecount = cursor.getPage()
            if pagecount > int(pagecountlimit):
                raise UnoException( "Input document has %d pages which exceeeds the page count limit of %d." % (pagecount, int(pagecountlimit)), None )
        except  AttributeError:
             # opened picture files will not behave, but do not need to have their page counted
             pass

        doc.storeToURL("private:stream",outProps)
    except IOException, e:
        sys.stderr.write( "Error during conversion: " + e.Message + "\n" )
        retVal = 1
    except UnoException, e:
        sys.stderr.write( "Error ("+repr(e.__class__)+") during conversion:" + e.Message + "\n" )
        retVal = 1
    if doc:
        doc.dispose()

    sys.exit(retVal)


if __name__ == '__main__':

    path = sys.argv[1]

    try:
        opts, args = getopt.gnu_getopt(sys.argv[2:], "", ["address=", "pagecount="])
    except:
        opts = []

    address = ''
    pagecount = ''

    for opt, arg in opts:
        if opt == "--address":
            address = arg
        elif opt == "--pagecount":
            pagecount = arg

    if len(address) == 0:
        address = 'localhost:2002'
    if len(pagecount) ==0:
        pagecount=50

    host, port = address.split(':')
    port = int(port)
    main(host, port, path, pagecount)

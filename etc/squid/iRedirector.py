#!/usr/bin/python -Ou
"""
/**********************************************************************
FILE     : $RCSfile$
PURPOSE  : squid redirector for icoya
NOTES    : uses redirector_class for custom rules
AUTHOR   : Simon Eisenmann
COPYRIGHT: (c) 2003-2007 by struktur AG
DATE     : 28JAN2003
REVISION : $Revision: 4359 $
VERSION  : $Id: iRedirector.py 4359 2007-06-15 07:19:12Z longsleep $ (Author: $Author: longsleep $)

struktur AG            Phone: +49 711 8966560
Kronenstr. 22A         Fax:   +49 711 89665610
70173 Stuttgart        email: info@struktur.de
GERMANY

http://www.struktur.de
http://www.strukturag.com

**********************************************************************/
 iRedirector.py -- a script for squid redirection.
 (a long-running process that uses unbuffered io; hence the -u flag in python)

 NOTE: use redirector_class to define the rules
       redirector_class can be automatically reloaded so you dont have to
       restart squid when the rules were changed.

"""
import sys, os, traceback
from thread import start_new_thread

# add current directory to sys.path to make py2exe work
cwd = os.getcwd()
if not cwd in sys.path:
    sys.path.insert(0, cwd)

import redirector_class

# set to 1 to enable logging
debug = 0 

# set to 1 to enable squid2.6 multithreaded redirector support
# NOTE: having this turned on safes a lot of resources
#       only enable this when url_rewrite_concurrency (squid.conf) is true
threaded = 1

# the logfile for the redirector log (only used when debug is 1)
logfile = "/data/zope/buildout/var/log/redirector.log"

class SquidRedirector:
    """ iRedirector main base class. """
    
    def __init__(self):
        pass

    def rewrite(self,line):
        if threaded:
            # start new thread
            start_new_thread(rewrite, (line,), {})
        else:
            # run single threaded
            rewrite(line)
        
    def run(self):
        # wait for stdin input

        line = read()
        while line:

            # launch rewriting function
            maybe_reload_redirector_class()
            try: self.rewrite(line)
            except:
                exc=sys.exc_info()
                log(str(traceback.format_exception(exc[0],exc[1],exc[2])))
                raise 
                # NOTE: this aborts this redirector process
                #       when no redirector is left squid exits as well

            # read new line
            line = read()

def maybe_reload_redirector_class():
    """ Helper for automatic reloading of the redirector class. """
    if redirector_class.reload_after == -1: return # reload is disabled
    if redirector_class.reload_after > 0:
        redirector_class.reload_after = redirector_class.reload_after - 1
    else:
        reload(redirector_class)

def log(s):
    """ Loggin facility. """
    if not debug: return
    f = open(logfile,"a")
    f.write(s+'\n')
    f.close()

def read():
    """ Returns one unbuffered line from squid. """
    try:
        return sys.stdin.readline()[:-1]
    except KeyboardInterrupt:
        return None
        
def write(s):
    """ Returns a single line to squid. """
    sys.stdout.write(s+'\n')
    sys.stdout.flush()

def rewrite(line):
    """ Splits up the line from squid and gives it to the redirector class. 
        This method can be called in a new thread so one redirector supports
        multiple redirections at the same time. This is a squid2.6 feature.
    """

    log("request : " + line)
    
    # split into parts
    line = line.split(" ")
    urlgroup = "-" # this is squid 2.6 only
    
    if not threaded: 
        # format url, src, ident, method
        url,src_address,ident,method=line[:4]
        if len(line) == 5:
            urlgroup = line[4]
            
    else: 
        # format index, url, src, ident, method
        index,url,src_address,ident,method=line[:5]
        if len(line) == 6:
            urlgroup = line[5]
 
    # send through redirector class
    new_url = redirector_class.rewrite(url, src_address)

    if not new_url: 
        # return empty line when redirector didnt return anything
        new_url=src_address=ident=method=""

    if not threaded: 
        # return without index
        response = " ".join((new_url,src_address,ident,method,urlgroup))
    else: 
        # give back the index
        response = " ".join((index,new_url,src_address,ident,method,urlgroup))

    # write it back to squid
    write(response)

    log("response: " + response)

if __name__ == "__main__":
    sr = SquidRedirector()
    sr.run()

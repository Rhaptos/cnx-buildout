"""
/**********************************************************************
FILE     : $RCSfile$
PURPOSE  : Rule set for icoya redirector
NOTES    : 
AUTHOR   : Simon Eisenmann
COPYRIGHT: (c) 2003-2007 by struktur AG
DATE     : 28JAN2003
REVISION : $Revision: 4357 $
VERSION  : $Id: redirector_class.py 4357 2007-06-15 07:14:19Z longsleep $ (Author: $Author: longsleep $)

struktur AG            Phone: +49 711 8966560
Kronenstr. 22A         Fax:   +49 711 89665610
70173 Stuttgart        email: info@struktur.de
GERMANY

http://www.struktur.de
http://www.strukturag.com

**********************************************************************/

 Reloadable module allows arbitrary url transformations.
 must define reload_after (an integer), and rewrite(url, src_address).


 SiteMap mapping
 ++++++++++++++++++++++++++++++++++++

 NOTE: use sitemap mapping to define rewrite rules,
       if the request does not match a rule the request is denied.
       You can use the $netloc$ keyword which is replaced with the user entered
       netloc. The key is a regex.

       The key of the sitemap mapping supports sorting when the key is a
       two tuple containing (int, regex). If its not a tuple it has to be a regex.
       Specifying the sitemap without tuple will result in random order regex 
       matching.

       The sitemap mapping supports also domain redirection. It is 
       used when the value starts with '302:'.

       Define the matchmode variable to select which part of the URL is to
       be matched by sitemap regular expression rules. Valid modes are
       hostname, path and url.

 EXAMPLES:

   Squid load balancing with ZEO client as parent caches:
   (10, '[\S]*mycompany.com'): 'backendpool/VirtualHostBase/http/${HTTP_HOST}:80/mycompanyportal/VirtualHostRoot'.

   Squid load balancing with ZEO client as parent cache and apache in front:
   (15, '[\S]*myothercompany.com'): 'backendpool',

   Usual rewrite to one http backend:
   (20, '[\S]*mydomain.com'):  '127.0.0.1:9065',

   Redirect to another domain:
   (30, '[\S]*myolddomain.(com|net|org)'): '302:www.mydomain.com',


 Redirection (moved) mapping
 +++++++++++++++++++++++++++++++++++

 NOTE: use redirs mapping to define custom 302:moved responsed for
       certain url(fragment)s. The key is a regex.
       use redirs mapping to redirect certain urls to another
       The value is a 2 element tuple containing the new path and the new host.
       When the host is None then it stays on the same domain.

 EXAMPLES:

    Download area has moved below support to www.mydomain.com: 
    '^/download_area(\/|$)': ('/support/download_area/', 'www.mydomain.com')


 Automatic reload of the rules
 +++++++++++++++++++++++++++++++++++

 NOTE: use the reload after parameter to auto reload this module
       after x requests. Use -1 to disable auto reload


 Logging
 +++++++++++++++++++++++++++++++++++

 NOTE: set debug to 1 to enable logging
       define the logfile in the logfile variable (enter full path)


"""
import urlparse, re
uparse, ujoin = urlparse.urlparse, urlparse.urljoin


"""
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
begin of configuration
"""

# log mode (set to 1 to enable logging)
debug = 0

# logfile for debugging (only required when debug == 1)
logfile = "/application/zope/buildout/var/log/redirector_class.log"

# set this to -1 to get best performance (no reload)
# reload squid to get new rules in effect instead
reload_after = -1

# define sitemap matching regex mapping
sitemap = {

(1, '[\S]*'): '127.0.0.1:8000/VirtualHostBase/http/${HTTP_HOST}:80/plone/VirtualHostRoot',


          }

# define the matchmode for sitemap regex
# (hostname, path and url are valid values)
matchmode = "hostname"

# define moved matching regex mapping
redirs =  {
          }


"""
end of configuration
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
"""


def log(s):
    if not debug: return
    f = open(logfile,"a")
    f.write(s+'\n')
    f.close()

def rewrite(url, src_address):
    """ just rewrites urls. """

    # scheme://netloc/path;parameters?query#fragment
    (scheme,netloc,path,parameters,query,fragment) = uparse(url)

    newnetloc=None
    newpath=None

    keys = sitemap.keys()
    keys.sort()

    for k in keys:
        v = sitemap[k]
        # we support a tuple to allow sorted processing
        if type(k) == type(()): k = k[1]
        if matchmode in ("hostname",):
            matchbox = netloc
        elif matchmode in ("path",):
            matchbox = path
        else:
            matchbox = url
        m = re.match(k, matchbox)
        if m:
            newnetloc=v
            if newnetloc.find('${HTTP_HOST}') != -1: newnetloc = newnetloc.replace('${HTTP_HOST}', netloc)
            break

    if newnetloc:
        log("MATCH : " + netloc + " -> " + newnetloc)

        redir=''
        redirpath=None
        redirloc=None
        for k, v in redirs.items():
            redirpath = re.sub(k,v[0], path)
            if redirpath != path and not redir:
                redir = 1
                redirloc=v[1]
                break

        if redir and redirpath:
            redir='302:'
            log("REDIR : " + path + " -> " + redirpath)
            path=redirpath
            if redirloc: newnetloc=redirloc
            else: newnetloc=netloc

        if newnetloc.startswith('302:'):
            # sitemap redirect support 
            url = newnetloc
        else:
            url =  urlparse.urlunparse((redir+'http',newnetloc,path,parameters,query,fragment))
        return url

    # redirect to something we can match by a squid acl
    # this special non existing domain should be denied 
    # by squid with a http_reply_access line
    return "http://denypool/denyme"

log("reloading user redirector module")


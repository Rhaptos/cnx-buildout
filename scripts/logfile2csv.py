#!/usr/bin/env python

# Takes a zope instance log file (usually in var/log/instance.log ) and generates a CSV file

import re
import sys

MATCH_RE = re.compile(r"""
  ^(?P<date>\d{4}-\d{2}-\d{2})
  T(?P<time>\d{2}:\d{2}:\d{2})     \s+
   (?P<level>INFO|WARNING|ERROR)?  \s+
   (?P<issite>Zope\.SiteErrorLog\s+)?
   (?(issite)                          # If it's a site error, continue matching
     (?P<site_url>.*) \n
     (?P<site_trace>((.|\n)(?!\ \ \ -\ <FSControllerPythonScript))*) \n  # Store the stack trace up to (if it exists) the affected page template
     (?:\ \ \ -\ <FSControllerPythonScript\ at\ )?                       # discard the start of the page template line
     (?P<site_template>.*)
     (?P<site_before_error>((.|\n)(?!\w*Error: ))*) \n                   # Match all text (including newlines) until we see a "XxxXxxxxError:"
     (?P<site_error>.*)
   |                                   # Otherwise, try matching something else
     (?P<title>.*)
   )
   (?P<rest>(.|\n)*)                   # The rest of the entry
""", re.VERBOSE)

def escape(s):
  s = re.sub(r"\n", r"\\n", s)
  # s = re.sub(r"'", r"\'", s)
  s = re.sub(r'"', r'\"', s)
  return s

def csvline(l):
  s = ''
  for x in l:
    if len(s) > 0:
      s += ', '
    if x is not None:
      s += '"%s"' % escape(x)
  return s

# Build up a list of group names
names1 = [ None for _ in range(MATCH_RE.groups - 1) ] # Make an empty list
for k in MATCH_RE.groupindex:                         # Fill the list up
  names1[MATCH_RE.groupindex[k] - 1] = k
# remove any unnamed groups
names = []
for x in names1:
  if x:
    names.append(x) 

# Print header
print csvline(names)


# Load, parse, and print
loglines = open(sys.argv[1], "r").readlines()
logfile = "\n" + "".join(loglines)
logentries = logfile.split("\n------\n")

# Print each entry
for entry in logentries:
  m = MATCH_RE.match(entry)
  if m:
    print csvline(m.groups())

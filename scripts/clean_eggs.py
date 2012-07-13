#!/usr/bin/python
import imp
import sys
import os
import shutil

edir=os.path.join(os.getcwd(),'eggs')
i = imp.load_source('instance','bin/instance')
if i:
    current_eggs=[e for e in i.sys.path if e.startswith(edir)]
    all_eggs = [os.path.join(edir,e) for e in os.listdir(edir)]
    old_eggs = [e for e in all_eggs if e not in current_eggs]

    for e in old_eggs:
	if os.path.isdir(e):
            shutil.rmtree(e)
	else:
            os.unlink(e)

#!/bin/sh
# Makefile to control module PDF generation.
# 
# Author: Philip Schatz
# (C) 2011 Rice University
# 
# This software is subject to the provisions of the GNU Lesser General
# Public License Version 2.1 (LGPL).  See LICENSE.txt for details.
#

#PYTHON = /usr/bin/python2.4
#PRINT_DIR = /opt/printing
#HOST = http://localhost:8080
#COLLECTION_VERSION = latest
#PROJECT_NAME = The Enterprise Rhaptos Project
#PROJECT_SHORT_NAME = Rhaptos
#EPUB_DIR = /opt/enter-prise-rhaptos/buildout-trunk/src/Products.Print/Products/Print/epub

MAKEFILE=$EPUB_DIR/../printing/module_print.mak

if [ "." != ".${PRINT_STYLE}" ]; then

  DIR=$(pwd)
  cd ${EPUB_DIR}
  python2.4 -c "import collectiondbk2pdf; collectiondbk2pdf.__doStuffModule('temp-module-id', '${DIR}', '${PRINT_STYLE}');" > ${DIR}/module.pdf

else

  cp $MAKEFILE Makefile
  make -e module.pdf > log.txt
  cat module.log >> log.txt
  cat module.mxt >> log.txt
  ls -al * >> log.txt
  
  echo "Hello there. TODO for you %%EOF" >> log.txt
  #cp log.txt module.pdf

fi

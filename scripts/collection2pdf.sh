#! /bin/sh -v -x
#
# Makefile to control collection PDF generation.
# 
# Author: Philip Schatz
# (C) 2011 Rice University
# 
# This software is subject to the provisions of the GNU Lesser General
# Public License Version 2.1 (LGPL).  See LICENSE.txt for details.
#

#HOST = http://localhost:8080
#COLLECTION_VERSION = latest
#PROJECT_NAME = The Enterprise Rhaptos Project
#PROJECT_SHORT_NAME = Rhaptos
#EPUB_DIR = /opt/enterprise-rhaptos/instance/src/Products.RhaptosPrint/.../epub
#COLLECTION_ID=col10001

XSLTPROC=xsltproc
PRINT_STYLE_XSL=${EPUB_DIR}/xsl/collxml-print-style.xsl
FILESTORE=/var/www/files



COMPLETENAME=${FILESTORE}/${COLLECTION_ID}-${COLLECTION_VERSION}.complete.zip

if [ -e $COMPLETENAME ]; then
    echo "Found complete zip in filestore"
    unzip $COMPLETENAME
else
    echo "Downloading and unzipping the complete zip"
    wget --timeout=300 -O complete.zip ${HOST}/content/${COLLECTION_ID}/${COLLECTION_VERSION}/complete && unzip complete.zip 
fi
mv ${COLLECTION_ID}_${COLLECTION_VERSION}_complete/* . && rm -rf ${COLLECTION_ID}_${COLLECTION_VERSION}_complete

PRINT_STYLE=$(${XSLTPROC} ${PRINT_STYLE_XSL} collection.xml)

if [ "." != ".${PRINT_STYLE}" ]; then
  echo "Running new-style PDF generation with PRINT_STYLE=${PRINT_STYLE}"


  DIR=$(pwd)
  cd ${EPUB_DIR}
  # PYTHONPATH points to python2.4 PIL which causes problems when run using 2.5 so force 2.4
  # python collectiondbk2pdf.py -d ${DIR} -s ${PRINT_STYLE} ${DIR}/${COLLECTION_ID}.pdf
  python2.4 -c "import collectiondbk2pdf; collectiondbk2pdf.__doStuff('${DIR}', '${PRINT_STYLE}');" > ${DIR}/${COLLECTION_ID}.pdf

else
  echo "Running old-style PDF generation using latex"

  COMPLETENAME=${FILESTORE}/${COLLECTION_ID}-${COLLECTION_VERSION}.complete.zip
  if [ -e $COMPLETENAME ]; then
    echo "Found complete zip in filestore"
    unzip $COMPLETENAME
  else
    echo "Downloading and unzipping the complete zip"
    wget --timeout=300 -O complete.zip ${HOST}/content/${COLLECTION_ID}/${COLLECTION_VERSION}/complete && unzip complete.zip 
  fi

  mv ${COLLECTION_ID}_${COLLECTION_VERSION}_complete/* . && rm -rf ${COLLECTION_ID}_${COLLECTION_VERSION}_complete
  cp ${EPUB_DIR}/../printing/course_print.mak Makefile
  make -e ${COLLECTION_ID}.pdf
fi

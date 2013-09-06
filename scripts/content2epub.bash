#!/bin/bash -xv

# 1st arg is either "Connexions" or some other Portal title (rhaptos)
# 2nd arg is the id
# 3rd arg is the version
# 4th arg is the working directory
# 5th arg is the input zip file within the working directory
# 6th arg is the output zip file within the working directory
# 7th arg is the output epub file within the working directory
# 8th arg is the epub code directory 

CNX_OR_RHAPTOS=$1
ID=$2
VERSION=$3
WORKING_DIR=$4
COMPLETE_ZIP_FILE=${WORKING_DIR}/$5
OFFLINE_ZIP_FILENAME=$6
EPUB_FILE=${WORKING_DIR}/$7
EPUB_MOD_FILE=${EPUB_FILE}_MOD
EPUB_CODE_DIR=$8
STAGING_DIR=${WORKING_DIR}/staging

# XSLT files and epub assume this is the name of the OEBPS dir.
CONTENT_DIR_NAME=content

CONTENT_DIR=${STAGING_DIR}/${CONTENT_DIR_NAME}

EXIT_STATUS=0

[ -d ${STAGING_DIR} ] && rm -rf ${STAGING_DIR}
mkdir ${STAGING_DIR}

unzip -n ${COMPLETE_ZIP_FILE} -d ${STAGING_DIR} # which should create and populate $BUILD_DIR
EXIT_STATUS=$EXIT_STATUS || $?

# The complete zips contain a root folder with the collection/module id, so move the files out of that dir
EXTRA_DIR=$(cd ${STAGING_DIR}/* && pwd)
EXTRA_DIR_NAME=$(basename ${EXTRA_DIR})
mv ${EXTRA_DIR} ${CONTENT_DIR}

if [[ ${ID#col} = ${ID} ]]; then
    # module
    README_FILE=${EPUB_CODE_DIR}/static/README-MODULE-OFFLINE.txt
else
    # collection
    README_FILE=${EPUB_CODE_DIR}/static/README-COLLECTION-OFFLINE.txt
fi

# all the code lives there
cd $EPUB_CODE_DIR

CONTENT_ID=$(basename ${EXTRA_DIR})

# Generate 2 epub files 
bash $EPUB_CODE_DIR/scripts/module2epub.sh "$CNX_OR_RHAPTOS" $CONTENT_DIR $EPUB_FILE ${CONTENT_ID} $EPUB_CODE_DIR/xsl/dbk2epub.xsl $EPUB_CODE_DIR/static/content.css
EXIT_STATUS=$EXIT_STATUS || $?

bash $EPUB_CODE_DIR/scripts/module2epub.sh "$CNX_OR_RHAPTOS" $CONTENT_DIR $EPUB_MOD_FILE ${CONTENT_ID} $EPUB_CODE_DIR/xsl/dbk2html.xsl $EPUB_CODE_DIR/static/offline-zip-overrides.css --skip-dbk-generation
EXIT_STATUS=$EXIT_STATUS || $?



#cd to working directory
cd ${BUILD_DIR}
  
#unzip epubfile and complete zip file
unzip -n ${EPUB_MOD_FILE} -d ${STAGING_DIR}
EXIT_STATUS=$EXIT_STATUS || $?

#add README.txt
cp ${README_FILE} ${STAGING_DIR}/README.txt
EXIT_STATUS=$EXIT_STATUS || $?

#remove the epub metadata files
rm -rf ${STAGING_DIR}/META-INF
EXIT_STATUS=$EXIT_STATUS || $?
rm ${STAGING_DIR}/mimetype
EXIT_STATUS=$EXIT_STATUS || $?
rm ${CONTENT_DIR}/toc.ncx
EXIT_STATUS=$EXIT_STATUS || $?
rm ${CONTENT_DIR}/content.opf                                     
EXIT_STATUS=$EXIT_STATUS || $?                                

# For offline zips we use a "special" CSS, so include the base one
cp ${EPUB_CODE_DIR}/static/content.css ${CONTENT_DIR} 

#create offline zip
# For no good reason the script that calls this file expects the offline zip file to be in $WORKING_DIR/colxxx_1.xxx_complete/$OFFLINE_ZIP_FILENAME
mv ${STAGING_DIR} ${WORKING_DIR}/${EXTRA_DIR_NAME}
EXIT_STATUS=$EXIT_STATUS || $?
cd ${WORKING_DIR} && zip -r ${WORKING_DIR}/${OFFLINE_ZIP_FILENAME} ${EXTRA_DIR_NAME}
EXIT_STATUS=$EXIT_STATUS || $?

mv ${WORKING_DIR}/${OFFLINE_ZIP_FILENAME} ${WORKING_DIR}/${EXTRA_DIR_NAME}
EXIT_STATUS=$EXIT_STATUS || $?

exit $EXIT_STATUS


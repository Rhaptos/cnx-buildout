This overly complex buildout is being cleaned up a bit at a time, but
will probably be end-of-lifed before it's sane. Basic install intructions are:

Get python2.4 and virtualenv installed on your system
postgresql >= 8.3 (9.1 or 9.2 are fine)
configure postgresql to allow 'trust' access for unix doamin socket connections

git clone git@github.com:Rhaptos/cnx-buildout.git cnx-buildout
cd cnx-buildout
git checkout gitify
virtualenv -p /usr/bin/python2.4 .
. ./bin/activate
ln devel.cfg buildout.cfg
mkdir downloads
python bootstrap.py 
pip install simplejson==1.9.2
pip install lxml
bin/buildout 


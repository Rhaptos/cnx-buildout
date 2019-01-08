Container usage is as follows:

  docker-compose up -d

Container release notes:

  docker build --target foundation --tag openstax/legacy-cnx-foundation:latest .
  docker build --target foundation --tag openstax/legacy-cnx-zeo:latest .
  docker build --target web --tag openstax/legacy-cnx-web:latest .
  docker build --target pdf-gen --tag openstax/legacy-cnx-pdf-gen:latest .

------------------------------------------------------------------------------

This overly complex buildout is being cleaned up a bit at a time, but
will probably be end-of-lifed before it's sane. Basic install instructions are:

Get python2.4 and virtualenv installed on your system

postgresql >= 8.3 (9.1 or 9.2 are fine)
configure postgresql to allow 'trust' access for unix domain socket connections

git clone git@github.com:Rhaptos/cnx-buildout.git cnx-buildout
cd cnx-buildout
virtualenv -p /usr/bin/python2.4 .
. ./bin/activate
mkdir downloads
python bootstrap.py 
pip install simplejson==1.9.2
bin/buildout 
. bin/libs.sh
pip install lxml


Detailed install for Ubuntu 12.0.4.2 LTS server:

base install
configure access to hardy (yes hardy):

echo "deb http://us.archive.ubuntu.com/ubuntu/ hardy main" >/etc/apt/sources.list.d/hardy.list

apt-get update

apt-get install postgresql postresql-contrib libpq-dev openjdk-7-jre-headless
apt-get install python2.4-dev python-virtualenv make git libjpeg-dev libpng-dev build-essential

Modify postgresql config to allow trusted access on local domain sockets:

as root:
vi /etc/postgresql/9.1/main/pg_hba.conf

replace 'peer' w/ 'trust' in two places.

Back to regular user:

git clone git@github.com:Rhaptos/cnx-buildout.git cnx-buildout
cd cnx-buildout
virtualenv -p /usr/bin/python2.4 .
source bin/activate
mkdir downloads
python bootstrap.py 
pip install simplejson==1.9.2
bin/buildout 

source bin/libs.sh
pip install lxml

then:

bin/zeoserver start
bin/instance fg

Use browser to connect to http://localhost:8888/manage_main

login admin:admin

Use dropdown to add a 'Rhaptos Site'

Assign an id ('site' usually)
accept other defaults

you now have 'generic rhaptos' site at: http://localhost:8888/site

----------------------------------------------------------------------------
For cnx.org styles:
in management interface, go to portal_setup.
Select "Properties" tab (which should be this url: http://localhost:8888/site/portal_setup/manage_tool)

Select "Products.CNXPloneSite" from dropdown and "Update"
Select "Import" tab
Select CNXPloneSite Customization Policy
Scroll to bottom, click "Import selected steps"

Go back to http://localhost:8888/site

You should see cnx.org styled site.

-----------------------------------------------------------------------------

from the commandline, go to cnx-buildout

kill the 'bin/instance fg' (crtl-C)

rerun as daemon: 

bin/instance start

run: scripts/add_users.sh
This will install user[1234], org[12] and manager1. Each has the same username and password.

Congrats, you have a local devel install of cnx.org codebase.

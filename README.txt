This overly complex buildout is being cleaned up a bit at a time, but
will probably be end-of-lifed before it's sane. Basic install intructions are:

Get python2.4 and virtualenv installed on your system
postgresql >= 8.3 (9.1 or 9.2 are fine)
configure postgresql to allow 'trust' access for unix doamin socket connections

git clone git@github.com:Rhaptos/cnx-buildout.git cnx-buildout
cd cnx-buildout
virtualenv -p /usr/bin/python2.4 .
. ./bin/activate
ln devel.cfg buildout.cfg
mkdir downloads
python bootstrap.py 
pip install simplejson==1.9.2
pip install lxml
bin/buildout 

then:

bin/zeoserver start
bin/instance fg

Use browser to connect to http://localhost:8080/manage_main

login admin:admin

Use dropdown to add a 'Rhaptos Plone Site'

Assign an id (either'plone' or 'site' usually)
accept other defaults

in management interface, go to portal_setup.
Select "Properties" tab (which should be this url: http://localhost:8080/plone/portal_setup/manage_tool)

Select "Products.CNXPloneSite" from dropdown and "Update"
Select "Import" tab
Select CNXPloneSite Customization Policy
Scroll to bottom, click "Import selected steps"

Go back to http://localhost:8080/plone

from the commandline, go to cnx-buildout
run: scripts/add_users.sh
This will install user[1234], org[12] and manager1. Each has the same username and password.

Congrats, you have a local devel install of cnx.org codebase.





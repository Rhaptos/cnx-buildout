# -*- coding: iso-8859-15 -*-
"""ModuleCreation FunkLoad test

$Id: $
"""
import unittest
from funkload.FunkLoadTestCase import FunkLoadTestCase
#from webunit.utility import Upload
from funkload.utils import xmlrpc_get_credential

from base64 import encodestring
from urllib import quote as urlquote
from Cookie import Morsel
from os import urandom

def randstr():
    return encodestring(urandom(6)).strip()

class ModuleCreation(FunkLoadTestCase):
    """XXX

    This test use a configuration file ModuleCreation.conf.
    """

    def setUp(self):
        """Setting up test."""
        self.logd("setUp")
        self.server_url = self.conf_get('main', 'url')
        # XXX here you can setup the credential access like this
        credential_host = self.conf_get('credential', 'host')
        credential_port = self.conf_getInt('credential', 'port')
        self.login, self.password = xmlrpc_get_credential(credential_host,
                                                           credential_port,
                                                           'members')
        #self.login = 'siyavula'
        #self.password = 'local'

        # Set the zope cookie. This is a little evil but avoids having to
        # call the login page.
        morsel = Morsel()
        morsel.key = '__ac'
        morsel.value = morsel.coded_value = urlquote(
            encodestring('%s:%s' % (self.login, self.password)))
        self._browser.cookies = {
            'rhaptos': {
                '/': {
                    '__ac': morsel
                }
            }
        }

    def test_ModuleCreation(self):
        # The description should be set in the configuration file
        server_url = self.server_url
        # begin of test ---------------------------------------------

        self.get(server_url + "/mydashboard/cc_license?type_name=Module",
            description="Get /mydashboard/cc_license")

        response = self.post(server_url + "/mydashboard/cc_license", params=[
            ['agree', 'on'],
            ['next', 'Next >>'],
            ['license', 'http://creativecommons.org/licenses/by/3.0/'],
            ['type_name', 'Module'],
            ['form.submitted', '1']],
            description="Accept the license agreement")

        # portal_factory is used for this, get the location of the temporary
        # object
        head = response.getDOM().getByName('head')[0]
        base = head.getByName('base')[0]
        temp = base.getattr('href')

        self.get('%s/getXMLSelectVocab?method=getLanguageWithSubtypes&param=lang&value=en' % temp,
            description="GET getXMLSelectVocab")

        self.post('%s/content_title' % temp, params=[
            ['location', '__home__'],
            ['title', 'Test Module %s' % randstr()],
            ['master_language', 'en'],
            ['language', 'en'],
            ['subject:list', 'Mathematics and Statistics'],
            ['keywords:lines', 'key\r\nwords'],
            ['abstract', 'summary'],
            ['templatefolder_uid', 'dummy'],
            ['license', 'http://creativecommons.org/licenses/by/3.0/'],
            ['form.button.next', 'Next >>'],
            ['form.submitted', '1']],
            description="POST content_title")

        self.get('%s/module_eip_content' % temp,
                description='GET module_eip_content')

        self.get('%s/module_source_fragment?xpath=/' % temp,
                description='GET module_source_fragment /')

        self.post('%s/handleEipRequest' % temp, params=[
            ['action', 'update'],
            ['xpath', '/cnx:document[1]/cnx:content[1]/cnx:para[1]'],
            ['content', '<para xmlns="http://cnx.rice.edu/cnxml" xmlns:m="http://www.w3.org/1998/Math/MathML" xmlns:q="http://cnx.rice.edu/qml/1.0"  id="delete_me"><!-- Insert module text here -->\n  This is the module text</para>']],
            description='POST handleEipRequest')

        self.get('%s/module_source_fragment?xpath=/cnx:document[1]/cnx:content[1]/cnx:para[1]' % temp,
                description='GET module_source_fragment /cnx:document')

        #self.get('%s/module_publish' % temp, description='GET module_publish')

        #self.post('%s/module_publish' % temp, params=[
        #    ['message', 'new module'],
        #    ['publish', 'Publish'],
        #    ['form.submitted', '1']],
        #    description='POST module_publish')

        #self.post('%s/publishContent' % temp, params=[
        #    ['message', 'new module'],
        #    ['publish', 'Yes, Publish']],
        #    description='POST publishContent')

        # end of test -----------------------------------------------

    def tearDown(self):
        """Setting up test."""
        self.logd("tearDown.\n")


if __name__ in ('main', '__main__'):
    unittest.main()

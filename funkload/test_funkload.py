from funkload.FunkLoadTestCase import FunkLoadTestCase

class Funkload(FunkLoadTestCase):
    """This test uses a configuration file Funkload.conf."""

    def setUp(self):
        self.logd("setUp")
        self.server_url = self.conf_get('main', 'url')
        self.admin_username = self.conf_get('main', 'admin_username')
        self.admin_pwd = self.conf_get('main', 'admin_pwd')

    def test_www(self):
        server_url = self.server_url
        self.get(server_url, description="Get %s" %server_url)

    def tearDown(self):
        """Setting up test."""
        self.logd("tearDown.\n")

if __name__ in ('main', '__main__'):
    unittest.main()

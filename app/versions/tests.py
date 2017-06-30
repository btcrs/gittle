from pygit2 import Repository, GIT_FILEMODE_BLOB, GIT_FILEMODE_TREE, Signature
from django.test import TestCase
from django.test import Client
from versions.views import generate_directory
from time import time
import logging
import shutil
import json
import os

logger = logging.getLogger(__name__)
logging.disable(logging.CRITICAL)


class VersionsViewsTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        login_client = Client()
        login_data = {
            'username': 'rodrigo@wevolver.com',
            'password': '123456',
        }
        login = login_client.post('/login', json.dumps(login_data), content_type="application/json")
        body = json.loads(login.content)
        cls.app = 'testapp'
        cls.token = body['access_token']
        cls.user = body['user'].split('/')[-2]

    @classmethod
    def tearDownClass(cls):
        path = generate_directory('rodrigo')
        path = os.path.join('./repos', path, cls.app)
        if os.path.exists(path):
            shutil.rmtree(path)

    def test_path_generation(self):
        path = generate_directory('rodrigo')
        path_duplicate = generate_directory('rodrigo')
        alternate_path = generate_directory('testuser')
        self.assertEqual(path, path_duplicate)
        self.assertNotEqual(path, alternate_path)
        self.assertEqual(len(path.split('/')), 5)

    def test_create(self):
        response = self.client.get('/create/rodrigo/{}'.format(self.app), {'access_token': self.token, 'user_id': self.user})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Created at ./repos/rodrigo/{}'.format(self.app).encode() in response.content)

    def test_created_bare(self):
        path = generate_directory('rodrigo')
        path = os.path.join("./repos", path, self.app)
        repo = Repository(path)
        self.assertTrue(repo.is_bare)

    def test_list_projects(self):
        response = self.client.get('/rodrigo', {'access_token': self.token, 'user_id': self.user})
        self.assertTrue(self.app in json.loads(response.content)['data'])

    def test_add_files(self):
        pass

    def test_list_files(self):
        response = self.client.get('/rodrigo/{}'.format(self.app), {'access_token': self.token, 'user_id': self.user})
        self.assertEqual('readme.md', json.loads(response.content)['data'][0]['name'])

    def test_show_file(self):
        pass

    def test_permissions(self):
        pass

    def test_delete(self):
        pass
    #     response = self.client.get('/delete/rodrigo/{}'.format(self.app), {'access_token': self.token, 'user_id': self.user})
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTrue('Deleted at ./repos/rodrigo/{}'.format(self.app).encode() in response.content)

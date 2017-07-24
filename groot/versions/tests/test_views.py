from pygit2 import Repository, GIT_FILEMODE_BLOB, GIT_FILEMODE_TREE, Signature, IndexEntry
from django.test.utils import override_settings
from versions.views import generate_directory
from django.conf import settings
from django.test import TestCase
from django.test import Client
from functools import wraps
from time import time
import logging
import shutil
import base64
import json
import time
import os

logger = logging.getLogger(__name__)
logging.disable(logging.CRITICAL)


@override_settings(API_BASE=settings.TEST_API_BASE)
@override_settings(AUTH_BASE=settings.TEST_AUTH_BASE)
class VersionsViewsTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        login_client = Client()
        login_data = {
            'username': 'rodrigo@wevolver.com',
            'password': '123456',
        }
        login = login_client.post('/login', json.dumps(login_data), content_type="application/json")
        body = json.loads(login.content)
        cls.app = 'testit'
        cls.token = body['access_token']
        cls.username = 'rodrigo.trespalacios'
        cls.user = body['user'].split('/')[-2]

    @classmethod
    def tearDownClass(cls):
        path = generate_directory('rodrigo')
        path = os.path.join('./repos', path, cls.app)
        if os.path.exists(path):
            shutil.rmtree(path)

    def setUp(self):
        response = self.client.get('/create/{}/{}'.format(self.username, self.app), { 'user_id': self.user}, HTTP_AUTHORIZATION='Bearer {}'.format(self.token))
        print(response)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Created at ./repos/{}/{}'.format(self.username, self.app).encode() in response.content)

    def tearDown(self):
        response = self.client.get('/delete/{}/{}'.format(self.username, self.app), { 'user_id': self.user}, HTTP_AUTHORIZATION='Bearer {}'.format(self.token))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Deleted at ./repos/{}/{}'.format(self.username, self.app).encode() in response.content)

    def test_path_generation(self):
        path = generate_directory('rodrigo')
        path_duplicate = generate_directory('rodrigo')
        alternate_path = generate_directory('testuser')
        self.assertEqual(path, path_duplicate)
        self.assertNotEqual(path, alternate_path)
        self.assertEqual(len(path.split('/')), 5)

    def test_created_bare(self):
        path = generate_directory(self.username)
        path = os.path.join("./repos", path, self.app)
        repo = Repository(path)
        self.assertTrue(repo.is_bare)

    def test_add_files(self):
        with open('./secrets.json') as fp:
            response = self.client.post('/{}/{}/upload?user_id={}'.format(self.username, self.app, self.user), {'file': fp, 'path': 'test.json'}, HTTP_AUTHORIZATION='Bearer {}'.format(self.token))
        self.assertTrue(b'File uploaded' in response.content)

    def test_list_files(self):
        with open('./secrets.json') as fp:
            self.client.post('/{}/{}/upload?user_id={}'.format(self.username, self.app, self.user), {'file': fp, 'path': 'test.json'}, HTTP_AUTHORIZATION='Bearer {}'.format(self.token))
        response = self.client.get('/{}/{}'.format(self.username, self.app), {'user_id': self.user},HTTP_AUTHORIZATION='Bearer {}'.format(self.token))
        self.assertEqual('readme.md', json.loads(response.content)['data'][0]['name'])
        self.assertEqual('test.json', json.loads(response.content)['data'][1]['name'])

    def test_show_file(self):
        response = self.client.get('/{}/{}'.format(self.username, self.app), {'user_id': self.user}, HTTP_AUTHORIZATION='Bearer {}'.format(self.token))
        oid = json.loads(response.content)['data'][0]['oid']
        response = self.client.get('/{}/{}/{}'.format(self.username, self.app, oid), {'user_id': self.user}, HTTP_AUTHORIZATION='Bearer {}'.format(self.token))
        oid = json.loads(response.content)['data'][0]['oid']
        response = self.client.get('/{}/{}/{}'.format(self.username, self.app, oid), {'user_id': self.user} , HTTP_AUTHORIZATION='Bearer {}'.format(self.token))
        self.assertEqual(str(base64.b64encode(b'Readme File Commitfed Automatically Upon Creation'), 'utf-8'), json.loads(response.content)['file'])

    def test_permissions(self):
        pass

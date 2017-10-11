from pygit2 import Repository, GIT_FILEMODE_BLOB, GIT_FILEMODE_TREE, Signature, IndexEntry
from django.test.utils import override_settings
from welder.versions.porcelain import generate_directory
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

settings.DEBUG = True
class VersionsViewsTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.app = 'testit'
        cls.username = 'wevolver'
        cls.user = 'wevolver'

    @classmethod
    def tearDownClass(cls):
        path = generate_directory('wevolver')
        path = os.path.join('./repos', path, cls.app)
        if os.path.exists(path):
            shutil.rmtree(path)

    def setUp(self):
        response = self.client.post('/{}/{}/create'.format(self.username, self.app), { 'user_id': self.user})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Created at ./repos/{}/{}'.format(self.username, self.app).encode() in response.content)

    def tearDown(self):
        response = self.client.post('/{}/{}/delete'.format(self.username, self.app), { 'user_id': self.user})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Deleted at ./repos/{}/{}'.format(self.username, self.app).encode() in response.content)

    def test_path_generation(self):
        path = generate_directory('wevolver')
        path_duplicate = generate_directory('wevolver')
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
        with open('./env.json') as fp:
            response = self.client.post('/{}/{}/upload?user_id={}&path={}'.format(self.username, self.app, self.user, "test,json"), {'file': fp, 'path': 'test.json'})
        self.assertTrue(b'Files uploaded' in response.content)

    def test_list_files(self):
        with open('./env.json') as fp:
            self.client.post('/{}/{}/upload?user_id={}&path=test.json'.format(self.username, self.app, self.user), {'file': fp, 'path': 'test.json'})
        response = self.client.get('/{}/{}?path=test.json'.format(self.username, self.app), {'user_id': self.user, 'path': 'test.json'})
        self.assertEqual('env.json', json.loads(response.content)['tree']['data'][0]['name'])

    def test_show_file(self):
        response = self.client.get('/{}/{}?path=test/'.format(self.username, self.app), {'user_id': self.user, 'path': "readme.md"})
        self.assertEqual(str(base64.b64encode(b"#testit \nThis is where you should document your project  \n### Getting Started"), 'utf-8'), json.loads(response.content)['file'])

    def test_permissions(self):
        pass

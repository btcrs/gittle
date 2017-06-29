from pygit2 import Repository, GIT_FILEMODE_BLOB, GIT_FILEMODE_TREE, Signature
from django.test import TestCase
from django.test import Client
from versions.views import generate_directory
from time import time
import logging
import shutil
import json
import os

logging.disable(logging.NOTSET)

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
        cls.token = body['access_token']
        cls.user = body['user'].split('/')[-2]


    def tearDownClass():
        path = generate_directory('rodrigo')
        path = os.path.join('./repos', path, 'testapp')
        if os.path.exists(path):
            shutil.rmtree(path)

    def create_directory_structure(self):
        path = generate_directory('rodrigo')
        path = os.path.join('./repos', path, 'testapp')
        repo = Repository(path)
        one = repo.create_blob('test file')
        two = repo.create_blob('test file 2')
        three = repo.create_blob('test file 3')
        tree1 = repo.TreeBuilder()
        tree1.insert('testfile1.txt', one, GIT_FILEMODE_BLOB)
        tree1.insert('testfile2.txt', two, GIT_FILEMODE_BLOB)
        tree2 = repo.TreeBuilder()
        tree3 = repo.TreeBuilder()
        tree3.insert('testfile3.txt', three, GIT_FILEMODE_BLOB)
        tree2.insert('tree3', tree3.write(), GIT_FILEMODE_TREE)
        tree1.insert('tree2', tree2.write(), GIT_FILEMODE_TREE)
        precommit = tree1.write()
        signature = Signature('Tester', 'test@example.com', int(time()), 0)
        commit = repo.create_commit('refs/heads/master', signature, signature, 'Test commit with pygit2', precommit, [])

    def test_create(self):
        response = self.client.get('/create/rodrigo/testapp', {'access_token': self.token, 'user_id': self.user})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Created at ./repos/rodrigo/testapp' in response.content)

    def test_created_bare(self):
        path = generate_directory('rodrigo')
        path = os.path.join("./repos", path, 'testapp')
        repo = Repository(path)
        self.assertTrue(repo.is_bare)

    # def test_list_files(self):
    #     self.create_directory_structure()
    #     response = self.client.get('/rodrigo/testapp')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTrue(b'testfile1.txt' in response.content)
    #     self.assertTrue(b'testfile2.txt' in response.content)
    #     self.assertTrue(b'tree2' in response.content)

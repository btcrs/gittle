from django.test import TestCase
from pygit2 import repository
import os

class VersionsViewsTestCase(TestCase):
    def test_create(self):
        response = self.client.get('/create/testuser/testapp')
        print(response)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Created at ./repos/testuser/testapp' in response.context)

    def test_created_bare(self):
        path = os.path.join("./repos", testuser, testapp, '.git')
        repo = Repository(path)
        self.assertTrue(repo.is_bare)

    def test_list_files(self):
        path = os.path.join("./repos", testuser, testapp, '.git')
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
        response = self.client.get('/testuser/testapp')
        self.assertEqual(response.status_code, 200)

from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import PermissionDenied
from django.conf import settings

from pygit2 import Repository, GIT_FILEMODE_BLOB, GIT_FILEMODE_TREE, Signature
from .decorators import git_access_required, wevolver_auth, has_permission_to
from .git import GitResponse
from functools import wraps
from urllib import parse
from time import time
from enum import Enum

import requests
import logging
import os.path
import tarfile
import hashlib
import base64
import pygit2
import urllib
import shutil
import json
import os

logger = logging.getLogger(__name__)

class Actions(Enum):
    advertisement = 'advertisement'
    result = 'result'

@require_http_methods(["POST"])
def login(request):
    post = json.loads(request.body)
    body = {'username': post['username'], 'password': post['password'], 'grant_type': 'password'}
    url = "{}/proxy-client-token".format(settings.AUTH_BASE)
    response = requests.post(url, data=body)
    return HttpResponse(response.text)

def generate_directory(username):
    """
    https://github.com/blog/117-scaling-lesson-23742
    """
    hash = hashlib.md5();
    hash.update(username.encode('utf-8'))
    hash = hash.hexdigest()
    a, b, c, d, *rest= hash[0], hash[1:3], hash[3:5], hash[5:7]
    return os.path.join(a, b, c, d, username)

def parse_file_tree(tree):
    """ Parses the repository's tree structure

    Returns a list of objects and metadata in the top level of the provided tree

    Args:
        tree (Tree): The most recent commit tree.

    Returns:
        dict: A list of all files in the top level of the provided tree.
    """

    logging.debug("Given tree is type {}".format(type(tree)))
    return {'data': [{'name': str(node.name), 'type': str(node.type), 'oid': str(node.id)} for node in tree]}

@wevolver_auth
def create(request, user, project_name):
    """ Creates a bare repository with the provided name

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.

    Returns:
        HttpResponse: A message indicating the success or failure of the create
    """

    directory = generate_directory(user)
    if not os.path.exists(os.path.join('./repos', directory)):
        os.makedirs(os.path.join('./repos', directory))

    path = os.path.join("./repos", directory, project_name)
    repo = pygit2.init_repository(path, True)
    readme = repo.create_blob('#Hello, World!')
    master = repo.TreeBuilder()
    master.insert('readme.md', readme, GIT_FILEMODE_BLOB)
    precommit = master.write()
    signature = Signature(user, '{}@example.com'.format(user), int(time()), 0)
    commit = repo.create_commit('refs/heads/master', signature, signature, 'Test commit with pygit2', precommit, [])
    return HttpResponse("Created at ./repos/{}/{}".format(user, project_name))

@wevolver_auth
@has_permission_to('write')
def delete(request, user, project_name):
    """ Deletes the repository with the provided name

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.

    Returns:
        HttpResponse: A message indicating the success or failure of the delete
    """

    directory = generate_directory(user)
    if os.path.exists(os.path.join('./repos', directory)):
        path = os.path.join("./repos", directory, project_name)
        shutil.rmtree(path)
    return HttpResponse("Deleted repository at {}".format(path))

@wevolver_auth
@has_permission_to('read')
def show_file(request, user, project_name, oid):
    """ Grabs and returns a single file from a user's repository

    if the requested object is a tree the function parses it intstead
    of returning blindly.

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.
        oid (string): The hash of the blob.

    Returns:
        JsonResponse: An object with the requested file's data
    """


    directory = generate_directory(user)
    if os.path.exists(os.path.join('./repos', directory)):
        repo = pygit2.Repository(os.path.join('./repos', directory, project_name))
        blob = repo.get(oid)
        if type(blob) == pygit2.Tree:
            return JsonResponse(parse_file_tree(blob))
    return JsonResponse({'file': str(base64.b64encode(blob.data), 'utf-8')})

@wevolver_auth
@has_permission_to('read')
def list_files(request, user, project_name):
    """ Grabs and returns all files from a user's repository

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.

    Returns:
        JsonResponse: An object with the requested repository's files
    """

    directory = generate_directory(user)
    if os.path.exists(os.path.join('./repos', directory)):
        repo = pygit2.Repository(os.path.join("./repos", directory, project_name))
        tree = repo.revparse_single('master').tree
    return JsonResponse(parse_file_tree(tree))

@wevolver_auth
def list_repos(request, user):
    """ Grabs and returns all of a user's repository

    Args:
        user (string): The user's name.

    Returns:
        JsonResponse: An object with the requested user's repositories
    """

    directory = generate_directory(user)
    path = os.path.join("./repos", directory)
    directories = [name for name in os.listdir(path)] if os.path.exists(path) else []
    return JsonResponse({'data': directories})


def write_file_to_index(repo, blob, path):
    # read contents of index fil
    index = repo.index
    index.read()

    # add blog as an entry to the index
    entry = pygit2.IndexEntry(path, blob, GIT_FILEMODE_BLOB)
    index.add(entry)

    #  write index object to index file
    index.write()

    # generate new commit, the function takes a tree so we generate one from the new index file.
    # TODO: Signature should be the real user's email.
    signature = Signature('Tester', 'test@example.com', int(time()), 0)
    commit = repo.create_commit('refs/heads/master', signature, signature, 'Test commit with pygit2', index.write_tree(), [repo.head.get_object().hex])



@wevolver_auth
@require_http_methods(["POST"])
def create_new_folder(request, user, project_name):
    """ Commits a single file to a specific path to create new folder in tree

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.

    Body:
        File
        path

    Returns:
        JsonResponse: An object
    """
    directory = generate_directory(user)
    post = json.loads(request.body)
    path = post['path'] + 'readme.md'
    repo = pygit2.Repository(os.path.join("./repos", directory, project_name))

    blob = repo.create_blob('Readme File Commitfed Automatically Upon Creation')
    write_file_to_index(repo, blob, path)

    return JsonResponse({'message': 'Folder Created'})

@wevolver_auth
@require_http_methods(["POST"])
def upload_file(request, user, project_name):
    """ Uploads and commits a single file to a specific path in a user's repository

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.

    Body:
        File
        path

    Returns:
        JsonResponse: An object
    """
    # path to upload location in repo.
    directory = generate_directory(user)
    path = request.POST['path'] + '/'

    repo = pygit2.Repository(os.path.join("./repos", directory, project_name))

    if request.FILES['file']:
        path = path + request.FILES['file'].name;

        # create file blob from file or generate one if there are none to create empty folder
        blob = repo.create_blob(request.FILES['file'].read())

        write_file_to_index(repo, blob, path)
        # # read contents of index fil
        # index = repo.index
        # index.read()

        # # add blog as an entry to the index
        # entry = pygit2.IndexEntry(path + request.FILES['file'].name, blob, GIT_FILEMODE_BLOB)
        # index.add(entry)

        # #  write index object to index file
        # index.write()

        # # generate new commit, the function takes a tree so we generate one from the new index file.
        # # TODO: Signature should be the real user's email.
        # signature = Signature('Tester', 'test@example.com', int(time()), 0)
        # commit = repo.create_commit('refs/heads/master', signature, signature, 'Test commit with pygit2', index.write_tree(), [repo.head.get_object().hex])

    return JsonResponse({'message': 'File uploaded'})

@wevolver_auth
@has_permission_to('read')
def download_archive(request, user, project_name):
    """ Grabs and returns all of a user's repository as a tarball

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.

    Returns:
        JsonResponse: An object with the requested user's repository as a tarball
    """

    filename = project_name + '.tar'
    response = HttpResponse(content_type='application/x-gzip')
    response['Content-Disposition'] = 'attachment; filename=' + filename

    directory = generate_directory(user)
    with tarfile.open(fileobj=response, mode='w') as archive:
        repo = pygit2.Repository(os.path.join("./repos", directory, project_name))
        repo.write_archive(repo.head.target, archive)

    return response


@git_access_required
@has_permission_to('read')
def info_refs(request, user, project_name):
    """ Initiates a handshake for a smart HTTP connection

    https://git-scm.com/book/en/v2/Git-Internals-Transfer-Protocols

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.

    Returns:
        GitResponse: A HttpResponse with the proper headers and payload needed by git.
    """

    directory = generate_directory(user)
    requested_repo = os.path.join('./repos', directory, project_name)
    response = GitResponse(service=request.GET['service'], action=Actions.advertisement.value,
                           repository=requested_repo, data=None)
    return response.get_http_info_refs()


@git_access_required
@has_permission_to('write')
def service_rpc(request, user, project_name):
    """ Calls the Git commands to pull or push data from the server depending on the received service.

    https://git-scm.com/book/en/v2/Git-Internals-Transfer-Protocols

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.

    Returns:
        GitResponse: An HttpResponse that indicates success or failure and may include the requested packfile
    """

    directory = generate_directory(user)
    requested_repo = os.path.join('./repos', directory, project_name)
    response = GitResponse(service=request.path_info.split('/')[-1], action=Actions.result.value,
                           repository=requested_repo, data=request.body)
    return response.get_http_service_rpc()

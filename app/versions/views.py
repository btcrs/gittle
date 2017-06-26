from pygit2 import Repository, GIT_FILEMODE_BLOB, GIT_FILEMODE_TREE, Signature
from django.http import HttpResponse, JsonResponse
from .git import GitResponse
from time import time
from enum import Enum
import logging
import os.path
import pygit2
import shutil
import json
import os

logger = logging.getLogger(__name__)

class Actions(Enum):
    advertisement = 'advertisement'
    result = 'result'

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

def create(request, user, project_name):
    """ Creates a bare repository with the provided name

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.

    Returns:
        HttpResponse: A message indicating the success or failure of the create
    """

    path = os.path.join("./repos", user, project_name)
    repo = pygit2.init_repository(path, True)
    readme = repo.create_blob('#Hello, World!')
    master = repo.TreeBuilder()
    master.insert('readme.md', readme, GIT_FILEMODE_BLOB)
    precommit = master.write()
    signature = Signature(user, '{}@example.com'.format(user), int(time()), 0)
    commit = repo.create_commit('refs/heads/master', signature, signature, 'Test commit with pygit2', precommit, [])
    return HttpResponse("Created at {}".format(path))

def delete(request, user, project_name):
    """ Deletes the repository with the provided name

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.

    Returns:
        HttpResponse: A message indicating the success or failure of the delete
    """

    path = os.path.join("./repos", user, project_name)
    shutil.rmtree(path)
    return HttpResponse("Deleted repository at {}".format(path))

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

    repo = pygit2.Repository(os.path.join('./repos', user, project_name))
    blob = repo.get(oid)
    if type(blob) == pygit2.Tree:
        return JsonResponse(parse_file_tree(blob))
    return JsonResponse({'file': str(blob.data, 'utf-8')})

def list_files(request, user, project_name):
    """ Grabs and returns all files from a user's repository

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.

    Returns:
        JsonResponse: An object with the requested repository's files
    """

    repo = pygit2.Repository(os.path.join("./repos", user, project_name))
    tree = repo.revparse_single('master').tree
    return JsonResponse(parse_file_tree(tree))

def list_repos(request, user):
    """ Grabs and returns all of a user's repository

    Args:
        user (string): The user's name.

    Returns:
        JsonResponse: An object with the requested user's repositories
    """

    path = os.path.join("./repos", user)
    directories = [name for name in os.listdir(path)]
    return JsonResponse({'data': directories})

def info_refs(request, user, project_name):
    """ Initiates a handshake for a smart HTTP connection

    https://git-scm.com/book/en/v2/Git-Internals-Transfer-Protocols

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.

    Returns:
        GitResponse: A HttpResponse with the proper headers and payload needed by git.
    """

    requested_repo = os.path.join('./repos', user, project_name)
    response = GitResponse(service=request.GET['service'], action=Actions.advertisement.value,
                           repository=requested_repo, data=None)
    return response.get_http_info_refs()

def service_rpc(request, user, project_name):
    """ Calls the Git commands to pull or push data from the server depending on the received service.

    https://git-scm.com/book/en/v2/Git-Internals-Transfer-Protocols

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.

    Returns:
        GitResponse: An HttpResponse that indicates success or failure and may include the requested packfile
    """

    requested_repo = os.path.join('./repos', user, project_name)
    response = GitResponse(service=request.path_info.split('/')[-1], action=Actions.result.value,
                           repository=requested_repo, data=request.body)
    return response.get_http_service_rpc()

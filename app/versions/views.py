from pygit2 import Repository, GIT_FILEMODE_BLOB, GIT_FILEMODE_TREE, Signature
from versions.decorators import git_access_required, requires_permission_to
from wsgiref.util import FileWrapper
from versions.git import GitResponse
from functools import wraps
from urllib import parse
from io import BytesIO
from time import time
from enum import Enum

from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.http import StreamingHttpResponse
from django.conf import settings

import mimetypes
import tokenlib
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
import csv
import os

logger = logging.getLogger(__name__)

class Actions(Enum):
    advertisement = 'advertisement'
    result = 'result'

def flatten(tree, repo):
    flattened = []
    for entry in tree:
        if entry.type == 'tree':
            flattened.extend(flatten(repo[entry.id], repo))
        else:
            flattened.append(entry)
    return flattened

@requires_permission_to('read')
def render_file(request, user, project_name, permissions_token):
    path = request.GET.get('path').rstrip('/')
    directory = generate_directory(user)
    if os.path.exists(os.path.join('./repos', directory)):
        repo = pygit2.Repository(os.path.join('./repos', directory, project_name))
        git_tree, git_blob = walk_tree(repo, path)
        parsed_file = None
        if type(git_blob) == pygit2.Blob:
            parsed_file = str(base64.b64encode(git_blob.data), 'utf-8')
        chunk_size = 8192
        filelike = FileWrapper(BytesIO(git_blob.data), chunk_size)
        response = StreamingHttpResponse(filelike,
                               content_type=mimetypes.guess_type(path)[0])
        response['Content-Length'] = len(git_blob.data)
        response['Permissions'] = permissions_token
        # response['Content-Disposition'] = "attachment; filename=%s" % path
        return response

def download_file(request, user, project_name):
    path = request.GET.get('path').rstrip('/')
    directory = generate_directory(user)
    if os.path.exists(os.path.join('./repos', directory)):
        repo = pygit2.Repository(os.path.join('./repos', directory, project_name))
        git_tree, git_blob = walk_tree(repo, path)
        parsed_file = None
        if type(git_blob) == pygit2.Blob:
            parsed_file = str(base64.b64encode(git_blob.data), 'utf-8')
        chunk_size = 8192
        filelike = FileWrapper(BytesIO(git_blob.data), chunk_size)
        response = StreamingHttpResponse(filelike,
                               content_type=mimetypes.guess_type(path)[0])
        response['Content-Length'] = len(git_blob.data)
        response['Content-Disposition'] = "attachment; filename=%s" % path
        return response


@requires_permission_to('read')
def list_bom(request, user, project_name, permissions_token):
    directory = generate_directory(user)
    if os.path.exists(os.path.join('./repos', directory)):
        repo = pygit2.Repository(os.path.join('./repos', directory, project_name))
        tree = (repo.revparse_single('master').tree)
        blobs = flatten(tree, repo)
        data = ''
        for b in [blob for blob in blobs if blob.name == 'bom.csv']:
            data += str(repo[b.id].data, 'utf-8')
        response = HttpResponse(data)
    else:
        response = HttpResponse('Failed')
    response['Permissions'] = permissions_token
    return response



@require_http_methods(["POST"])
def login(request):
    """ Logs the user in and sets the token

    Returns:
        HttpResponse: An object containing all session metadata
    """
    post = json.loads(request.body)
    body = {'username': post['username'], 'password': post['password'], 'grant_type': 'password'}
    url = "{}/proxy-client-token".format(settings.AUTH_BASE)
    response = requests.post(url, data=body)
    return HttpResponse(response.text)

def generate_directory(username):
    """ Generates a unique directory structure for the project

    https://github.com/blog/117-scaling-lesson-23742

    Returns:
        Path (str): The unique path as a string
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

    return {'data': [{'name': str(node.name), 'type': str(node.type), 'oid': str(node.id)} for node in tree]}

@requires_permission_to("create")
def create(request, user, project_name, permissions_token):
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

    message = "Initial Commit - Automated"
    comitter = pygit2.Signature('Wevolver', 'Wevolver')
    parents = []

    tree = repo.TreeBuilder()
    readme = "#{} \nThis is where you should document your project  \n### Getting Started".format(project_name)
    blob = repo.create_blob(readme)
    tree.insert('readme.md', blob, GIT_FILEMODE_BLOB)

    sha = repo.create_commit('HEAD',
                             comitter, comitter, message,
                             tree.write(), [])

    return HttpResponse("Created at ./repos/{}/{}".format(user, project_name))

@requires_permission_to('write')
def delete(request, user, project_name, permissions_token):
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
    response = HttpResponse("Deleted at ./repos/{}/{}".format(user, project_name))
    response['Permissions'] = permissions_token
    return response

def walk_tree(repo, full_path):
    current_object = repo.revparse_single('master').tree
    locations = full_path.split('/')
    if locations[0] == "":
        locations = []
    blob = None
    for location in locations:
        next_object = current_object.__getitem__(location)
        temp_object = current_object
        current_object = repo.get(next_object.id)
        if type(current_object) == pygit2.Blob:
            blob = current_object
            current_object = temp_object
    return current_object, blob


@requires_permission_to('read')
def show_file(request, user, project_name, permissions_token):
    """ Grabs and returns a single file or a tree from a user's repository

    if the requested object is a tree the function parses it intstead
    of returning blindly.

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.
        oid (string): The hash of the blob.

    Returns:
        JsonResponse: An object with the requested file's data
    """
    path = request.GET.get('path').rstrip('/')
    directory = generate_directory(user)
    if os.path.exists(os.path.join('./repos', directory)):
        repo = pygit2.Repository(os.path.join('./repos', directory, project_name))
        git_tree, git_blob = walk_tree(repo, path)
        parsed_tree = None
        parsed_file = None
        if type(git_tree) == pygit2.Tree:
            parsed_tree = parse_file_tree(git_tree)
        if type(git_blob) == pygit2.Blob:
            parsed_file = str(base64.b64encode(git_blob.data), 'utf-8')

        response = JsonResponse({'file': parsed_file, 'tree': parsed_tree})
    else:
        response = JsonResponse({'file': 'None', 'tree': 'None'})
    response['Permissions'] = permissions_token
    return response

def add_blobs_to_tree(previous_commit_tree, repo, blobs, path):
    current_tree = previous_commit_tree
    trees = []

    if path[0] != '':
        for location in path:
            try:
                next_tree_entry = current_tree.__getitem__(location)
                current_tree = repo.get(next_tree_entry.id)
            except:
                current_tree = False
            trees.append(current_tree)

        is_tree = trees[-1]
        current_tree_builder = repo.TreeBuilder(trees[-1]) if is_tree else repo.TreeBuilder()
        for blob, name in blobs:
            current_tree_builder.insert(name, blob, GIT_FILEMODE_BLOB)

        for index in range(len(path) - 1, 0, -1):
            previous_tree_builder = current_tree_builder
            is_tree = trees[index - 1]
            current_tree_builder = repo.TreeBuilder(is_tree) if is_tree else repo.TreeBuilder()
            current_tree_builder.insert(path[index], previous_tree_builder.write(), GIT_FILEMODE_TREE)

        previous_commit_tree_builder = repo.TreeBuilder(previous_commit_tree)
        previous_commit_tree_builder.insert(path[0], current_tree_builder.write(), GIT_FILEMODE_TREE)
        return previous_commit_tree_builder.write()
    else:
        previous_commit_tree_builder = repo.TreeBuilder(previous_commit_tree)
        for blob, name in blobs:
            previous_commit_tree_builder.insert(name, blob, GIT_FILEMODE_BLOB)
        return previous_commit_tree_builder.write()

def commit_tree(repo, newTree):
    signature = Signature('Tester', 'test@example.com', int(time()), 0)
    commit = repo.create_commit(repo.head.name, signature, signature, 'Test commit with pygit2', newTree, [repo.head.peel().id])

def commit_blob(repo, blob, path, name='readme.md'):
    previous_commit_tree = repo.revparse_single('master').tree
    newTree = add_blobs_to_tree(previous_commit_tree, repo, [(blob, name)], path)
    if newTree:
        commit_tree(repo, newTree)


@require_http_methods(["POST"])
@requires_permission_to("write")
def create_new_folder(request, user, project_name, permissions_token):
    """ Commits a single file to a specific path to create new folder in tree

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.

    Returns:
        JsonResponse: An object
    """

    directory = generate_directory(user)
    post = json.loads(request.body)
    path = post['path'].lstrip('/').rstrip('/')
    repo = pygit2.Repository(os.path.join("./repos", directory, project_name))
    blob = "#{} \nThis is where you should document your project  \n### Getting Started".format(project_name)
    commit_blob(repo, blob, path.split('/'), 'readme.md')
    response = JsonResponse({'message': 'Folder Created'})
    response['Permissions'] = permissions_token
    return response


@require_http_methods(["POST"])
@requires_permission_to("write")
def upload_file(request, user, project_name, permissions_token):
    """ Uploads and commits a single file to a specific path in a user's repository

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.

    Returns:
        JsonResponse: An object
    """
    directory = generate_directory(user)
    path = request.GET.get('path').rstrip('/')
    repo = pygit2.Repository(os.path.join("./repos", directory, project_name))

    if request.FILES:
        old_commit_tree = repo.revparse_single('master').tree
        blobs = []
        for key, file in request.FILES.items():
            blob = repo.create_blob(file.read())
            blobs.append((blob, file.name))

        new_commit_tree = add_blobs_to_tree(old_commit_tree, repo, blobs, path.split('/'))
        commit_tree(repo, new_commit_tree)

    response = JsonResponse({'message': 'Files uploaded'})
    response['Permissions'] = permissions_token
    return response


@requires_permission_to('read')
def get_archive_token(request, user, project_name, permissions_token):
    """ Return a fast expiration token to allow downlaod of archive

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.

    Returns:
        JsonResponse: An object with the archive download token
    """
    token = tokenlib.make_token({"project_name": project_name}, timeout=1, secret=settings.TOKEN_SECRET)
    response = JsonResponse({'token': token})
    response['Permissions'] = permissions_token
    return response

def download_archive(request, user, project_name):
    """ Grabs and returns all of a user's repository as a tarball

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.

    Returns:
        JsonResponse: An object with the requested user's repository as a tarball
    """
    token = request.GET.get("token")
    if token:
        try:
            parsed_token = tokenlib.parse_token(token, secret=settings.TOKEN_SECRET)
        except:
            raise PermissionDenied
        else:
            filename = project_name + '.tar'
            response = HttpResponse(content_type='application/x-gzip')
            response['Content-Disposition'] = 'attachment; filename=' + filename

            directory = generate_directory(user)
            with tarfile.open(fileobj=response, mode='w') as archive:
                repo = pygit2.Repository(os.path.join("./repos", directory, project_name))
                repo.write_archive(repo.head.target, archive)
            return response
    else:
        raise PermissionDenied


@git_access_required
@requires_permission_to('read')
def info_refs(request, user, project_name, permissions_token):
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
@requires_permission_to('read')
def upload_pack(request, user, project_name, access_token=None):
    """ Calls service_rpc assuming the user is authenicated and has read permissions """

    return service_rpc(user, project_name, request.path_info.split('/')[-1], request.body)

@git_access_required
@requires_permission_to('write')
def receive_pack(request, user, project_name, access_token=None):
    """ Calls service_rpc assuming the user is authenicated and has write permissions """

    return service_rpc(user, project_name, request.path_info.split('/')[-1], request.body)

def service_rpc(user, project_name, request_service, request_body):
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
    response = GitResponse(service=request_service, action=Actions.result.value,
                           repository=requested_repo, data=request_body)
    return response.get_http_service_rpc()

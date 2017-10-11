from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.http import StreamingHttpResponse
from django.http import HttpResponseBadRequest
from django.conf import settings

from gittle.versions import porcelain
from gittle.versions.git import GitResponse

from wsgiref.util import FileWrapper
from io import BytesIO
from time import time
from enum import Enum
import mimetypes
import tokenlib
import logging
import tarfile
import base64
import pygit2
import shutil
import json
import os

logger = logging.getLogger(__name__)

class Actions(Enum):
    advertisement = 'advertisement'
    result = 'result'

@require_http_methods(["GET"])
def info_refs(request, user, project_name):
    """ Initiates a handshake for a smart HTTP connection

    https://git-scm.com/book/en/v2/Git-Internals-Transfer-Protocols

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.

    Returns:
        GitResponse: A HttpResponse with the proper headers and payload needed by git.
    """

    directory = porcelain.generate_directory(user)
    requested_repo = os.path.join('./repos', directory, project_name)
    response = GitResponse(service=request.GET['service'], action=Actions.advertisement.value,
                           repository=requested_repo, data=None)
    return response.get_http_info_refs()

@permissions.requires_git_permission_to('read')
def upload_pack(request, user, project_name):
    """ Calls service_rpc assuming the user is authenticated and has read permissions """

    return service_rpc(user, project_name, request.path_info.split('/')[-1], request.body)

@permissions.requires_git_permission_to('write')
def receive_pack(request, user, project_name):
    """ Calls service_rpc assuming the user is authenticated and has write permissions """

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

    directory = porcelain.generate_directory(user)
    requested_repo = os.path.join('./repos', directory, project_name)
    response = GitResponse(service=request_service, action=Actions.result.value,
                           repository=requested_repo, data=request_body)
    return response.get_http_service_rpc()

@require_http_methods(["GET"])
def read_tree(request, user, project_name, permissions_token):
    """ Grabs and returns a single file or a tree from a user's repository

        The requested tree is first parsed into JSON.

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.
        permissions_token (string): JWT token signed by Wevolver.

    Returns:
        JsonResponse: An object with the requested tree as JSON
    """
    try:
        path = request.GET.get('path').rstrip('/').lstrip('/')
        directory = porcelain.generate_directory(user)
        print(directory)
        print(project_name)
        repo = pygit2.Repository(os.path.join('./repos', directory, project_name))
        git_tree, git_blob = porcelain.walk_tree(repo, path)
        parsed_tree = None
        parsed_file = None
        if type(git_tree) == pygit2.Tree:
            parsed_tree = porcelain.parse_file_tree(git_tree)
        if type(git_blob) == pygit2.Blob:
            parsed_file = str(base64.b64encode(git_blob.data), 'utf-8')
        response = JsonResponse({'file': parsed_file, 'tree': parsed_tree})
    except pygit2.GitError as e:
        response = HttpResponseBadRequest("Not a git repository")
    except AttributeError as e:
        response = HttpResponseBadRequest("No path parameter")
    response['Permissions'] = permissions_token
    return response

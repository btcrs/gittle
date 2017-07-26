from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.http import StreamingHttpResponse
from django.http import HttpResponseBadRequest
from django.conf import settings

from groot.permissions import decorators as permissions
from groot.versions import porcelain
from groot.versions.git import GitResponse

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

@require_http_methods(["POST"])
@permissions.requires_permission_to("create")
def create_project(request, user, project_name, permissions_token):
    """ Creates a bare repository (project) based on the user name
        and project name in the URL.

        It generates a unique path based on the user name and 
        project, creates a default readme and commits it.

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.
        permissions_token (string): JWT token signed by Wevolver.

    Returns:
        HttpResponse: A message indicating the success or failure of the create
    """

    directory = porcelain.generate_directory(user)
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
    tree.insert('readme.md', blob, pygit2.GIT_FILEMODE_BLOB)

    sha = repo.create_commit('HEAD',
                             comitter, comitter, message,
                             tree.write(), [])

    return HttpResponse("Created at ./repos/{}/{}".format(user, project_name))

@require_http_methods(["POST"])
@permissions.requires_permission_to('write')
def delete_project(request, user, project_name, permissions_token):
    """ Finds the repository specified in the URL and deletes from the file system.

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.
        permissions_token (string): JWT token signed by Wevolver.

    Returns:
        HttpResponse: A message indicating the success or failure of the delete
    """

    directory = porcelain.generate_directory(user)
    if os.path.exists(os.path.join('./repos', directory)):
        path = os.path.join("./repos", directory, project_name)
        shutil.rmtree(path)
    response = HttpResponse("Deleted at ./repos/{}/{}".format(user, project_name))
    response['Permissions'] = permissions_token
    return response

@require_http_methods(["GET"])
@permissions.requires_permission_to('read')
def read_file(request, user, project_name, permissions_token):
    """ Finds a file in the path of the repository specified by the URL
        and returns the blob.

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.
        permissions_token (string): JWT token signed by Wevolver.

    Returns:
        StreamingHttpResponse: The file's raw data.
    """

    path = request.GET.get('path').rstrip('/')
    directory = porcelain.generate_directory(user)
    if os.path.exists(os.path.join('./repos', directory)):
        repo = pygit2.Repository(os.path.join('./repos', directory, project_name))
        git_tree, git_blob = porcelain.walk_tree(repo, path)
        parsed_file = None
        if type(git_blob) == pygit2.Blob:
            parsed_file = str(base64.b64encode(git_blob.data), 'utf-8')
        chunk_size = 8192
        filelike = FileWrapper(BytesIO(git_blob.data), chunk_size)
        response = StreamingHttpResponse(filelike,
                               content_type=mimetypes.guess_type(path)[0])
        response['Content-Length'] = len(git_blob.data)
        response['Permissions'] = permissions_token

        # for download needs and argument in the call
        # response['Content-Disposition'] = "attachment; filename=%s" % path
        return response

@require_http_methods(["POST"])
@permissions.requires_permission_to("write")
def create_new_folder(request, user, project_name, permissions_token):
    """ Commits a single file to a specified path, creating a new folder in the repository.

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.
        permissions_token (string): JWT token signed by Wevolver.

    Returns:
        JsonResponse: An object
    """

    directory = porcelain.generate_directory(user)
    post = json.loads(request.body)
    path = post['path'].lstrip('/').rstrip('/')
    repo = pygit2.Repository(os.path.join("./repos", directory, project_name))
    readme = "#{} \nThis is where you should document your project  \n### Getting Started".format(project_name)
    blob = repo.create_blob(readme)
    porcelain.commit_blob(repo, blob, path.split('/'), 'readme.md')
    response = JsonResponse({'message': 'Folder Created'})
    response['Permissions'] = permissions_token
    return response

@require_http_methods(["POST"])
@permissions.requires_permission_to("write")
def receive_files(request, user, project_name, permissions_token):
    """ Receives and commits an array of files to a specific path in the repository.

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.
        permissions_token (string): JWT token signed by Wevolver.

    Returns:
        JsonResponse: An object
    """
    directory = porcelain.generate_directory(user)
    path = request.GET.get('path').rstrip('/')

    try:
        repo = pygit2.Repository(os.path.join("./repos", directory, project_name))
    except err:
        return HttpResponseBadRequest('Repo does not exist.')

    if request.FILES:
        old_porcelain.commit_tree = repo.revparse_single('master').tree
        blobs = []
        for key, file in request.FILES.items():
            blob = repo.create_blob(file.read())
            blobs.append((blob, file.name))

        new_porcelain.commit_tree = porcelain.add_blobs_to_tree(old_porcelain.commit_tree, repo, blobs, path.split('/'))
        porcelain.commit_tree(repo, new_porcelain.commit_tree)
        response = JsonResponse({'message': 'Files uploaded'})
    else:
        response = HttpResponseBadRequest('No files sent.')

    response['Permissions'] = permissions_token
    return response

@require_http_methods(["GET"])
@permissions.requires_permission_to('read')
def list_bom(request, user, project_name, permissions_token):
    """ Collects all the bom.csv files in a repository and return their sum.

        Flattens the repository's tree into an array. Then filters the array for 'bom.csv',
        concatenates them and returns unique lines.

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.
        permissions_token (string): JWT token signed by Wevolver.

    Returns:
        HttpResponse: The full Bill of Materials (BOM)
    """

    directory = porcelain.generate_directory(user)
    if os.path.exists(os.path.join('./repos', directory)):
        repo = pygit2.Repository(os.path.join('./repos', directory, project_name))
        tree = (repo.revparse_single('master').tree)
        blobs = porcelain.flatten(tree, repo)
        data = ''
        for b in [blob for blob in blobs if blob.name == 'bom.csv']:
            data += str(repo[b.id].data, 'utf-8')
        response = HttpResponse(data)
    else:
        response = HttpResponse('Failed')
    return response

@require_http_methods(["GET"])
@permissions.requires_permission_to('read')
def get_archive_token(request, user, project_name, permissions_token):
    """ Return a fast expiration token to allow download of archive

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.
        permissions_token (string): JWT token signed by Wevolver.

    Returns:
        JsonResponse: An object with the archive download token
    """

    token = tokenlib.make_token({"project_name": project_name}, timeout=1, secret=settings.TOKEN_SECRET)
    response = JsonResponse({'token': token})
    response['Permissions'] = permissions_token
    return response

@require_http_methods(["GET"])
def download_archive(request, user, project_name):
    """ Grabs and returns a user's repository as a tarball.

    Args:
        user (string): The user's name.
        project_name (string): The user's repository name.

    Returns:
        JsonResponse: An object with the requested user's repository as a tarball.
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

            directory = porcelain.generate_directory(user)
            with tarfile.open(fileobj=response, mode='w') as archive:
                repo = pygit2.Repository(os.path.join("./repos", directory, project_name))
                repo.write_archive(repo.head.target, archive)
            return response
    else:
        raise PermissionDenied

@require_http_methods(["GET"])
@permissions.requires_git_permission_to('read')
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
@permissions.requires_permission_to('read')
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
    path = request.GET.get('path').rstrip('/')
    directory = porcelain.generate_directory(user)
    if os.path.exists(os.path.join('./repos', directory)):
        repo = pygit2.Repository(os.path.join('./repos', directory, project_name))
        git_tree, git_blob = porcelain.walk_tree(repo, path)
        parsed_tree = None
        parsed_file = None
        if type(git_tree) == pygit2.Tree:
            parsed_tree = porcelain.parse_file_tree(git_tree)
        if type(git_blob) == pygit2.Blob:
            parsed_file = str(base64.b64encode(git_blob.data), 'utf-8')

        response = JsonResponse({'file': parsed_file, 'tree': parsed_tree})
    else:
        response = JsonResponse({'file': 'None', 'tree': 'None'})
    response['Permissions'] = permissions_token
    return response

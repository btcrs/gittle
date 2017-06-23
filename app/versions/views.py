from django.http import HttpResponse, JsonResponse
from .git import GitResponse
from enum import Enum
import os.path
import pygit2
import json

class Actions(Enum):
    advertisement = 'advertisement'
    result = 'result'

def parse_file_tree(repo, tree):
    return {node.name: parse_file_tree(repo, repo.get(node.id)) if node.type == 'tree'
            else {'oid': str(node.id), 'type': str(node.type)}
            for node in tree}

def create(request, user, project_name):
    path = os.path.join("./repos", user, project_name)
    pygit2.init_repository(path, True)
    return HttpResponse("Created at {}".format(path))

def show_file(request, user, project_name, oid):
    repo = pygit2.Repository(os.path.join('./repos', user, project_name))
    blob = repo.get(oid)
    return JsonResponse({'file': str(blob.data, 'utf-8')})

def list_files(request, user, project_name):
    repo = pygit2.Repository(os.path.join("./repos", user, project_name))
    tree = repo.revparse_single('master').tree
    return JsonResponse(parse_file_tree(repo, tree))

def info_refs(request, user, project_name):
    requested_repo = os.path.join('./repos', user, project_name)
    response = GitResponse(service=request.GET['service'], action=Actions.advertisement.value,
                           repository=requested_repo, data=None)
    return response.get_http_info_refs()

def service_rpc(request, user, project_name):
    requested_repo = os.path.join('./repos', user, project_name)
    response = GitResponse(service=request.path_info.split('/')[-1], action=Actions.result.value,
                           repository=requested_repo, data=request.body)
    return response.get_http_service_rpc()

from django.http import HttpResponse
from .git import GitResponse
import subprocess, os.path
import binascii
import pygit2
import json
import sys

GIT_ACTION_ADVERTISEMENT = 'advertisement'
GIT_ACTION_RESULT = 'result'

def index(request):
    return HttpResponse("Hello, world.")

def add_headers(res, content_type):
    res['Expires'] = 'Fri, 01 Jan 1980 00:00:00 GMT'
    res['Pragma'] = 'no-cache'
    res['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
    res['Content-Type'] = content_type
    return res

def parse_file_tree(repo, tree):
    temp_dict = {}
    for e in tree:
        print('name: {}, type:  {}'.format(e.name, e.type))
        if e.type == 'tree':
            temp_dict[e.name] = parse_file_tree(repo, repo.get(e.id))
        else:
            temp_dict[e.name] = {'oid': e.id, 'type': e.type}
    return temp_dict

def create(request, user, project_name):
    path = os.path.join("./repos", project_name)
    pygit2.init_repository(path, True)
    return HttpResponse("Created at {}".format(path))

def show_file(request, project_name, oid):
    repo = pygit2.Repository(os.path.join('./repos', project_name))
    blob = repo.get(oid)
    return HttpResponse(blob.data)
    # return render_template('file.html', oid=oid, file=blob.data)

def list_files(request, project_name):
    repo = pygit2.Repository(os.path.join("./repos", project_name))
    tree = repo.revparse_single('master').tree
    tree_dict = {}
    tree_dict = parse_file_tree(repo, tree)
    print(tree_dict)
    return HttpResponse(str(tree_dict))
    # return render_template('filetree.html', file_list=tree_dict.items(), base_url='/{}/{}'.format('user', project_name))

def info_refs(request, project_name):
    requested_repo = os.path.join('./repos', project_name)
    response = GitResponse(service=request.GET['service'], action=GIT_ACTION_ADVERTISEMENT,
                    repository=requested_repo, data=None)
    return response.get_http_info_refs()

def service_rpc(request, project_name):
    requested_repo = os.path.join('./repos', project_name)
    response = GitResponse(service=request.path_info.split('/')[-1], action=GIT_ACTION_RESULT,
                    repository=requested_repo, data=request.body)
    return response.get_http_service_rpc()

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/create$', views.create_project, name='create-project'), # GET -> POST, changed
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/delete$', views.delete_project, name='delete-project'), # GET  -> POST
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/readfile$', views.read_file, name='read-file'), # GET, changed
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/newfolder$', views.create_new_folder, name='new-folder'), # POST
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/upload$', views.receive_files, name='receive-files'), # POST
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/listbom$', views.list_bom, name='list-bom'), # GET
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/archive/download$', views.download_archive, name='download-archive'), # GET
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/git-upload-pack$', views.upload_pack, name='upload_pack'), # GET
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/git-receive-pack$', views.receive_pack, name='receive_pack'), # GET
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/info/refs$', views.info_refs, name='info-refs'), # GET
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)$', views.read_tree, name='read-tree'), # GET
]

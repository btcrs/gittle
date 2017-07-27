from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/create$', views.create_project, name='create-project'),
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/delete$', views.delete_project, name='delete-project'),
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/readfile$', views.read_file, name='read-file'),
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/newfolder$', views.create_new_folder, name='new-folder'),
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/upload$', views.receive_files, name='receive-files'),
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/listbom$', views.list_bom, name='list-bom'),
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/archive/download$', views.download_archive, name='download-archive'),
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/git-upload-pack$', views.upload_pack, name='upload_pack'),
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/git-receive-pack$', views.receive_pack, name='receive_pack'),
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/info/refs$', views.info_refs, name='info-refs'),
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)$', views.read_tree, name='read-tree'),
]

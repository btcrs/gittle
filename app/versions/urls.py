from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^login', views.login, name='login'),
    url(r'^create/(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)$', views.create, name='create'),
    url(r'^delete/(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)$', views.delete, name='delete'),
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/archive$', views.download_archive, name='download-archive'),
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/upload$', views.upload_file, name='upload-file'),
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/newfolder$', views.create_new_folder, name='new-folder'),
    url(r'(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/git-upload-pack$', views.upload_pack, name='upload_pack'),
    url(r'(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/git-receive-pack$', views.receive_pack, name='receive_pack'),
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/info/refs$', views.info_refs, name='info-refs'),
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)/(?P<oid>[-.\w]+)$', views.show_file, name='show-file'),
    url(r'^(?P<user>[-.\w]+)/(?P<project_name>[-.\w]+)$', views.list_files, name='list-files'),
]

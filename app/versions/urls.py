from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^login/', views.login, name='login'),
    url(r'^refresh/', views.refresh, name='refresh'),
    url(r'^create/(?P<user>\w+)/(?P<project_name>\w+)$', views.create, name='create'),
    url(r'^delete/(?P<user>\w+)/(?P<project_name>\w+)$', views.delete, name='delete'),
    url(r'^(?P<user>\w+)/(?P<project_name>\w+)/(?P<oid>\w+)$', views.show_file, name='show-file'),
    url(r'^(?P<user>\w+)/(?P<project_name>\w+)$', views.list_files, name='list-files'),
    url(r'^(?P<user>\w+)$', views.list_repos, name='list-repos'),
    url(r'(?P<user>\w+)/(?P<project_name>\w+)/git-upload-pack$', views.service_rpc, name='service_rpc'),
    url(r'(?P<user>\w+)/(?P<project_name>\w+)/git-receive-pack$', views.service_rpc, name='service_rpc'),
    url(r'^(?P<user>\w+)/(?P<project_name>\w+)/info/refs$', views.info_refs, name='info-refs'),
]

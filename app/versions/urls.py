from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^create/(?P<user>\w+)/(?P<project_name>\w+)$', views.create, name='create'),
    url(r'^user/(?P<project_name>\w+)/(?P<oid>\w+)$', views.show_file, name='show-file'),
    url(r'^user/(?P<project_name>\w+)$', views.list_files, name='list-files'),
    url(r'user/(?P<project_name>\w+)/git-upload-pack$', views.service_rpc, name='service_rpc'),
    url(r'user/(?P<project_name>\w+)/git-receive-pack$', views.service_rpc, name='service_rpc'),
    url(r'^user/(?P<project_name>\w+)/info/refs$', views.info_refs, name='info-refs'),
]

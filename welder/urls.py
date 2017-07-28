from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('welder.permissions.urls')),
    url(r'^', include('welder.versions.urls')),
]

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.http import HttpResponseForbidden
from functools import wraps
from .auth import basic_auth
import requests
import logging

logger = logging.getLogger(__name__)
api_base_url = "https://dev.wevolver.com/api/2"

def refresh(user, authorization):
    url = "{}/users/{}/checktoken/".format(api_base_url, user)
    headers = {'Authorization': 'Bearer {}'.format(authorization)}
    response = requests.get(url, headers=headers)
    return response.status_code == requests.codes.ok

def wevolver_auth(function):
    def wrap(request, *args, **kwargs):
        headers = request.GET.get("access_token")
        user = request.GET.get("user_id")
        if refresh(user, headers):
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap

def git_access_required(func):
    @wraps(func)
    def _decorator(request, *args, **kwargs):
        if request.META.get('HTTP_AUTHORIZATION'):
            user = basic_auth(request.META['HTTP_AUTHORIZATION'])
            if user:
                return func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden('Access forbidden.')
        res = HttpResponse()
        res.status_code = 401
        res['WWW-Authenticate'] = 'Basic'
        return res
    return _decorator

def has_permission_to(permission):
    def has_permission(func):
        @wraps(func)
        def _decorator(request, *args, **kwargs):
            authorization = request.GET.get("access_token")
            project_id = request.GET.get("project_id")
            ##############################
            project_id = 436
            ##############################
            url = "{}/projects/{}/permissions/".format(api_base_url, project_id)
            headers = {'Authorization': 'Bearer {}'.format(authorization)}
            response = requests.get(url, headers=headers)
            if permission in response.text:
                return func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden('Access forbidden.')
        return _decorator
    return has_permission

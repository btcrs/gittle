from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.http import HttpResponseForbidden
from django.conf import settings
from functools import wraps
from .auth import basic_auth
import requests
import logging

logger = logging.getLogger(__name__)

def refresh(user, authorization):
    """ Checks against the Wevolver API to see if the users token is currently valid

    Args:
        authorization (str): the current user's bearer token
        user (str): the current requesting user's id
    """
    url = "{}/users/{}/checktoken/".format(settings.API_BASE, user)
    headers = {'Authorization': 'Bearer {}'.format(authorization)}
    response = requests.get(url, headers=headers)
    return response.status_code == requests.codes.ok

def wevolver_auth(function):
    """ Determines the user and authorization through Wevolver token based auth

    Uses the request's access_token and user_id params to check the user's bearer
    token against the Wevolver API
    """

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
    """ Determines the user and authorization through basic http auth

    Uses the requests HTTP_AUTHORIZATION to authorize the user against
    basic HTTP auth
    """
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
    """ Checks user's permission set for the requested project

    Calls the project permission endpoint with the current user's id to
    get a list of permissions based on their role

    ####################
         UNFINISHED
    ####################
    """
    def has_permission(func):
        @wraps(func)
        def _decorator(request, *args, **kwargs):
            authorization = request.GET.get("access_token")
            project_id = request.GET.get("project_id")
            ##############################
            project_id = 436
            ##############################
            url = "{}/projects/{}/permissions/".format(settings.API_BASE, project_id)
            headers = {'Authorization': 'Bearer {}'.format(authorization)}
            response = requests.get(url, headers=headers)
            if permission in response.text:
                return func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden('Access forbidden.')
        return _decorator
    return has_permission

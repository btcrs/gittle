from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.http import HttpResponseForbidden
from django.conf import settings
from functools import wraps
import requests
import logging
import base64
import json

logger = logging.getLogger(__name__)

def git_access_required(func):
    """ Determines the user and authorization through basic http auth

    Uses the requests HTTP_AUTHORIZATION to authorize the user against
    basic HTTP auth
    """
    @wraps(func)
    def _decorator(request, *args, **kwargs):
        if request.META.get('HTTP_AUTHORIZATION'):
            user_token, user = basic_auth(request.META['HTTP_AUTHORIZATION'])
            token = checktoken(user, kwargs['user'], kwargs['project_name'], user_token)
            if user and token:
                kwargs['access_token'] = user
                return func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden('Access forbidden.')
        res = HttpResponse()
        res.status_code = 401
        res['WWW-Authenticate'] = 'Basic'
        return res
    return _decorator

def basic_auth(authorization_header):
    """ Basic auth middleware for git requests

    Attempts to log the current user into the Wevolver API login endpoint

    Args:
        authorization_header (str): the current user's bearer token
    """
    authorization_method, authorization = authorization_header.split(' ', 1)
    if authorization_method.lower() == 'basic':
        authorization = base64.b64decode(authorization.strip()).decode('utf8')
        username, password = authorization.split(':', 1)
        username = username
        password = password
        body = {'username': str(username),
                'password': str(password),
                'grant_type': 'password'}
        url = "{}/proxy-client-token".format(settings.AUTH_BASE)
        response = requests.post(url, data=body)
        return (json.loads(response.content)['access_token'], json.loads(response.content)['user'].split('/')[-2])
    else:
        return None

def wevolver_auth(function):
    """ Determines the user and authorization through Wevolver token based auth

    Uses the request's access_token and user_id params to check the user's bearer
    token against the Wevolver API
    """

    def wrap(request, *args, **kwargs):
        headers = request.META.get('Authorization', None)
        kwargs['access_token'] = headers
        user = request.GET.get("user_id")
        success, response = checktoken(user, kwargs['user'], kwargs['project_name'], headers)
        if success:
            kwargs['access_token'] = headers
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap

def checktoken(user, user_name, project_name, authorization):
    """ Checks against the Wevolver API to see if the users token is currently valid

    Args:
        authorization (str): the current user's bearer token
        user (str): the current requesting user's id
    """
    url = "{}/users/{}/checktoken/?project={}/{}".format(settings.API_BASE, user, user_name, project_name)
    headers = {'Authorization': 'Bearer {}'.format(authorization)}
    response = requests.get(url, headers=headers)
    return (response.status_code == requests.codes.ok, response)

def has_permission_to(permission):
    """ Checks user's permission set for the requested project

    Calls the project permission endpoint with the current user's id to
    get a list of permissions based on their role
    """
    def has_permission(func):
        @wraps(func)
        def _decorator(request, *args, **kwargs):
            authorization = kwargs['access_token']
            project_name = kwargs['project_name']
            user_name = kwargs['user']
            code, response = checktoken(-1, user_name, project_name, authorization)
            if permission in response.text:
                return func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden('Access forbidden.')
        return _decorator
    return has_permission

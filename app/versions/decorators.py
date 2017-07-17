from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.http import HttpResponseForbidden
from django.conf import settings
from profilehooks import profile
from functools import wraps
import requests
import logging
import base64
import json
import jwt
import os

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

def checktoken(user, user_name, project_name, authorization):
    """ Checks against the Wevolver API to see if the users token is currently valid

    Args:
        authorization (str): the current user's bearer token
        user (str): the current requesting user's id
    """
    url = "{}/users/{}/checktoken/?project={}/{}".format(settings.API_BASE, user, user_name, project_name)
    print(url)
    headers = {'Authorization': 'Bearer {}'.format(authorization)}
    response = requests.get(url, headers=headers)
    return (response.status_code == requests.codes.ok, response)

def gettoken(user_id, user_name, project_name, access_token):
    url = "{}/users/{}/checktoken/?project={}/{}".format(settings.API_BASE, user_id, user_name, project_name)
    access_token = access_token if access_token.split()[0] == "Bearer" else "Bearer " + access_token
    headers = {'Authorization': '{}'.format(access_token)}
    response = requests.get(url, headers=headers)
    return (response.status_code == requests.codes.ok, response)

def decode_token(token):
    with open('versions/jwt.verify','r') as verify:
        try:
            return jwt.decode(token, verify.read(), algorithms=['RS256'], issuer='wevolver')
        except jwt.ExpiredSignatureError as error:
            print(error)

def requires_permission_to(permission):
    """ Determines the user and authorization through Wevolver token based auth

    Uses the request's access_token and user_id params to check the user's bearer
    token against the Wevolver API

    Calls the project permission endpoint with the current user's id to
    get a list of permissions based on their role
    """
    # @profile(immediate=True)
    def has_permission(func):
        @wraps(func)
        def _decorator(request, *args, **kwargs):
            access_token = request.META.get('HTTP_AUTHORIZATION', None)
            user_id = request.GET.get("user_id")
            user_name = kwargs['user']
            project_name = kwargs['project_name']
            permissions = request.META.get('HTTP_PERMISSIONS', None)

            print(access_token)
            print('permissions')
            print(permissions)
            if not permissions:
                success, response = gettoken(user_id, user_name, project_name, access_token)
                token = response.content
                decoded_token = decode_token(token)
                permissions = decoded_token['permissions']
                print(decoded_token)
            else:
                token = permissions
                permissions = decode_token(permissions)['permissions']

            if permissions and permission in permissions:
                kwargs['permissions_token'] = token
                return func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden('No Permissions')
        return _decorator
    return has_permission

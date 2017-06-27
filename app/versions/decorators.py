from django.core.exceptions import PermissionDenied
from functools import wraps
from .auth import basic_auth

def poor_auth(function):
    def wrap(request, *args, **kwargs):
        client_id = request.GET.get('client_id')
        client_secret = request.GET.get('client_secret')
        refresh_token = request.GET.get('refresh_token')
        if refresh(client_id, client_secret, refresh_token):
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

def refresh(client_id, client_secret, refresh_token):
    body = {'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
           }
    url = "https://dev.wevolver.com/o/token"
    response = requests.post(url, data=body)
    return response.status_code == requests.codes.ok

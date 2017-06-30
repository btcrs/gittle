from django.conf import settings
import requests
import base64

def basic_auth(authorization_header):
    """ Basic auth middleware for git requests

    Attempts to log the current user into the Wevolver API login endpoint

    Args:
        authorization_header (str): the current user's bearer token
    """
    authmeth, auth = authorization_header.split(' ', 1)
    if authmeth.lower() == 'basic':
        auth = base64.b64decode(auth.strip()).decode('utf8')
        username, password = auth.split(':', 1)
        username = username
        password = password
        body = {'username': str(username),
                'password': str(password),
                'grant_type': 'password'}
        url = "{}/proxy-client-token".format(settings.AUTH_BASE)
        response = requests.post(url, data=body)
        print(response.content)
        return response
    else:
        return None

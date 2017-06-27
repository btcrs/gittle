import requests
import base64

def basic_auth(authorization_header):
    authmeth, auth = authorization_header.split(' ', 1)
    if authmeth.lower() == 'basic':
        auth = base64.b64decode(auth.strip()).decode('utf8')
        username, password = auth.split(':', 1)
        username = username
        password = password
        body = {'username': str(username),
                'password': str(password),
                'grant_type': 'password'}
        url = "https://dev.wevolver.com/o/proxy-client-token"
        response = requests.post(url, data=body)
        return response
    else:
        return None

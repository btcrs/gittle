from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.conf import settings
import requests
import logging
import json

logger = logging.getLogger(__name__)

@require_http_methods(["POST"])
def login(request):
    """ Logs the user in and sets the token

    Returns:
        HttpResponse: An object containing all session metadata
    """
    post = json.loads(request.body)
    body = {'username': post['username'], 'password': post['password'], 'grant_type': 'password'}
    url = "{}/proxy-client-token".format(settings.AUTH_BASE)
    response = requests.post(url, data=body)
    return HttpResponse(response.text)

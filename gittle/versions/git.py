from django.http import HttpResponse, HttpResponseNotFound
from django.http import HttpResponse
import subprocess, os.path
from enum import Enum
import logging
import sys

logger = logging.getLogger(__name__)

class Services(Enum):
    git_upload_pack = 'git-upload-pack'
    git_receive_pack = 'git-receive-pack'

plumbing = Enum('git_plumbing', [
    'git_info_refs',
    'git_upload_pack',
    'git_receive_pack'
])

def get_http_error(exception):
    if 'Not a git repository' in exception.args[0]:
        return HttpResponseNotFound()

class GitResponse(HttpResponse):
    """An extension of Django's HttpResponse that meets Git's smart HTTP specs

    The responses to Git's requests must follow a protocol, and this class is
    meant to build properly formed responses.

    Attributes:
        service (str): the initiated git plumbing command
        action (str): the action initiated by the service
        repository (str): target repository of the request
        data (str): uploaded data

    """

    def __init__(self, *args, **kwargs):
        self.service = Services(kwargs.pop('service', None))
        self.action = kwargs.pop('action', None)
        self.repository = kwargs.pop('repository', None)
        self.data = kwargs.pop('data', None)
        super(GitResponse, self).__init__(*args, **kwargs)

    def set_response_header(self):
        """ Writes the required headers for a git handshake

        Primarily disables caching and sets the content type to the requested service and action
        """

        self.__setitem__('Expires', 'Fri, 01 Jan 1980 00:00:00 GMT')
        self.__setitem__('Pragma', 'no-cache')
        self.__setitem__('Cache-Control', 'no-cache, max-age=0, must-revalidate')
        self.__setitem__('Content-Type', 'application/x-{0}-{1}'.format(self.service.value, self.action))

    def set_response_first_line(self):
        """ Writes the first line of the responses body

        Constructs a line to detail the service of the current request. Adds the a prefix
        (total line length in hex) to tell the client where the payload starts.

        e.g. 001f# service=git-receive-pack0000
        """

        service = '# service={}\n'.format(self.service.value)
        length = len(service) + 4
        prefix = "{:04x}".format(length & 0xFFFF)
        self.write('{0}{1}0000'.format(prefix, service))

    def set_response_payload(self, payload_type):
        """ Executes the service requested and writes the data to the payload

        Args:
            payload_type (plumbing): git plumbing call initiated by the request.
        """

        if payload_type == plumbing.git_info_refs:
            process = subprocess.Popen([self.service.value,
                                        '--stateless-rpc',
                                        '--advertise-refs',
                                        self.repository],
                                        stdout=subprocess.PIPE)

            self.write(process.stdout.read())

        elif payload_type == plumbing.git_receive_pack:
            process = subprocess.Popen(['git-receive-pack',
                                        '--stateless-rpc',
                                        self.repository],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE)

            self.write(process.communicate(input=self.data)[0])

        elif payload_type == plumbing.git_upload_pack:
            process = subprocess.Popen(['git-upload-pack',
                                        '--stateless-rpc',
                                        self.repository],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE)

            self.write(process.communicate(input=self.data)[0])

    def get_http_info_refs(self):
        """ Creates a response for git's info_refs request

        Sets the headers, generates the first line of the request, and adds
        the info_refs functions data to the payload.

        Returns:
            GitResponse: An HttpResponse for the handshake response for the info_refs function.
        """

        try:
            self.set_response_header()
            self.set_response_first_line()
            self.set_response_payload(plumbing.git_info_refs)
            return self
        except BaseException as e:
            return get_http_error(e)

    def get_http_service_rpc(self):
        """ Initiates a git plumbing rpc call depending on the received service request

        Sets the headers and sets the payload to the data generated by receive_pack or
        upload_pack depending on whether the request is a push or a pull respectively.

        Returns:
            GitResponse: An HttpResponse containing the data requested by git's service call.
        """

        try:
            self.set_response_header()
            if self.service == Services.git_receive_pack:
                self.set_response_payload(plumbing.git_receive_pack)
            elif self.service == Services.git_upload_pack:
                self.set_response_payload(plumbing.git_upload_pack)
            return self
        except BaseException as e:
            return get_http_error(e)

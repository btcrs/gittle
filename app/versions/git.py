from django.http import HttpResponse, HttpResponseNotFound
from django.http import HttpResponse
import subprocess, os.path
from enum import Enum
import sys

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
    def __init__(self, *args, **kwargs):
        self.service = Services(kwargs.pop('service', None))
        self.action = kwargs.pop('action', None)
        self.repository = kwargs.pop('repository', None)
        self.data = kwargs.pop('data', None)
        super(GitResponse, self).__init__(*args, **kwargs)

    def set_response_header(self):
        self.__setitem__('Expires', 'Fri, 01 Jan 1980 00:00:00 GMT')
        self.__setitem__('Pragma', 'no-cache')
        self.__setitem__('Cache-Control', 'no-cache, max-age=0, must-revalidate')
        self.__setitem__('Content-Type', 'application/x-{0}-{1}'.format(self.service.value, self.action))

    def set_response_first_line(self):
        """ e.g. 001f# service=git-receive-pack """

        service = '# service={}\n'.format(self.service.value)
        length = len(service) + 4
        prefix = "{:04x}".format(length & 0xFFFF)
        self.write('{0}{1}0000'.format(prefix, service))

    def set_response_payload(self, payload_type):
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
        try:
            self.set_response_header()
            self.set_response_first_line()
            self.set_response_payload(plumbing.git_info_refs)
            return self
        except BaseException as e:
            return get_http_error(e)

    def get_http_service_rpc(self):
        try:
            self.set_response_header()
            if self.service == Services.git_receive_pack:
                self.set_response_payload(plumbing.git_receive_pack)
            elif self.service == Services.git_upload_pack:
                self.set_response_payload(plumbing.git_upload_pack)
            return self
        except BaseException as e:
            return get_http_error(e)

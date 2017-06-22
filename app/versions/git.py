from django.http import HttpResponse, HttpResponseNotFound
from django.http import HttpResponse
import subprocess, os.path
import sys

GIT_SERVICE_UPLOAD_PACK = 'git-upload-pack'
GIT_SERVICE_RECEIVE_PACK = 'git-receive-pack'
GIT_SERVICES = [GIT_SERVICE_UPLOAD_PACK, GIT_SERVICE_RECEIVE_PACK]

GIT_HTTP_INFO_REFS = 1
GIT_HTTP_SERVICE_UPLOAD_PACK = 2
GIT_HTTP_SERVICE_RECEIVE_PACK = 3

def get_http_error(exception):
    if 'Not a git repository' in exception.args[0]:
        return HttpResponseNotFound()

class GitResponse(HttpResponse):
    def __init__(self, *args, **kwargs):
        self.service = kwargs.pop('service', None)
        self.action = kwargs.pop('action', None)
        self.repository = kwargs.pop('repository', None)
        self.data = kwargs.pop('data', None)
        super(GitResponse, self).__init__(*args, **kwargs)

    def set_response_header(self):
        self.__setitem__('Expires', 'Fri, 01 Jan 1980 00:00:00 GMT')
        self.__setitem__('Pragma', 'no-cache')
        self.__setitem__('Cache-Control', 'no-cache, max-age=0, must-revalidate')
        self.__setitem__('Content-Type', 'application/x-{0}-{1}'.format(self.service, self.action))

    def set_response_first_line(self):
        """
            Sets first line of git response that includes length and requested service.
            e.g.
                001f# service=git-receive-pack
        """

        first_line = '# service={0}\n'.format(self.service)
        length = len(first_line) + 4
        prefix = "{:04x}".format(length & 0xFFFF)
        self.write('{0}{1}0000'.format(prefix, first_line))

    def set_response_payload(self, payload_type):
        if payload_type == GIT_HTTP_INFO_REFS:
            p = subprocess.Popen([self.service, '--stateless-rpc', '--advertise-refs', self.repository], stdout=subprocess.PIPE)
            data = p.stdout.read()
            self.write(data)
        elif payload_type == GIT_HTTP_SERVICE_RECEIVE_PACK:
            p = subprocess.Popen(['git-receive-pack', '--stateless-rpc', self.repository], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            data = p.communicate(input=self.data)[0]
            self.write(data)
        elif payload_type == GIT_HTTP_SERVICE_UPLOAD_PACK:
            p = subprocess.Popen(['git-upload-pack', '--stateless-rpc', self.repository], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            data = p.communicate(input=self.data)[0]
            self.write(data)

    def get_http_info_refs(self):
        try:
            self.set_response_header()
            self.set_response_first_line()
            self.set_response_payload(GIT_HTTP_INFO_REFS)
            return self
        except BaseException as e:
            return get_http_error(e)

    def get_http_service_rpc(self):
        try:
            self.set_response_header()
            if self.service == GIT_SERVICE_RECEIVE_PACK:
                self.set_response_payload(GIT_HTTP_SERVICE_RECEIVE_PACK)
            elif self.service == GIT_SERVICE_UPLOAD_PACK:
                self.set_response_payload(GIT_HTTP_SERVICE_UPLOAD_PACK)
            return self
        except BaseException as e:
            return get_http_error(e)

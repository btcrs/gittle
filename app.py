from flask import Flask, make_response, request, abort
import subprocess, os.path
app = Flask(__name__)

import sys
import pygit2
import binascii

# @app.route("/")
# def hello():
#     return "Hello World!"

# @app.route("/create")
# def create():
#     pygit2.init_repository('repos/git/test', True)
#     return "Create!"

# @app.route("/clone/info/<path:path>")
# def clone(path):
#     return 'h'

# @app.route("/clone/<path:path>")
# def cloneHead(path):
#     environ = dict(request.environ)
#     environ['PATH_INFO'] = environ['PATH_INFO'][4:]
#     (
#         status_line, headers, response_body_generator
#     ) = gitHttpBackend.wsgi_to_git_http_backend(environ, 'repos/git/test')
#     return Response(response_body_generator, status_line, headers)
    # return send_from_directory('repos/git/test/', path)

@app.route('/<string:project_name>/info/refs')
def info_refs(project_name):
    service = request.args.get('service')
    if service[:4] != 'git-':
        abort(500)
    p = subprocess.Popen([service, '--stateless-rpc', '--advertise-refs', 'test'], stdout=subprocess.PIPE)
    packet = '# service=%s\n' % service
    length = len(packet) + 4
    _hex = '0123456789abcdef'
    prefix = ''
    prefix += _hex[length >> 12 & 0xf]
    prefix += _hex[length >> 8  & 0xf]
    prefix += _hex[length >> 4 & 0xf]
    prefix += _hex[length & 0xf]
    data = str.encode(prefix) + str.encode(packet) + b'0000'
    data += p.stdout.read()
    res = make_response(data)
    res.headers['Expires'] = 'Fri, 01 Jan 1980 00:00:00 GMT'
    res.headers['Pragma'] = 'no-cache'
    res.headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
    res.headers['Content-Type'] = 'application/x-%s-advertisement' % service
    p.wait()
    return res

@app.route('/<string:project_name>/git-receive-pack', methods=('POST',))
def git_receive_pack(project_name):
    p = subprocess.Popen(['git-receive-pack', '--stateless-rpc', 'test'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    p.stdin.write(binascii.b2a_qp(request.data))
    print(binascii.b2a_qp(request.data))
    data = p.stdout.read()
    res = make_response()
    res.headers['Expires'] = 'Fri, 01 Jan 1980 00:00:00 GMT'
    res.headers['Pragma'] = 'no-cache'
    res.headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
    res.headers['Content-Type'] = 'application/x-git-receive-pack-result'
    p.wait()
    return 'res'

@app.route('/<string:project_name>/git-upload-pack', methods=('POST',))
def git_upload_pack(project_name):
    p = subprocess.Popen(['git-upload-pack', '--stateless-rpc', os.path.join('.', project_name)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    p.stdin.write(binascii.b2a_qp(request.data))
    data = p.stdout.read()
    res = make_response(data)
    res.headers['Expires'] = 'Fri, 01 Jan 1980 00:00:00 GMT'
    res.headers['Pragma'] = 'no-cache'
    res.headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
    res.headers['Content-Type'] = 'application/x-git-upload-pack-result'
    p.wait()
    return res

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
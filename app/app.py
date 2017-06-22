from flask import Flask, make_response, request, abort, jsonify, render_template
import subprocess, os.path
app = Flask(__name__)

import sys
import pygit2
import binascii

@app.route("/")
def hello():
    return render_template("index.html")

@app.route("/create/<string:user>/<string:project_name>")
def create():
    pygit2.init_repository(project_name, True)
    return "Create!"

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

def parse_file_tree(repo, tree):
    temp_dict = {}
    for e in tree:
        print('name: {}, type:  {}'.format(e.name, e.type))
        if e.type == 'tree':
            temp_dict[e.name] = parse_file_tree(repo, repo.get(e.id))
        else:
            temp_dict[e.name] = e.id
    return temp_dict

@app.route("/user/<string:project_name>")
def list_files(project_name):
    repo = pygit2.Repository(project_name)
    tree = repo.revparse_single('master').tree
    tree_dict = {}
    tree_dict = parse_file_tree(repo, tree)
    # file_list = [e for e in tree]
    return render_template("filetree.html", file_list=tree_dict)
    # return jsonify(file_list)

@app.route('/<string:project_name>/info/refs')
def info_refs(project_name):
    service = request.args.get('service')
    if service[:4] != 'git-':
        abort(500)
    p = subprocess.Popen([service, '--stateless-rpc', '--advertise-refs', os.path.join('.', project_name)], stdout=subprocess.PIPE)
    packet = '# service=%s\n' % service
    length = len(packet) + 4
    prefix = "{:04x}".format(length & 0xFFFF);
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
    p = subprocess.Popen(['git-receive-pack', '--stateless-rpc', os.path.join('.', project_name)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    data = p.communicate(input=request.data)[0]
    res = make_response(data)
    res.headers['Expires'] = 'Fri, 01 Jan 1980 00:00:00 GMT'
    res.headers['Pragma'] = 'no-cache'
    res.headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
    res.headers['Content-Type'] = 'application/x-git-receive-pack-result'
    return res

@app.route('/<string:project_name>/git-upload-pack', methods=('POST',))
def git_upload_pack(project_name):
    p = subprocess.Popen(['git-upload-pack', '--stateless-rpc', os.path.join('.', project_name)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    data = p.communicate(input=request.data)[0]
    res = make_response(data)
    res.headers['Expires'] = 'Fri, 01 Jan 1980 00:00:00 GMT'
    res.headers['Pragma'] = 'no-cache'
    res.headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
    res.headers['Content-Type'] = 'application/x-git-upload-pack-result'
    return res

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')

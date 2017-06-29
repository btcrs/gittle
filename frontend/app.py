from flask import Flask, make_response, request, abort, jsonify, render_template, redirect
import requests
import subprocess, os.path
app = Flask(__name__)

import sys

@app.route("/")
def hello():
    return render_template("home.html")



# def add_headers(res, content_type):
#     res.headers['Expires'] = 'Fri, 01 Jan 1980 00:00:00 GMT'
#     res.headers['Pragma'] = 'no-cache'
#     res.headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
#     res.headers['Content-Type'] = content_type
#     return res

# def parse_file_tree(repo, tree):
#     temp_dict = {}
#     for e in tree:
#         print('name: {}, type:  {}'.format(e.name, e.type))
#         if e.type == 'tree':
#             temp_dict[e.name] = parse_file_tree(repo, repo.get(e.id))
#         else:
#             temp_dict[e.name] = {'oid': e.id, 'type': e.type}
#     return temp_dict

@app.route("/user", methods=["POST"])
def login():
    if request.method == 'POST':
        requestJson = request.get_json(force=True)

        username = requestJson['username']
        password = requestJson['password']
        r = requests.post('https://dev.wevolver.com/o/proxy-client-token', data={'username': username, 'password':password, 'grant_type':'password'})
        if r.json() and r.json()['access_token']:
            return jsonify(r.json())
        else:
            return jsonify({})
    else:
        return jsonify({})

# @app.route("/create/<string:user>/<string:project_name>")
# def create(user, project_name):
#     pygit2.init_repository(os.path.join("./repos", project_name), True)
#     return "Create!"

# @app.route("/user/<string:project_name>/<string:oid>")
# def show_file(project_name, oid):
#     repo = pygit2.Repository(os.path.join('./repos', project_name))
#     blob = repo.get(oid)
#     return render_template('file.html', oid=oid, file=blob.data)


# @app.route("/user/<string:project_name>")
# def list_files(project_name):
#     repo = pygit2.Repository(os.path.join("./repos", project_name))
#     tree = repo.revparse_single('master').tree
#     tree_dict = parse_file_tree(repo, tree)
#     print(tree_dict)
#     return render_template('filetree.html', file_list=tree_dict.items(), base_url='/{}/{}'.format('user', project_name))


# @app.route('/<string:project_name>/info/refs')
# def info_refs(project_name):
#     service = request.args.get('service')
#     if service[:4] != 'git-':
#         abort(500)
#     p = subprocess.Popen([service, '--stateless-rpc', '--advertise-refs', os.path.join('./repos', project_name)], stdout=subprocess.PIPE)
#     packet = '# service=%s\n' % service
#     length = len(packet) + 4
#     prefix = "{:04x}".format(length & 0xFFFF);
#     data = str.encode(prefix) + str.encode(packet) + b'0000'
#     data += p.stdout.read()
#     res = make_response(data)
#     p.wait()
#     return add_headers(res, 'application/x-%s-advertisement' % service)


# @app.route('/<string:project_name>/git-receive-pack', methods=('POST',))
# def git_receive_pack(project_name):
#     p = subprocess.Popen(['git-receive-pack', '--stateless-rpc', os.path.join('./repos', project_name)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
#     data = p.communicate(input=request.data)[0]
#     res = make_response(data)
#     return add_headers(res, 'application/x-git-receive-pack-result')


# @app.route('/<string:project_name>/git-upload-pack', methods=('POST',))
# def git_upload_pack(project_name):
#     p = subprocess.Popen(['git-upload-pack', '--stateless-rpc', os.path.join('./repos', project_name)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
#     data = p.communicate(input=request.data)[0]
#     res = make_response(data)
#     return add_headers(res, 'application/x-git-upload-pack-result')


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')

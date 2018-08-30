#!/usr/bin/env python3
import configparser, os
import sys
from flask import Flask, render_template, flash, request, make_response, redirect, url_for, jsonify
from flask_httpauth import HTTPBasicAuth
from TransloadManager import TransloadMan
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

# App config.
dir_path = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
config.read(os.path.join(dir_path, 'settings.ini'))
USERNAME = config['server']['USERNAME']
PASSWORD = config['server']['PASSWORD']
SERVER_PORT = int(config['server']['SERVER_PORT'])

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['DEBUG'] = True

# Resources
man = TransloadMan()
auth = HTTPBasicAuth()
url_validator = URLValidator()
last_auth_url = None


@auth.get_password
def get_password(username):
    return PASSWORD if username == USERNAME else None


@auth.error_handler
def unauthorized():
    return make_response("error: Unauthorized access", 401)


@app.route("/back", methods=['GET'])
@auth.login_required
def back():
    return redirect(url_for('index'))


@app.route("/authGD", methods=['GET', 'POST'])
@auth.login_required
def authGD():
    if man.ready():
        return redirect(url_for('back'))

    global last_auth_url
    if request.method == 'POST':
        code = request.form.get('code')
        if code is None or code == '':
            flash('Error: Please input code. ')
            return render_template('authGD.html', link=last_auth_url)
        if man.put_auth_code(code):
            return redirect(url_for('back'))
        else:
            flash('Error: Authentication Failed. ')
    last_auth_url = man.get_auth_url()
    return render_template('authGD.html', link=last_auth_url)


@app.route("/newtask", methods=['POST'])
@auth.login_required
def newtask():
    if not request.is_json:
        return jsonify({'result': 'not json!? come on!'})
    data = request.get_json()
    name = data.get('name')
    link = data.get('link')
    upload = data.get('upload')
    delete = data.get('delete')
    try:
        url_validator(link)
        valid_link = True
    except ValidationError:
        valid_link = False
    if name != '' and valid_link:
        man.add_task(link, name, upload=upload, delete=delete)
        return jsonify({'result': 'success'})
    else:
        if name != '' and link != '' and not valid_link:
            return jsonify({'result': 'invalid link'})
        else:
            return jsonify({'result': 'missing parameter'})


@app.route("/remove", methods=['POST'])
@auth.login_required
def remove():
    if not request.is_json:
        return jsonify({'result': 'not json!? come on!'})
    data = request.get_json()
    name = data.get('name')
    type = data.get('type')
    if name != '' and type != '':
        if type == "upload":
            man.remove_up_task(name)
        elif type == "download":
            man.remove_dl_task(name)
        return jsonify({'result': 'success'})
    else:
        return jsonify({'result': 'missing parameter'})


@app.route("/status", methods=['GET'])
@auth.login_required
def status():
    return jsonify(man.get_status())


@app.route("/", methods=['GET'])
@auth.login_required
def index():
    wb = ''
    if not man.ready():
        wb = "<br><div class=\"alert alert-danger\">"
        wb += "<a href=\"/authGD\">Authentication Required with Google Drive</a></div>"
    return render_template('GDD.html', WarningBar=wb)


if __name__ == "__main__":
    #if len(sys.argv) > 1 and sys.argv[1] == '--aria2':
    import subprocess
    subprocess.Popen(['aria2c', '--enable-rpc'])
    app.run(host='0.0.0.0', port=SERVER_PORT)

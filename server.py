from flask import Flask, render_template, flash, request, make_response, redirect, url_for
from wtforms import Form, StringField
from flask_httpauth import HTTPBasicAuth
from transport import Manager
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

# App config.
USERNAME = 'admin'
PASSWORD = 'password'
DEBUG = False
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = 'B12r98j/3yX R~XHH!jmN]LWX/,?RT'

# Resources
man = Manager()
auth = HTTPBasicAuth()
url_validator = URLValidator()
last_auth_url = None


@auth.get_password
def get_password(username):
    if username == USERNAME:
        return PASSWORD
    return None


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
    if man.auth_ready:
        return redirect(url_for('back'))

    class AuthForm(Form):
        code = StringField('Code:')
    form = AuthForm(request.form)
    global last_auth_url
    if request.method == 'POST':
        code = request.form['code']
        if code is None or code == '':
            flash('Error: Please input code. ')
            return render_template('authGD.html', form=form, link=last_auth_url)
        if man.put_auth_code(code):
            flash('Authentication Successful. ')
            return redirect(url_for('back'))
        else:
            flash('Error: Authentication Failed. ')
    last_auth_url = man.get_auth_url()
    return render_template('authGD.html', form=form, link=last_auth_url)


@app.route("/", methods=['GET', 'POST'])
@auth.login_required
def index():
    class NewTaskForm(Form):
        name = StringField('Name:')
        link = StringField('Link:')
    form = NewTaskForm(request.form)

    if request.method == 'POST':
        name = request.form['name']
        link = request.form['link']
        try:
            url_validator(link)
            valid_link = True
        except ValidationError:
            valid_link = False
        if form.validate() and valid_link:
            man.add_new_task(link, name)
            flash('Add new task succeed ' + name)
        else:
            if name != '' and link != '' and not valid_link:
                flash('Error: Link is not valid. ')
            else:
                flash('Error: All the form fields are required. ')
        return redirect(url_for('back'))
    res_down, res_up, res_err = man.status()
    info = ''
    for x in res_down: info += x['formatedstring'] + '\n'
    for x in res_up: info += x['formatedstring'] + '\n'
    for x in res_err: info += x['formatedstring'] + '\n'

    wb = ''
    if not man.auth_ready:
        wb = "<br><div class=\"alert alert-danger\">"
        wb += "<a href=\"/authGD\">Authentication Required with Google Drive</a></div>"
    return render_template('GDD.html', form=form, GDDstatus=info.replace('\n', '<br>'), WarningBar=wb)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)

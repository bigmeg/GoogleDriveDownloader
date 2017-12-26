from flask import Flask, render_template, flash, request, make_response, redirect, url_for
from wtforms import Form, StringField
from flask_httpauth import HTTPBasicAuth
from transport import Manager
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import os

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


def url_exist(url):
    try:
        url_validator(url)
        return True
    except ValidationError:
        return False


@auth.get_password
def get_password(username):
    if username == USERNAME:
        return PASSWORD
    return None


@auth.error_handler
def unauthorized():
    return make_response("error: Unauthorized access", 401)


class ReusableForm(Form):
    name = StringField('Name:')
    link = StringField('Link:')


@app.route("/back", methods=['GET'])
@auth.login_required
def back():
    return redirect(url_for('index'))


@app.route("/", methods=['GET', 'POST'])
@auth.login_required
def index():
    form = ReusableForm(request.form)

    print(form.errors)
    if request.method == 'POST':
        name = request.form['name']
        link = request.form['link']
        valid_link = url_exist(link)
        if form.validate() and valid_link:
            # Save the comment here.
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
    return render_template('GDD.html', form=form, GDDstatus=info.replace('\n', '<br>'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)

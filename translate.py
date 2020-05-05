import pickle
import subprocess as sp
import os
import time
from urllib.parse import urlparse, urljoin
import json
import datetime
import string
from random import choice
import gc
from functools import wraps
import re

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_file, send_from_directory
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
from pymysql import escape_string as thwart
import sqlite3
from sqlalchemy import create_engine
from websocket import create_connection
import pycld2
from flask_mail import Mail, Message
from iso639 import languages as iso_languages

from dbconnect import connection
import request_handler
from highlight import highlight
from file_uploader import upload_webpage, upload_tm, upload_translations, tm_extensions, td_extensions
from language_util import get_lang_directions

rh = request_handler.RequestHandler()

app = Flask(__name__)

euser = os.environ["EMAILUSER"]
epass = os.environ["EMAILPASSWORD"]
    
mail_settings = {
        "MAIL_SERVER": 'smtp.gmail.com',
        "MAIL_PORT": 465,
        "MAIL_USER_TLS": False,
        "MAIL_USE_SSL": True,
        "MAIL_USERNAME": euser,
        "MAIL_PASSWORD": epass
    }

app.config.update(mail_settings)
mail = Mail(app)

key = os.environ["SECRETKEY"]
app.secret_key = key

UPLOAD_FOLDER = os.environ["UPLOAD_FOLDER"] 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def upload_files(request, username):
    email_address = request.form["emailaddress"]

    sendtmx = False
    if "sendtmx" in request.form and request.form["sendtmx"] == "on" and email_address != "":
        sendtmx = True

    if "webpage-url-original" in request.form.keys():
        upload_webpage(request.form, username, email_address, sendtmx)
    elif "tm-file" in request.files:
        upload_tm(request.files, username, email_address, sendtmx)
    elif "original-doc" in request.files and "translation-doc" in request.files:
        upload_translations(request.files, username, email_address, sendtmx)
    else:
        flash("No file selected", "uploaderror")

    return redirect(url_for("index"))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        if session:
            username = session['username']
        else:
            username = 'anonymous'

        upload_files(request, username)

    return render_template('index.html', tds=', .'.join(td_extensions),
        tms=', .'.join(tm_extensions))

@app.route('/ui/<ui_name>')
def show_ui(ui_name):
    with open('ui_db.pickle', 'rb') as f:
        ui_db = pickle.load(f)

    if ui_name in ui_db.keys():
        ui_config = ui_db[ui_name].copy()

        return render_template('ui.html', ui_config=ui_config)

    return 'No such UI'

def validate_ui_form(form):
    errors = {}
    ui_key = form['key']
    lp = request.form['lang_pairs']
    if not sha256_crypt.verify(ui_key, os.environ['UI_KEY']):
        errors['key'] = "Wrong key"
    if form['name'] == '':
        errors['name'] = "No name specified"
    if lp == '':
        errors['lang_pairs'] = "No language pairs specified"
    return errors

@app.route('/new_ui', methods=['GET', 'POST'])
def new_ui():
    with open('ui_db.pickle', 'rb') as f:
        ui_db = pickle.load(f)
    if request.method == 'POST':
        url_name = request.form['name'].lower()
        url_name = re.sub('\W+', '_', url_name)
        url_name = re.sub('^_|_$', '', url_name)

        pairs = request.form['lang_pairs']
        src_langs, tgt_langs = get_lang_directions(pairs)
        print(src_langs)
        print(tgt_langs)

        errors = validate_ui_form(request.form)
        if errors != {}:
            return render_template('new_ui.html', prev_form=request.form, errors=errors)

        ui_db[url_name] = {
            'name': request.form['name'],
            'name_color': request.form['name_color'],
            'banner_color': request.form['banner_color'],
            'src_langs': src_langs,
            'tgt_langs': tgt_langs,
        }

        with open('ui_db.pickle', 'wb') as f:
            pickle.dump(ui_db, f)

        return redirect(url_for('show_ui', ui_name=url_name))

    return render_template('new_ui.html', prev_form={}, errors={})

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/fix_language')
def fix_language():
    return render_template('fix_language.html', no_logos=True,
        fix_language=True)

@app.route('/about_fix_language')
def about_fix_language():
    return render_template('about.html', no_logos=True, fix_language=True)

@app.route('/highlight_test')
def highlight_test():
    return render_template('highlight_test.html', no_logos=True)

@app.route('/goethe', methods=['GET', 'POST'])
def goethe():
    if request.method == 'POST':
        if session:
            username = session['username']
        else:
            username = 'anonymous'

        upload_files(request, username)

    return render_template('goethe.html', tds=', .'.join(td_extensions),
        tms=', .'.join(tm_extensions), no_logos=True, goethe=True)

@app.route('/about_goethe')
def about_goethe():
    return render_template('about.html', no_logos=True, goethe=True)

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for('login_page'))
        
    return wrap

@app.route("/userpage", methods=["GET", "POST"])
@login_required
def user_page():
    if session:
        username = session["username"]

    if request.method == "POST":
        c, conn = connection()
        data = c.execute("SELECT * FROM users WHERE username = (%s)", username)
        
        data = c.fetchone()['password']
        
        if sha256_crypt.verify(request.form['current_pass'], data):
            password = sha256_crypt.encrypt((str(request.form["new_pass"])))
            c.execute("UPDATE users SET password = (%s) WHERE username = (%s)", (password, username))
            conn.commit()

            flash("Password changed")
        else:
            flash("Wrong password")

        c.close()
        conn.close()
        gc.collect()
        return redirect(url_for("user_page"))

    return render_template("userpage.html", username=username)

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = thwart(request.form["username"])
        c, conn = connection()
        
        data = c.execute("SELECT * FROM users WHERE username = (%s)", username)

        if data == 0:
            c.close()
            gc.collect()
            flash('See your email for further instructions.')
            return redirect(url_for("login_page"))
        
        email = c.fetchone()['email']

        allchar = string.ascii_letters + string.digits
        token = "".join(choice(allchar) for x in range(18))
        
        c.execute("INSERT INTO tokens (username, token) VALUES ((%s), (%s))", (username, token))
        conn.commit()
        
        c.close()
        conn.close()
        gc.collect()

        with app.app_context():
            msg = Message(subject="Account management",
                    sender=app.config.get("MAIL_USERNAME"),
                    recipients=[email],
                    body='Follow this link to reset your Fiskmö and Opus Repository account password:\n\n'+os.environ['TRBASEURL']+'/reset_password/'+token+'\n\nThe link will expire in 60 minutes.')
            mail.send(msg)
        flash('See your email for further instructions.')
        return redirect(url_for("login_page"))

    return render_template("forgot_password.html")

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    c, conn = connection()
        
    data = c.execute("SELECT * FROM tokens WHERE token = (%s)", token)

    if data == 0:
        flash("Invalid password reset link")
        return redirect(url_for("index"))

    values = c.fetchone()
    date = values['timestamp']
    
    if datetime.datetime.now().timestamp()-date.timestamp() > 3600:
        c.execute("DELETE FROM tokens WHERE token =(%s)", token)
        conn.commit()
        c.close()
        conn.close()
        gc.collect()
        flash("Invalid password reset link")
        return redirect(url_for("index"))

    username = values['username']

    if request.method == "POST":
        if request.form["password"] != request.form["confirm_password"]:
            flash("The passwords must match")
            return redirect(url_for("reset_password", token=token))
        elif request.form["password"] == "":
            flash("The password cannot be empty")
            return redirect(url_for("reset_password", token=token))
        else:
            password = sha256_crypt.encrypt((request.form["password"]))
            c.execute("UPDATE users SET password = (%s) WHERE username = (%s)", (password, username))
            c.execute("DELETE FROM tokens WHERE token =(%s)", token)
            conn.commit()
            c.close()
            conn.close()
            gc.collect()
            flash("Password updated successfully!")
            return redirect(url_for("login_page"))
    
    c.close()
    conn.close()
    gc.collect()
    return render_template("reset_password.html")
  
@app.route('/translate')
def translate():
    text = request.args.get('sent', 'empty', type=str)
    direction = request.args.get('direction', 'empty', type=str)
    model = request.args.get('model', 'empty', type=str)
    do_highlight = request.args.get('highlight', 0, type=int)

    text = text[:500]
    source, target = direction.split('-')

    input_json = {'text': text, 'source': source, 'target': target}
    if model != 'empty':
        input_json['model'] = model
    
    if text.strip() == '':
        return jsonify(result='')

    host = os.environ['TRANSLATION_HOST']
    port = os.environ['TRANSLATION_PORT']

    ws = create_connection('ws://{}:{}/translate'.format(host, port))

    ws.send(json.dumps(input_json))
    response = ws.recv()
    response = json.loads(response)

    ws.close()

    if do_highlight == 1 and 'alignment' in response.keys():
        if 'source-sentences' in response.keys():
            source_seg, target_seg, all_segs = highlight(response, raw=True)
        else:
            source_seg, target_seg, all_segs = highlight(response, raw=False)
        
        return jsonify(source_seg=source_seg, target_seg=target_seg,
            all_segs=list(all_segs), result=response['result'])
    else:
        return jsonify(source_seg=source, target_seg=response['result'],
            all_segs='', result=response['result'])


'''
@app.route('/translate')
def translate():
    text = request.args.get('sent', 'empty', type=str)

    if text.strip() == "":
        return jsonify(result="")

    text = text[:500]

    direction = request.args.get('direction', 'empty', type=str)

    if direction[:2] == "DL":
        sourcelan = pycld2.detect(text)[2][0][1]
        if sourcelan != "fi":
            sourcelan = "sv"
        direction = sourcelan + direction[2:]
        if direction == "fi-fi":
            direction = "fi-sv"
        elif direction in ["sv-sv", "sv-no", "sv-da"]:
            direction = "sv-fi"

    if direction in ["da-fi", "no-fi", "sv-fi"]:
        ws = create_connection("ws://localhost:{}/translate".format(5003))
        preprocess = "preprocess_danosv.sh"
    elif direction in ["fi-da", "fi-no", "fi-sv"]:
        ws = create_connection("ws://localhost:{}/translate".format(5004))
        preprocess = "preprocess_fi.sh"
    else:
        return jsonify(result="translation direction not found")

    sourcelan = direction[:2]
    targetlan = direction[-2:]

    paragraphs = text.split("\n")
    
    batch = ""
    for paragraph in paragraphs:
        sentences = sp.Popen([os.environ["TRSCRIPTS"]+"split.sh", paragraph], stdout=sp.PIPE).stdout.read().decode("utf-8")
        sentences = sentences[:-1].split("\n")
        for sentence in sentences:
            sentence = sp.Popen([os.environ["TRSCRIPTS"]+preprocess, sentence, sourcelan], stdout=sp.PIPE).stdout.read().decode("utf-8").strip()
            if sourcelan == "fi" and targetlan in ["da", "no", "sv"] and sentence != "":
                sentence = ">>"+targetlan+"<< "+sentence
            batch += "\n"+sentence

    batch = batch.strip()
    ws.send(batch)

    translation_temp = ws.recv().strip()
    translation = ""
    prev = "start"
    linestart = {"start": "", "txt": " ", "br": "\n"}

    for i in translation_temp.split("\n"):
        line = sp.Popen([os.environ["TRSCRIPTS"]+"postprocess.sh", i], stdout=sp.PIPE).stdout.read().decode("utf-8").strip()
        if line == "":
            translation += "\n"
            prev = "br"
        else:
            translation += linestart[prev] + line
            prev = "txt"

    ws.close()

    return jsonify(result=translation, source=sourcelan, target=targetlan)
'''

@app.route('/suggest/')
def suggest():
    if session:
        username = session['username']
    else:
        username = request.remote_addr
        
    direction = request.args.get('direction', 'empty', type=str)
    source = request.args.get('source', 'empty', type=str)
    suggestion = request.args.get('suggestion', 'empty', type=str)
    suggestion = suggestion[:500]
    
    c, conn = connection()

    c.execute("INSERT INTO suggestions (username, direction, source, suggestion) VALUES (%s, %s, %s, %s)",
              (thwart(username), thwart(direction), thwart(source), thwart(suggestion)))
    conn.commit()
    c.close()
    conn.close()
    gc.collect()

@app.route('/report/')
def report():
    if session:
        username = session['username']
    else:
        username = request.remote_addr

    direction = request.args.get('direction', 'empty', type=str)
    source = request.args.get('source', 'empty', type=str)
    sentence = request.args.get('sentence', 'empty', type=str)

    c, conn = connection()

    c.execute("INSERT INTO rubbish (username, direction, source, sentence) VALUES (%s, %s, %s, %s)",
              (thwart(username), thwart(direction), thwart(source), thwart(sentence)))
    conn.commit()
    c.close()
    conn.close()
    gc.collect()

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@app.route('/login/', methods=["GET", "POST"])
def login_page():
    error = ''
    try:
        c, conn = connection()
        if request.method == "POST":
            data = c.execute("SELECT * FROM users WHERE username = (%s)",
                             thwart(request.form['username']))
            
            data = c.fetchone()['password']
            
            if sha256_crypt.verify(request.form['password'], data):
                session['logged_in'] = True
                session['username'] = request.form['username']
                
                flash("You are now logged in")

                next_url = request.args.get('next')

                if not is_safe_url(next_url):
                    return flask.abort(400)

                return redirect(url_for("index"))
            
            else:
                error = "Invalid credentials, try again."
                
        gc.collect()
                
        return render_template("login.html", error=error)

    except Exception as e:
        error = "Invalid credentials, try again."
        return render_template("login.html", error=error)

class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=20)])
    email = TextField('Email Address', [validators.Length(min=6, max=50)])
    password = PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    
@app.route('/register/', methods=["GET", "POST"])
def register_page():
    try:
        form = RegistrationForm(request.form)

        if request.method == "POST" and form.validate():
            username = form.username.data
            email = form.email.data
            password = sha256_crypt.encrypt((str(form.password.data)))
            c, conn = connection()

            x =  c.execute("SELECT * FROM users WHERE username = (%s)", (thwart(username)))

            if int(x) > 0:
                error = "That username is already taken, please choose another"
                return render_template('register.html', form=form, error=error)

            else:
                c.execute("INSERT INTO users (username, password, email, tracking) VALUES (%s, %s, %s, %s)",
                         (thwart(username), thwart(password), thwart(email), thwart("translate")))
                response = rh.post("/group/"+thwart(username), {"uid": thwart(username)})
                conn.commit()
                flash("Thanks for registering!")
                c.close()
                conn.close()
                gc.collect()

                session['logged_in'] = True
                session['username'] = username

                return redirect(url_for('index'))

        return render_template("register.html", form=form)

    except Exception as e:
        return(str(e))

@app.route("/logout/")
@login_required
def logout():
    session.clear()
    flash("You have been logged out!")
    gc.collect()
    return redirect(url_for('index'))

if __name__=='__main__':
    app.run()

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_file, send_from_directory
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
from pymysql import escape_string as thwart
import gc
from dbconnect import connection
from functools import wraps
import sqlite3
from sqlalchemy import create_engine
import pickle
from websocket import create_connection
import subprocess as sp
import os
from werkzeug.utils import secure_filename
import time
import re
from urllib.parse import urlparse, urljoin
import json
import datetime
import request_handler
import pycld2
from flask_mail import Mail, Message
import string
from random import choice

rh = request_handler.RequestHandler()

import traceback

app = Flask(__name__)

with open("secrets/euser") as f:
    euser = f.read()[:-1]

with open("secrets/epass") as f:
    epass = f.read()[:-1]
    
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

UPLOAD_FOLDER = "/var/www/uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

tm_extensions = ['tmx', 'xliff']
td_extensions = ['xml', 'html', 'txt', 'pdf', 'doc']
ALLOWED_EXTENSIONS_tm = set(tm_extensions)
ALLOWED_EXTENSIONS_td = set(td_extensions)
def allowed_file(filename, ftype):
    if ftype == "tm":
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_tm
    elif ftype == "td":
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_td        

with open("secrets/secretkey") as f:
    key = f.read()[:-1].encode("utf-8")
app.secret_key = key

opusapi_connection = create_engine('sqlite:///opusdata.db')

@app.route('/', methods=["GET", "POST"])
def index():
    try:
        if request.method == "POST":
            if session:
                username = session["username"]
            else:
                username = "anonymous"
            email_address = request.form["emailaddress"]
            if "tm-file" in request.files:
                tm_file = request.files["tm-file"]
                if tm_file.filename == "":
                    flash("No file selected", "error")
                    return redirect(url_for("index"))
                if tm_file and allowed_file(tm_file.filename, "tm"):
                    tm_filename = secure_filename(tm_file.filename)
                    extension = re.search("(\..*)$", tm_filename).group(1)
                    tm_timename = datetime.datetime.today().strftime('%Y%m%d-%H%M%S')
                    tm_file.save(os.path.join(app.config['UPLOAD_FOLDER'], tm_timename+extension))
                    path = username + "/" + username + "/uploads/tm/" + tm_timename + extension
                    response = rh.upload("/storage/" + path, {"uid": username}, UPLOAD_FOLDER+"/"+tm_timename+extension)
                    response = rh.put("/metadata/" + path, {"uid": username, "original_name": tm_filename, "email": email_address})
                    os.remove(UPLOAD_FOLDER+"/"+tm_timename+extension)
                    flash('File "' + tm_file.filename + '" uploaded')
                else:
                    flash("Invalid file format", "error")
            if "original-doc" in request.files and "translation-doc" in request.files:
                original_doc = request.files["original-doc"]
                translation_doc = request.files["translation-doc"]
                if original_doc.filename == "" or translation_doc.filename == "":
                    flash("No file selected", "error")
                    return redirect(url_for("index"))
                if original_doc and translation_doc and allowed_file(original_doc.filename, "td") and allowed_file(translation_doc.filename, "td"):
                    original_docname = secure_filename(original_doc.filename)
                    translation_docname = secure_filename(translation_doc.filename)
                    
                    original_extension = re.search("(\..*)$", original_docname).group(1)
                    translation_extension = re.search("(\..*)$", translation_docname).group(1)

                    if original_extension != translation_extension:
                        flash("The file formats have to match ("+original_extension+" vs "+translation_extension+")", "error")
                        return redirect(url_for("index"))
                    
                    datename = datetime.datetime.today().strftime('%Y%m%d-%H%M%S')

                    original_doc.save(os.path.join(app.config['UPLOAD_FOLDER'], "org"+datename+original_extension))
                    path = username + "/" + username + "/uploads/original/" + datename + original_extension
                    response = rh.upload("/storage/" + path, {"uid": username}, UPLOAD_FOLDER+"/org"+datename+original_extension)
                    response = rh.put("/metadata/" + path, {"uid": username, "original_name": original_docname, "email": email_address})
                    os.remove(UPLOAD_FOLDER+"/org"+datename+original_extension)
                    
                    translation_doc.save(os.path.join(app.config['UPLOAD_FOLDER'], "tra"+datename+translation_extension))
                    path = username + "/" + username + "/uploads/translation/" + datename + translation_extension
                    response = rh.upload("/storage/" + path, {"uid": username}, UPLOAD_FOLDER+"/tra"+datename+translation_extension)
                    response = rh.put("/metadata/" + path, {"uid": username, "original_name": translation_docname, "email": email_address})
                    os.remove(UPLOAD_FOLDER+"/tra"+datename+translation_extension)
                    
                    flash('Files "' + original_doc.filename + '" and "' + translation_doc.filename + '" uploaded')
                else:
                    flash("Invalid file format", "error")

            return redirect(url_for("index"))

        return render_template("index.html", tds = ", .".join(td_extensions), tms = ", .".join(tm_extensions))
    except:
        traceback.print_exc()    

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
    try:
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
    except:
        traceback.print_exc()

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    try:
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
                        body='Follow this link to reset your Fiskmö account password:\n\nhttps://translate.ling.helsinki.fi/reset_password/'+token+'\n\nThe link will expire in 60 minutes.')
                mail.send(msg)
            flash('See your email for further instructions.')
            return redirect(url_for("login_page"))

        return render_template("forgot_password.html")
    except:
        traceback.print_exc()

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
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

    except:
        traceback.print_exc()
  
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

    translation = ""
    
    for paragraph in paragraphs:
        if paragraph.strip() == "":
            translation += "\n"
            continue

        sentences = sp.Popen(["./scripts/split.sh", paragraph], stdout=sp.PIPE).stdout.read().decode("utf-8")
        sentences = sentences[:-1].split("\n")
    
        for sentence in sentences:
            sentence = sp.Popen(["./scripts/"+preprocess, sentence, sourcelan], stdout=sp.PIPE).stdout.read().decode("utf-8").strip()
            if sourcelan == "fi" and targetlan in ["da", "no", "sv"]:
                sentence = ">>"+targetlan+"<< "+sentence

            ws.send(sentence)
            translation_temp = ws.recv().strip()
            translation_temp = sp.Popen(["./scripts/postprocess.sh", translation_temp], stdout=sp.PIPE).stdout.read().decode("utf-8").strip()

            translation = translation + translation_temp + " "
        translation = translation[:-1] + "\n"

    ws.close()

    translation = translation[:-1]

    return jsonify(result=translation, source=sourcelan, target=targetlan)

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

    
def make_sql_command(parameters, direction):
    sql_command = "SELECT * FROM opusfile WHERE "
    
    so = parameters[0][1]
    ta = parameters[1][1]
    
    if direction:
        sql_command += "((source='"+so+"' AND target='"+ta+"') OR (source='"+so+\
                       "' AND target='') OR (source='"+ta+"' AND target='')) AND "
        parameters[0] = ("source", "#EMPTY#")
        parameters[1] = ("target", "#EMPTY#")
    
    if ta == "#EMPTY#" and so != "#EMPTY#":
        sql_command += "((source='"+so+"') or (target='"+so+"')) AND "
        parameters[0] = ("source", "#EMPTY#")
     
    for i in parameters:
        if i[1] != "#EMPTY#":
            sql_command += i[0] + "='" + i[1] + "' AND "

    sql_command = sql_command.strip().split(" ")
    sql_command = " ".join(sql_command[:-1])

    if direction and parameters[3][1] not in ["dic", "moses", "smt", "xml", "tmx", "wordalign"]:
        sql_command += " UNION SELECT url, size, source, target, corpus, preprocessing, version FROM opusfile WHERE source='"+so+"' AND target='"+ta+"' AND "        
        for i in parameters:
            if i[0] == "preprocessing":
                sql_command += "preprocessing='xml' AND "
            elif i[1] != "#EMPTY#":
                sql_command += i[0] + "='" + i[1] + "' AND "
        sql_command = sql_command.strip().split(" ")
        sql_command = " ".join(sql_command[:-1])

        
    print(sql_command)
    return sql_command
    
@app.route('/opusapi/')
def opusapi():
    source = request.args.get('source', '#EMPTY#', type=str)
    target = request.args.get('target', '#EMPTY#', type=str)
    corpus = request.args.get('corpus', '#EMPTY#', type=str)
    preprocessing = request.args.get('preprocessing', '#EMPTY#', type=str)
    version = request.args.get('version', '#EMPTY#', type=str)

    sou_tar = [thwart(source), thwart(target)]
    sou_tar.sort()

    direction = True
    if "#EMPTY#" in sou_tar or "" in sou_tar:
        sou_tar.sort(reverse=True)
        direction = False

    parameters = [("source", sou_tar[0]), ("target", sou_tar[1]), ("corpus", thwart(corpus)),
                  ("preprocessing", thwart(preprocessing)), ("version", thwart(version))]

    sql_command = make_sql_command(parameters, direction)
    #if sql_command == "SELECT url FROM opusfile":
    #    sql_command = sql_command + " LIMIT 10"

    conn = opusapi_connection.connect()
    query = conn.execute(sql_command)

    ret = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]

    return jsonify(corpora=ret)

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

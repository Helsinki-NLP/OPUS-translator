from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_file
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
import xml_parser

import traceback

UPLOAD_FOLDER = "/var/www/uploads"
ALLOWED_EXTENSIONS = set(['txt', 'xml', 'html', 'tar'])

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

with open("secrets/secretkey") as f:
    key = f.read()[:-1].encode("utf-8")
app.secret_key = key

opusapi_connection = create_engine('sqlite:///opusdata.db')

letsmt_connect = "curl --silent --show-error --cacert /var/www/cert/vm1637.kaj.pouta.csc.fi/ca.crt --cert /var/www/cert/vm1637.kaj.pouta.csc.fi/user/certificates/developers@localhost.crt:letsmt --key /var/www/cert/vm1637.kaj.pouta.csc.fi/user/keys/developers@localhost.key"

letsmt_url = "https://vm1637.kaj.pouta.csc.fi:443/ws"

previous_download = ""

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template("index.html")

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for('login_page'))
        
    return wrap

@app.route('/frontpage')
@login_required
def frontpage():
    if session:
        username = session['username']
            
    command = letsmt_connect.split() + ["-X", "GET", letsmt_url + "/storage?uid=" + username]
    corporaXml = sp.Popen(command, stdout=sp.PIPE).stdout.read().decode("utf-8")
    parser = xml_parser.XmlParser(corporaXml.split("\n"))
    corpora = parser.corporaForUser(username)

    command = letsmt_connect.split() + ["-X", "GET", letsmt_url + "/group?uid=" + username]
    groupsXml = sp.Popen(command, stdout=sp.PIPE).stdout.read().decode("utf-8")
    parser = xml_parser.XmlParser(groupsXml.split("\n"))
    groups = parser.groupsForUser(username)

    return render_template("frontpage.html", corpora=corpora, groups=groups)

@app.route('/create_corpus', methods=["GET", "POST"])
def create_corpus():
    if session:
        username = session['username']

    command = letsmt_connect.split() + ["-X", "GET", letsmt_url + "/group?uid=" + username]
    groupsXml = sp.Popen(command, stdout=sp.PIPE).stdout.read().decode("utf-8")
    parser = xml_parser.XmlParser(groupsXml.split("\n"))
    groups = parser.groupsForUser(username)            

    if request.method == "POST":
        corpusName = request.form["name"]
        if corpusName == "" or " " in corpusName or not all(ord(char) < 128 for char in corpusName):
            private = False
            if "private" in request.form.keys():
                private = True
            flash("Name must be ASCII only and must not contain spaces")
            return render_template("create_corpus.html", groups=groups, name=request.form['name'], domain=request.form['domain'], origin=request.form['origin'], description=request.form['description'], selectedgroup=request.form['group'], private=private)
        
        command = letsmt_connect.split() + ["-X", "PUT", letsmt_url + "/storage/" + corpusName + "?uid=" + username]
        response = sp.Popen(command, stdout=sp.PIPE).stdout.read().decode("utf-8")
        
        flash('Corpus "' + corpusName + '" created!')
        return redirect(url_for('frontpage'))

    return render_template("create_corpus.html", groups=groups)

@app.route('/create_group', methods=["GET", "POST"])
def create_group():
    if session:
        username = session['username']
    if request.method == "POST":
        groupName = request.form["name"]
        if groupName == "" or " " in groupName or not all(ord(char) < 128 for char in groupName):
            flash("Name must be ASCII only and must not contain spaces")
            return render_template("create_group.html", name=request.form['name'], members=request.form['members'], description=request.form['description'])
        command = letsmt_connect.split() + ["-X", "POST", letsmt_url + "/group/" + groupName + "?uid=" + username]
        response = sp.Popen(command, stdout=sp.PIPE).stdout.read().decode("utf-8")

        flash('Group "' + groupName + '" created!')
        return redirect(url_for('frontpage'))
        
    return render_template("create_group.html")

@app.route('/show_corpus/<corpusname>')
def show_corpus(corpusname):
    if session:
        username = session['username']
    command = letsmt_connect.split() + ["-X", "GET", letsmt_url + "/storage/" + corpusname + "?uid=" + username]
    branchesXml = sp.Popen(command, stdout=sp.PIPE).stdout.read().decode("utf-8")
    parser = xml_parser.XmlParser(branchesXml.split("\n"))
    branches = parser.branchesForCorpus(corpusname)
    
    return render_template("show_corpus.html", name=corpusname, branches=branches)

@app.route('/download/<filename>')
def download(filename):
    try:
        if session:
            username = session['username']
        command = letsmt_connect.split() + ["-X", "GET", letsmt_url + "/storage/mikkoslot/mikkotest/xml/en/html/" + filename + "?uid=" + username + "&action=download&archive=0"]
        ret = sp.Popen(command, stdout=sp.PIPE).stdout.read().decode("utf-8")
        timename = str(time.time())+"###TIME###"+filename
        global previous_download
        if previous_download != "":
            os.remove("/var/www/downloads/"+previous_download)
        previous_download = timename
        with open("/var/www/downloads/"+timename, "w") as f:
            f.write(ret)
        return send_file("/var/www/downloads/"+timename, attachment_filename=filename)
    except:
        traceback.print_exc()

@app.route('/letsmtui', methods=['GET', 'POST'])
def letsmtui():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timename = str(time.time())+"###TIME###"+filename
            directory = request.form['directory']
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], timename))
            if session:
                username = session['username']
            try:
                command = letsmt_connect.split() + ["-X", "PUT", letsmt_url + directory + "?uid=" + username, "--form", "payload=@/var/www/uploads/"+timename]
                ret = sp.Popen(command , stdout=sp.PIPE).stdout.read().decode("utf-8")
            except:
                traceback.print_exc()
            os.remove("/var/www/uploads/" + timename)
            flash("Uploaded file " + filename + " to " + directory)
            return redirect(url_for('letsmtui', directory=directory))
    return render_template("letsmt.html")

@app.route('/letsmt')
def letsmt():
    try:
        branch = request.args.get("branch", "", type=str)
        corpusname = request.args.get("corpusname", "", type=str)
        method = request.args.get("method", "GET", type=str)
        command = request.args.get("command", "/storage", type=str)
        action = request.args.get("action", "", type=str)
        payload = request.args.get("payload", "", type=str)
        if payload != "":
            payload = " --form payload=@/var/www/uploads/" + payload
        username = ""
        if session:
            username = session['username']
        if branch != "":
            apicommand = letsmt_connect.split() + ["-X", "GET", letsmt_url+"/storage/"+corpusname+"/"+branch+"/uploads?uid=" + username]
            uploadsContents = sp.Popen(apicommand, stdout=sp.PIPE).stdout.read().decode("utf-8")
            apicommand = letsmt_connect.split() + ["-X", "GET", letsmt_url+"/storage/"+corpusname+"/"+branch+"/xml?uid=" + username]
            xmlContents = sp.Popen(apicommand, stdout=sp.PIPE).stdout.read().decode("utf-8")
        else:
            ret = sp.Popen(letsmt_connect.split() + ["-X", method, letsmt_url+command+"?uid=" + username + action + payload], stdout=sp.PIPE).stdout.read().decode("utf-8")
        return jsonify(result=ret, testlist=["ok"])
    except Exception:
        traceback.print_exc()
        
@app.route('/translate')
def translate():
    text = request.args.get('sent', 'empty', type=str)

    if text.strip() == "":
        return jsonify(result="")

    text = text[:500]

    direction = request.args.get('direction', 'empty', type=str)

    if direction in ["da-fi", "no-fi", "sv-fi"]:
        ws = create_connection("ws://localhost:{}/translate".format(5003))
        preprocess = "preprocess_danosv.sh"
    elif direction in ["fi-da", "fi-no", "fi-sv"]:
        ws = create_connection("ws://localhost:{}/translate".format(5004))
        preprocess = "preprocess_fi.sh"

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


    return jsonify(result=translation)

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

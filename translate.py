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
import re
from urllib.parse import urlparse, urljoin
import request_handler

import traceback

rh = request_handler.RequestHandler()

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

    corporaXml = rh.get("/metadata", {"uid": username, "owner": username, "resource-type": "branch"})
    parser = xml_parser.XmlParser(corporaXml.split("\n"))
    corpora = parser.corporaForUser()
    corpora.sort()

    groupsXml = rh.get("/group/"+username, {"uid": username, "action": "showinfo"})
    parser = xml_parser.XmlParser(groupsXml.split("\n"))
    groups = parser.groupsForUser()
    groups.sort()

    return render_template("frontpage.html", corpora=corpora, groups=groups)

@app.route('/create_corpus', methods=["GET", "POST"])
@login_required
def create_corpus():
    if session:
        username = session['username']

    groupsXml = rh.get("/group/"+username, {"uid": username, "action": "showinfo"})
    parser = xml_parser.XmlParser(groupsXml.split("\n"))
    groups = parser.groupsForUser()
    groups.sort()

    if request.method == "POST":
        corpusName = request.form["name"]
        if corpusName == "" or " " in corpusName or not all(ord(char) < 128 for char in corpusName):
            private = False
            if "private" in request.form.keys():
                private = True
            flash("Name must be ASCII only and must not contain spaces")
            return render_template("create_corpus.html", groups=groups, name=request.form['name'], domain=request.form['domain'], origin=request.form['origin'], description=request.form['description'], selectedgroup=request.form['group'], private=private)

        parameters = {"uid": username}
        if request.form["group"] != "public":
            parameters["gid"] = request.form["group"]
        response = rh.put("/storage/"+corpusName+"/"+username, parameters)

        try:
            parameters = {"uid": username}
            for key in request.form.keys():
                if key in ["origin", "domain", "description"]:
                    parameters[key] = request.form[key]

            response = rh.put("/metadata/"+corpusName+"/"+username, parameters)
        except:
            traceback.print_exc()
            
        flash('Corpus "' + corpusName + '" created!')
        return redirect(url_for('frontpage'))

    return render_template("create_corpus.html", groups=groups)

@app.route('/create_group', methods=["GET", "POST"])
@login_required
def create_group():
    try:
        if session:
            username = session['username']

        usersXml = rh.get("/group/public", {"uid": username, "action": "showinfo"})
        parser = xml_parser.XmlParser(usersXml.split("\n"))
        users = parser.getUsers()
        for user in users:
            if user in ["admin", username]:
                users.remove(user)
        users.sort()

        if request.method == "POST":
            groupName = request.form["name"]
            if groupName == "" or " " in groupName or not all(ord(char) < 128 for char in groupName):
                flash("Name must be ASCII only and must not contain spaces")
                return render_template("create_group.html", name=request.form['name'], description=request.form['description'], users=users)

            response = rh.post("/group/"+groupName, {"uid": username})
            
            members = request.form["members"].split(",")

            for i in range(len(members)-1):
                response = rh.put("/group/"+groupName+"/"+members[i], {"uid": username})

            flash('Group "' + groupName + '" created!')
            return redirect(url_for('frontpage'))

        return render_template("create_group.html", users=users)
    except:
        traceback.print_exc()

@app.route('/show_corpus/<corpusname>')
@login_required
def show_corpus(corpusname):
    try:
        if session:
            username = session['username']

        branchesXml = rh.get("/storage/"+corpusname, {"uid": username})
        parser = xml_parser.XmlParser(branchesXml.split("\n"))
        branches = parser.branchesForCorpus()
        branches.sort()
    except:
        traceback.print_exc()
    
    return render_template("show_corpus.html", name=corpusname, branches=branches)

@app.route('/download/<filename>')
def download(filename):
    try:
        if session:
            username = session['username']

        ret = rh.get("/storage/mikkoslot/xml/en/html/"+filename, {"uid": username, "action": "download", "archive": "0"})
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
@login_required
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
@login_required
def letsmt():
    try:
        ret = ""

        method = request.args.get("method", "GET", type=str)
        command = request.args.get("command", "/storage", type=str)
        action = request.args.get("action", "", type=str)
        payload = request.args.get("payload", "", type=str)
        if payload != "":
            payload = " --form payload=@/var/www/uploads/" + payload
        username = ""
        if session:
            username = session['username']
        ret = sp.Popen(letsmt_connect.split() + ["-X", method, letsmt_url+command+"?uid=" + username + action + payload], stdout=sp.PIPE).stdout.read().decode("utf-8")
        return jsonify(result=ret)
    except Exception:
        traceback.print_exc()


@app.route('/get_branch')
@login_required
def get_branch():
    try:
        uploads = []
        monolingual = []
        parallel = []
        
        branch = request.args.get("branch", "", type=str)
        corpusname = request.args.get("corpusname", "", type=str)

        if session:
            username = session['username']

        uploadsContents = rh.get("/storage/"+corpusname+"/"+branch+"/uploads", {"uid": username})
        parser = xml_parser.XmlParser(uploadsContents.split("\n"))
        uploads = parser.navigateDirectory()

        xmlContents = rh.get("/metadata/"+corpusname+"/"+branch, {"uid": username})
        parser = xml_parser.XmlParser(xmlContents.split("\n"))
        monolingual, parallel = parser.getMonolingualAndParallel()
        
        return jsonify(uploads=uploads, parallel=parallel, monolingual=monolingual)
    except Exception:
        traceback.print_exc()

@app.route('/get_subdirs')
@login_required
def get_subdirs():
    try:
        subdirs = []
        
        branch = request.args.get("branch", "", type=str)
        corpusname = request.args.get("corpusname", "", type=str)
        subdir = request.args.get("subdir", "", type=str)

        if session:
            username = session['username']

        subdir = subdir.replace("-_-", "/")
        subdir = subdir.replace("monolingual", "xml")
        subdir = subdir.replace("parallel", "xml")

        subdirContents = rh.get("/storage/"+corpusname+"/"+branch+subdir, {"uid": username})
        parser = xml_parser.XmlParser(subdirContents.split("\n"))
        subdirs = parser.navigateDirectory()

        return jsonify(subdirs=subdirs)
    except Exception:
        traceback.print_exc()

@app.route('/upload_file', methods=['GET', 'POST'])
@login_required
def upload_file():
    try:
        if request.method == 'POST':
            path = request.form['path']
            m = re.search("^\/(.*?)\/(.*?)\/", path)
            corpus = m.group(1)
            branch = m.group(2)
            language = request.form['language']
            fileformat = request.form['format']
            description = request.form['description']
            direction = "unknown"
            autoimport = "false"
            if "direction" in request.form.keys():
                direction = request.form["direction"]
            if "autoimport" in request.form.keys():
                autoimport = "true"
            if 'file' not in request.files:
                flash('No file part')
                return redirect(url_for("upload_file", corpus=corpus, branch=branch, language=language, fileformat=fileformat, description=description, direction=direction, autoimport=autoimport))
            file = request.files['file']
            if file.filename == '':
                flash('No selected file')
                return redirect(url_for("upload_file", corpus=corpus, branch=branch, language=language, fileformat=fileformat, description=description, direction=direction, autoimport=autoimport))
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timename = str(time.time())+"###TIME###"+filename
                path = request.form['path']
                description = request.form['description']
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], timename))
                if session:
                    username = session['username']

                parameters = {"uid": username}
                if "autoimport" in request.form.keys():
                    parameters["action"] = "import"
                    #command = letsmt_connect.split() + ["-X", "PUT", letsmt_url + "/storage" + path + "?uid=" + username + "&action=import", "--form", "payload=@/var/www/uploads/"+timename]
                #else:
                    #command = letsmt_connect.split() + ["-X", "PUT", letsmt_url + "/storage" + path + "?uid=" + username, "--form", "payload=@/var/www/uploads/"+timename]
                '''
                print(command)
                ret = sp.Popen(command, stdout=sp.PIPE).stdout.read().decode("utf-8")
                '''
                files = {"file": open("/var/www/uploads/"+timename, "rb")}
                print(parameters)  
                ret = rh.upload("/storage" + path, parameters, files)
                print(ret)
                '''
                command = letsmt_connect.split() + ["-X", "PUT", letsmt_url + "/metadata" + path + "?uid=" + username + "&description=" + description + "&direction=" + direction]

                response = sp.Popen(command, stdout=sp.PIPE).stdout.read().decode("utf-8")
                '''
                response = rh.put("/metadata"+path, {"uid": username, "description": description, "direction": direction})
                traceback.print_exc()

                os.remove("/var/www/uploads/" + timename)
                flash('Uploaded file "' + filename + '" to "' + path + '"')

                return redirect(url_for('show_corpus', corpusname=corpus, branch=branch))

        return render_template("upload_file.html", formats=["txt", "html", "pdf", "doc", "tar"], languages=["da", "en", "fi", "no", "sv"])
    except:
        traceback.print_exc()
        
@app.route('/get_metadata')
@login_required
def get_metadata():
    try:
        if session:
            username = session['username']

        path = request.args.get("path", "", type=str)

        metadataXml = rh.get("/metadata"+path, {"uid": username})
        parser = xml_parser.XmlParser(metadataXml.split("\n"))
        metadata = parser.getMetadata()
        metadataKeys = list(metadata.keys()).copy()
        metadataKeys.sort()

        return jsonify(metadata = metadata, metadataKeys = metadataKeys)

    except:
        traceback.print_exc()

@app.route('/get_filecontent')
@login_required
def get_filecontent():
    if session:
        username = session['username']

    path = request.args.get("path", "", type=str)
    content = rh.get("/storage"+path, {"uid": username, "action": "download", "archive": "0"})
    
    return jsonify(content = content)
        
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

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
import xml_parser
import re
from urllib.parse import urlparse, urljoin
import request_handler
import json

import traceback

app = Flask(__name__)

with open("secrets/secretkey") as f:
    key = f.read()[:-1].encode("utf-8")
app.secret_key = key

opusapi_connection = create_engine('sqlite:///opusdata.db')

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
                response = rh.post("/group/"+thwart(username), {"uid": thwart(username)})
                print(response)
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

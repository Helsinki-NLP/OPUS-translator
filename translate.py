from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
from pymysql import escape_string as thwart
import gc
import socket
from dbconnect import connection
from functools import wraps
import sqlite3
from sqlalchemy import create_engine
import pickle

app = Flask(__name__)

with open("secrets/secretkey") as f:
    key = f.read()[:-1].encode("utf-8")
app.secret_key = key

opusapi_connection = create_engine('sqlite:///opusdata.db')

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/translate')
def translate():
    sock = socket.socket()

    sent = request.args.get('sent', 'empty', type=str)
    if sent.strip() == "":
        sock.close()
        return jsonify(result="")
    
    direction = request.args.get('direction', 'empty', type=str)
    if direction == "en-de":
        sock.connect(("localhost", 5001))
    elif direction == "en-fr":
        sock.connect(("localhost", 5002))
    elif direction in ["da-fi", "no-fi", "sv-fi"]:
        sock.connect(("localhost", 5003))
    
    sentencedata = [sent, direction[:2]]

    data = pickle.dumps(sentencedata)
    sock.send(data)
    translation = sock.recv(1024)

    sock.close()
    
    return jsonify(result=translation.decode('utf-8'))

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

    print(username, direction, source, suggestion, timestamp)

def make_sql_command(parameters, direction):
    sql_command = "SELECT url, size, source, target, corpus, preprocessing, version FROM opusfile WHERE "
    
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
    try:
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

    except Exception as e:
        print(e)

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
                
                #flash("You are now logged in")
                return redirect(url_for("index"))
            
            else:
                error = "Invalid credentials, try again."
                
        gc.collect()
                
        return render_template("login.html", error=error)

    except Exception as e:
        #flash(e)
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
                #flash("Thanks for registering!")
                c.close()
                conn.close()
                gc.collect()

                session['logged_in'] = True
                session['username'] = username

                return redirect(url_for('index'))

        return render_template("register.html", form=form)

    except Exception as e:
        return(str(e))

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            #flash("You need to login first")
            return redirect(url_for('login_page'))
        
    return wrap

@app.route("/logout/")
@login_required
def logout():
    session.clear()
    #flash("You have been logged out!")
    gc.collect()
    return redirect(url_for('index'))

if __name__=='__main__':
    app.run()

# OPUS-translator

OPUS-translator is an online translation demonstrator. OPUS-translator is a [Flask](http://flask.pocoo.org/) application that serves translation models online. The translation models are run on [Marian NMT](https://marian-nmt.github.io/). An example instance is running at [https://translate.ling.helsinki.fi/](https://translate.ling.helsinki.fi/).

## How to deploy OPUS-translator

The are two ways to deploy OPUS-translator:

1. Clone the project from GitHub.
2. Launch an instance from a snapshot on cPouta.

### Deployment method 1: Clone project from GitHub

Clone the repository.

`git clone https://github.com/Helsinki-NLP/OPUS-translator.git`

Compile Marian, see the [documentation](https://marian-nmt.github.io/docs/).

After compiling, run your models with `marian-server`, for example:

`./marian-dev/build/marian-server -c fi-danosv-config.yml > fi_danosv.log 2>&1 &`

This runs the model based on a configuration file and logs messages to a log file. The process is set to run in background. By default, the translator uses ports `5003` and `5004`, so set the port to one of those in the configuration file. `OPUS-translator/scripts/example_config` contains example configuration files.

Install [subword-nmt](https://github.com/rsennrich/subword-nmt).

`pip install subword-nmt`

Create a virtual environment and activate it.

```
python3 -m venv translatorenv
source translatorenv/bin/activate
```

Install requirements:

```
cd OPUS-translator
pip3 install -r requirements.txt
```

Set flask environment to development and set the flask app to `translate.py`:

```
export FLASK_ENV=development
export FLASK_APP=translate.py
```

There are also other environment variables that you need to set for user authenticiation, uploads, databases etc., but if you are only using the translation functionality, you can set them to dummy values.

```
export EMAILUSER=dummy
export EMAILPASSWORD=dummy
export DBUSER=dummy
export DBPASSWORD=dummy
export DBNAME=dummy
export SECRETKEY=dummy
export BACKENDCERT=dummy
export BACKENDKEY=dummy
export BACKENDCA=dummy
export BACKENDURL=dummy
export UPLOAD_FOLDER=dummy
```

Run the flask app.

`flask run`

Go to [localhost:5000](localhost:5000).

### Deployment method 2: cPouta

The following only works if you have access to project 2000661.

#### Launch an instance

Launch an instance from "translation_snapshot2" snapshot.

In order to have enough memory (4G) to run two translation models reliably, use "standard.medium" flavor.

On "Access & Security" tab, tick all checkboxes (Web, default, SSH) under "Security Groups".

#### Configure apache

Connect to you instance and go to Apache configuration file at `/etc/apache2/sites-available/translate.conf`

Change `ServerName` to your server name or ip-address.

If you want to use secure connection, you need to set up an SSL certificate. Secure connection is required if you want to keep usernames and passwords safe, when users are registering or logging in. [Let's Encrypt](https://letsencrypt.org/) offers free SSL certificates.
If you have an SSL certificate, replace `SSLCertificateFile` and `SSLCertificateKeyFile` with your files.

If you are not worried about usernames and passwords, you can set up the server without a secure connection. In this case, replace the contents of the configuration file with:

```
## /etc/apache2/sites-available/translate.conf

NameVirtualHost *:80
<VirtualHost *:80>
  ServerName <your_server_name_or_ip-address>

  WSGIDaemonProcess translate
  WSGIScriptalias / /home/cloud-user/translation-demo/translate.wsgi

<Directory /home/cloud-user/translation-demo/>
  WSGIProcessGroup translate
  WSGIApplicationGroup %{GLOBAL}
  WSGIScriptReloading On

  Require all granted
</Directory>

  ErrorLog ${APACHE_LOG_DIR}/error.log
  CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
    
```

Remember to change `<your_server_name_or_ip-address>` in the configuration file.

Restart apache server with:

```
sudo systemctl restart apache2
```

The application is now online at your ip-address, and it runs the translation models danosv-fi and fi-danosv.

#### Configure translation models

To stop running the current translation models, find the process ids for the models with:

```
ps -ef | grep model_server
```

Then kill each of the processes with:

```
kill <process-id>
```

To work with new translation models, first:

```
cd ~/translation-demo/model-server
```

To run a new translation model in the background and redirect errors to `<log-file>`, run:

```
python3 model_server.py <model_config_file> <port> <preprocess_script> <postprocess_script> <sentence_splitter_script> > <log_file> 2>&1 &
```

For example danosv-fi model is run with:

```
python3 model_server.py danosv-fi-config.yml 5003 preprocess_danosv.sh postprocess.sh split.sh > danosv-fi.log 2>&1 &
```

**There are currently a couple of hardcoded things that you need to change, if you use different models than the ones that are currently on the virtual machine:**

In `~/translation-demo/templates/index.html` under the `<select>` tag on line 7, change the option values and names to correspond with your translation directions.

In `~/translation-demo/translate.py` on line 35 onwards, there are if clauses that tie the translation directions from `index.html` to translation model server ports. Add a clause, where your option value from `index.html` is tied to the port where your translation model is served with `model_server.py`:

```
elif direction == <value_from_index.html>:
    sock.connect(("localhost", <port_from_model_server_command>)
```

After making changes to `translate.py`, restart the server with:

```
sudo systemctl restart apache2
```

Your model is now online at you ip-address


import os
import re
import datetime
import request_handler

from flask import flash
from werkzeug.utils import secure_filename

rh = request_handler.RequestHandler()

UPLOAD_FOLDER = os.environ["UPLOAD_FOLDER"] 

tm_extensions = ['tmx', 'xliff']
td_extensions = ['xml', 'html', 'txt', 'pdf', 'doc', 'srt', 'rtf', 'epub']

ALLOWED_EXTENSIONS_tm = set(tm_extensions)
ALLOWED_EXTENSIONS_td = set(td_extensions)

def allowed_file(filename, ftype):
    if ftype == "tm":
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_tm
    elif ftype == "td":
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_td        

def process_and_upload(document, datename, extension, username, docname, email_address, directory, sendtmx):
    document.save(os.path.join(UPLOAD_FOLDER, "org"+datename+extension))
    path = username + "/" + username + "/uploads/" + directory + "/" + datename + extension
    parameters = {"uid": username, "action": "import"}
    if sendtmx:
        parameters["email"] = email_address
    response = rh.upload("/storage/" + path, parameters, UPLOAD_FOLDER+"/org"+datename+extension)
    response = rh.post("/metadata/" + path, {"uid": username, "original_name": docname, "email": email_address})
    os.remove(UPLOAD_FOLDER+"/org"+datename+extension)

def upload_url(username, directory, datename, webpage, email_address, sendtmx):
    parameters = {"uid": username, "action": "import", "url": webpage}
    if sendtmx:
        parameters["email"] = email_address
    response = rh.put("/storage/"+username+"/"+username+"/uploads/url/"+directory+"/"+datename, parameters)
    rh.post("/metadata/"+username+"/"+username+"/uploads/url/"+directory+"/"+datename, {"uid": username, "original_url": webpage, "email": email_address})
    return response

def upload_webpage(form, username, email_address, sendtmx):
    webpage_original = form["webpage-url-original"]
    webpage_translation = form["webpage-url-translation"]
    if webpage_original == "" or webpage_translation == "":
        flash("No webpage selected", "uploaderror")
    else:
        datename = datetime.datetime.today().strftime('%Y%m%d-%H%M%S')
        datename = datename + ".html"
        response_original = upload_url(username, "original", datename, webpage_original, email_address, sendtmx)
        response_translation = upload_url(username, "translation", datename, webpage_translation, email_address, sendtmx)
        if 'type="error"' in response_original or 'type="error"' in response_translation:
            flash("Upload failed", "uploaderror")
        else:
            flash("Webpage uploaded!", "upload")

def upload_tm(files, username, email_address, sendtmx):
    tm_file = files["tm-file"]

    if tm_file.filename == "":
        flash("No file selected", "uploaderror")
        return redirect(url_for("index"))

    if tm_file and allowed_file(tm_file.filename, "tm"):
        tm_filename = secure_filename(tm_file.filename)
        extension = re.search("(\..*)$", tm_filename).group(1)
        tm_timename = datetime.datetime.today().strftime('%Y%m%d-%H%M%S')
        
        process_and_upload(tm_file, tm_timename, extension, username, tm_filename, email_address, "tm", sendtmx)
        flash('File "' + tm_file.filename + '" uploaded', "upload")
    else:
        flash("Invalid file format", "uploaderror")

def upload_translations(files, username, email_address, sendtmx):
    original_doc = files["original-doc"]
    translation_doc = files["translation-doc"]
    
    if original_doc.filename == "" or translation_doc.filename == "":
        flash("No file selected", "uploaderror")
        return redirect(url_for("index"))

    if original_doc and translation_doc and allowed_file(original_doc.filename, "td") and allowed_file(translation_doc.filename, "td"):
        original_docname = secure_filename(original_doc.filename)
        translation_docname = secure_filename(translation_doc.filename)
        
        original_extension = re.search("(\..*)$", original_docname).group(1)
        translation_extension = re.search("(\..*)$", translation_docname).group(1)

        if original_extension != translation_extension:
            flash("The file formats have to match ("+original_extension+" vs "+translation_extension+")", "uploaderror")
            return redirect(url_for("index"))
        
        datename = datetime.datetime.today().strftime('%Y%m%d-%H%M%S')
        process_and_upload(original_doc, datename, original_extension, username, original_docname, email_address, "original", sendtmx)
        process_and_upload(translation_doc, datename, translation_extension, username, translation_docname, email_address, "translation", sendtmx)

        flash('Files "' + original_doc.filename + '" and "' + translation_doc.filename + '" uploaded', "upload")
    else:
        flash("Invalid file format", "uploaderror")

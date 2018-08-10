import sys
with open("secrets/marianpath") as f:
    marianpath = f.read()[:-1]
sys.path.append(marianpath)
import libamunmt
import socket
import subprocess as sp
import pickle

configFile = sys.argv[1]
port = sys.argv[2]
preprocess = sys.argv[3]
postprocess = sys.argv[4]
splitter = sys.argv[5]

libamunmt.init("-c " + configFile)

s = socket.socket()
s.bind(("localhost", int(port)))

s.listen(5)

while True:
    c, addr = s.accept()
    
    data = c.recv(1024)

    sentencedata = pickle.loads(data)

    sentence = sentencedata[0]
    sourcelan = sentencedata[1]
    targetlan = sentencedata[2]
    sentence = sentence[:500]

    result = ""

    paragraphs = sentence.split("\n")

    for paragraph in paragraphs:

        if paragraph.strip() == "":
            result += "\n"
            continue
        
        sentences = sp.Popen(["./"+splitter, paragraph], stdout=sp.PIPE).stdout.read().decode('utf-8')
        sentences = sentences[:-1].split("\n")

        for sentence in sentences:
            sentence = sp.Popen(["./"+preprocess, sentence, sourcelan], stdout=sp.PIPE).stdout.read().decode('utf-8').strip()

            if sourcelan == "fi" and targetlan in ["da", "no", "sv"]:
                sentence = ">>"+targetlan+"<< "+sentence
            
            sentence = [sentence]
            translation = libamunmt.translate(sentence)
            translation = " ".join(translation)

            translation = translation.replace("@@ ", "")
            translation = translation.replace("&quot;", '"')
            translation = translation.replace("&apos;", "'")
            translation = sp.Popen(["./"+postprocess, translation], stdout=sp.PIPE).stdout.read().decode('utf-8').strip()

            result = result + translation + " "

        result += "\n"

    result = result[:-1]
    c.send(bytes(result, 'utf-8'))

    c.close()
    

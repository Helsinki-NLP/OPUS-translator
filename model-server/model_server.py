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
    print(data)
    sentencedata = pickle.loads(data)
    print(sentencedata)
    sentence = sentencedata[0]
    language = sentencedata[1]
    sentence = sentence[:500]
    sentences = sp.Popen(["./"+splitter, sentence], stdout=sp.PIPE).stdout.read().decode('utf-8')
    sentences = sentences[:-1].split("\n")

    result = ""
    
    for sentence in sentences:
        sentence = sp.Popen(["./"+preprocess, sentence, language], stdout=sp.PIPE).stdout.read().decode('utf-8').strip()
        sentence = [sentence]
    
        translation = libamunmt.translate(sentence)
        translation = " ".join(translation)

        translation = translation.replace("@@ ", "")
        translation = translation.replace("&quot;", '"')
        translation = translation.replace("&apos;", "'")

        result = result + translation + " "

    result = sp.Popen(["./"+postprocess, result], stdout=sp.PIPE).stdout.read().decode('utf-8').strip()
    
    c.send(bytes(result, 'utf-8'))

    c.close()
    

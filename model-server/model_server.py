import sys
with open("/home/cloud-user/secrets/marianpath") as f:
    marianpath = f.read()[:-1]
sys.path.append(marianpath)
import libamunmt
import socket
import subprocess as sp

libamunmt.init("-c " + sys.argv[1])

s = socket.socket()
s.bind(("localhost", int(sys.argv[2])))

s.listen(5)

while True:
    c, addr = s.accept()
    
    sentence = c.recv(1024)
    sentence = sentence.decode('utf-8')
    sentence = sp.Popen(["./preprocess.sh", sentence], stdout=sp.PIPE).stdout.read().decode('utf-8').strip()
    sentence = [sentence]
    
    translation = libamunmt.translate(sentence)
    translation = " ".join(translation)

    translation = translation.replace("@@ ", "")
    translation = translation.replace("&quot;", '"')
    translation = translation.replace("&apos;", "'")

    c.send(bytes(translation, 'utf-8'))

    c.close()
    

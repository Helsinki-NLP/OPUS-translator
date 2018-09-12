import xml.parsers.expat
import re

class XmlParser:

    def __init__(self, xmlData):
        self.xmlData = xmlData
        self.start = ""
        self.attrs = {}
        self.chara = ""
        self.end = ""

        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler = self.startElement
        self.parser.CharacterDataHandler = self.charData
        self.parser.EndElementHandler = self.endElement

    def startElement(self, name, attrs):
        self.start = name
        self.attrs = attrs

    def charData(self, data):
        self.chara = data

    def endElement(self, name):
        self.end = name

    def parseLine(self, line):
        self.parser.Parse(line)
        return('"'+self.start+'"', '"'+self.chara+'"', '"'+self.end+'"', self.attrs)
        
    def parse(self):
        for line in self.xmlData:
            print(self.parseLine(line))

    def groupsForUser(self):
        groups = []
        for line in self.xmlData:
            self.parseLine(line)
            if self.start == "member_of" and self.end == "member_of":
                groups = self.chara.split(",")
                break
        return groups

    def corporaForUser(self):
        corpora = []
        for line in self.xmlData:
            self.parseLine(line)
            if self.start == "entry" and self.end == "entry":
                m = re.search("^(.*)\/", self.attrs["path"])
                if m.group(1) not in corpora:
                    corpora.append(m.group(1))
        return corpora
            
    def branchesForCorpus(self, corpus):
        branches = []
        for line in self.xmlData:
            self.parseLine(line)
            if self.start == "name" and self.end == "name":
                branches.append(self.chara)
        return branches

    def getUsers(self):
        users = []
        for line in self.xmlData:
            self.parseLine(line)
            if self.start == "user" and self.end == "user":
                users.append(self.chara)
        return users

    def navigateDirectory(self):
        dirs = []
        entryFound = False
        kind = ""
        for line in self.xmlData:
            self.parseLine(line)
            if self.start == "entry":
                kind = self.attrs["kind"]
            if self.start == "name" and kind in ["dir", "file"]:
                dirs.append([self.chara, kind])
                kind = ""
        return dirs
    
'''
xmlData = """
<letsmt-ws version="56">
  <list path="/group/">
    <entry id="public" kind="group" owner="admin">
      <user>mikkotest</user>
      <user>admin</user>
      <user>mikkotest5</user>
      <user>mikkotest3</user>
    </entry>
  </list>
  <status code="0" location="/group/public" operation="GET" type="ok"></status>
</letsmt-ws>
"""

parser = XmlParser(xmlData.split("\n"))

print(parser.getUsers())
'''


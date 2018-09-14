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
            
    def branchesForCorpus(self):
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

    def getMonolingualAndParallel(self):
        monolingual_pre = []
        parallel_pre = []
        for line in self.xmlData:
            self.parseLine(line)
            if self.start == "langs":
                monolingual_pre = self.chara.split(",")
            elif self.start == "parallel-langs":
                parallel_pre = self.chara.split(",")
            if monolingual_pre != [] and parallel_pre != []:
                break
        monolingual = [[x, "dir"] for x in monolingual_pre]
        parallel = [[x, "dir"] for x in parallel_pre]
        return (monolingual, parallel)

    def getMetadata(self):
        metadata = {}
        storeValues = False
        for line in self.xmlData:
            self.parseLine(line)
            if self.end == "entry":
                storeValues = False
            if storeValues and self.start != "":
                metadata[self.start] = self.chara
            if self.start == "entry":
                storeValues = True
                if "path" in self.attrs.keys():
                    metadata["path"] = self.attrs["path"]
        return metadata

'''
xmlData = """
<letsmt-ws version="56">
  <list path="">
    <entry path="testcorpus/mikkotest/uploads/html/fi/1.html">
      <description></description>
      <gid>mikkotest</gid>
      <import_runtime>3</import_runtime>
      <imported_to>xml/fi/1.xml</imported_to>
      <owner>mikkotest</owner>
      <status>imported</status>
    </entry>
  </list>
  <status code="0" location="/metadata/testcorpus/mikkotest/uploads/html/fi/1.html" operation="GET" type="ok">Found matching path ID. Listing all of its properties</status>
</letsmt-ws>
"""

parser = XmlParser(xmlData.split("\n"))

print(parser.getMetadata())

'''

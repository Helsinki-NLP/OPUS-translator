import xml.parsers.expat

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

    def groupsForUser(self, username):
        groups = []
        currentGroup = ""
        for line in self.xmlData:
            info = self.parseLine(line)
            if self.start == "entry" and "id" in self.attrs.keys() and "kind" in self.attrs.keys():
                if self.attrs["kind"] == "group":
                    currentGroup = self.attrs["id"]
            if self.start == "user" and self.end == "user" and self.chara == username:
                groups.append(currentGroup)
        return groups

    def corporaForUser(self, username):
        # TODO: filtering by username
        corpora = []
        for line in self.xmlData:
            info = self.parseLine(line)
            if self.start == "name" and self.end == "name":
                corpora.append(self.chara)
        return corpora
            
'''         
xmlData = """<letsmt-ws version="55">
  <list path="/">
    <entry kind="slot">
      <name>slot_name914804797226</name>
      <group>users</group>
      <owner>root</owner>
      <perm>drwrwrw</perm>
    </entry>
    <entry kind="slot">
      <name>test2</name>
      <group>users</group>
      <owner>root</owner>
      <perm>drwrwrw</perm>
    </entry>
    <entry kind="slot">
      <name>slot_name29507134416</name>
      <group>users</group>
      <owner>root</owner>
      <perm>drwrwrw</perm>
    </entry>
    <entry kind="slot">
      <name>mikkoslot</name>
      <group>users</group>
      <owner>root</owner>
      <perm>drwrwrw</perm>
    </entry>
</list>
  <status code="0" location="/storage" operation="GET" type="ok"></status>
</letsmt-ws>"""

parser = XmlParser(xmlData.split("\n"))

print(parser.corporaForUser("mikkotest"))
'''

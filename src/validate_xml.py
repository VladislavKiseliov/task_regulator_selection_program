import xml.etree.ElementTree as ET

try:
    tree = ET.parse('GUI/mainwindow.ui')
    # XML is valid
except ET.ParseError as e:
    # XML Parse Error
except Exception as e:
    # Error occurred
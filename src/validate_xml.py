import xml.etree.ElementTree as ET

try:
    tree = ET.parse('GUI/mainwindow.ui')
    print('XML is valid')
except ET.ParseError as e:
    print(f'XML Parse Error: {e}')
except Exception as e:
    print(f'Error: {e}')
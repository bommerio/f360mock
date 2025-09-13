# f360mock
Mocking support for Python Fusion 360 tests

Before you use this, you should link or copy the Fusion 360 API files into your project path.

* Find the API definitions:

Mac OS: `~/Library/Application\ Support/Autodesk/webdeploy/production/<hash>/Api/Python/packages/adsk`\
Windows: `<User Directory>\AppData\Local\Autodesk\webdeploy\production\<hash>\Api\Python\packages\adsk`

Look for the hash where the above directory contains (_core|_fusion|_cam).so (Mac), or (_core|_cam|_fusion).pyd (Windows)

* Create a shortcut or link into your project:
```
ln –s ~/Library/Application\ Support/Autodesk/webdeploy/production/<hash>/Api/Python/packages/adsk <add-in folder>/adsk-lib
```
* Add API folder to test/__init__.py:
```
import sys
import os
sys.path.append(os.path.abspath(’addin-path'))
sys.path.append(os.path.abspath('adsk-lib/defs'))
```
* Run tests by navigating to your project root (which contains your add-in folder, and test folder) and running:
```
python -m unittest discover -s test -t .
```

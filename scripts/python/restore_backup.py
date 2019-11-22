## File by _baku89 on twitter
## Source: https://gist.github.com/baku89/615a15228e5747d4e83fa579796009fe

## Modified & Added to toolset by: Paul Ambrosiussen

import hou
import glob, os, re
from stat import ST_MTIME
from datetime import datetime

def recoverFile():
    # Get a filename of the most recent opened file
    userPrefDir = hou.getenv('HOUDINI_USER_PREF_DIR')
    historyPath = os.path.join(userPrefDir, 'file.history')

    destPath = None
    filename = None

    if not os.path.exists(historyPath):
        return False
    
        
    with open(historyPath, 'r') as file:
        txt = file.read()
        result = re.search(r'^HIP\n{\n((?:[^\n]*(\n+))+?)}', txt)
        
        if not result:
            return False

        recentFiles = [path for path in result.groups()[0].split('\n') if path]

        if len(recentFiles) == 0:
            return False
        
        destPath = recentFiles[-1]
        filename = os.path.basename(destPath)
    
    # Get the backup file
    tempDir = hou.getenv('HOUDINI_TEMP_DIR')

    os.chdir(tempDir)
    
    bakPattern = r"^crash\.%s\.(.*)\%s" % os.path.splitext(filename)
    entries = [name for name in glob.glob('*.hip*') if re.match(bakPattern, name)]
    entries = [(os.stat(path)[ST_MTIME], path) for path in entries]

    if len(entries) == 0:
        hou.ui.displayMessage('No backup file for %s has found' % filename)
        return False
        
    bakDate, bakFile = sorted(entries, reverse=True)[0]
    bakPath = os.path.join(tempDir, bakFile)
    
    bakDate = datetime.fromtimestamp(int(bakDate))
    bakDate = bakDate.strftime("%m/%d/%Y, %H:%M:%S")
    
    
    # Ask whether restore or not
    msg = "The backup of the most recent opened file has found. Do you want to restore it?"
    details = (
        "Location: " + os.path.dirname(destPath) + "\n"
        "Original: " + filename + "\n"
        "Backup: " + bakFile + " (" + bakDate + ")")
    options = ('Yes', 'Cancel')
    
    if hou.ui.displayMessage(msg, options, close_choice=1, details=details, details_expanded=True) == 1:
        return False
    
    prefix, ext = os.path.splitext(destPath)
    os.rename(destPath, prefix + '_copy' + ext)
    os.rename(bakPath, destPath)
    
    if hou.ui.displayMessage('Do you want to open the file?', ('Yes', 'Cancel'), close_choice=1):
        hou.hipFile.load(destPath)
    

import hou, os, subprocess, json

def evaluateparmtoargument(node, parm):
    
    if parm.parmTemplate().type() == hou.parmTemplateType.Toggle:
        return str(parm.evalAsInt())
    else:
        return parm.evalAsString()



def process(cmd, cache, folder, node):

    HDA = node.parent()

    log = HDA.parm("bExportLog").evalAsInt() == 1

    with hou.InterruptableOperation(node.name(), open_interrupt_dialog=True) as Operation:
        if log:
            print("--------")
            print(node.name())

        logfile = open(os.path.join(cache, folder, node.name()+"_log.txt"), 'a')
        errorlogfile = open(os.path.join(cache, folder, node.name()+"_errorlog.txt"), 'a')

        StartupInfo = None
        if os.name == 'nt':
            StartupInfo = subprocess.STARTUPINFO()
            subprocess.STARTF_USESHOWWINDOW = 1
            StartupInfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        clean_env = os.environ.copy()
        
        if HDA.parm("enablecustomenv").evalAsInt() == 1:
            customenv = json.loads(HDA.parm("customenv").eval())
            clean_env = {str(key): str(value) for key, value in customenv.items()}

        Process = subprocess.Popen(cmd, stdout=logfile, stderr=errorlogfile, startupinfo=StartupInfo, env=clean_env)

        # Process is still running
        while Process.poll() == None:
            try:
                Operation.updateProgress(0.0)
            # User interrupted
            except hou.OperationInterrupted:
                Process.kill()

        # Close log file, because Process has ended
        logfile.close()
        errorlogfile.close()

        with open(os.path.join(cache, folder, node.name()+"_errorlog.txt"), 'r') as myfile:
            data = myfile.read()
            if len(data) > 0:
                hou.ui.displayMessage(data, buttons=('OK',), severity=hou.severityType.Error, title="%s AliceVision Processing Failed!" % node.name())
            else:
                myfile.close()
                os.remove(os.path.join(cache, folder, node.name()+"_errorlog.txt"))

        if log:
            print(node.name() + " completed")
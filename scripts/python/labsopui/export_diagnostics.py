import subprocess
import os
import json
import sys
import multiprocessing
import platform
import zipfile
import hou

def ExportDiagnostics(directory):

    StartupInfo = subprocess.STARTUPINFO()
    subprocess.STARTF_USESHOWWINDOW = 1
    StartupInfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    LicenseDiagnosticFile = os.path.join(hou.text.expandString("$HOUDINI_TEMP_DIR"), "LicenseDiagnostic.txt")
    AboutHoudiniFile = os.path.join(hou.text.expandString("$HOUDINI_TEMP_DIR"), "AboutHoudini.txt")

    cmd = [hou.text.expandString("$HFS/bin/sesictrl"), "diagnostic"]

    with open(LicenseDiagnosticFile, 'w') as logfile:
        with subprocess.Popen(cmd, startupinfo=StartupInfo, stdout=logfile) as Process:
            pass
            
    cmd = [hou.text.expandString("$HFS/bin/hgpuinfo")]

    with open(AboutHoudiniFile, 'w') as logfile:

        # Operating System:         Windows 10 Home x64
        # Physical Memory:          15.90 GB
        # Number of Screens:        1
        #     Screen 0:             1920 x 1080 at 0,0
        #     Work Area 0:          1920 x 1050 at 0,0
        #     Screen 0 DPI:         96.0

        # Qt Version:               5.15.2
        # USD Version:              21.08
        # USD git URL:              https://github.com/sideeffects/USD.git
        # USD git Revision:         365456ca1e7358099c3673e3f72dfd07dc30306a


        logfile.write("Houdini: {0} {1}\n".format(hou.applicationVersionString(), hou.licenseCategory()))
        logfile.write("Build Platform: {}\n".format(hou.applicationPlatformInfo()))
        logfile.write("Python: {}\n".format(sys.version))
        logfile.write("UI Scale: {}\n".format(hou.ui.globalScaleFactor()))
        logfile.write("Number of Cores: {}\n".format(multiprocessing.cpu_count()))
        logfile.write("Platform: {}\n".format(platform.platform()))
        logfile.write("Architecture: {}\n".format(platform.architecture()))
        logfile.write("Machine: {}\n".format(platform.machine()))
        logfile.write("Host Name: {}\n".format(platform.node()))
        logfile.write("Processor: {}\n".format(platform.processor())) 
        logfile.write("\n") 


    with open(AboutHoudiniFile, 'a') as logfile:
        # OpenCL
        process = subprocess.Popen(cmd, startupinfo=StartupInfo, stdout=logfile)
        process.wait()

    with open(AboutHoudiniFile, 'a') as logfile:
        # Env Vars
        env_copy = os.environ.copy()
        logfile.write(json.dumps(env_copy, indent = 4))

    from datetime import datetime
    time_str = datetime.now().strftime('%d-%b-%Y-%I-%M-%p')

    file_name = "Houdini_Diagnostics_{0}.zip".format(time_str)

    zip_file = zipfile.ZipFile(os.path.join(directory, file_name), 'w', zipfile.ZIP_DEFLATED)
    zip_file.write(LicenseDiagnosticFile, "LicenseDiagnostic.txt")
    zip_file.write(AboutHoudiniFile, "AboutHoudini.txt")
    zip_file.close()

    return os.path.join(directory, file_name)
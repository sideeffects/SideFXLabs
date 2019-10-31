import os
import logging
import subprocess

HOUDINI_VERSION = "18.0"

def get_latest_houdini_version():
    logging.info("Determining latest Houdini Version...")
    sidefx_path = os.path.join(os.getenv("ProgramW6432"), "Side Effects Software")
    version_list = os.listdir(sidefx_path)
    version_list.reverse()
    for possible_dir in version_list:
        if HOUDINI_VERSION in possible_dir and not "Reality Capture" in possible_dir:
            logging.info("Latest Local Houdini Install is %s..."%possible_dir)
            return os.path.join(sidefx_path, possible_dir)

latest_houdini = get_latest_houdini_version()
local_dir = os.path.dirname(__file__)
my_env = os.environ.copy()
my_env["HOUDINI_OGL_SOFTWARE"] = "1"
my_env["HOUDINI_PATH"] = os.path.abspath(os.path.join(os.path.dirname(local_dir), "..")).replace("\\", "/") + ";&" #"C:\\GameDevToolset;&"

print latest_houdini

for filename in os.listdir(local_dir):
    #print filename
    if "test" in filename:
        print "Running Test:", filename
        subprocess.call([latest_houdini + "/bin/hython2.7.exe", os.path.join(local_dir, filename)], env=my_env)
    
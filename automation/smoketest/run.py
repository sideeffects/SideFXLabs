import os
import logging
import subprocess
import platform

HOUDINI_VERSION = "18.5"

def get_latest_houdini_version():
    logging.info("Determining latest Houdini Version...")
    machineos = platform.system()

    if machineos == "Windows":
        sidefx_path = os.path.join(os.getenv("ProgramW6432"), "Side Effects Software")
        version_list = os.listdir(sidefx_path)
        version_list.reverse()

        for possible_dir in version_list:
            if HOUDINI_VERSION in possible_dir and not "Reality Capture" in possible_dir:

                return os.path.join(sidefx_path, possible_dir, "bin", "hython2.7.exe")

    elif machineos == "Linux":
        sidefx_path = "/opt/hfs{0}/".format(HOUDINI_VERSION)

        return os.path.join(sidefx_path, "bin", "hython2.7")


latest_houdini = get_latest_houdini_version()
local_dir = os.path.dirname(os.path.abspath(__file__))

my_env = os.environ.copy()
my_env["HOUDINI_OGL_SOFTWARE"] = "1"
my_env["HOUDINI_PATH"] = os.path.abspath(os.path.join(os.path.dirname(local_dir), "..")) + ";&"
my_env["PATH"] = os.path.abspath(os.path.join(os.path.dirname(local_dir), "..", "bin")) + my_env["PATH"]
my_env["SIDEFXLABS"] = os.path.abspath(os.path.join(os.path.dirname(local_dir), ".."))
my_env["HOUDINI_DSO_ERROR"] = "1"

print latest_houdini, os.path.isfile(latest_houdini)

if os.path.isfile(latest_houdini):
	subprocess.call([latest_houdini, os.path.join(local_dir,"smoke_tests.py")], env=my_env)
else:
    print "ERROR, No matching Houdini install found"

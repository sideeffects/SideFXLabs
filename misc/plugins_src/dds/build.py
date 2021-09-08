import os
import shutil
import subprocess

versions = [  "18.0"]

version_dic = {}
SideFXDIR = r"C:\Program Files\Side Effects Software"
msbuild = r"C:/Program Files (x86)/Microsoft Visual Studio/2017/Professional/MSBuild/15.0/Bin/amd64/msbuild.exe"
SOLUTION_FILE = "IMG_DDS.sln"

build_dir = os.path.join(os.getenv("APPDATA"), "SideFX")
temp_dir = os.path.join(build_dir, "DDS_File")

VERSION = "0.6"

def get_installed_versions_dic():
    installed_versions = os.listdir(SideFXDIR)
    for v in installed_versions:
        if v.startswith("Houdini "):
            major_v = v.split()[-1].split(".")[0]
            minor_v = v.split()[-1].split(".")[1]

            # if minor_v != "0":
            major_v += "." + minor_v
            if major_v not in version_dic:
                version_dic[major_v] = []

            version_dic[major_v].append(v)
    return version_dic.copy()

def compile_plugin(version):
    global version_dic, build_dir

    build_dir = "build_" + str(version)

    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)

    os.makedirs(build_dir)
    version_dic = get_installed_versions_dic()

    my_env = os.environ.copy()
    my_env["HFS"] = os.path.join(SideFXDIR, version_dic[version][-1])

    if version == "18.0":
        my_env["INSTDIR"] = "D:/work/SideFX/SideFXLabs/dso/fb"
    else:
        my_env["INSTDIR"] = "D:/work/SideFX/GameDevelopmentToolset/dso/fb"

    if version in ["17.0", "17.5", "18.0"]:
        subprocess.call(["cmake", "-G", "Visual Studio 15 2017 Win64", ".."], cwd=build_dir,
                        env=my_env)

        subprocess.call([msbuild, SOLUTION_FILE , "/p:Configuration=Release", "/p:Platform=x64"],
                        cwd=build_dir, env=my_env)

    if version == "16.5":
        subprocess.call(["cmake", "-G", "Visual Studio 14 2015 Win64", ".."], cwd=build_dir, env=my_env)
        subprocess.call([msbuild, SOLUTION_FILE, "/p:Configuration=Release", "/p:Platform=x64" ], cwd=build_dir, env=my_env)

def wipe_folder(path):
    if os.path.exists(path):
        shutil.rmtree(path)

    os.makedirs(path)

if __name__ == '__main__':

    for houdini_version in versions:
        compile_plugin(houdini_version)






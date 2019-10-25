import os
import hou
import csv
import unittest
import glob
import subprocess
import shutil


local_dir = os.path.dirname(__file__)

class TestStringMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def test_1_test_demoscenes_output(self):

        with open(os.path.dirname(local_dir) + "/tests/geometry_tools_index.csv") as csvfile:
            csvdata = csv.reader(csvfile, delimiter=' ', quotechar='|')

            for x, data in enumerate(csvdata):
                if x == 0: continue
                Hipfile = data[0].split(",")[0]
                OutputNode = data[0].split(",")[1]
                Frames = data[0].split(",")[2:3] or None
                Action = data[0].split(",")[3:4] or None
                ParmName = data[0].split(",")[4:5] or None

                print "opening", Hipfile

                try:

                    # Saving out a fresh export
                    hou.hipFile.load(os.path.join(os.path.dirname(local_dir), "hip", Hipfile).replace("\\", "/"))
                    Node = hou.node(OutputNode)

                    if Node.type().category().name() == "Sop":
                        GEOROP = Node.parent().createNode("rop_geometry")
                        GEOROP.setNextInput(Node) 
                        GEOROP.parm("sopoutput").set(os.path.join(local_dir, "hip", "export", Hipfile.split(".")[0], Hipfile.split(".")[0]+".$F.bgeo.sc").replace("\\", "/"))

                        if "-" in Frames[0]:
                            GEOROP.parm("trange").set("normal")
                            GEOROP.parm("f1").deleteAllKeyframes()
                            GEOROP.parm("f2").deleteAllKeyframes()
                            GEOROP.parm("f1").set(Frames[0].split("-")[0])
                            GEOROP.parm("f2").set(Frames[0].split("-")[1])

                        if Action != None:
                            pass

                        GEOROP.parm("execute").pressButton()

                    # Testing against baseline
                    Errors = []

                    baselinefiles = glob.glob(os.path.join(local_dir, "hip", "baseline", Hipfile.split(".")[0], "*.bgeo.sc"))

                    for baselinefile in baselinefiles:
                        baselinefile = baselinefile.replace("\\", "/")
                        testfile = (os.path.join(local_dir, "hip", "export", Hipfile.split(".")[0], baselinefile.split("/")[-1])).replace("\\", "/")

                        with open(os.devnull, 'wb') as devnull:

                            print "testing", testfile

                            process = subprocess.Popen("geodiff %s %s" % (baselinefile, testfile), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) 
                            Errors.append(process.returncode)

                            if process.returncode == 1:

                                Errors.append(1)

                                while True:
                                    nextline = process.stdout.readline()
                                    
                                    if nextline == '' and process.poll() is not None:
                                        break
                                    
                                    if nextline != "":
                                        print nextline

                    shutil.rmtree(os.path.join(local_dir, "hip", "export", Hipfile.split(".")[0]))

                    assert(max(Errors) == 0)



                except Exception, e:
                    print str(e)
                    pass


if __name__ == '__main__':
    unittest.main()
import hou
import os
import difflib
import glob
import subprocess
import shutil

import unittest
local_dir = os.path.dirname(__file__)

class TestStringMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def test_1_loadfile(self):
        hou.hipFile.load(os.path.join(local_dir, "hip", "simple_baker.hip").replace("\\", "/"))

    def test_2_render(self):
        node = hou.node("/obj/grid1/sop_simple_baker1")
        node.hm().render(node)
        assert(os.path.exists(os.path.join(local_dir, "hip", "export", "simplebaker", "simplebaker_ao.tga")))

    def test_3_baseline(self):
        pass
        # Errors = []

        # baselinetextures = glob.glob(os.path.join(local_dir, "hip", "baseline", "simplebaker", "simplebaker_*.tga"))

        # for baselinefile in baselinetextures:
        #     baselinefile = baselinefile.replace("\\", "/")
        #     testfile = (os.path.join(local_dir, "hip", "export", "simplebaker", baselinefile.split("/")[-1])).replace("\\", "/")

        #     with open(os.devnull, 'wb') as devnull:
        #         Errors.append(subprocess.call("idiff -t 0.001 %s %s" % (baselinefile, testfile), shell=True))

        # assert(max(Errors) == 0)


    @classmethod
    def tearDownClass(cls):
       shutil.rmtree(os.path.join(local_dir, "hip", "export", "simplebaker"))

if __name__ == '__main__':
    unittest.main()
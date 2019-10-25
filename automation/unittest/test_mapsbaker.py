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
        hou.hipFile.load(os.path.join(local_dir, "hip", "maps_baker.hip").replace("\\", "/"))

    def test_2_render(self):
        node = hou.node("/obj/grid1/sop_maps_baker1")
        node.hm().Render(node)
        assert(os.path.exists(os.path.join(local_dir, "hip", "export", "mapsbaker", "mapsbaker_ao.png")))

    def test_3_baseline(self):
        pass
        # Errors = []

        # baselinetextures = glob.glob(os.path.join(local_dir, "hip", "baseline", "mapsbaker", "mapsbaker_*.png"))

        # for baselinefile in baselinetextures:
        #     baselinefile = baselinefile.replace("\\", "/")
        #     testfile = (os.path.join(local_dir, "hip", "export", "mapsbaker", baselinefile.split("/")[-1])).replace("\\", "/")

        #     with open(os.devnull, 'wb') as devnull:
        #         Errors.append(subprocess.call("idiff -t 0.001 %s %s" % (baselinefile, testfile), shell=True))

        # assert(max(Errors) == 0)


    @classmethod
    def tearDownClass(cls):
       shutil.rmtree(os.path.join(local_dir, "hip", "export", "mapsbaker"))

if __name__ == '__main__':
    unittest.main()
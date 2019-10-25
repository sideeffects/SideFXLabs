import hou
import os
import difflib
import shutil

import unittest
local_dir = os.path.dirname(__file__)

class TestStringMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def test_1_loadfile(self):
        hou.hipFile.load(os.path.join(local_dir, "hip", "csv_editor.hip").replace("\\", "/"))

    def test_2_render(self):
        node = hou.node("/out/rop_csv_exporter1")
        node.render()
        assert(os.path.exists(os.path.join(local_dir, "hip", "export", "csv_editor", "csv_editor.csv")))

    def test_3_baseline(self):

        baselinefile = open(os.path.join(local_dir, "hip", "baseline", "csv_editor", "csv_editor.csv"),'r')
        testfile = open(os.path.join(local_dir, "hip", "export", "csv_editor", "csv_editor.csv"),'r') 

        baselinedata = baselinefile.read().splitlines()
        baselinedata.sort()
        testdata = testfile.read().splitlines()
        testdata.sort()

        diffList = difflib.unified_diff(baselinedata, testdata, lineterm='')
        
        assert(len(list(diffList)) == 0)

    @classmethod
    def tearDownClass(cls):
       shutil.rmtree(os.path.join(local_dir, "hip", "export", "csv_editor"))

if __name__ == '__main__':
    unittest.main()
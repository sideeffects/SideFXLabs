
import os
import hou

import unittest
local_dir = os.path.dirname(__file__)

class TestStringMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def test_1_test_demoscenes(self):

        demo_files = os.listdir(os.path.dirname(local_dir) + "/hip")
        for demo_file in demo_files:
            if demo_file.endswith(".hip"):
                print "opening", demo_file
                try:
                    hou.hipFile.load(os.path.join(os.path.dirname(local_dir), "hip", demo_file).replace("\\", "/"))

                    GameDevNodeInstances = [x for x in hou.node("/").allSubChildren() if x.type().nameComponents()[1] == "gamedev"] 

                    for node in GameDevNodeInstances:
                        if node.type().definition().nodeType().name() != hou.nodeType(node.type().definition().nodeTypeCategory(), node.type().definition().nodeTypeName()).namespaceOrder()[0]:
                            print "Warning... Node instance is using older definition:", node.path()
                            
                except Exception, e:
                    print str(e)
                    pass


if __name__ == '__main__':
    unittest.main()
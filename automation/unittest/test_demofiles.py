
import os
import hou

import unittest
local_dir = os.path.dirname(os.path.abspath(__file__))

class TestStringMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def test_1_test_demoscenes(self):

        hipdir = os.path.abspath(os.path.join(os.path.dirname(local_dir), "..", "hip")).replace("\\", "/")

        demo_files = os.listdir(hipdir)

        print "testing %s files!" % len(demo_files)
        for demo_file in demo_files:
            if demo_file.endswith(".hip"):
                print "opening", demo_file
                try:
                    hou.hipFile.load(os.path.join(hipdir, demo_file).replace("\\", "/"))

                    LabsNodeInstances = [x for x in hou.node("/").allSubChildren() if x.type().nameComponents()[1] == "labs"]

                    for node in LabsNodeInstances:
                        namespaceOrder = [x for x in node.type().namespaceOrder() if "labs::" in x]
                        if node.type().name() != namespaceOrder[0]:
                            print "Warning... Node instance is using older definition:", node.path()
                            print "Using {0} instead of {1}".format(node.type().name(), namespaceOrder[0])

                except Exception, e:
                    print str(e)
                    pass


if __name__ == '__main__':
    unittest.main()


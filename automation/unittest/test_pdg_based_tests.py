
import os
import hou

local_dir = os.path.dirname(__file__)

if __name__ == '__main__':

	try:
		hou.hipFile.load(os.path.join(local_dir, "PDG_UnitTest.hip").replace("\\", "/"))

		_topnet = hou.node("/obj/topnet1")
		
		_topnet.dirtyAllTasks(True)
		_topnet.executeGraph(False, True, False, False)

		print "starting pdg"
		hou.node("/obj/topnet1").parm("dirtybutton").pressButton()
		print "done with pdg"


		if os.path.isfile(os.path.join(local_dir, "REGTEST-LOG.txt").replace("\\", "/")):
			with open(os.path.join(local_dir, "REGTEST-LOG.txt").replace("\\", "/")) as file:
				lines = file.readlines()

				for line in lines:
					print line
		else:
			print "ERROR, SOMETHING FAILED IN PDG"

	except Exception, e:
		print str(e)
		pass
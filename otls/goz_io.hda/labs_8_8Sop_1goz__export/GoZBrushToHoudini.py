import hrpyc
import os

connection, hou = hrpyc.import_remote_module()
ZBRUSH_DIR = "C:\Users\Public\Pixologic\GoZBrush"


def load_goz_files():
        goz_files = []
        
        object_list_file = os.path.join(ZBRUSH_DIR, "GoZ_ObjectList.txt")

        f = open(object_list_file, "r")
        for line in f.readlines():
                goz_files.append(line.strip())
        f.close()
        
        return goz_files


def get_instances(class_type):
        node_type = hou.nodeType(hou.sopNodeTypeCategory(), class_type)
        return node_type.instances()

        
def get_current_network_editor_pane():
    editors = [pane for pane in hou.ui.paneTabs() if isinstance(pane, hou.NetworkEditor) and pane.isCurrentTab()]
    return editors[-1]


def create_new_goz_instance():

        for i in hou.selectedNodes():
            i.setSelected(False)

        cur_editor = get_current_network_editor_pane()
        cur_node = cur_editor.currentNode()
        parent = cur_node.parent()
        if parent != hou.node("/"): 
            
            goz_instance = parent.createNode("sop_goz_import", "GoZ_Mesh")
            selected_nodes = hou.selectedNodes()

            pos = cur_node.position()
            pos[1] = pos[1]-1 
            goz_instance.setPosition(pos)
            
        else:
            go_z_node = hou.node("/obj").createNode("geo", "GoZ_Mesh")
            if go_z_node.node("file1"):
                go_z_node.node("file1").destroy()    
            go_z_node.moveToGoodPosition()
            goz_instance = go_z_node.createNode("sop_goz_import", "GoZ_Mesh")

        goz_instance.parm("reload").pressButton()
        goz_instance.setDisplayFlag(True)
        goz_instance.setRenderFlag(True)
        goz_instance.setSelected(True)


def load_goz_file(goz_instance, goz_filepath):

        goz_instance.parm("load_from_disk").set(1)
        file_node = goz_instance.node("IN_MESH")
        file_node.parm("file").set(goz_filepath + ".GoZ")
        file_node.parm("reload").pressButton()


def check_instance_against_filename(instance, filename):
        return instance.parm("tool_name").eval().upper() == filename.upper()


def main():
        create_new_goz_instance()




main()
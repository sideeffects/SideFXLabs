import os
import tempfile
import hou
import importlib
import sys

def reload_module():
    """Force reload the node_utils module to ensure latest changes are applied."""
    if 'labsopui.node_utils' in sys.modules:
        importlib.reload(sys.modules['labsopui.node_utils'])

def copy_nodes_for_object_merge():
    """Copy selected nodes for object merge."""
    reload_module()  # Reload module to ensure latest changes
    nodes = hou.selectedNodes()
    if not nodes:
        hou.ui.displayMessage("No nodes selected.", severity=hou.severityType.Warning)
    else:
        # Use a fixed temp file path for cross-platform compatibility
        temp_file_path = os.path.join(tempfile.gettempdir(), "pyobjpath.txt")
        with open(temp_file_path, 'w') as temp_file:
            for n in nodes:
                temp_file.write(n.path() + '\n')

def paste_as_object_merge_nodes(editor):
    """Paste as object merge nodes in the specified editor."""
    reload_module()  # Reload module to ensure latest changes
    if not editor:
        hou.ui.displayMessage("No active Network Editor pane found.", severity=hou.severityType.Warning)
    else:
        # Get the current network context from the editor
        current_network = editor.pwd()
        # Use selectPosition for interactive placement
        pos = editor.selectPosition()
        
        # Use the same temp file path as the copy command
        temp_file_path = os.path.join(tempfile.gettempdir(), "pyobjpath.txt")
        # Debug information
        # print("Temporary file path: " + temp_file_path)
        if not os.path.exists(temp_file_path):
            hou.ui.displayMessage("No saved node paths found.", severity=hou.severityType.Warning)
        else:
            with open(temp_file_path, 'r') as fl:
                paths = fl.readlines()
            if not paths:
                hou.ui.displayMessage("No node paths found in file.", severity=hou.severityType.Warning)
            else:
                names = [path.strip().split('/')[-1] for path in paths]
                objmNodes = []
                for i, path in enumerate(paths):
                    # Create node in the current network context
                    objmerge = current_network.createNode('object_merge')
                    objmerge.setPosition(hou.Vector2(pos[0] + i, pos[1] - i * 0.5))
                    abspath = path.strip()
                    relpath = objmerge.relativePathTo(hou.node(abspath))
                    objmerge.parm('objpath1').set(relpath)
                    objmerge.parm('xformtype').set('local')
                    objmerge.setSelected(1)
                    objmerge.setName('MERGE_' + names[i] + '_1', unique_name=True)
                    # Copy the color of the original node
                    original_node = hou.node(abspath)
                    if original_node:
                        objmerge.setColor(original_node.color())
                    objmNodes.append(objmerge)
                
                # Focus the network view on the newly created nodes
                if objmNodes:
                    editor.setCurrentNode(objmNodes[-1])
                    editor.homeToSelection() 
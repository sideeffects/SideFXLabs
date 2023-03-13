import hou
import sys
import os
import string

prefix = "    "

dirsubs = { "chop":"CHOP", 
            "cop2":"COP2",
            "dop": "DOP",
            "lop": "LOP",
            "obj": "OBJ",
            "out": "ROP",
            "pop": "POP", 
            "shop":"SHOP",
            "sop": "SOP",
            "vex": "VEX",
            "vop": "VOP",
            "top": "TOP" }

catsubs = { "chop":"Chop", 
            "cop2":"Cop2", 
            "dop": "Dop",
            "lop": "Lop",
            "obj": "Object", 
            "out": "Driver", 
            "pop": "Particle", 
            "shop":"Shop", 
            "sop": "Sop", 
            "vex": "VopNet", 
            "vop": "Vop",
            "top": "Top" }


def writeHeader(node, nodename, context):
    sys.stdout.write("#type:     node\n")
    sys.stdout.write("#context:  " + context + "\n")
    sys.stdout.write("#internal: " + nodename + "\n")
    dirname = context
    if(context in dirsubs): 
        dirname = dirsubs[context]
    sys.stdout.write("#icon:     " + dirname + "/" + nodename + "\n")
    sys.stdout.write("\n= " + node.description() + " =\n")
    sys.stdout.write("\n\"\"\"Summary.\"\"\"\n\n")
    sys.stdout.write("[Image:/images/sidefxlabs_banner.jpg]\n\n")
    sys.stdout.write(":video:\n")
    sys.stdout.write(prefix + "#src:/movies/cablegenerator.mp4\n\n")
    sys.stdout.write("<Description goes here>\n\n\n")
    sys.stdout.write("@parameters\n\n")

def writeFooter():
    sys.stdout.write("@locals\n    \n    \n")
    sys.stdout.write("@related\n")
    sys.stdout.write("- [item | /link ]\n")
    sys.stdout.write("\n")


#recursive for nested folders.
def writeTemplates(templates, indent):
    for temp in templates:
        if(temp.type() == hou.parmTemplateType.Separator or
           temp.type() == hou.parmTemplateType.Label) or temp.isHidden():
            continue

        if(temp.type() == hou.parmTemplateType.Folder):
            sys.stdout.write(prefix + indent + " " + temp.label() + " " + indent +"\n\n")
            writeTemplates( temp.parmTemplates(), "===" )
        else:
            if(len(temp.label()) > 0):
                sys.stdout.write(prefix + temp.label() + ":\n")
                sys.stdout.write(prefix + prefix + "#id: " + temp.name() + "\n")
                sys.stdout.write(prefix + prefix + "\n")

            if(temp.type() == hou.parmTemplateType.Menu):
                for i in range(len(temp.menuLabels())):
                    sys.stdout.write(prefix + prefix + temp.menuLabels()[i] 
                                     + ":\n"+prefix + prefix+ prefix+"\n")
                
def create_node_help(nodetypename, context, directory):

    if context not in catsubs.keys():
        raise hou.NodeError("Specified context not found. Available contexts: {}".format([x + " " for x in catsubs.keys()]))

    table = hou.nodeTypeCategories()[ catsubs[context] ]

    if nodetypename not in table.nodeTypes().keys():
        raise hou.NodeError("Specified node type does not exist.")

    node = table.nodeTypes()[ nodetypename ]
    
    namecomponents = node.nameComponents()
    txtname = namecomponents[1]+"--"+namecomponents[2]

    if namecomponents[3] != "":
        txtname += "-"+namecomponents[3]
    txtname += ".txt"

    sys.stdout = open(os.path.join(hou.text.expandString(directory), txtname), 'w')

    writeHeader(node, nodetypename, context)
    writeTemplates(node.parmTemplateGroup().entries(), "==")
    writeFooter()

    sys.stdout.close()


def create_node_help_auto(node):

    if node:

        node_type_name = node.type().name()

        category_name = node.type().category().name()
        node_context = 'sop'  # Default value

        for context, name in catsubs.items():
            if name == category_name:
                node_context = context
                break
    
        node_directory = '$SIDEFXLABS/help/nodes/{0}/'.format(node_context)

        create_node_help(node_type_name, node_context, node_directory)

    return
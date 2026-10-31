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
            "top": "TOP",
            "cop": "COP"}

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
            "top": "Top",
            "cop": "Cop" }

def writeHeader(node, nodename, context):
    sys.stdout.write("#type:     node\n")
    sys.stdout.write("#context:  " + context + "\n")
    sys.stdout.write("#internal: " + nodename + "\n")
    dirname = context
    if(context in dirsubs): 
        dirname = dirsubs[context]
        
    #The document's icon path points to a single icon in the help file. Previous version commented out but kept for reference
    #sys.stdout.write("#icon:     " + dirname + "/" + nodename + "\n")
    sys.stdout.write("#icon:     /labs_icons/sidefx_labs_default.svg")

    sys.stdout.write("\n= " + node.description() + " =\n")
    sys.stdout.write("\n\"\"\"Summary.\"\"\"\n\n")
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

def writeConnectors(node):
    inputLabelsFormatted = []
    outputLabelsFormatted = []

    numInputs = node.maxNumInputs()
    numOutputs = node.maxNumOutputs()
    nodeProperties = node.definition().sections()["DialogScript"].contents()

    connectorLabels = [line.strip() for line in nodeProperties.splitlines() if line.strip().startswith(("inputlabel", "outputlabel"))]
    inputLabels = [line for line in connectorLabels if line.startswith("inputlabel")]
    outputLabels = [line for line in connectorLabels if line.startswith("outputlabel")]

    for i in range(numInputs):
        inLabel = inputLabels[i].split(None, 2)[2].strip('"')
        inputLabelsFormatted.append(inLabel)

    for j in range(numOutputs):
        outLabel = outputLabels[j].split(None, 2)[2].strip('"')
        outputLabelsFormatted.append(outLabel)

    sys.stdout.write("@inputs\n")
    for i in inputLabelsFormatted:
        sys.stdout.write(prefix + i + ":" + "\n" + prefix + prefix + "\n")
    sys.stdout.write("\n")

    sys.stdout.write("@outputs\n")
    for j in outputLabelsFormatted:
        sys.stdout.write(prefix + j + ":" + "\n" + prefix + prefix + "\n")
    sys.stdout.write("\n")


                
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

    filepath = os.path.join(hou.text.expandString(directory), txtname)

    if os.path.exists(filepath):
        msg = "Help file already exists:\n{}\n\nOverwrite it?".format(filepath)
        confirmed = hou.ui.displayConfirmation(msg, severity=hou.severityType.Warning, title="Overwrite Help File")

        if not confirmed:
            print("Process cancelled.")
            return


    stdout = sys.stdout
    sys.stdout = open(filepath, 'w')

    writeHeader(node, nodetypename, context)
    writeTemplates(node.parmTemplateGroup().entries(), "==")
    writeConnectors(node)
    writeFooter()

    sys.stdout.close()

    # Reset sys.stdout to what it was previously to prevent Python errors with other scripts using it
    sys.stdout = stdout
    print(filepath + " written successfully.")


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
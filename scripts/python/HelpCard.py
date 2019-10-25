import hou
import pprint

MULTIPARM_TYPES = [hou.folderType.MultiparmBlock,
                   hou.folderType.ScrollingMultiparmBlock,
                   hou.folderType.TabbedMultiparmBlock]

FOLDER_TYPES = [hou.parmTemplateType.FolderSet,
                hou.parmTemplateType.Folder]

def createHelpCard(node):
    parms = node.parms()
    unorderedlabels = []
    labels = []
    parmLabels = {}
    #get parameter labels
    for parm in parms:
        unorderedlabels.append(parm.description())
        parmLabels[parm.description()] = parm.name()

    #sort and remove duplicate parameter labels
    for label in unorderedlabels:
        if label not in labels:
            labels.append(label)

    definition = node.type().definition()    
    sections = definition.sections()
    ptg = node.parmTemplateGroup()
    
    help = sections.get("Help", None)
    
    help_card_descriptions = get_existing_help_card_descriptions(help.contents())
    
    tooltips = get_existing_help(node)
    
    tool_name = node.type().description()
    internal_name = node.type().name()
    #icon = node.type().icon()
    #icon path can cause errors when building the help card. need to fix.
    icon = ""
    #formatting the icon path is still troublesome. needs work.
            
    help_card_template = "= %s =\n\n#type: node\n#context: sop\n#internal: %s\n#icon: %s\n#tags: tech, model\n\n\"\"\" [Basic Description] \"\"\"\n\n[ Detailed description]\n\n" % (tool_name, internal_name, icon)
    
    parm_string = "@parameters\n    "
    for label in labels:
        #The parameter help card is king. The script will check that field
        #first, then the help tab, and then if neither exists create a place
        #holder
        pt = node.parm("%s" % parmLabels[label]).parmTemplate()
        if pt.type() == hou.parmTemplateType.FolderSet:
            parm_string += "== %s ==\n    " % pt.folderNames()[0]
        elif pt.isHidden() == False:
            if label in help_card_descriptions:
                description = help_card_descriptions[label]
                if description != "[Needs parameter tooltip]":
                    parm = node.parm(parmLabels[label])
                    pt = parm.parmTemplate()
                    pt.setHelp(description)
                    ptg.replace(pt.name(), pt)
            elif label in tooltips:
                description = tooltips[label]
            else:
                description = "[Needs parameter tooltip]"
            parm_string += "%s:\n        %s\n    " % (label, description)
    
    node.allowEditingOfContents()
    
    help.setContents(help_card_template + parm_string)
    definition.setParmTemplateGroup(ptg)
    
def get_existing_help(node):
    #get any existing tooltips from the parameter properties
    parms = node.parms()
    existing_help = {}
    for parm in parms:
        if parm.parmTemplate().help() != '':
            existing_help[parm.description()] = parm.parmTemplate().help()
    return existing_help
    
def get_existing_help_card_descriptions(help_tab_content):
    #get any existing help descriptions from the help tab
    sections = help_tab_content.split("@")
    parameters_raw = []
    for section in sections:
        if section.startswith("parameters"):
            parameters_raw = section.split("\n")
            
    existing_help = {}
    for index in range(len(parameters_raw)):
        if parameters_raw[index].endswith(":"):
            existing_help[parameters_raw[index].strip()[:-1]] = parameters_raw[index+1].strip()
            
    return existing_help
    
def create_folder_structure(node):
    parms_dict = {}
    parms_dict["_NO_FOLDER_"] = []
    parms = node.parms()
    parm_tuples = node.parmTuples()
    
    for p in [_p for _p in parm_tuples if \
            _p.parmTemplate().type() in FOLDER_TYPES]:

        t = p.parmTemplate()
        #if t.folderType() in MULTIPARM_TYPES:
        #    continue

        lbl = t.label()
        if lbl:
            parms_dict[lbl] = []
    #return parms_dict
    
    for parm in parms:
        pt = parm.parmTemplate()
        container = parm.containingFolders()
        if parm.parmTemplate().type() in FOLDER_TYPES:
            continue

        if len(container) == 0:
            parms_dict["_NO_FOLDER_"].append([pt.label(), pt.help()])
        else:
            container = container[-1]
            if container not in parms_dict.keys():
                parms_dict[container] = [[pt.label(), pt.help()]]
            else:
                print pt.label()
                print parms_dict.values()
                if pt.label() not in parms_dict.values():
                    parms_dict[container].append([pt.label(), pt.help()])
                
    return parms_dict

#!/usr/bin/env python

import hou
import os 

class ParmContainer():
    def __init__(self, parms):
        self.parms = parms
        self.size = len(parms)        
        self.wedgeattribname, self.wedgeattribtokens, self.values = self.convertParams()
        self.wedgeattribtype = self.findAttribType()
  
    def getWedgeAttribName(self):
        return self.wedgeattribname

    def getFirstValue(self):
        return self.values[0]

    def getWedgeAttribType(self):
        return self.wedgeattribtype

    def findAttribType(self):        
        if self.size == 1:
            return 'float'
        elif self.size == 3:
            template = self.parms[0].parmTemplate()
            if template.look() == hou.parmLook.ColorSquare:
                return 'color'
            return 'vector'
        return 'float'

    def convertParams(self):   
        '''
        Converts the parameter names to wedge attributes with @ syntax.
        '''     
        tokens = []
        wedgeattribname = ''
        values = []
        if self.size == 1: 
            wedgeattribname = self.parms[0].name()
            tokens.append('@{}'.format(self.parms[0].name()))
            values.append(self.parms[0].eval())
        elif self.size == 3:   
            wedgeattribname= self.parms[0].name()[:-1] 
            for parm in self.parms:
                basename = parm.name()[:-1]
                component = parm.name()[-1:]
                token = '@{}.{}'.format(basename,component)
                tokens.append(token)
                values.append(parm.eval())

        return wedgeattribname, tokens, values

    def setParms(self):
        for i in range(0,self.size):
            self.parms[i].setExpression(self.wedgeattribtokens[i])            

def canWedgeValue(parm):
    template = parm.parmTemplate()

    if template.type() == hou.parmTemplateType.Int or template.type() == hou.parmTemplateType.Float:
        if template.numComponents() == 1 or template.numComponents() == 3:
            return True
    elif template.type() == hou.parmTemplateType.Toggle or template.type() == hou.parmTemplateType.Menu:
        return True

    return False

def canSetWedgeIndex(parm):
    template = parm.parmTemplate()
    if (template.type() == hou.parmTemplateType.Int or 
       template.type() == hou.parmTemplateType.Float or 
       template.type() == hou.parmTemplateType.Menu or
       template.type() == hou.parmTemplateType.String): 
        return True
    else:
        return False

def setWedgeIndex(parms):    

    parm = parms[0]
    parm.deleteAllKeyframes()

    if (parm.parmTemplate().type() == hou.parmTemplateType.String):
        parm.set('`' + 'pdgattrib("wedgeindex", 0)' + '`')
    else:
        parm.setExpression('pdgattrib("wedgeindex", 0)')  

def isFileCache(node):    
    if 'labs::filecache' in node.type().name() and node.type().category().name() == 'Sop':
        return True

    if 'labs::karma' in node.type().name() and node.type().category().name() == 'Lop':
        return True    

    return False

def createWedgeGeo(node, index, attribname, attribtype):
    '''
    Called when wedging parameter that is not a float
    ''' 
    digit = int(index)
    
    attribparmname = "attrib" + str(digit)
    geopathparmname = "geopath" + str(digit)
    
    attribname = attribname    
    '''
    choices = ['Float', 'Integer', 'Vector', 'Color']
    defaults = [-1]
    selected = hou.ui.selectFromList(choices,
                                     defaults,
                                     True,
                                     message=None,
                                     title='Data Type',
                                     column_header='Data Types',
                                     clear_on_cancel=True,
                                     width=200,
                                     height=155)
    '''

    parent = node.parent()
    pos = node.position()
    
    nwedgesparmname = 'wedgecount'

    # Deal with none sop contexts
    if node.type().category().name() == "Sop":
        container = parent
    else:
        container = parent.createNode('sopnet', 'wedgesopnet_' + node.name())
        container.setPosition(pos + hou.Vector2(2,1))

    pointgenerate = container.createNode('pointgenerate','create_wedgepoints')        
    pointgenerate.parm('npts').setExpression('ch("' + pointgenerate.relativePathTo(node) + '/' + nwedgesparmname + '")')
    pointgenerate.setPosition(pos + hou.Vector2(2,3))
    
    adjustnode = None
    parms = None
    

    '''
    if attribtype == 0: # Float
        adjustnode = container.createNode('attribadjustfloat', 'wedge_attributes')
        parms = {   'attrib': '`chs("' + adjustnode.relativePathTo(node) + '/' + attribparmname + '")`',
                    'valuetype': 'rand',
                    'dodefault': 1,
                    'default': 1 }
        
    elif selected[0] == 1: # Integer
        adjustnode = container
        t.createNode('attribadjustinteger', 'wedge_attributes')
        parms = {   'attrib': '`chs("' + adjustnode.relativePathTo(node) + '/' + attribparmname + '")`',
                    'valuetype': 'rand',
                    'dodefault': 1,
                    'default': 1 }
    '''
    if attribtype == 'vector': 
        adjustnode = container.createNode('attribadjustvector', 'wedge_attributes')
        parms = {   'attrib': '`chs("' + adjustnode.relativePathTo(node) + '/' + attribparmname + '")`',
                    'dirlen_valuetype': 'rand',
                    'dirlen_noiserange': 'zcentered',
                    'dodefault': 1 }
    elif attribtype == 'color': # Color
        adjustnode = container.createNode('attribadjustcolor', 'wedge_attributes')
        parms = {   'attrib': '`chs("' + adjustnode.relativePathTo(node) + '/' + attribparmname + '")`',
                    'valuetype': 'rand',                        
                    'dodefault': 1 } 
                    
    adjustnode.setParms(parms)       
    adjustnode.setPosition(pos + hou.Vector2(2,2))
    adjustnode.setNextInput(pointgenerate) 

    endnode = container.createNode('null', node.name() + "_wedge_attributes")
    endnode.setPosition(pos + hou.Vector2(2,1))
    endnode.setNextInput(adjustnode) 
    
    node.parm(geopathparmname).set(node.relativePathTo(endnode)) 

    endnode.setGenericFlag(hou.nodeFlag.Display,True)
    endnode.setGenericFlag(hou.nodeFlag.Render,True)
    endnode.setCurrent(True,True)   

def setupWedgeAttrib(node, index, wedgeattribname, attribtype, wedgevalue):
    node.parm('attrib{}'.format(index)).set(wedgeattribname)  
    
    node.parm('minvalue{}'.format(index)).set(wedgevalue)
    node.parm('maxvalue{}'.format(index)).set(wedgevalue)
    node.parm('values{}'.format(index)).set('{}-{}'.format(wedgevalue,wedgevalue))

    if attribtype != 'float':
        node.parm('wedgetype{}'.format(index)).set(6)
        createWedgeGeo(node, index, wedgeattribname, attribtype)   

def wedge(parms):
    
    selected = hou.ui.selectNode(title='Select File Cache node for wedging', custom_node_filter_callback=isFileCache)

    if selected:
        wedge_node = hou.node(selected)
        
        parm_container = ParmContainer(parms)
        parm_container.setParms()
        wedgeattribname = parm_container.getWedgeAttribName()
        wedgeattribtype = parm_container.getWedgeAttribType()
        wedgevalue = parm_container.getFirstValue()

        wedge_node.parm('enablewedging').set(1)
        nattribs = wedge_node.parm('nwedgeattribs').evalAsInt()
        

        if nattribs == 0:            
            wedge_node.parm('nwedgeattribs').set(1)
            wedge_node.parm('attrib1').set(wedgeattribname)

            setupWedgeAttrib(wedge_node, 1, wedgeattribname, wedgeattribtype, wedgevalue)

        else:
            has_attrib = False
            for i in range(0,nattribs):
                stri = str(i+1)  
                attribname = wedge_node.evalParm('attrib' + stri)
                if attribname == wedgeattribname:
                    has_attrib = True

            if not has_attrib:
                wedge_node.parm('nwedgeattribs').set(nattribs+1)
                setupWedgeAttrib(wedge_node, nattribs + 1, wedgeattribname, wedgeattribtype, wedgevalue)        
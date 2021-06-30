import hou

def ResetViewport():

    sceneviewers = [_pane for _pane in hou.ui.paneTabs() if _pane.type() == hou.paneTabType.SceneViewer]

    # Attempt to copy all settings for the sceneviewer and make new instances    
    for _oldSceneViewer in sceneviewers:
        

        # Get old sceneview name, create new sceneview, and get its name   
        _pane = _oldSceneViewer.pane()
        _oldViewportName = _oldSceneViewer.pane().desktop().name() + "." + _oldSceneViewer.name() + ".world" + "." + _oldSceneViewer.curViewport().name()
        _newSceneViewer = _pane.createTab(hou.paneTabType.SceneViewer)
        _newSceneViewerName = _newSceneViewer.pane().desktop().name() + "." + _newSceneViewer.name() + ".world"
        _newViewportName = _newSceneViewer.pane().desktop().name() + "." + _newSceneViewer.name() + ".world" +"." + _newSceneViewer.curViewport().name()


        # If the old sceneview was looking through a camera, make new scene viewer look through the same camera. Otherwise match perspective
        _sceneViewCamera = _oldSceneViewer.curViewport().camera()
        if _sceneViewCamera is None:
            _viewTransform = hou.hscript("viewtransform -p {}".format(_oldViewportName))[0]
            _newTransform = _viewTransform.replace(_oldViewportName, _newViewportName)
            hou.hscript("{}".format(_newTransform))        
        else:
            _newSceneViewer.curViewport().setCamera(hou.node(_sceneViewCamera.path()))        
        
        hou.hscript("viewcopy {0} {1}".format(_oldViewportName, _newViewportName))

        # Set the new sceneview to "hide other objects", to prevent unwanted cooking 
        hou.hscript("vieweroption -a 0 {}".format(_newSceneViewerName))
        # Set the left viewport toolbar to be visible
        hou.hscript("viewerstow -l open {}".format(_newSceneViewerName))



        # Split Views
        _newSceneViewer.setViewportLayout(_oldSceneViewer.viewportLayout())

        # Snapping
        _newSceneViewer.setSnappingMode(_oldSceneViewer.snappingMode())

        # View Options
        _newSceneViewer.setPickingVisibleGeometry(_oldSceneViewer.isPickingVisibleGeometry())
        _newSceneViewer.setPickingContainedGeometry(_oldSceneViewer.isPickingContainedGeometry())
        _newSceneViewer.setWholeGeometryPicking(_oldSceneViewer.isWholeGeometryPicking())
        _newSceneViewer.setSecureSelection(_oldSceneViewer.isSecureSelection())   
        _newSceneViewer.setPickingCurrentNode(_oldSceneViewer.isPickingCurrentNode())
        _newSceneViewer.setPickGeometryType(_oldSceneViewer.pickGeometryType())
        _newSceneViewer.setPickStyle(_oldSceneViewer.pickStyle())
        _newSceneViewer.setPickModifier(_oldSceneViewer.pickModifier())
        _newSceneViewer.setPickFacing(_oldSceneViewer.pickFacing())
        #_newSceneViewer.setHydraRenderer(_oldSceneViewer.currentHydraRenderer())

        # Group List
        _newSceneViewer.setGroupListColoringGeometry(_oldSceneViewer.isGroupListColoringGeometry())
        _newSceneViewer.setGroupListShowingEmptyGroups(_oldSceneViewer.isGroupListShowingEmptyGroups())
        _newSceneViewer.setGroupListVisible(_oldSceneViewer.isGroupListVisible())
        _groupListSize = _oldSceneViewer.groupListSize()
        _newSceneViewer.setGroupListSize(_groupListSize[0], _groupListSize[1])
        _newSceneViewer.setGroupListType(_oldSceneViewer.groupListType())
        _newSceneViewer.setGroupListMask(_oldSceneViewer.groupListMask())
        _newSceneViewer.setGroupPicking(_oldSceneViewer.isGroupPicking()) 

        # Pinning and Link Grouping
        _newSceneViewer.setPin(_oldSceneViewer.isPin())
        _newSceneViewer.setLinkGroup(_oldSceneViewer.linkGroup())

        _oldSceneViewer.close()

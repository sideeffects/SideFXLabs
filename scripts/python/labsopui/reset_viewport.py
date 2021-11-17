import hou

def resetSceneViewers(external_object_visibility = 0):

    scene_viewers = [pane_tab for pane_tab in hou.ui.paneTabs() if pane_tab.type() == hou.paneTabType.SceneViewer]

    for old_scene_viewer in scene_viewers:
        resetSceneViewer(old_scene_viewer, external_object_visibility)


def resetSceneViewer(old_scene_viewer, external_object_visibility = 0):

        desktop = hou.ui.curDesktop()
        desktop_name = desktop.name()

        pane = old_scene_viewer.pane()

        if pane is not None:
            new_scene_viewer = pane.createTab(hou.paneTabType.SceneViewer)

        else:
            new_scene_viewer = desktop.createFloatingPaneTab(hou.paneTabType.SceneViewer, (0, 100), old_scene_viewer.size(), None, True)

        old_scene_viewer_name = old_scene_viewer.name()
        new_scene_viewer_name = new_scene_viewer.name()

        # Sets new Scene Viewer's external object visibility.
        # 0 is to "Hide Other Objects"; 1 is to "Show All Objects"; 2 is to "Ghost Other Objects".
        # Currently this seems to be no way to read the Scene Viewer's existing setting.
        hou.hscript("vieweroption -a {0} {1}".format(external_object_visibility, desktop_name + "." + new_scene_viewer_name + ".world"))

        # Sets the visibilities of Toolbars
        new_scene_viewer.showOperationBar(old_scene_viewer.isShowingOperationBar())
        new_scene_viewer.showSelectionBar(old_scene_viewer.isShowingSelectionBar())
        new_scene_viewer.showDisplayOptionsBar(old_scene_viewer.isShowingDisplayOptionsBar())
        new_scene_viewer.setIncludeColorCorrectionBar(old_scene_viewer.includeColorCorrectionBar())
        new_scene_viewer.setIncludeMemoryBar(old_scene_viewer.includeMemoryBar())
        new_scene_viewer.showColorCorrectionBar(old_scene_viewer.isShowingColorCorrectionBar())
        new_scene_viewer.showMemoryBar(old_scene_viewer.isShowingMemoryBar())

        # Scene Viewer settings

        # Currently doesn't seem to work on Floating Pane Tabs
        new_scene_viewer.referencePlane().setIsVisible(old_scene_viewer.referencePlane().isVisible())

        new_scene_viewer.setSnappingMode(old_scene_viewer.snappingMode())
        new_scene_viewer.setPickingVisibleGeometry(old_scene_viewer.isPickingVisibleGeometry())
        new_scene_viewer.setPickingContainedGeometry(old_scene_viewer.isPickingContainedGeometry())
        new_scene_viewer.setWholeGeometryPicking(old_scene_viewer.isWholeGeometryPicking())
        new_scene_viewer.setSecureSelection(old_scene_viewer.isSecureSelection())
        new_scene_viewer.setPickGeometryType(old_scene_viewer.pickGeometryType())
        new_scene_viewer.setPickStyle(old_scene_viewer.pickStyle())
        new_scene_viewer.setPickModifier(old_scene_viewer.pickModifier())
        new_scene_viewer.setPickFacing(old_scene_viewer.pickFacing())
        if old_scene_viewer.viewerType() != hou.stateViewerType.SceneGraph:
            new_scene_viewer.setPickingCurrentNode(old_scene_viewer.isPickingCurrentNode())
            
        #new_scene_viewer.setHydraRenderer(old_scene_viewer.currentHydraRenderer())

        # Group List
        new_scene_viewer.setGroupListColoringGeometry(old_scene_viewer.isGroupListColoringGeometry())
        new_scene_viewer.setGroupListShowingEmptyGroups(old_scene_viewer.isGroupListShowingEmptyGroups())
        new_scene_viewer.setGroupListVisible(old_scene_viewer.isGroupListVisible())
        groupListSize = old_scene_viewer.groupListSize()
        new_scene_viewer.setGroupListSize(groupListSize[0], groupListSize[1])
        new_scene_viewer.setGroupListType(old_scene_viewer.groupListType())
        new_scene_viewer.setGroupListMask(old_scene_viewer.groupListMask())
        new_scene_viewer.setGroupPicking(old_scene_viewer.isGroupPicking())

        # Pinning and Link Grouping
        new_scene_viewer.setPin(old_scene_viewer.isPin())
        new_scene_viewer.setLinkGroup(old_scene_viewer.linkGroup())


        # Viewports

        # Disables applying display options to all split viewports
        hou.hscript("vieweroption -s 0 {}".format(desktop_name + "." + new_scene_viewer_name + ".world"))

        new_scene_viewer.setViewportLayout(old_scene_viewer.viewportLayout())

        for i in range(len(old_scene_viewer.viewports())):

            old_viewport = old_scene_viewer.viewports()[i]
            new_viewport = new_scene_viewer.viewports()[i]

            # Sets new current viewport name
            old_viewport_name = desktop_name + "." + old_scene_viewer_name + ".world" + "." + old_viewport.name()
            new_viewport_name = desktop_name + "." + new_scene_viewer_name + ".world" +"." + new_viewport.name()

            hou.hscript("viewcopy {0} {1}".format(old_viewport_name, new_viewport_name))

            # Viewport names may change after the viewcopy command
            new_viewport_name = desktop_name + "." + new_scene_viewer_name + ".world" +"." + new_viewport.name()

            # Sets view transform or camera to look through
            if old_viewport.camera() is None:

                view_transform = hou.hscript("viewtransform -p {}".format(old_viewport_name))[0]
                new_transform = view_transform.replace(old_viewport_name, new_viewport_name)
                hou.hscript("{}".format(new_transform))

            else:

                # Currently if the camera is ortho., only in the main viewport can it be properly set.
                # In any other viewport, only the view transform is set but the camera is not.
                new_viewport.setCamera(hou.node(old_viewport.cameraPath()))
                new_viewport.lockCameraToView(old_viewport.isCameraLockedToView())

            old_display_options = old_viewport.settings()
            new_display_options = new_viewport.settings()
            new_display_options.showsName(old_display_options.showName())
            new_display_options.showsCameraName(old_display_options.showCameraName())
            new_display_options.setLighting(old_display_options.lighting())
        

        old_scene_viewer.close()
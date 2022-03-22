import hou

def node_to_network_origin(move_images=False):

    pane_tab = hou.ui.paneTabUnderCursor()

    if type(pane_tab) is hou.NetworkEditor:

        current_node = pane_tab.currentNode()

        if isinstance(current_node, hou.Node):

            if type(current_node) is hou.CopNode:
                # Collapsed COP nodes snap to a slightly different position
                network_origin = hou.Vector2(-0.5, -0.0752)

            else:
                network_origin = hou.Vector2(-0.5, -0.15)

            offset = network_origin.__sub__(current_node.position())
    
            for item in current_node.parent().allItems():
    
                # Moves 'item' if it's not inside any NetworkBox
                if item.parentNetworkBox() is None:
    
                    position = item.position().__add__(offset)
                    item.setPosition(position)
    
            images = pane_tab.backgroundImages()
    
            for image in images:
    
                # Moves 'image' if it's not tied to any item
                if image.relativeToPath() == '':

                    if not move_images:
                        continue
    
                    rect = image.rect()
                    bound_min = rect.min().__add__(offset)
                    bound_max = rect.max().__add__(offset)
                    rect.setTo((bound_min.x(), bound_min.y(), bound_max.x(), bound_max.y()))
                    image.setRect(rect)
    
            pane_tab.setBackgroundImages(images)
    
            pane_tab.redraw()

    return
import hou

def openInHelpBrowser(url):

    desktop = hou.ui.curDesktop()
    browser = desktop.paneTabOfType(hou.paneTabType.HelpBrowser)

    if not browser:
        panel = desktop.createFloatingPanel(hou.paneTabType.HelpBrowser, immediate=True)
        browser = panel.paneTabOfType(hou.paneTabType.HelpBrowser)

    if not browser:
        print ("Failed to find or create a Help Browser tab.")
        return

    browser.setIsCurrentTab()
    browser.setUrl(url)

    return
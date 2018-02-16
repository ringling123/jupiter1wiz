import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import xbmcvfs
import os
import xml.etree.ElementTree as xmltree
import urllib

ADDON = xbmcaddon.Addon()
ADDONID = ADDON.getAddonInfo('id').decode('utf-8')
ADDONNAME = ADDON.getAddonInfo('name').decode('utf-8')
DATAPATH = os.path.join(xbmc.translatePath(
    "special://profile/").decode('utf-8'), "addon_data", ADDONID)


def log(txt):
    if isinstance(txt, str):
        txt = txt.decode('utf-8')
    message = u'%s: %s' % (ADDONID, txt)
    xbmc.log(msg=message.encode('utf-8'), level=xbmc.LOGDEBUG)


def show(handle):
    # Show search history

    # Load xml file we keep search history in
    searchTerms = xmltree.parse(os.path.join(
        DATAPATH, "history.xml")).getroot().findall("search")
    for searchTerm in searchTerms:
        # Get search term
        search = searchTerm.text
        # Add list item
        xbmcplugin.addDirectoryItem(handle, "plugin://plugin.library.search?search=%s" % (
            urllib.quote(search)), xbmcgui.ListItem(label=search), isFolder=True)

    xbmcplugin.setContent(handle, 'files')
    xbmcplugin.endOfDirectory(handle=handle)


def hasHistory():
    # Check that history is enabled
    if ADDON.getSetting("historyEnabled") == "false":
        return False

    # Return whether there is a search history
    return xbmcvfs.exists(os.path.join(DATAPATH, "history.xml"))


def update(searchterm):
    # Update search history

    # Check datadir exists, and create it if necessary
    if not xbmcvfs.exists(DATAPATH):
        xbmcvfs.mkdir(DATAPATH)

    # Create new xmltree with <history /> root
    tree = xmltree.ElementTree(xmltree.Element("history"))
    root = tree.getroot()

    # Add the search term we've been passed
    searchelement = xmltree.SubElement(root, "search")
    searchelement.text = searchterm

    # Load xml file we keep search history in
    history = []
    if xbmcvfs.exists(os.path.join(DATAPATH, "history.xml")):
        history = xmltree.parse(os.path.join(
            DATAPATH, "history.xml")).getroot().findall("search")

    for i, search in enumerate(history, start=1):
        if i == ADDON.getSetting("historyLimit"):
            # We have 20 items, so stop
            break

        if search.text == searchterm:
            # This is the same as the new item we've added, so pass on it
            i = i - 1
            continue

        # Add the search term
        searchelement = xmltree.SubElement(root, "search")
        searchelement.text = search.text

    # Write the search history
    tree.write(os.path.join(DATAPATH, "history.xml"), encoding="UTF-8")


def clear():
    # Clear search history
    if xbmcvfs.exists(os.path.join(DATAPATH, "history.xml")):
        xbmcvfs.delete(os.path.join(DATAPATH, "history.xml"))

    # Inform user history has been cleared
    xbmcgui.Dialog().notification(
        ADDONNAME, ADDON.getLocalizedString(30068), xbmcgui.NOTIFICATION_INFO)

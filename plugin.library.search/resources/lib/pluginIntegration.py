import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import xbmcvfs
import os
import xml.etree.ElementTree as xmltree
import urllib
import json

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


def runFunction(functionName):
    # Run a particular function, as called from settings
    if functionName == "pluginManage":
        managePlugins()
    elif functionName == "pluginAdd":
        addPlugin()
    elif functionName == "pluginDocs":
        pluginDocs()


def pluginDocs():
    # Show docs for how to add a plugin
    log("Showing docs")
    xbmcgui.Dialog().textviewer(ADDONNAME, ADDON.getLocalizedString(30040))
    log("Shown docs")


def addPlugin():
    # Attempt to detect the search params for a plugin

    # Show the user some instructions

    # Get type of plugin the user is interested in
    types = [(xbmc.getLocalizedString(1037), ("xbmc.addon.video", "Videos")),
             (xbmc.getLocalizedString(1038), ("xbmc.addon.audio", "Music")),
             (xbmc.getLocalizedString(1039), ("xbmc.addon.image", "Pictures"))]
    pluginType = select(types, ADDON.getLocalizedString(30042))
    if pluginType is None:
        return

    log("Plugin type: " + repr(pluginType))

    # Get the specific plugin the user is interested in
    plugin = selectPlugin(pluginType[0])
    if plugin is None:
        return

    log("Plugin: " + repr(plugin))

    # Explore the plugin
    pluginPath = explorePlugin("plugin://%s" % (plugin[1]))
    if pluginPath is None:
        return

    log("Base path: " + repr(pluginPath))

    # Allow user to edit path
    path = xbmcgui.Dialog().input(ADDON.getLocalizedString(30044),
                                  pluginPath, type=xbmcgui.INPUT_ALPHANUM)
    if path == "":
        # User cancelled
        return

    # Allow user to choose label
    label = xbmcgui.Dialog().input(ADDON.getLocalizedString(30045),
                                   plugin[0], type=xbmcgui.INPUT_ALPHANUM)

    if label == "":
        # User cancelled
        return

    # Save the plugin
    log("(%s) %s: %s" % (pluginType[1], label, path))
    savePlugin(pluginType[1], label, path)


def select(items, title):
    displayList = []
    displayReturn = []
    for item in items:
        displayList.append(item[0])
        displayReturn.append(item[1])

    selected = xbmcgui.Dialog().select(title, displayList)
    if selected == -1:
        return None
    else:
        return displayReturn[selected]


def selectPlugin(pluginType):
    # Selects a specific plugin
    plugins = []

    # Get all plugins of the type we've been passed
    json_query = xbmc.executeJSONRPC(
        '{ "jsonrpc": "2.0", "id": 0, "method": "Addons.Getaddons", "params": { "type": "%s", "properties": ["name", "path", "thumbnail", "enabled"] } }' % pluginType)
    json_query = unicode(json_query, 'utf-8', errors='ignore')
    json_response = json.loads(json_query)

    if json_response.has_key('result') and json_response['result'].has_key('addons') and json_response['result']['addons'] is not None:
        for item in json_response['result']['addons']:
            if item['enabled'] == False:
                # Not enabled
                continue
            if item["type"] != "xbmc.python.pluginsource":
                # Not a plugin
                continue

            plugins.append((item["name"], (item["name"], item["addonid"])))

    if len(plugins) == 0:
        # No plugins found
        return None

    return select(plugins, ADDON.getLocalizedString(30043))


def explorePlugin(path):
    log("Explore: " + repr(path))
    # Explore a plugin to try and find the search url
    paths = []

    # Show busy Dialog
    busy = xbmcgui.DialogBusy()
    busy.create()

    # Add option to use as base path
    paths.append("* %s" % (ADDON.getLocalizedString(30041)), (True, path))

    json_query = xbmc.executeJSONRPC(
        '{ "jsonrpc": "2.0", "id": 0, "method": "Files.GetDirectory", "params": { "properties": ["file"], "directory": "%s", "media": "files" } }' % (path))
    json_query = unicode(json_query, 'utf-8', errors='ignore')
    json_response = json.loads(json_query)

    # Add all directories returned by the json query
    if json_response.has_key('result') and json_response['result'].has_key('files') and json_response['result']['files']:
        json_result = json_response['result']['files']
        for item in json_result:
            if item["filetype"] != "directory":
                # Not a directory
                continue
            paths.append((item["label"], (False, item["file"])))

    busy.close()

    selected = select(paths, ADDON.getLocalizedString(30049))
    if selected is None:
        # User cancelled
        return None

    if selected[0] == True:
        # User choose to use as base path
        return selected[1]

    # User chose to go to another level
    return explorePlugin(selected[1])


def savePlugin(window, label, path):
    # Adds a new plugin to plugins.xml

    # Check datadir exists, and create it if necessary
    if not xbmcvfs.exists(DATAPATH):
        xbmcvfs.mkdir(DATAPATH)

    allPlugins = {}

    # Load xml file we keep plugins in
    plugins = []
    if xbmcvfs.exists(os.path.join(DATAPATH, "plugins.xml")):
        plugins = xmltree.parse(os.path.join(
            DATAPATH, "plugins.xml")).getroot().findall("plugin")

    # Add each plugin to our list
    for plugin in plugins:
        pluginlabel = plugin.get("label")
        log(repr(pluginlabel))
        allPlugins[pluginlabel] = plugin

    # Create a new element for the plugin we've been passed
    pluginelement = xmltree.Element("plugin")
    pluginelement.text = path
    pluginelement.set("window", window)
    # Ensure its label is unique
    i = 0
    uniqueLabel = label
    while uniqueLabel in allPlugins:
        i = i + 1
        uniqueLabel = label + " (%i)" % (i)
    pluginelement.set("label", uniqueLabel)
    log(repr(uniqueLabel))
    allPlugins[uniqueLabel] = pluginelement

    # Create new xmltree with <plugins /> root
    tree = xmltree.ElementTree(xmltree.Element("plugins"))
    root = tree.getroot()

    # Add all the plugins in order
    for plugin in sorted(allPlugins):
        root.append(allPlugins[plugin])

    # Write the search history
    tree.write(os.path.join(DATAPATH, "plugins.xml"), encoding="UTF-8")


def listPlugins(searchterm, handle):
    # Returns a list of items to plugin searches

    if not xbmcvfs.exists(os.path.join(DATAPATH, "plugins.xml")):
        # No plugins defined
        return

    plugins = xmltree.parse(os.path.join(
        DATAPATH, "plugins.xml")).getroot().findall("plugin")
    for plugin in plugins:
        label = plugin.get("label")
        window = plugin.get("window")
        path = urllib.quote(plugin.text.replace("::SEARCHTERM::", searchterm))

        path = "plugin://plugin.library.search?search=%s&plugin=%s&window=%s" % (
            searchterm, path, window)
        xbmcplugin.addDirectoryItem(
            handle, path, xbmcgui.ListItem(label=label), isFolder=False)


def launchPlugin(path, window):
    log("Launch plugin")

    # Display template
    if xbmc.getCondVisibility("Window.IsActive(%s)" % (window)):
        xbmc.executebuiltin("Container.Update(%s)" % (path))
    else:
        xbmc.executebuiltin("ActivateWindow(%s,%s,return)" % (window, path))


def managePlugins():
    # Manage the plugins which have been integrated

    if not xbmcvfs.exists(os.path.join(DATAPATH, "plugins.xml")):
        # No plugins defined
        return

    # Get all plugins
    allPlugins = []
    tree = xmltree.parse(os.path.join(DATAPATH, "plugins.xml"))
    root = tree.getroot()
    for plugin in root.findall("plugin"):
        allPlugins.append((plugin.get("label"), plugin))

    # Let user pick plugin to manage
    selectedPlugin = select(allPlugins, ADDON.getLocalizedString(30043))
    if selectedPlugin is None:
        return

    log(repr(selectedPlugin))

    # Show management options
    options = [(ADDON.getLocalizedString(30046), changeLabel),
               (ADDON.getLocalizedString(30047), changePath),
               (ADDON.getLocalizedString(30048), deletePlugin)]
    action = select(options, selectedPlugin.get("label"))
    if action is None:
        return

    # Call the function for the action
    action(tree, root, selectedPlugin)


def changeLabel(tree, root, plugin):
    log("Change label")
    # Allow user to choose label
    label = xbmcgui.Dialog().input(ADDON.getLocalizedString(
        30045), plugin.get("label"), type=xbmcgui.INPUT_ALPHANUM)

    if label == "":
        return

    # If label has been changed, and to ensure that the label remains unique, we're going to delete
    # the plugin and re-add it
    deletePlugin(tree, root, plugin)
    savePlugin(plugin.get("window"), label, plugin.text)


def changePath(tree, root, plugin):
    log("Change path")
    path = xbmcgui.Dialog().input(ADDON.getLocalizedString(30044),
                                  plugin.text, type=xbmcgui.INPUT_ALPHANUM)

    if path == "":
        return

    plugin.text = path
    tree.write(os.path.join(DATAPATH, "plugins.xml"), encoding="UTF-8")


def deletePlugin(tree, root, plugin):
    log("Delete plugin")
    root.remove(plugin)
    log(repr(plugin))
    tree.write(os.path.join(DATAPATH, "plugins.xml"), encoding="UTF-8")

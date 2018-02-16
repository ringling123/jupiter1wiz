import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import xbmcvfs
import os
import shutil
import json
import xml.etree.ElementTree as xmltree

ADDON = xbmcaddon.Addon()
ADDONID = ADDON.getAddonInfo('id').decode('utf-8')
CWD = ADDON.getAddonInfo('path').decode("utf-8")

import pluginIntegration


def log(txt):
    if isinstance(txt, str):
        txt = txt.decode('utf-8')
    message = u'%s: %s' % (ADDONID, txt)
    xbmc.log(msg=message.encode('utf-8'), level=xbmc.LOGDEBUG)


def getSearchTerm():
    # Get a search term from the user
    result = xbmcgui.Dialog().input(ADDON.getLocalizedString(30032),
                                    type=xbmcgui.INPUT_ALPHANUM)

    if result != "":
        return result
    else:
        return None


def showSearchResults(searchterm, searchtype, searchfield, explore=False):
    log("Show search results")
    # Create a fake node to show the results the user wants

    # Find our template node which matches the searchtype we've been passed
    template, target, default = getTemplates(searchtype)

    log(repr(template))
    log(repr(target))

    if explore:
        default = ""

    # Copy nodes
    copyNodes(template, target)

    # Update the nodes with the search term
    updateNodes(template, target, searchterm, searchfield)

    if target == "music":
        window = "Music"
    else:
        window = "Videos"

    # Display template
    if xbmc.getCondVisibility("Window.IsActive(%s)" % (window)):
        log("Container.Update(library://%s/plugin.library.search/nodes/%s)" %
            (target, default))
        xbmc.executebuiltin(
            "Container.Update(library://%s/plugin.library.search/nodes/%s)" % (target, default))
    else:
        log("ActivateWindow(%s,library://%s/plugin.library.search/nodes/%s,return)" %
            (window, target, default))
        xbmc.executebuiltin(
            "ActivateWindow(%s,library://%s/plugin.library.search/nodes/%s,return)" % (window, target, default))


def getTemplates(searchtype):
    # Parses the searchtypes.xml file to display a list of possible result
    # types
    log("Getting search type")
    templates = xmltree.parse(os.path.join(
        CWD, "resources", "searchtypes.xml")).getroot().findall("search")
    log(repr(templates))
    for template in templates:
        log(repr(template))
        log(repr(template.attrib))
        log("A search type")
        if template.attrib.get("id") == searchtype:
            log("Matched")
            return template.attrib.get("id"), template.attrib.get("target"), template.attrib.get("default")


def copyNodes(templates, target):
    # Copy our template nodes to the users nodes folder

    # Update the target if library nodes are flattened
    if target == "video" and areNodesFlattened():
        target = "video_flat"

    # Ensure default nodes are in place
    copyDefaultNodes(target)

    # Remove any previous template nodes
    targetDir = os.path.join(xbmc.translatePath(
        "special://profile".decode('utf-8')), "library", target, "plugin.library.search", "nodes")
    if os.path.exists(targetDir):
        shutil.rmtree(targetDir)

    # Copy template nodes
    shutil.copytree(os.path.join(CWD, "resources",
                                 "nodes", templates), targetDir)


def areNodesFlattened():
    json_query = xbmc.executeJSONRPC(
        '{ "jsonrpc": "2.0", "id": 0, "method": "Settings.GetSettingValue", "params": {"setting": "myvideos.flatten"}}')
    json_query = unicode(json_query, 'utf-8', errors='ignore')
    json_response = json.loads(json_query)

    if json_response.has_key('result') and json_response['result'].has_key('value'):
        if json_response['result']['value']:
            return True


def copyDefaultNodes(target):
    # Copy default library nodes if needed
    targetDir = os.path.join(xbmc.translatePath(
        "special://profile".decode('utf-8')), "library", target)
    if not os.path.exists(targetDir):
        originDir = os.path.join(xbmc.translatePath(
            "special://xbmc".decode("utf-8")), "system", "library", target)
        shutil.copytree(originDir, targetDir)


def updateNodes(template, target, searchterm, searchfield, path=None):
    # Recursive function to update nodes with the search term
    if path is None:
        # Update the target if library nodes are flattened
        if target == "video" and areNodesFlattened():
            target = "video_flat"
        path = os.path.join(xbmc.translatePath(
            "special://profile".decode('utf-8')), "library", target, "plugin.library.search", "nodes")

    log(repr(path))

    directories, files = xbmcvfs.listdir(path)
    for file in files:
        updateNode(os.path.join(path, file), searchterm, searchfield)
    for directory in directories:
        updateNodes(template, target, searchterm, searchfield,
                    os.path.join(path, directory))


def updateNode(file, searchterm, searchfield):
    # Entrance function to replace occurences of "::SEARCHTERM::" in the node
    # with the actual search term

    # Load the file
    node = xmltree.parse(file)

    # Update the elements
    updateNodeElement(node.getroot(), searchterm, searchfield)

    # Re-write the file
    node.write(file, encoding="UTF-8")


def updateNodeElement(elements, searchterm, searchfield):
    # Iterable function to actually replace occurences of "::SEARCHTERM::"
    for elem in elements:
        if elem.text is not None:
            if "$LABEL[" in elem.text:
                elem.text = localiseLabel(elem.text)
            elem.text = elem.text.replace("::SEARCHTERM::", searchterm)
            elem.text = elem.text.replace("::SEARCHTYPE::", searchfield)

        for attrib in elem.attrib:
            elem.set(attrib, elem.attrib.get(attrib).replace(
                "::SEARCHTERM::", searchterm))
            elem.set(attrib, elem.attrib.get(attrib).replace(
                "::SEARCHTYPE::", searchfield))

        updateNodeElement(elem, searchterm, searchfield)


def localiseLabel(text):
    while "$LABEL[" in text:
        # Split the string into its composite parts
        stringStart = text.split("$LABEL[", 1)
        stringEnd = stringStart[1].split("]", 1)
        # stringStart[ 0 ] = Any text before the $LABEL property
        # StringEnd[ 0 ] = The label to be parsed
        # stringEnd[ 1 ] = Any text after the $LABEL property

        labelElements = stringEnd[0].split(",")
        labelBase = labelElements[0]
        labelElements.pop(0)
        translatedElements = []

        for labelElement in labelElements:
            if unicode(labelElement, "utf-8").isnumeric():
                translatedElements.append(
                    ADDON.getLocalizedString(int(labelElement)))
            else:
                translatedElements.append(labelElement)

        log(repr(ADDON.getLocalizedString(int(labelBase))))
        log(repr(translatedElements))
        translatedLabel = ADDON.getLocalizedString(
            int(labelBase)) % tuple(translatedElements)

        return stringStart[0] + translatedLabel + stringEnd[1]


def showSearchTypes(searchterm, handle):
    # Parses the searchtypes.xml file to display a list of possible result
    # types
    searchtypes = xmltree.parse(os.path.join(
        CWD, "resources", "searchtypes.xml")).getroot().findall("search")
    xbmcplugin.setContent(handle, 'files')
    for searchtype in searchtypes:
        # Check any visibility condition
        if "visible" in searchtype.attrib and not xbmc.getCondVisibility(searchtype.attrib.get("visible")):
            continue

        searchid = searchtype.attrib.get("id")
        searchlabel = int(searchtype.attrib.get("label"))

        for searchfield in searchtype.findall("field"):
            log(repr(ADDON.getLocalizedString(searchlabel)))
            log(repr(searchterm))
            log(repr(xbmc.getLocalizedString(int(searchfield.attrib.get("label")))))
            label = ADDON.getLocalizedString(searchlabel) % (
                searchterm, xbmc.getLocalizedString(int(searchfield.attrib.get("label"))))
            field = searchfield.text
            log(repr(label))

            path = "plugin://plugin.library.search?search=%s&type=%s&field=%s" % (
                searchterm, searchid, field)

            listitem = xbmcgui.ListItem(label="%s" % (label))
            listitem.addContextMenuItems(
                [("Explore...", "Container.Update(%s&explore=True)" % (path))])

            xbmcplugin.addDirectoryItem(handle, path, listitem, isFolder=False)

    # Add any plugins
    pluginIntegration.listPlugins(searchterm, handle)

    xbmcplugin.endOfDirectory(handle=handle)

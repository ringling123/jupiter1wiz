import xbmc
import xbmcgui
import xbmcplugin
import os
import xbmcaddon
import urllib
import sys

ADDON = xbmcaddon.Addon()
ADDONID = ADDON.getAddonInfo('id').decode('utf-8')
ADDONVERSION = ADDON.getAddonInfo('version')
LANGUAGE = ADDON.getLocalizedString
CWD = ADDON.getAddonInfo('path').decode("utf-8")
ADDONNAME = ADDON.getAddonInfo('name').decode("utf-8")
RESOURCE = xbmc.translatePath(os.path.join(
    CWD, 'resources', 'lib')).decode("utf-8")
DATAPATH = os.path.join(xbmc.translatePath(
    "special://profile/").decode('utf-8'), "addon_data", ADDONID)

sys.path.append(RESOURCE)


def log(txt):
    if isinstance(txt, str):
        txt = txt.decode('utf-8')
    message = u'%s: %s' % (ADDONID, txt)
    xbmc.log(msg=message.encode('utf-8'), level=xbmc.LOGDEBUG)


def runFunction(functionName):
    if functionName == "clearHistory":
        import searchHistory
        searchHistory.clear()
        return True

    if functionName.startswith("plugin"):
        import pluginIntegration
        pluginIntegration.runFunction(functionName)
        return True


def runPlugin(params):
    import searchFunctions
    import searchHistory
    import pluginIntegration
    log(repr(params))

    if "new" in params:
        # We want to do a new search
        log("New search")
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
        result = searchFunctions.getSearchTerm()
        if result:
            log("Searching for %s" % (result))
            xbmc.executebuiltin(
                "Container.Update(plugin://plugin.library.search?search=%s)" % (urllib.quote(result)))
        else:
            log("No search term given")
    elif "history" in params:
        # Show search history
        searchHistory.show(int(sys.argv[1]))
    elif "search" in params:
        # We have a search terms
        searchterm = urllib.unquote(params["search"])
        searchHistory.update(searchterm)
        if "type" in params:
            log("Show results")
            xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=False)
            explore = False
            if "explore" in params:
                explore = bool(params["explore"])
            searchFunctions.showSearchResults(
                searchterm, params["type"], params["field"], explore)
        elif "plugin" in params:
            log("Launch plugin")
            pluginIntegration.launchPlugin(
                urllib.unquote(params["plugin"]), params["window"])
        else:
            log("Show search types")
            searchFunctions.showSearchTypes(
                urllib.quote(searchterm), int(sys.argv[1]))
    else:
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), "plugin://plugin.library.search?new=True",
                                    xbmcgui.ListItem(label=ADDON.getLocalizedString(30030)), isFolder=False)
        if searchHistory.hasHistory():
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), "plugin://plugin.library.search?history=True",
                                        xbmcgui.ListItem(label=ADDON.getLocalizedString(30031)), isFolder=True)
        xbmcplugin.setContent(int(sys.argv[1]), 'files')
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))


def entryPoint():
    log(repr(sys.argv))

    params = {}

    if len(sys.argv) == 2:
        # Called as addon, not plugin
        if runFunction(sys.argv[1]):
            return

        if sys.argv[1] != '':
            params = dict(arg.split("=") for arg in sys.argv[1][1:].split("&"))

    else:
        # Called as a plugin
        # Extract any params
        params = {}
        if sys.argv[2] != '':
            params = dict(arg.split("=") for arg in sys.argv[2][1:].split("&"))

    runPlugin(params)

if (__name__ == "__main__"):
    log('script version %s started' % ADDONVERSION)

    entryPoint()

    log('script stopped')

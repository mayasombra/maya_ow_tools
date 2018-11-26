"""A plugin designed to import and export OW formats from Autodesk Maya"""

# OW formats import / export plugin for Maya

import os
import os.path

import maya.mel as mel
import maya.cmds as cmds
import maya.OpenMayaMPx as OpenMayaMPx

from OWMImporter import import_owmdl

Version = "0.7.0 Alpha"


def __import_owmodel__():
    import_file = __importfile_dialog__(
        "OWMDL Files (*.owmdl)", "Import OWMDL")
    if import_file:
        import_owmdl.read(import_file, None)


def __log_info__(format_str=""):
    """Logs a line to the console"""
    print "[OWImporter] " + format_str


def __about_window__():
    """Present the about information"""
    cmds.confirmDialog(
        message="An OW Formats import and export plugin for Autodesk Maya.",
        button=['OK'], defaultButton='OK', title="About OW Tools")


def __importfile_dialog__(filter_str="", caption_str=""):
    """Ask the user for an input file"""
    if cmds.about(version=True)[:4] == "2012":
        import_from = cmds.fileDialog2(
            fileMode=1, fileFilter=filter_str, caption=caption_str)
    else:
        import_from = cmds.fileDialog2(fileMode=1,
                                       dialogStyle=2,
                                       fileFilter=filter_str,
                                       caption=caption_str)

    if not import_from or import_from[0].strip() == "":
        return None

    path = import_from[0].strip()
    path_split = os.path.splitext(path)
    if path_split[1] == ".*":
        path = path_split

    return path


def __reload_plugin__():
    """Reloads the plugin, not all Maya versions support this"""
    cmds.unloadPlugin("OWIMenus.py")
    cmds.loadPlugin("OWIMenus.py")


def __remove_menu__():
    """Removes the plugin menu"""
    if cmds.control("OWToolsMenu", exists=True):
        cmds.deleteUI("OWToolsMenu", menu=True)


def __create_menu__():
    """Creates the plugin menu"""
    __remove_menu__()

    # Create the base menu object
    cmds.setParent(mel.eval("$tmp = $gMainWindow"))
    menu = cmds.menu("OWToolsMenu", label="OW Tools", tearOff=True)

    # Model menu controls
    cmds.menuItem(label="Model", subMenu=True)

    cmds.menuItem(label="Import OWMDL File",
                  annotation="Imports an OW Model File",
                  command=lambda x: __import_owmodel__())

    cmds.setParent(menu, menu=True)
    # cmds.menuItem(divider=True)

    # Reload and about controls
    cmds.menuItem(label="Reload Plugin", command=lambda x: __reload_plugin__(
    ), annotation="Attempts to reload the plugin")
    cmds.menuItem(label="About", command=lambda x: __about_window__())


def initializePlugin(m_object):
    """Register the plugin"""
    OpenMayaMPx.MFnPlugin(m_object, "mayasombra", Version, "Any")
    __create_menu__()


def uninitializePlugin(m_object):
    """Unregister the plugin"""
    __remove_menu__()

"""A plugin designed to import and export OW formats from Autodesk Maya"""

# OW formats import / export plugin for Maya

import maya.OpenMayaMPx as OpenMayaMPx

from OWMImporter import ui, options, read_owmat, read_owmdl
from OWMImporter import import_owmat, import_owmdl

Version = "0.7.0 Alpha"


def __remove_menu__():
    ui.remove_menu()


def __reload_hook__():
    reload(ui)
    reload(options)
    reload(import_owmdl)
    reload(import_owmat)
    reload(read_owmat)
    reload(read_owmdl)


def __create_menu__():
    ui.create_menu(__reload_hook__)


def initializePlugin(m_object):
    """Register the plugin"""
    OpenMayaMPx.MFnPlugin(m_object, "mayasombra", Version, "Any")
    __create_menu__()


def uninitializePlugin(m_object):
    """Unregister the plugin"""
    __remove_menu__()

import settings
import os.path
import maya.cmds as cmds
import maya.mel as mel

from OWMImporter import import_owmdl, import_owmap, import_owentity


model_options = ['Models', 'Locators']


def about_window():
    """Present the about information"""
    cmds.confirmDialog(
        message="An OW Formats import and export plugin for Autodesk Maya.",
        button=['OK'], defaultButton='OK', title="About OW Tools")


def importfile_dialog(filter_str="", caption_str=""):
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


def remove_menu():
    """Removes the plugin menu"""
    if cmds.control("OWToolsMenu", exists=True):
        cmds.deleteUI("OWToolsMenu", menu=True)


def create_menu(hook):
    """Creates the plugin menu"""
    remove_menu()

    # Create the base menu object
    cmds.setParent(mel.eval("$tmp = $gMainWindow"))
    menu = cmds.menu("OWToolsMenu", label="OW Tools", tearOff=True)

    # This try clause is here to support iterating on the UI. If
    # there's a bug that causes this part to fail, we'll still
    # execute the finally code which includes the reload hook.
    # That way, I can always use the reload button to fix the code.
    try:
        # Model menu controls
        cmds.menuItem(label="Model", subMenu=True)

        cmds.menuItem(label="Import OWMDL File",
                      annotation="Imports an OW Model File",
                      command=lambda x: importModel())

        cmds.setParent(menu, menu=True)

        cmds.menuItem(label="Map", subMenu=True)
        cmds.menuItem(label="Import OWMAP File",
                      annotation="Imports an OW Map File",
                      command=lambda x: importMap())
        cmds.setParent(menu, menu=True)

        cmds.menuItem(label="Entity", subMenu=True)
        cmds.menuItem(label="Import OWENTITY File",
                      annotation="Imports an OW Entity File",
                      command=lambda x: importEntity())
        cmds.setParent(menu, menu=True)

        cmds.menuItem(divider=True)

        cmds.setParent(menu, menu=True)
        cmds.menuItem(label="Options",
                      annotation="Configure options for plugin",
                      command=lambda x: options_menu())

    # Reload and about controls
    finally:
        cmds.menuItem(label="Reload Plugin", command=lambda x: reload_plugin(
            hook), annotation="Attempts to reload the plugin")
        cmds.menuItem(label="About", command=lambda x: about_window())


def options_menu():
    window = cmds.window(t='Overwatch Model Import Configuration')
    cmds.columnLayout(adj=True)
    cmds.frameLayout(cll=True, label='Model Options')
    cmds.columnLayout()
    cmds.checkBoxGrp(ncb=3, l='Model Import: ',
                     la3=['Materials', 'Bones', 'Empties'],
                     ann='Choose what to import.',
                     v1=settings.get_setting('ModelImportMaterials'),
                     v2=settings.get_setting('ModelImportBones'),
                     v3=settings.get_setting('ModelImportEmpties'),
                     cc1=lambda x: cs('ModelImportMaterials', x),
                     cc2=lambda x: cs('ModelImportBones', x),
                     cc3=lambda x: cs('ModelImportEmpties', x),
                     en3=False)
    cmds.setParent('..')
    cmds.setParent('..')
    cmds.frameLayout(cll=True, label='Map Options')
    cmds.columnLayout()
    cmds.checkBoxGrp(ncb=3, l='Maps Import: ',
                     la3=['Models', 'Materials', 'Lights Objects'],
                     ann='Choose what to import.',
                     v1=settings.get_setting('MapImportModels'),
                     v2=settings.get_setting('MapImportMaterials'),
                     v3=settings.get_setting('MapImportLights'),
                     cc1=lambda x: cs('MapImportModels', x),
                     cc2=lambda x: cs('MapImportMaterials', x),
                     cc3=lambda x: cs('MapImportLights', x),
                     en3=True)
    cmds.setParent('..')
    ima = cmds.optionMenu(l='Import Models As',
                          cc=lambda x: cs('MapImportModelsAs',
                                          model_options.index(x)+1))
    cmds.menuItem(l='Models', ann='Loads the models for the level.')
    cmds.menuItem(l='Locators', ann='Replaces models with a locator (null) '
                  'with the proper location, rotation, and scale.')
    cmds.optionMenu(ima, e=True,
                    sl=settings.get_setting('MapImportModelsAs'))

    cmds.setParent('..')
    cmds.checkBoxGrp(ncb=3, l='Object Import: ',
                     la3=['Large Models', 'Detail Models', 'Physics Model'],
                     ann='Large models are for buildings, trees, and '
                         'landscapes. Detail models are for video games, '
                         'cars, and laptops. The Physics model is used for '
                         'collision detection.',
                     v1=int(settings.get_setting('MapImportObjectsLarge')),
                     v2=int(settings.get_setting('MapImportObjectsDetail')),
                     v3=int(settings.get_setting('MapImportObjectsPhysics')),
                     cc1=lambda x: cs('MapImportObjectsLarge', x),
                     cc2=lambda x: cs('MapImportObjectsDetail', x),
                     cc3=lambda x: cs('MapImportObjectsPhysics', x),
                     en3=False)
    cmds.setParent('..')
    cmds.columnLayout()
    cmds.checkBox(l='Hide Reference Models',
                  v=settings.get_setting('MapHideReferenceModels'),
                  cc=lambda x: cs('MapHideReferenceModels', x))
    cmds.setParent('..')
    cmds.frameLayout(cll=True, label='Render Options')
    cmds.columnLayout()
    rm = cmds.optionMenu(l='Model Renderer',
                         cc=lambda x: settings.change_setting('Renderer', x))
    rs = settings.renderers
    for r in rs:
        cmds.menuItem(l=r)

    cmds.optionMenu(rm, e=True,
                    sl=rs.index(settings.get_setting('Renderer'))+1)
    cmds.setParent('..')

    footer = cmds.formLayout()
    save = cmds.button(l='Save', command=lambda x: settings.save_settings())
    close = cmds.button(l='Close', command=lambda x: cmds.deleteUI(window))
    cmds.formLayout(footer, e=True, af=[
        (save, "left", 5), (save, "bottom", 5),
        (close, "bottom", 5), (close, "right", 5)],
        ap=[(save, "right", 1, 50), (close, "left", 1, 50)])
    cmds.setParent('..')

    cmds.showWindow()


def cs(k, v):
    settings.change_setting(k, v)


def importEntity():
    import_file = importfile_dialog(
        "OWENTITY Files (*.owentity)", "Import OWENTITY")
    if import_file:
        import_owentity.read(import_file, settings.Settings, True)


def importMap():
    import_file = importfile_dialog(
        "OWMAP Files (*.owmap)", "Import OWMAP")
    if import_file:
        import_owmap.read(import_file, settings.Settings)


def importModel():
    import_file = importfile_dialog(
        "OWMDL Files (*.owmdl)", "Import OWMDL")
    if import_file:
        import_owmdl.read(import_file, settings.Settings)


def reload_plugin(hook):
    """Reloads the plugin, not all Maya versions support this"""
    # cmds.unloadPlugin("OWImporter.py")
    # cmds.loadPlugin("OWImporter.py")
    hook()

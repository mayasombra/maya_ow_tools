import options
import os.path
import maya.cmds as cmds
import maya.mel as mel

from OWMImporter import import_owmdl

renderers = ['Stingray', 'Arnold', 'Redshift']


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
                      command=lambda x: import_owmodel())

        cmds.setParent(menu, menu=True)
        # cmds.menuItem(divider=True)

        cmds.setParent(menu, menu=True)
        cmds.menuItem(label="Options",
                      annotation="Configure options for plugin",
                      command=lambda x: options_menu())

        cmds.menuItem(label="Print Selected Renderer",
                      annotation="...",
                      command=lambda x: options.print_selected_renderer())

    # Reload and about controls
    finally:
        cmds.menuItem(label="Reload Plugin", command=lambda x: reload_plugin(
            hook), annotation="Attempts to reload the plugin")
        cmds.menuItem(label="About", command=lambda x: about_window())


def options_menu():
    global pluginSettings
    window = cmds.window(t='Overwatch Model Import Configuration')
    cmds.columnLayout(adj=True)
    cmds.text(l='TODO: none of these options except Model Renderer actually do anything yet')
    cmds.frameLayout(cll=True, label='Global Options')
    cmds.columnLayout()
    cmds.checkBox(l='Import Textures',
                  v=options.get_setting('import_textures', bool),
                  cc=lambda x: options.change_setting('import_textures', x),
                  en=True)
    cmds.checkBox(l='Hide Reference Models', v=True)
    cmds.setParent('..')
    cmds.setParent('..')
    cmds.frameLayout(cll=True, label='Model Options')
    cmds.columnLayout()
    cmds.checkBoxGrp(ncb=3, l='Models Import: ',
                     la3=['Materials', 'Bones', 'Empty Objects'],
                     va3=[1, 1, 1], en3=True)
    cmds.setParent('..')
    cmds.setParent('..')
    cmds.frameLayout(cll=True, label='Render Options')
    cmds.columnLayout()
    rm = cmds.optionMenu(l='Model Renderer', cc=options.selectRenderer)
    for r in options.renderers:
        cmds.menuItem(l=r)

    cmds.optionMenu(rm, e=True,
                    sl=renderers.index(options.get_setting('renderer'))+1)
    cmds.setParent('..')

    footer = cmds.formLayout()
    save = cmds.button(l='Save', command=lambda x: options.save_settings())
    close = cmds.button(l='Close', command=lambda x: cmds.deleteUI(window))
    cmds.formLayout(footer, e=True, af=[
        (save, "left", 5), (save, "bottom", 5),
        (close, "bottom", 5), (close, "right", 5)],
        ap=[(save, "right", 1, 50), (close, "left", 1, 50)])
    cmds.setParent('..')

    cmds.showWindow()


def import_owmodel():
    import_file = importfile_dialog(
        "OWMDL Files (*.owmdl)", "Import OWMDL")
    if import_file:
        import_owmdl.read(import_file, None)


def reload_plugin(hook):
    """Reloads the plugin, not all Maya versions support this"""
    # cmds.unloadPlugin("OWImporter.py")
    # cmds.loadPlugin("OWImporter.py")
    hook()

import ast
import maya.cmds as cmds

renderers = ['Stingray', 'Arnold', 'Redshift']

defaultPluginSettings = {
    'renderer': 'Arnold',
    'hide_reference_models': 'True',
    'import_textures': 'True',
}

pluginSettings = {
}


def selectRenderer(item):
    print "Selected renderer: ", item
    change_setting('renderer', item)


def __print_selected_renderer():
    print "Renderer: ", renderers[get_setting('renderer', int)]


def get_setting(name, typ=str):
    global pluginSettings
    if typ == bool:
        return ast.literal_eval(pluginSettings[name])
    if typ == str:
        return pluginSettings[name]
    if typ == int:
        return int(pluginSettings[name])


def change_setting(name, val):
    # TODO(fix typing here)
    print "changing %s to %s" % (name, val)
    pluginSettings[name] = str(val)


def save_settings():
    settings = ';'.join(['='.join(x) for x in pluginSettings.items()])
    print "save_settings: ", settings
    cmds.optionVar(sv=('MayaOverwatchSettings', settings))


def load_settings():
    global defaultPluginSettings, pluginSettings
    if cmds.optionVar(exists='MayaOverwatchSettings'):
        settings = cmds.optionVar(q='MayaOverwatchSettings')
        if settings != "":
            pluginSettings = {k: v for k, v in [
                x.split('=') for x in settings.split(';')]}
            print pluginSettings
            return
    print "Using default settings"
    pluginSettings = defaultPluginSettings

load_settings()

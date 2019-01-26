import maya.cmds as cmds

renderers = ['Stingray', 'Redshift']


class DefSettings:
        def __init__(self,
                     MapImportModels=1,
                     MapImportTextures=1,
                     MapImportMaterials=1,
                     MapImportLights=1,
                     MapImportModelsAs=1,
                     MapImportObjectsLarge=1,
                     MapImportObjectsDetail=1,
                     MapImportObjectsPhysics=0,
                     ModelImportMaterials=1,
                     ModelImportBones=1,
                     ModelImportEmpties=0,
                     MapHideReferenceModels=1,
                     Renderer='Stingray'):
            self.MapImportTextures = int(MapImportTextures)

            self.MapImportModels = int(MapImportModels)
            self.MapImportMaterials = int(MapImportMaterials)
            self.MapImportLights = int(MapImportLights)
            self.MapImportModelsAs = int(MapImportModelsAs)

            self.MapImportObjectsLarge = int(MapImportObjectsLarge)
            self.MapImportObjectsDetail = int(MapImportObjectsDetail)
            self.MapImportObjectsPhysics = int(MapImportObjectsPhysics)

            self.ModelImportMaterials = int(ModelImportMaterials)
            self.ModelImportBones = int(ModelImportBones)
            self.ModelImportEmpties = int(ModelImportEmpties)

            self.MapHideReferenceModels = int(MapHideReferenceModels)

            self.Renderer = Renderer

        def save_settings(self):
            settings = ';'.join(
                ['%s=%s' % (x[0], x[1]) for x in vars(self).items()])
            cmds.optionVar(sv=('MayaOverwatchSettings', settings))

        def load_settings(self):
            if not cmds.optionVar(exists='MayaOverwatchSettings'):
                return
            settings = cmds.optionVar(q='MayaOverwatchSettings')
            if settings != "":
                pluginSettings = {k: v for k, v in [
                    x.split('=') for x in settings.split(';')]}
                for key in pluginSettings:
                    if hasattr(self, key):
                        setattr(self, key, pluginSettings[key])


def change_setting(name, val):
    setattr(Settings, name, val)


def get_setting(name):
    return getattr(Settings, name)


def save_settings():
    Settings.save_settings()


Settings = DefSettings()
Settings.load_settings()

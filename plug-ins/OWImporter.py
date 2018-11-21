import os
import sys
import re
import maya.cmds as cmds
import maya.OpenMayaMPx as OpenMayaMPx

from OWMImporter import import_owmat
from OWMImporter import import_owmap
from OWMImporter import import_owmdl
from OWMImporter import import_owanim

PluginName = "Overwatch Importer"
Version = "0.7.0 Alpha"
settings = None


class ImportOverwatchSettings:
    def __init__(self,
                 MapImportModels=True,
                 MatImportTextures=True,
                 MapImportMaterials=True,
                 MapImportLights=True,
                 MapImportModelsAs=1,
                 MapImportObjectsLarge=True,
                 MapImportObjectsDetail=True,
                 MapImportObjectsPhysics=False,
                 ModelImportMaterials=True,
                 ModelImportBones=True,
                 ModelImportEmpties=False,
                 MapHideReferenceModels=True):
        self.MatImportTextures = int(MatImportTextures)

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

    def toString(self):
        string = "-%s %s" % ("MapImportModels",
                             self.MapImportModels)
        string += "-%s %s" % ("MatImportTextures",
                              self.MatImportTextures)
        string += "-%s %s" % ("MapImportMaterials",
                              self.MapImportMaterials)
        string += "-%s %s" % ("MapImportLights",
                              self.MapImportLights)
        string += "-%s %s" % ("MapImportModelsAs",
                              self.MapImportModelsAs)
        string += "-%s %s" % ("MapImportObjectsLarge",
                              self.MapImportObjectsLarge)
        string += "-%s %s" % ("MapImportObjectsDetail",
                              self.MapImportObjectsDetail)
        string += "-%s %s" % ("MapImportObjectsPhysics",
                              self.MapImportObjectsPhysics)
        string += "-%s %s" % ("ModelImportMaterials",
                              self.ModelImportMaterials)
        string += "-%s %s" % ("ModelImportBones",
                              self.ModelImportBones)
        string += "-%s %s" % ("MapHideReferenceModels",
                              self.MapHideReferenceModels)

        return string

    def fromString(self, string):
        string = string[1:]
        tokens = string.split('-')
        values = {}
        # print tokens
        for t in tokens:
            o = t.split()
            values[o[0].strip()] = o[1].strip()

        self.MapImportModels = int(values["MapImportModels"])
        self.MatImportTextures = int(values["MatImportTextures"])
        self.MapImportMaterials = int(values["MapImportMaterials"])
        self.MapImportLights = int(values["MapImportLights"])
        self.MapImportModelsAs = int(values["MapImportModelsAs"])
        self.MapImportObjectsLarge = int(values["MapImportObjectsLarge"])
        self.MapImportObjectsDetail = int(values["MapImportObjectsDetail"])
        self.MapImportObjectsPhysics = int(values["MapImportObjectsPhysics"])
        self.ModelImportMaterials = int(values["ModelImportMaterials"])
        self.ModelImportBones = int(values["ModelImportBones"])
        self.MapHideReferenceModels = int(values["MapHideReferenceModels"])


# main Command
class ImportOverWatch(OpenMayaMPx.MPxFileTranslator):
    global settings

    def __init__(self):
        OpenMayaMPx.MPxFileTranslator.__init__(self)

    # Can not be Exported
    def canBeOpened(self):
        return False

    # Can Import
    def haveReadMethod(self):
        return True

    # Filters and Extensions
    def defaultExtension(self):
        return "OWMdl"

    def filter(self):
        return "*.OWMdl *.OWMap *.OWMat *.OWAnim"

    def readFile(self, file, options):
        # print "Supplied Options: %s"%options
        options = re.sub('[;]', '', options)
        settings.fromString(options)

        self.filepath = os.path.normpath(file.fullName())
        fpath, fext = os.path.splitext(self.filepath)
        fpath, fname = os.path.split(fpath)
        fpath = os.path.normpath(fpath)
        print "fpath: %s, fname: %s, fext: %s" % (fpath, fname, fext)
        if cmds.upAxis(q=True, axis=True) != "y":
            cmds.upAxis(ax='y', rv=True)

        if(fext.lower() == ".owmap"):
            print("loading map...")
            import_owmap.read(self.filepath, settings)
        elif(fext.lower() == ".owmdl"):
            print("loading model...")
            import_owmdl.read(self.filepath, settings)
        elif(fext.lower() == ".owmat"):
            print("loading material...")
            import_owmat.read(self.filepath)
        elif(fext.lower() == ".owanim"):
            print("loading animation...")
            import_owanim.read(self.filepath, settings)
        else:
            return 1

    # Read the File
    def reader(self, file, options, mode):
        return self.readFile(file, options)


# Creator
def translatorCreator():
    print ("// %s, v%s" % (PluginName, Version))
    return OpenMayaMPx.asMPxPtr(ImportOverWatch())


# initialize the script plug-in
def initializePlugin(mobject):
    global settings
    mplugin = OpenMayaMPx.MFnPlugin(mobject, "Kjasi", Version, "Any")
    settings = ImportOverwatchSettings()
    try:
        mplugin.registerFileTranslator(
            PluginName, None, translatorCreator,
            "OWMImporterOptions", settings.toString())
    except:
        sys.stderr.write(
            "Failed to register command: %s\n" % "OverWatchImporter")
        raise


# uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterFileTranslator(PluginName)
    except:
        sys.stderr.write(
            "Failed to unregister command: OverwatchImporter\n")

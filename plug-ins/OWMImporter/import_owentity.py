import os

from . import read_owentity, import_owmdl

import maya.cmds as cmds


def read(filename, settings, import_children=True, is_child=False):
    root, file = os.path.split(filename)
    entity = file.replace('.003.owentity', '')

    data = read_owentity.read(filename)
    if data is None:
        return None, None

    entityObject = None
    baseModel = None

    if data.model != 'null':
        modelFile = os.path.join(root, "..", "..", "Models", data.model,
                                 data.model.replace('.00C', '.owmdl'))
        modelFile = os.path.normpath(modelFile)

        baseModel = import_owmdl.read(modelFile, settings)
        entityGroupName = ("entity_%s_0" % entity)
        entityObject = cmds.group(em=True, name=entityGroupName, w=True)
        cmds.parent(baseModel[0], entityObject)

    if import_children:
        for child in data.children:
            child_file = os.path.normpath(os.path.join(
                root, "..", child.file, child.file+'.owentity'))
            child_object, child_data, child_mdl = read(child_file, True, True)

    return entityObject, data, baseModel
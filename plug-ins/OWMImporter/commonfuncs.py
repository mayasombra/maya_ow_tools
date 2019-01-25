import re
import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya


def get_mobject(node):
    if not node:
        return None
    selectionList = OpenMaya.MSelectionList()
    selectionList.add(node)
    if selectionList.getDependNode(0):
        oNode = selectionList.getDependNode(0)
        return oNode
    else:
        return None


def get_mobjname(node):
    if (not node) or (not (type(node) == type(OpenMaya.MObject()))):
        return ""
    oNode = OpenMaya.MFnDependencyNode(node)
    return oNode


def get_NameFromLong(node):
    out = node[(node.rfind('|')+1):]

    return out


def adjustAxis(vector):
    axis = cmds.upAxis(q=True, axis=True)
    if axis == "y":
        return vector
    else:
        # axis is Z-up
        return (vector[0], -vector[2], vector[1])


def wadjustAxis(vector):
    return vector


def MayaSafeName(input):
    output = re.sub(u"\u00F6", 'o', input)
    output = re.sub('[\']', '', output)
    output = re.sub('[\'()]', '', output)
    output = re.sub('[. ]', '_', output)
    output = re.sub('_+', '_', output)
    output = re.sub('_$', '', output)
    return output

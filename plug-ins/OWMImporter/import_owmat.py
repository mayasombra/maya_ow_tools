import os
import maya.cmds as cmds

from OWMImporter import read_owmat

textureList = {}
TexErrors = {}


def getRealPath(root, texture, inPath):
    global textureList, TexErrors
    outPath = inPath
    doPass = False

    if not os.path.isabs(inPath):
        inPath = os.path.normpath('%s/%s' % (root, inPath))

    if os.path.isfile("%s.psd" % inPath):
        outPath = "%s.psd" % inPath
    elif os.path.isfile("%s.tif" % inPath):
        outPath = "%s.tif" % inPath
    elif os.path.isfile("%s.tga" % inPath):
        outPath = "%s.tga" % inPath
    elif os.path.isfile("%s.png" % inPath):
        outPath = "%s.png" % inPath
    else:
        if texture not in TexErrors:
            cmds.warning("Unable to find compatible image for %s. "
                         "Please convert to TIF, TGA, PSD or PNG." % texture)
            outPath = "%s.tif" % inPath
            TexErrors[texture] = inPath
        doPass = True

    return outPath, doPass


def buildCollision(mname):
    # Build initial network
    shader = cmds.shadingNode("lambert", asShader=True, name=mname)
    shadinggroup = cmds.sets(renderable=True, empty=True, name="%sSG" % shader)
    cmds.connectAttr('%s.outColor' % shader, '%s.surfaceShader' % shadinggroup,
                     force=True)

    checkerNode = cmds.shadingNode("checker", at=True, name="collisionChecker")
    p2dTex = cmds.shadingNode("place2dTexture", au=True)
    cmds.connectAttr('%s.outUV' % p2dTex, '%s.uv' % checkerNode)
    cmds.connectAttr('%s.outUvFilterSize' % p2dTex,
                     '%s.uvFilterSize' % checkerNode)

    cmds.setAttr('%s.color1' % checkerNode, 1, 0, 1, type="double3")
    cmds.setAttr('%s.color2' % checkerNode, 0, 1, 0.25, type="double3")
    cmds.setAttr('%s.repeatU' % p2dTex, 50)
    cmds.setAttr('%s.repeatV' % p2dTex, 50)

    cmds.connectAttr('%s.outColor' % checkerNode, '%s.color' % shader)

    # Return the name of the finished shader
    return shadinggroup


# The Stingray node is our ideal material (for now) At some point, I might
# build a Overwatch-specific shader network...
def buildStingray(root, mname, material):
    global textureList
    # print "Building Stingray shader..."

    # Build initial network
    shader = cmds.shadingNode("StingrayPBS", asShader=True, name=mname)
    # print "Built shader: ", shader
    shadinggroup = cmds.sets(renderable=True, empty=True, noSurfaceShader=True,
                             name="%sSG" % shader)
    cmds.shaderfx(sfxnode=shader, initShaderAttributes=True)
    cmds.connectAttr('%s.outColor' % shader, '%s.surfaceShader' % shadinggroup,
                     force=True)

    cmds.setAttr("%s.metallic" % shader, 0)
    cmds.setAttr("%s.roughness" % shader, 1)

    for texturetype in material.textures:
        typ = texturetype[2]
        texture = texturetype[0]
        realpath = os.path.splitext(texture)[0]+'.tif'
        # print "raw realpath", realpath, " texture ", texture, "type ", typ
        realpath = realpath.replace('\\', os.sep)
        if not os.path.isabs(realpath):
            # TODO: check this on Windows
            realpath = os.path.normpath('%s/dummy/%s' % (root, realpath))

        try:
            fn, fext = os.path.splitext(realpath)
            fpath, name = os.path.split(fn)
            finame = ("img_%s" % name)
            if fn in textureList:
                file_node = textureList[fn]
            else:
                if not cmds.objExists(fn):
                    file_node = cmds.shadingNode(
                        'file', name=finame, asTexture=True)
                    textureUV = cmds.shadingNode(
                        'place2dTexture',
                        name=("place2dTexture_%s" % name), asUtility=True)
                    cmds.connectAttr(("%s.outUV" % textureUV),
                                     '%s.uvCoord' % file_node)
                    textureList[fn] = file_node
                    cmds.setAttr(("%s.fileTextureName" % file_node),
                                 realpath, type="string")
                else:
                    file_node = finame

            if typ == 2903569922 or typ == 1716930793 or typ == 1239794147:
                # print "binding color"
                cmds.setAttr("%s.use_color_map" % shader, 1)
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.TEX_color_map' % shader)
            elif typ == 378934698 or typ == 562391268:
                # print "binding normal"
                cmds.setAttr("%s.use_normal_map" % shader, 1)
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.TEX_normal_map' % shader)
            elif typ == 548341454 or typ == 3111105361:
                # print "binding metallic"
                cmds.setAttr("%s.use_metallic_map" % shader, 1)
                cmds.setAttr("%s.use_roughness_map" % shader, 1)
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.TEX_roughness_map' % shader)
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.TEX_metallic_map' % shader)
            elif typ == 3166598269:
                # print "binding emissive"
                cmds.setAttr("%s.use_emissive_map" % shader, 1)
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.TEX_emissive_map' % shader)
            elif typ == 3761386704:
                # print "binding AO"
                cmds.setAttr("%s.use_ao_map" % shader, 1)
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.TEX_ao_map' % shader)
            else:
                print ("import_owmat: ignoring unknown "
                       "texture type ", typ)

        except:
            pass

    # Return the name of the finished shader
    # print "Assigned materials to shader: ", shader
    return shadinggroup


def read(filename, prefix=''):
    global textureList
    textureList = {}
    root, file = os.path.split(filename)
    data = read_owmat.read(filename)
    if not data:
        return None

    m = {}

    for material in data.materials:
        mname = 'Mat_%s%016X' % (prefix, material.key)
        if cmds.objExists(mname):
            shader = mname
        else:
            shader = buildStingray(root, mname, material)
            m[material.key] = shader
    return m, textureList

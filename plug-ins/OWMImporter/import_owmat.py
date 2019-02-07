import json
import os
import maya.cmds as cmds

from OWMImporter import read_owmat, redshift, settings, stingray


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


def buildShader(root, mname, material, textureList):
    # Load textures
    texture_nodes = {}
    for texturetype in material.textures:
        typ = texturetype[2]
        texture = texturetype[0]
        file_node, name, realpath = make_texture_node(
            texture, root, textureList)
        texture_nodes[typ] = (file_node, name, realpath)

    if settings.get_setting('Renderer') == 'Redshift':
        return redshift.buildRedshift(material, mname, texture_nodes)

    # Stingray by default
    return stingray.buildShader(material, mname, texture_nodes)


def texture_path(texture, root):
    realpath = os.path.splitext(texture)[0]+'.tif'
    realpath = realpath.replace('\\', os.sep)
    if not os.path.isabs(realpath):
        realpath = os.path.normpath('%s/%s' % (root, realpath))
    return realpath


def make_texture_node(texture, root, textureList):
    realpath = texture_path(texture, root)
    file_node, name = bind_node(realpath, textureList)
    return file_node, name, realpath


def bind_node(realpath, textureList):
    fn, fext = os.path.splitext(realpath)
    fpath, name = os.path.split(fn)
    finame = ("img_%s" % name)
    if fn in textureList:
        file_node = textureList[fn]
    else:
        # For loading maps, it's a good idea to use just the
        # base name (which is globally unique because of the export
        # process). This keeps us from having many copies of the same
        # input textures.
        if not cmds.objExists(finame):
            file_node = cmds.shadingNode(
                'file', name=finame, asTexture=True)
            textureUV = cmds.shadingNode(
                'place2dTexture',
                name=("place2dTexture_%s" % name), asUtility=True)
            cmds.connectAttr(("%s.outUV" % textureUV),
                             '%s.uvCoord' % file_node)
            cmds.setAttr(("%s.fileTextureName" % file_node),
                         realpath, type="string")
        else:
            file_node = finame
            realpath = cmds.getAttr("%s.fileTextureName" % file_node)
            fn, fext = os.path.splitext(realpath)
        textureList[fn] = file_node
    return file_node, name


def read(filename, prefix=''):
    # Normalize the filename for OS-independent separators
    filename = filename.replace('\\', os.sep)

    root, file = os.path.split(filename)
    data = read_owmat.read(filename)
    if not data:
        return None, None

    m = {}
    textureList = {}
    for material in data.materials:
        mname = 'Mat_%s%016X' % (prefix, material.key)
        if cmds.objExists(mname):
            shader = mname
        else:
            localTextures = {}
            shader = buildShader(root, mname, material, localTextures)
            cmds.addAttr(mname,
                         ln="textureList", dt='string')
            cmds.setAttr(mname+".textureList",
                         json.dumps(localTextures), type='string')
        localTextures = json.loads(cmds.getAttr(mname+".textureList"))
        textureList.update(localTextures)
        m[material.key] = shader
    return m, textureList

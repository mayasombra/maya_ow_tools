import os
import maya.cmds as cmds

from OWMImporter import read_owmat
from OWMImporter import gfx

textureList = {}
TexErrors = {}


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
    shader = cmds.shadingNode('StingrayPBS',
                              asShader=True,
                              name=mname)
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
        print "texture identifier: ", texture

        try:
            if typ == 2903569922 or typ == 1716930793 or typ == 1239794147:
                print "binding color", typ, " on material ", mname
                file_node = make_texture_node(texture, root)
                cmds.setAttr("%s.use_color_map" % shader, 1)
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.TEX_color_map' % shader)
            elif typ == 378934698 or typ == 562391268:
                print "binding normal", typ, " on material ", mname
                file_node = make_texture_node(texture, root)
                cmds.setAttr("%s.use_normal_map" % shader, 1)
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.TEX_normal_map' % shader)

                # This map also provides the emissive color
                # emissive is only enabled if there is an emissive
                # texture, so this linkage is safe.
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.emissive' % shader)

            elif typ == 548341454 or typ == 3111105361:
                print "binding metallics ", typ, " on material ", mname
                cmds.setAttr("%s.use_metallic_map" % shader, 1)
                cmds.setAttr("%s.use_roughness_map" % shader, 1)

                pbr = texture_path(texture, root)
                rough_path = pbr.replace('.tif', '-rough.tif')
                if not os.path.isfile(rough_path):
                    gfx.transform(pbr, gfx.roughness, rough_path)
                rough = bind_node(rough_path)
                metal_path = pbr.replace('.tif', '-metal.tif')
                if not os.path.isfile(metal_path):
                    gfx.transform(pbr, gfx.metal, metal_path)
                metal = bind_node(metal_path)

                cmds.connectAttr('%s.outColor' % rough,
                                 '%s.TEX_roughness_map' % shader)

                cmds.connectAttr('%s.outColor' % metal,
                                 '%s.TEX_metallic_map' % shader)

                # This is completely wrong for specular. Not sure what
                # to do for Stingray.
                # cmds.connectAttr('%s.outColor' % specular,
                #                  '%s.TEX_global_specular_cube' % shader,
                #                  force=True)

            elif typ == 3166598269:
                print "binding emissive ", typ, " on material ", mname
                file_node = make_texture_node(texture, root)
                cmds.setAttr("%s.use_emissive_map" % shader, 1)
                cmds.setAttr("%s.emissive_intensity" % shader, 0.3)
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.TEX_emissive_map' % shader)
            elif typ == 3761386704:
                print "binding AO ", typ, " on material ", mname
                # Need to figure this out. The AO map is a strength bit,
                # not sure what Maya is expecting.
                file_node = make_texture_node(texture, root)
                cmds.setAttr("%s.use_ao_map" % shader, 1)
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.TEX_ao_map' % shader)
            else:
                print ("import_owmat: ignoring unknown "
                       "texture type ", typ, " on material ", mname,
                       " from ", texture_path(texture, root))

        except Exception as e:
            print "Exception while materialing: %s" % e

    # Return the name of the finished shader
    # print "Assigned materials to shader: ", shader
    return shadinggroup


def texture_path(texture, root):
    realpath = os.path.splitext(texture)[0]+'.tif'
    realpath = realpath.replace('\\', os.sep)
    if not os.path.isabs(realpath):
        realpath = os.path.normpath('%s/%s' % (root, realpath))
    return realpath


def make_texture_node(texture, root):
    realpath = texture_path(texture, root)
    return bind_node(realpath)


def bind_node(realpath):
    global textureList
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
            cmds.setAttr(("%s.colorSpace" % file_node),
                         "Raw", type="string")
        else:
            file_node = finame
    return file_node


def read(filename, prefix=''):
    global textureList
    textureList = {}
    # Normalize the filename for OS-independent separators
    filename = filename.replace('\\', os.sep)

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

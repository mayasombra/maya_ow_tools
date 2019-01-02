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
        realpath = os.path.splitext(texture)[0]+'.tif'
        realpath = realpath.replace('\\', os.sep)
        if not os.path.isabs(realpath):
            realpath = os.path.normpath('%s/%s' % (root, realpath))

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
                    cmds.setAttr(("%s.colorSpace" % file_node),
                                 "Raw", type="string")
                else:
                    file_node = finame

            if typ == 2903569922 or typ == 1716930793 or typ == 1239794147:
                print "binding color", typ, " on material ", mname
                cmds.setAttr("%s.use_color_map" % shader, 1)
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.TEX_color_map' % shader)
            elif typ == 378934698 or typ == 562391268:
                print "binding normal", typ, " on material ", mname
                cmds.setAttr("%s.use_normal_map" % shader, 1)

                doubleX = double_node('DoubleX', '%s.outColorR' % file_node)

                xPrim1 = make_math_node('xPrim', 1,
                                        '%s.outFloat' % doubleX, 1.0)
                xPrime = square_node('xPrime', '%s.outFloat' % xPrim1)

                doubleY = double_node('DoubleY', '%s.outColorG' % file_node)

                yPrim1 = make_math_node('yPrim', 1,
                                        '%s.outFloat' % doubleY, 1.0)
                yPrime = square_node('yPrime', '%s.outFloat' % yPrim1)

                primeDiff = make_math_node('PrimeDiff', 1,
                                           '%s.outFloat' % xPrime,
                                           '%s.outFloat' % yPrime)

                fromOne = make_math_node('SubFromOne', 1, 1.0,
                                         '%s.outFloat' % primeDiff)
                clampTo0 = clamp('Clamp_0_X_', '%s.outFloat' % fromOne,
                                 minn=0.0, maxx=2.0)

                addOne = make_math_node('AddOne', 0,
                                        '%s.outputR' % clampTo0, 1.0)

                half = make_math_node('Half', 3,
                                      '%s.outFloat' % addOne,
                                      2.0)

                finalClamp = clamp('FinalClamp', '%s.outFloat' % half,
                                   minn=0.0, maxx=1.0)

                cmds.connectAttr('%s.outColorR' % file_node,
                                 '%s.TEX_normal_mapX' % shader)
                cmds.connectAttr('%s.outColorG' % file_node,
                                 '%s.TEX_normal_mapY' % shader)
                cmds.connectAttr('%s.outputR' % finalClamp,
                                 '%s.TEX_normal_mapZ' % shader)

            elif typ == 548341454 or typ == 3111105361:
                print "binding metallics ", typ, " on material ", mname
                cmds.setAttr("%s.use_metallic_map" % shader, 1)
                cmds.setAttr("%s.use_roughness_map" % shader, 1)

                # Roughness texture extraction
                subFromOne = cmds.shadingNode('floatMath',
                                              asUtility=True,
                                              name='Invert')
                cmds.setAttr('%s.floatA' % subFromOne, 1.0)
                cmds.setAttr('%s.operation' % subFromOne, 1)  # subtract
                cmds.connectAttr('%s.outColorG' % file_node,
                                 '%s.floatB' % subFromOne)

                roughness = cmds.shadingNode('channels',
                                             asUtility=True,
                                             name='MakeRoughness')
                cmds.setAttr('%s.channelR' % roughness, 0)
                cmds.setAttr('%s.channelG' % roughness, 0)
                cmds.setAttr('%s.channelB' % roughness, 0)
                cmds.connectAttr('%s.outFloat' % subFromOne,
                                 '%s.inColorR' % roughness)

                cmds.connectAttr('%s.outColor' % roughness,
                                 '%s.TEX_roughness_map' % shader)

                # Metallic texture extraction
                clampX1 = cmds.shadingNode('clamp',
                                           asUtility=True,
                                           name='Clamp_X_1_')
                cmds.setAttr('%s.minR' % clampX1, 0.5)
                cmds.setAttr('%s.maxR' % clampX1, 1.0)
                cmds.connectAttr('%s.outColorR' % file_node,
                                 '%s.inputR' % clampX1)

                subHalf = cmds.shadingNode('floatMath',
                                           asUtility=True,
                                           name='SubHalf')
                cmds.setAttr('%s.operation' % subHalf, 1)
                cmds.setAttr('%s.floatB' % subHalf, 0.5)
                cmds.connectAttr('%s.outputR' % clampX1,
                                 '%s.floatA' % subHalf)

                divHalf = cmds.shadingNode('floatMath',
                                           asUtility=True,
                                           name='DivHalf')
                cmds.setAttr('%s.operation' % divHalf, 3)
                cmds.setAttr('%s.floatB' % divHalf, 0.5)
                cmds.connectAttr('%s.outFloat' % subHalf,
                                 '%s.floatA' % divHalf)

                metallic = cmds.shadingNode('channels',
                                            asUtility=True,
                                            name='MakeMetallic')
                cmds.setAttr('%s.channelR' % metallic, 0)
                cmds.setAttr('%s.channelG' % metallic, 0)
                cmds.setAttr('%s.channelB' % metallic, 0)
                cmds.connectAttr('%s.outFloat' % divHalf,
                                 '%s.inColorR' % metallic)

                cmds.connectAttr('%s.outColor' % metallic,
                                 '%s.TEX_metallic_map' % shader)

                # Specular texture extraction (not sure about this)
                clamp0X = cmds.shadingNode('clamp',
                                           asUtility=True,
                                           name='Clamp_0_X_')
                cmds.setAttr('%s.minR' % clamp0X, 0.0)
                cmds.setAttr('%s.maxR' % clamp0X, 0.5)
                cmds.connectAttr('%s.outColorR' % file_node,
                                 '%s.inputR' % clamp0X)

                divHalf = cmds.shadingNode('floatMath',
                                           asUtility=True,
                                           name='DivHalf')
                cmds.setAttr('%s.operation' % divHalf, 3)
                cmds.setAttr('%s.floatB' % divHalf, 0.5)
                cmds.connectAttr('%s.outputR' % clamp0X,
                                 '%s.floatA' % divHalf)

                unitClamp = cmds.shadingNode('clamp',
                                             asUtility=True,
                                             name='ClampUnit')
                cmds.setAttr('%s.minR' % unitClamp, 0.0)
                cmds.setAttr('%s.maxR' % unitClamp, 1.0)
                cmds.connectAttr('%s.outFloat' % divHalf,
                                 '%s.inputR' % unitClamp)

                invert = cmds.shadingNode('floatMath',
                                          asUtility=True,
                                          name='Invert')
                cmds.setAttr('%s.floatA' % invert, 1.0)
                cmds.setAttr('%s.operation' % invert, 1)  # subtract
                cmds.connectAttr('%s.outputR' % unitClamp,
                                 '%s.floatB' % invert)

                specular = cmds.shadingNode('channels',
                                            asUtility=True,
                                            name='MakeSpecular')
                cmds.setAttr('%s.channelR' % specular, 0)
                cmds.setAttr('%s.channelG' % specular, 0)
                cmds.setAttr('%s.channelB' % specular, 0)
                cmds.connectAttr('%s.outFloat' % invert,
                                 '%s.inColorR' % specular)

                cmds.connectAttr('%s.outColor' % specular,
                                 '%s.TEX_global_specular_cube' % shader,
                                 force=True)

            elif typ == 3166598269:
                print "binding emissive ", typ, " on material ", mname
                cmds.setAttr("%s.use_emissive_map" % shader, 1)
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.TEX_emissive_map' % shader)
            elif typ == 3761386704:
                print "binding AO ", typ, " on material ", mname
                cmds.setAttr("%s.use_ao_map" % shader, 1)
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.TEX_ao_map' % shader)
            else:
                print ("import_owmat: ignoring unknown "
                       "texture type ", typ, " on material ", mname,
                       " from ", file_node)

        except Exception as e:
            print "Exception while materialing: %s" % e

    # Return the name of the finished shader
    # print "Assigned materials to shader: ", shader
    return shadinggroup


def clamp(n, val, minn=None, maxx=None):
    c = cmds.shadingNode('clamp', asUtility=True, name=n)
    if minn:
        cmds.setAttr('%s.minR' % c, minn)
    if maxx:
        cmds.setAttr('%s.maxR' % c, maxx)

    cmds.connectAttr(val, '%s.inputR' % c)
    return c


def make_math_node(n, opcode, a, b):
    c = cmds.shadingNode('floatMath', asUtility=True, name=n)
    cmds.setAttr('%s.operation' % c, opcode)

    print "binding value %s to A: %s %s" % (a, isinstance(a, str), type(a))
    if isinstance(a, (str, unicode)):
        cmds.connectAttr(a, '%s.floatA' % c)
    else:
        cmds.setAttr('%s.floatA' % c, a)

    print "binding value %s to B: %s" % (b, isinstance(b, str))
    if isinstance(b, (str, unicode)):
        cmds.connectAttr(b, '%s.floatB' % c)
    else:
        cmds.setAttr('%s.floatB' % c, b)

    return c


def double_node(n, val):
    return make_math_node(n, 0, val, val)


def square_node(n, val):
    return make_math_node(n, 2, val, val)


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

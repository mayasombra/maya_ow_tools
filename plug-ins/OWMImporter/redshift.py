import maya.cmds as cmds


def buildRedshift(material, mname, texture_nodes):
    tt = {
        0: "Unknown1",
        # Appears to be AO, but uses the second UVset some times ... maybe only
        # if it exists
        3335614873: "AO",
        2903569922: "DiffuseAO",  # Alpha channel is AO
        1239794147: "DiffuseOpacity",
        3093211343: "DiffusePlant",
        1281400944: "DiffuseFlag",
        1716930793: "Diffuse2",
        378934698: "Normal",
        562391268: "HairNormal",  # why?
        562391268: "CorneaNormal",  # maybe not
        548341454: "Specstuff",  # Metal (R) + Highlight (G) + Detail (B)
        3852121246: "Specstuff2",  # used for Mei's ice wall

        # sharp opacity (foliage, fences or anything else with sharp edges)
        1482859648: "Opacity",

        # used for smooth opacity, unless diffuse is "DiffusePlant", in which
        # case it should be sharp transparency. ugh!
        1140682086: "Opacity2",
        1557393490: "MaterialMask",  # ?
        3004687613: "SubsurfaceScattering",
        3166598269: "Emission",
        1523270506: "Emission2",
        4243598436: "Emission3",  # used for Mei's ice wall

        # Use this instead of diffuse for emission color. Emission mask is
        # likely an opacity map
        3989656707: "EmissionColor",
        2337956496: "HairAnisotropy",
        1117188170: "Specular",  # maybe hairspec
        3761386704: "AO"  # maybe hairao
    }

    # function to create a remapValue node to split out metalness and specular
    # map from a texture's red channel
    def remapForSpec(mname, remapName, matInput, graphPoint, pointPos):
        if not cmds.objExists(remapName):
            cmds.shadingNode("remapValue", asUtility=True, name=remapName)
            cmds.connectAttr('%s.outColor.outColorR' % file_node,
                             '%s.inputValue' % remapName)
            cmds.setAttr("%s.value[%s].value_Position" % (
                remapName, graphPoint), pointPos)
        cmds.connectAttr('%s.outValue' % remapName,
                         '%s.%s' % (mname, matInput))

    if cmds.objExists(mname):
        return "%sSG" % mname

    # Build initial network
    shader = cmds.shadingNode("RedshiftMaterial", asShader=True, name=mname)
    # print "Built shader: ", shader
    shadinggroup = cmds.sets(renderable=True, empty=True, noSurfaceShader=True,
                             name="%sSG" % shader)
    cmds.connectAttr('%s.outColor' % shader, '%s.surfaceShader' % shadinggroup,
                     force=True)

    cmds.setAttr("%s.refl_fresnel_mode" % mname, 2)
    cmds.setAttr("%s.refl_isGlossiness" % mname, 1)

    for typ, (file_node, name, realpath) in texture_nodes.items():
        # instead of trying for a key later, read the value here and put it in
        # a new variable.  if a key does not exist, set that variable to
        # "undefined" and hook this texture up like any other unused textures.
        # the file node's name will contain the undefined key, so the
        # dictionary above can be expanded by the user.
        typName = tt.get(typ, "Undefined")

        # print "working on", typName
        if typName in ['DiffuseAO', 'DiffuseOpacity', 'DiffuseBlack',
                       'DiffusePlant', 'DiffuseFlag', 'Diffuse2']:
            # print "binding color"
            cmds.connectAttr('%s.outColor' % file_node,
                             '%s.diffuse_color' % mname)
            # connecting the diffuse texture of the material to emission setup,
            # if it exists in case diffuse is set up before the emission, this
            # step is also attempted in the emission setup
            emissionTex = "emission_%s" % mname
            if cmds.objExists(emissionTex):
                cmds.connectAttr("%s.outColor" % file_node,
                                 "%s.inputs[1].color" % emissionTex)
        elif typName in ["Opacity2"]:
            # print "binding smooth opacity"
            # used for materials with many levels of transparency
            cmds.connectAttr('%s.outColor' % file_node,
                             '%s.opacity_color' % mname)
            # connecting the opacity texture of the material to emissionTransp
            # setup, if it exists in case opacity is set up before the
            # emissionTransp, this step is also attempted in the emissionTransp
            # setup
            emissionTranspTex = "emissionTransp_%s" % mname
            if cmds.objExists(emissionTranspTex):
                cmds.connectAttr("%s.outColor" % file_node,
                                 "%s.inputs[0].color" % emissionTranspTex)
        elif typName in ["Opacity"]:
            # print "binding sharp opacity"
            # used for binary transparency like on foliage in Redshift, the
            # base material needs to be piped into a special material
            # (rsSprite) rsSprite is what will be assigned to the mesh, so the
            # shadinggroup variable will have to be updated in this step
            # rsSprite shows up as a gray material in the viewport, so the base
            # material will be assigned for viewport representation
            rsSprite = "%s_sprite" % mname
            rsSpriteSG = "%s_spriteSG" % mname
            cmds.sets(renderable=True, empty=True, noSurfaceShader=True,
                      name=rsSpriteSG)
            cmds.shadingNode("RedshiftSprite", asShader=1, n=rsSprite)
            cmds.connectAttr('%s.outColor' % mname,
                             '%s.surfaceShader' % rsSpriteSG, force=True)
            cmds.connectAttr('%s.outColor' % rsSprite,
                             '%s.rsSurfaceShader' % rsSpriteSG, force=True)
            cmds.connectAttr("%s.outColor" % mname, "%s.input" % rsSprite)
            cmds.setAttr("%s.tex0" % rsSprite, realpath, type="string")
            cmds.setAttr("%s.mode" % rsSprite, 1)
            cmds.setAttr("%s.threshold" % rsSprite, 0.5)
            shadinggroup = rsSpriteSG
        elif typName in ['Normal', 'CorneaNormal']:
            # print "binding normal"
            rsBump = "rsBump_%s" % name
            if not cmds.objExists(rsBump):
                cmds.shadingNode("RedshiftBumpMap",
                                 asUtility=True,
                                 name=rsBump)
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.input' % rsBump)
                cmds.setAttr("%s.inputType" % rsBump, 1)
                cmds.setAttr("%s.scale" % rsBump, 1)
                cmds.setAttr("%s.colorSpace" % file_node, "Raw", typ="string")
            cmds.connectAttr('%s.out' % rsBump,
                             '%s.bump_input' % mname)

        elif typName in ['Specstuff', 'Specstuff2']:
            # print "binding spec stuff"
            remapMetal = "metal_%s" % name
            remapSpec = "spec_%s" % name
            cmds.setAttr("%s.colorSpace" % file_node, "Raw", typ="string")
            cmds.connectAttr('%s.outColor.outColorG' % file_node,
                             '%s.refl_roughness' % mname)
            # split out and connect metalness map
            remapForSpec(mname, remapMetal, "refl_metalness", 0, 0.505)
            # split out and connect spec map
            remapForSpec(mname, remapSpec, "refl_weight", 1, 0.495)
        elif typName in ['Emission', 'Emission2', 'Emission3']:
            # print "binding emission"
            # regular emission setup
            # using a layeredTexture to multiply the diffuse map with the
            # emmissive map
            emissionTex = "emission_%s" % mname
            cmds.shadingNode("layeredTexture", asTexture=1, name=emissionTex)
            cmds.connectAttr("%s.outColor" % file_node,
                             "%s.inputs[0].color" % emissionTex)
            cmds.setAttr("%s.inputs[0].blendMode" % emissionTex, 6)
            cmds.connectAttr("%s.outColor" % emissionTex,
                             "%s.emission_color" % mname)
            cmds.setAttr("%s.emission_weight" % mname, 1)
            # reading the diffuse texture of the material
            # in case emission is set up before diffuse, this step is also
            # attempted in the diffuse setup
            try:
                diffTex = cmds.listConnections("%s.diffuse_color" % mname)[0]
                cmds.connectAttr("%s.outColor" % diffTex,
                                 "%s.inputs[0].color" % emissionTex)
            except:
                pass
        elif typName in ['EmissionColor']:
            # print "binding emissionTransp"
            # special emission setup. used on glowing graffiti decals for
            # example using a layeredTexture to multiply this map with the
            # opacity map unlike the emission map above, this is a color map
            # and will take the diffuse map's job from above for the emission
            # mask (the equivalent of the map above) the opacity map will be
            # used
            emissionTranspTex = "emissionTransp_%s" % mname
            cmds.shadingNode("layeredTexture", asTexture=1,
                             name=emissionTranspTex)
            cmds.connectAttr("%s.outColor" % file_node,
                             "%s.inputs[1].color" % emissionTranspTex)
            cmds.setAttr("%s.inputs[0].blendMode" % emissionTranspTex, 6)
            cmds.connectAttr("%s.outColor" % emissionTranspTex,
                             "%s.emission_color" % mname)
            cmds.setAttr("%s.emission_weight" % mname, 1)
            # reading the opacity texture of the material in case emission is
            # set up before opacity, this step is also attempted in the opacity
            # setup
            try:
                opacityTex = cmds.listConnections(
                    "%s.opacity_color" % mname)[0]
                cmds.connectAttr("%s.outColor" % opacityTex,
                                 "%s.inputs[0].color" % emissionTranspTex)
            except:
                pass
        else:
            # all unused textures are connected to a layeredTexture.
            # the layeredTexture is then connected to the material's third
            # subsurface scattering layer, which will be unused.  from there,
            # the user can inspect and integrate those textures into the
            # material if needed.  otherwise they will have no influence on the
            # look of the material.
            unusedTex = "unused_%s" % mname
            if not cmds.objExists(unusedTex):
                cmds.shadingNode("layeredTexture", asTexture=1, name=unusedTex)
                cmds.connectAttr("%s.outColor" % unusedTex,
                                 "%s.ms_color2" % mname)
            # find next free slot and connect the texture to it
            count = 0
            inputs = cmds.listAttr("%s.inputs" % unusedTex,
                                   m=True, st="color")
            if inputs:
                count = len(inputs)
            cmds.connectAttr("%s.outColor" % file_node,
                             "%s.inputs[%s].color" % (unusedTex, count))

    # Return the name of the finished shader
    # print "Assigned materials to shader: ", shader
    return shadinggroup

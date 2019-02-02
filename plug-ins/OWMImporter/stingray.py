import maya.cmds as cmds
import os

DEBUG_OUTPUT = False


def buildShader(material, mname, texture_nodes):
    # Build initial network
    shader = cmds.shadingNode('StingrayPBS',
                              asShader=True,
                              name=mname)
    # print "Built shader: ", shader
    shadinggroup = cmds.sets(renderable=True, empty=True, noSurfaceShader=True,
                             name="%sSG" % shader)
    cmds.shaderfx(sfxnode=shader, initShaderAttributes=True)

    shader_dir = os.path.dirname(os.path.realpath(__file__))
    shader_file = os.path.join(
        shader_dir, ('ow_shader_%d.sfx' % material.shader))

    # If the shader isn't implemented, use #44 as it's pretty good.
    if not os.path.isfile(shader_file):
        shader_file = os.path.join(shader_dir, 'ow_shader_44.sfx')

    cmds.shaderfx(sfxnode=shader, loadGraph=shader_file)
    cmds.connectAttr('%s.outColor' % shader, '%s.surfaceShader' % shadinggroup,
                     force=True)

    for typ, (file_node, name, realpath) in texture_nodes.items():
        if DEBUG_OUTPUT:
            print "new loop on %s:(%s,%s,%s)" % (
                typ, file_node, name, realpath)
        try:
            if typ == 2903569922 or typ == 1716930793 or typ == 1239794147:
                if DEBUG_OUTPUT:
                    print "binding color", typ, " on material ", mname
                cmds.setAttr("%s.use_color_map" % shader, 1)
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.TEX_color_map' % shader)

                # This map also provides the emissive color
                # emissive is only enabled if there is an emissive
                # texture, so this linkage is safe.
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.emissive' % shader)
            elif typ == 378934698 or typ == 562391268:
                if DEBUG_OUTPUT:
                    print "binding normal", typ, " on material ", mname
                cmds.setAttr("%s.use_normal_map" % shader, 1)
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.TEX_normal_map' % shader)
                cmds.setAttr("%s.colorSpace" % file_node, "Raw",
                             typ="string")

            elif typ == 548341454 or typ == 3111105361:
                if DEBUG_OUTPUT:
                    print "binding PBR ", typ, " on material ", mname
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.TEX_PBR_map' % shader)
                cmds.setAttr("%s.colorSpace" % file_node, "Raw",
                             typ="string")

                # This is completely wrong for specular. Not sure what
                # to do for Stingray.
                # cmds.connectAttr('%s.outColor' % specular,
                #                  '%s.TEX_global_specular_cube' % shader,
                #                  force=True)

            elif typ == 3166598269:
                if DEBUG_OUTPUT:
                    print "binding emissive ", typ, " on material ", mname
                cmds.setAttr("%s.use_emissive_map" % shader, 1)
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.TEX_emissive_map' % shader)
            elif typ == 3761386704:
                if DEBUG_OUTPUT:
                    print "binding AO ", typ, " on material ", mname
                # Need to figure this out. The AO map is a strength bit,
                # not sure what Maya is expecting.
                cmds.setAttr("%s.use_ao_map" % shader, 1)
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.TEX_ao_map' % shader)
            elif typ == 1140682086 or typ == 1482859648:
                if DEBUG_OUTPUT:
                    print "binding mask", typ, " on material ", mname
                cmds.setAttr("%s.use_mask_map" % shader, 1)
                cmds.connectAttr('%s.outColor' % file_node,
                                 '%s.TEX_mask_map' % shader)
            elif typ == 1557393490:
                if DEBUG_OUTPUT:
                    print ("material mask ", typ,
                           " not yet implemented on material ", mname)
            elif typ == 3004687613:
                if DEBUG_OUTPUT:
                    print ("subsurface scattering ", typ,
                           " not yet implemented on material ", mname)
            elif typ == 2337956496:
                if DEBUG_OUTPUT:
                    print ("anisotropy tangent ", typ,
                           " not yet implemented on material ", mname)
            elif typ == 1117188170:
                if DEBUG_OUTPUT:
                    print ("specular ", typ,
                           " not yet implemented on material ", mname)
            else:
                if DEBUG_OUTPUT:
                    print ("import_owmat: ignoring unknown "
                           "texture type ", typ, " on material ", mname)

        except Exception as e:
            print "Exception while materialing: %s" % e

    # Return the name of the finished shader
    # print "Assigned materials to shader: ", shader
    return shadinggroup

from OWMImporter import bin_ops
from OWMImporter import owm_types
import io
import os


def openStream(filename):
    stream = None
    with open(filename, "rb") as f:
        stream = io.BytesIO(f.read())
    return stream


LOG_MATERIAL_DETAILS = False


def read(filename, sub=False):
    filename = os.path.normpath(filename.replace('\\', os.sep))
    if LOG_MATERIAL_DETAILS:
        print "read(%s) sub=%s" % (filename, sub)
    stream = openStream(filename)
    if stream is None:
        return False

    major, minor, materialCount = bin_ops.readFmtFlat(
        stream, owm_types.OWMATHeader.structFormat)
    header = owm_types.OWMATHeader(major, minor, materialCount)

    if major >= 2 and minor >= 0:
        mat_type = bin_ops.readFmtFlat(
            stream, owm_types.OWMATHeader.new_format)
        if LOG_MATERIAL_DETAILS:
            print ("Major: ", major, " Minor: ", minor, " MC: ", materialCount,
                   " mat_type: ", mat_type, " sub: ", sub)
        if mat_type == 0:
            shader, id_count = bin_ops.readFmtFlat(
                stream, owm_types.OWMATHeader.new_material_header_format)
            if LOG_MATERIAL_DETAILS:
                print "shader: %x id_count: %d" % (shader, id_count)
            ids = []
            for i in range(id_count):
                ids.append(bin_ops.readFmtFlat(
                    stream, owm_types.OWMATHeader.new_id_format))
            textures = []
            for i in range(materialCount):
                texture, texture_type = bin_ops.readFmtFlat(
                    stream, owm_types.OWMATMaterial.new_material_format)
                if LOG_MATERIAL_DETAILS:
                    print "texture %s tex_type: %d" % (texture, texture_type)
                textures += [(texture, 0, texture_type)]
            if sub:
                return textures, shader, ids
            else:
                materials = []
                for mat_id in ids:
                    materials.append(
                        owm_types.OWMATMaterial(mat_id, len(textures),
                                                textures, shader))
                return owm_types.OWMATFile(header, materials)
        elif mat_type == 1:
            materials = []
            for i in range(materialCount):
                material_file = bin_ops.readFmtFlat(
                    stream, owm_types.OWMATMaterial.new_modellook_format)
                textures, shader, ids = read(os.path.join(filename,
                                             material_file), True)
                if LOG_MATERIAL_DETAILS:
                    print "ids: ", ["%X" % id for id in ids]
                for mat_id in ids:
                    materials += [owm_types.OWMATMaterial(
                        mat_id, len(textures), textures, shader)]
            return owm_types.OWMATFile(header, materials)
        else:
            pass
        materials = []
        for i in range(materialCount):
            key, textureCount = bin_ops.readFmtFlat(
                stream, owm_types.OWMATMaterial.structFormat)
            textures = []
            for j in range(textureCount):
                t = bin_ops.readFmtFlat(stream,
                                        [owm_types.OWMATMaterial.exFormat[0]])
                y = 0
                if major >= 1 and minor >= 1:
                    y = ord(stream.read(1))
                textures += [(t, y)]
            materials += [owm_types.OWMATMaterial(key, textureCount, textures)]

    return owm_types.OWMATFile(header, materials)

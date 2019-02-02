OWMATTypes = {
    "ALBEDO": 0x00,
    "NORMAL": 0x01,
    "SHADER": 0x02
}


class OWSettings:
    def __init__(self, filename, uvDisplaceX,
                 uvDisplaceY, autoIk, importNormals,
                 importEmpties, importMaterial, importSkeleton):
        self.filename = filename
        self.uvDisplaceX = uvDisplaceX
        self.uvDisplaceY = uvDisplaceY
        self.autoIk = autoIk
        self.importNormals = importNormals
        self.importEmpties = importEmpties
        self.importMaterial = importMaterial
        self.importSkeleton = importSkeleton

    def mutate(self, filename):
        return OWSettings(filename, self.uvDisplaceX,
                          self.uvDisplaceY, self.autoIk, self.importNormals,
                          self.importEmpties, self.importMaterial,
                          self.importSkeleton)


class OWMATFile:
    def __init__(self, header, materials):
        self.header = header
        self.materials = materials


class OWMATHeader:
    structFormat = ['<HHQ']
    new_format = ['<I']
    new_material_header_format = ['<Ii']
    new_id_format = ['<Q']

    def __init__(self, major, minor, materialCount):
        self.major = major
        self.minor = minor
        self.materialCount = materialCount


class OWMATMaterial:
    structFormat = ['<QI']
    exFormat = [str]
    typeFormat = ['<I']
    new_material_format = [str, '<I']
    new_modellook_format = [str]

    def __init__(self, key, textureCount, textures, shader=0):
        self.key = key
        self.textureCount = textureCount
        self.textures = textures
        self.shader = shader


class OWMDLFile:
    def __init__(self, header, bones, refpose_bones, meshes, empties,
                 cloths, guid):
        self.header = header
        self.bones = bones
        self.refpose_bones = refpose_bones
        self.meshes = meshes
        self.empties = empties
        self.cloths = cloths
        self.guid = guid


class OWMDLHeader:
    structFormat = ['<HH', str, str, '<HII']
    guidFormat = ['<I']

    def __init__(self, major, minor, material, name,
                 boneCount, meshCount, emptyCount):
        self.major = major
        self.minor = minor
        self.material = material
        self.name = name
        self.boneCount = boneCount
        self.meshCount = meshCount
        self.emptyCount = emptyCount


class OWMDLIndex:
    structFormat = ['B']
    exFormat = ['<I']

    def __init__(self, pointCount, points):
        self.pointCount = pointCount
        self.points = points


class OWMDLVertex:
    structFormat = ['<fff', '<fff']
    exFormat = ['<ff', 'B', '<H', '<f', '<ffff']

    def __init__(self, position, normal, uvs, boneCount, boneIndices,
                 boneWeights, col1, col2):
        self.position = position
        self.normal = normal
        self.uvs = uvs
        self.boneCount = boneCount
        self.boneIndices = boneIndices
        self.boneWeights = boneWeights
        self.color1 = col1
        self.color2 = col2


class OWMDLMesh:
    structFormat = [str, '<QBII']

    def __init__(self, name, materialKey, uvCount, vertexCount, indexCount,
                 vertices, indices):
        self.name = name
        self.materialKey = materialKey
        self.uvCount = uvCount
        self.vertexCount = vertexCount
        self.indexCount = indexCount
        self.vertices = vertices
        self.indices = indices


class OWMDLBone:
    structFormat = [str, '<h', '<fff', '<fff', '<ffff']

    def __init__(self, name, parent, pos, scale, rot):
        self.name = name
        self.parent = parent
        self.pos = pos
        self.scale = scale
        self.rot = rot


class OWMDLEmpty:
    structFormat = [str, '<fff', '<ffff']
    exFormat = [str]

    def __init__(self, name, position, rotation):
        self.name = name
        self.position = position
        self.rotation = rotation


class OWMAPFile:

    def __init__(self, header, objects, details, lights=[], sounds=[]):
        self.header = header
        self.objects = objects
        self.details = details
        self.lights = lights
        self.sounds = sounds


class OWMAPHeader:
    structFormat = ['<HH', str, '<II']
    structFormat11 = ['<I']
    structFormat12 = ['<I']

    def __init__(self, major, minor, name, objectCount,
                 detailCount, lightCount=0, soundCount=0):
        self.major = major
        self.minor = minor
        self.name = name
        self.objectCount = objectCount
        self.detailCount = detailCount
        self.lightCount = lightCount
        self.soundCount = soundCount


class OWMAPRecord:
    structFormat = ['<fff', '<fff', '<ffff']

    def __init__(self, position, scale, rotation):
        self.position = position
        self.scale = scale
        self.rotation = rotation


class OWMAPObject:
    structFormat = [str, '<I']

    def __init__(self, model, entityCount, entities):
        self.model = model
        self.entityCount = entityCount
        self.entities = entities


class OWMAPEntity:
    structFormat = [str, '<I']

    def __init__(self, material, recordCount, records):
        self.material = material
        self.recordCount = recordCount
        self.records = records


class OWMAPDetail:
    structFormat = [str, str]
    exFormat = ['<fff', '<fff', '<ffff']

    def __init__(self, model, material, position, scale, rotation):
        self.model = model
        self.material = material
        self.position = position
        self.scale = scale
        self.rotation = rotation


class OWMAPLight:
    structFormat = ['<fff', '<ffff', '<I', '<f', '<fff', '<I', '<I',
                    '<B', '<B', '<B', '<B', '<I', '<I', '<fff', '<ffff',
                    '<fff', '<ffff', '<fff', '<ff', '<ff', '<f', '<f',
                    '<I', '<H', '<H', '<I', '<I']

    def __init__(self, position, rotation, LightType, LightFOV, Color, uk1a,
                 uk1b, uk2a, uk2b, uk2c, uk2d, uk3a, uk3b, ukp1, ukq1, ukp2,
                 ukq2, ukp3, uk4a, uk4b, uk8b, uk8c, uk9, uk10a, uk10b,
                 uk11a, uk11b):
        self.position = position
        self.rotation = rotation
        self.LightType = LightType[0]
        self.LightFOV = LightFOV[0]
        self.Color = Color
        self.uk1a = uk1a
        self.uk1b = uk1b
        self.uk2a = uk2a
        self.uk2b = uk2b
        self.uk2c = uk2c
        self.uk2d = uk2d
        self.uk3a = uk3a
        self.uk3b = uk3b
        self.ukp1 = ukp1
        self.ukq1 = ukq1
        self.ukp2 = ukp2
        self.ukq2 = ukq2
        self.ukp3 = ukp3
        self.uk4a = uk4a
        self.uk4b = uk4b
        self.uk8b = uk8b
        self.uk8c = uk8c
        self.uk9 = uk9
        self.uk10a = uk10a
        self.uk10b = uk10b
        self.uk11a = uk11a
        self.uk11b = uk11b


class OWANIMHeader:
    structFormat = ['<HH', str, '<ff', '<I']

    def __init__(self, major, minor, name, duration,
                 framesPerSecond, numKeyframes):
        self.major = major
        self.minor = minor
        self.name = name
        self.duration = duration
        self.framesPerSecond = framesPerSecond
        self.numKeyframes = numKeyframes


class OWANIMFile:
    def __init__(self, header, KeyFrames):
        self.header = header
        self.KeyFrames = KeyFrames


class OWANIMKeyFrame:
    structFormat = ['<f', '<I']

    def __init__(self, frameTime, numAnimBones, AnimBoneList):
        self.frameTime = frameTime
        self.numAnimBones = numAnimBones
        self.AnimBoneList = AnimBoneList


class OWANIMBoneAnim:
    structFormat = [str, '<I']

    def __init__(self, boneName, valueCount, values):
        self.boneName = boneName
        self.valueCount = valueCount
        self.values = values


class OWANIMFrameValue:
    structFormat = ['<I', '<d', '<d', '<d']

    def __init__(self, channelID, keyValue1, keyValue2, keyValue3):
        self.channelID = channelID
        self.keyValue1 = keyValue1
        self.keyValue2 = keyValue2
        self.keyValue3 = keyValue3


class OWMDLCloth:
    structFormat = [str, '<I']
    beforeFmt = ['<I']

    def __init__(self, name, meshes):
        self.name = name
        self.meshes = meshes


class OWMDLClothMesh:
    structFormat = ['<II', str]
    pinnedVertFmt = ['<I']

    def __init__(self, name, id, pinnedVerts):
        self.name = name
        self.id = id
        self.pinnedVerts = pinnedVerts


class OWMDLRefposeBone:
    structFormat = [str, '<h', '<fff', '<fff', '<fff']

    def __init__(self, name, parent, pos, scale, rot):
        self.name = name
        self.parent = parent
        self.pos = pos
        self.scale = scale
        self.rot = rot


class OWMAPSound:
    structFormat = [str]
    exFormat = ['<fff', '<i']

    def __init__(self, position, soundCount, sounds=list()):
        self.position = position
        self.soundCount = soundCount
        self.sounds = sounds


class OWEntityFile:
    def __init__(self, header, file, model, effect, idx,
                 model_idx, effect_idx, children):
        self.header = header
        self.file = file
        self.model = model
        self.effect = effect
        self.index = idx
        self.model_index = model_idx
        self.effect_index = effect_idx
        self.children = children


class OWEntityHeader:
    structFormat = [str, '<HH', str, str, str, '<IIIi']

    def __init__(self, magic, major, minor, guid, model_guid,
                 effect_guid, idx, model_idx, effect_idx, child_count):
        self.magic = magic
        self.major = major
        self.minor = minor
        self.guid = guid
        self.model_guid = model_guid
        self.effect_guid = effect_guid
        self.child_count = child_count
        self.index = idx
        self.model_index = model_idx
        self.effect_index = effect_idx


class OWEntityChild:
    structFormat = [str, '<QQII', str]

    def __init__(self, file, hardpoint, var, hp_index, var_index, attachment):
        self.file = file
        self.hardpoint = hardpoint
        self.var = var
        self.attachment = attachment
        self.var_index = var_index
        self.hardpoint_index = hp_index

    def __repr__(self):
        return '<OWEntityChild: {} (attached to:{})>'.format(
            self.file, self.attachment)

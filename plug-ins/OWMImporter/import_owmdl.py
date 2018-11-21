import os
import math
from types import TupleType
import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya
from maya.api.OpenMaya import MVector as Vector
from maya.api.OpenMaya import MQuaternion as Quaternion

from OWMImporter.commonfuncs import get_mobject, adjustAxis
from OWMImporter.commonfuncs import MayaSafeName
from OWMImporter import read_owmdl
from OWMImporter import import_owmat

root = ''
settings = None
data = None
rootObject = None
BoneNames = []


def newBoneName():
    global BoneNames
    BoneNames = []


def addBoneName(newName):
    global BoneNames
    BoneNames += [newName]


def getBoneName(originalIndex):
    if originalIndex < len(BoneNames):
        return BoneNames[originalIndex]
    else:
        return None


def getBoneNameIndex(Name):
    for index in range(len(BoneNames)):
        bn = BoneNames[index]
        if bn == Name:
            return index


class UVTarget:
    def __init__(self, iid=0, uvset="UVSet_0", ix=0, iy=0):
        self.id = iid
        self.uvset = uvset
        self.x = ix
        self.y = iy


def fixLength(bone):
    default_length = 0.005
    if bone.length == 0:
        bone.tail = bone.head - Vector((0, .001, 0))
    if bone.length < default_length:
        bone.length = default_length


def importArmature(parentName):
    bones = data.bones
    armature = None
    if len(bones) > 0:
        newBoneName()

        armname = ("Skeleton_%s" % parentName)
        parentRoot = ("root_%s" % parentName)
        armature = cmds.group(em=True, name=armname, parent=parentRoot)

        for bone in bones:
            parent = getBoneName(bone.parent)
            if parent is not None:
                cmds.select(d=True)

            pos = adjustAxis(bone.pos)
            scale = adjustAxis(bone.scale)
            qrot = Quaternion(bone.rot[0], bone.rot[1],
                              bone.rot[2], bone.rot[3])
            erot = qrot.asEulerRotation()

            bbone = cmds.joint(name=bone.name, rad=0.05,
                               p=(pos[0], pos[1], pos[2]),
                               s=(scale[0], scale[1], scale[2]),
                               o=tuple(math.degrees(x) for x in [
                                   erot[0], erot[1], erot[2]]),
                               angleX=0,
                               angleY=0,
                               angleZ=0)
            addBoneName(bbone)
            if parent is not None:
                cmds.connectJoint(bbone, parent, pm=True)

    return armature


def segregate(vertex):
    pos = OpenMaya.MFloatPointArray()
    norms = []
    uvs = []
    boneData = []
    vertID = 0

    scale = OpenMaya.MDistance.uiToInternal(1.0)
    for vert in vertex:
        vec = Vector(*adjustAxis(vert.position)) * scale
        # print("Vec: %s, %s, %s"%(vec.x, vec.y, vec.z))
        pvert = OpenMaya.MFloatPoint(vec.x, vec.y, vec.z)
        # print("PVert: %s, %s, %s"%(pvert.x, pvert.y, pvert.z))
        pos.append(pvert)
        norm = Vector(*vert.normal).normal()
        norm.x = -norm.x
        norm.y = -norm.y
        norm.z = -norm.z
        norms += [adjustAxis(norm)]
        uvs += [vert.uvs]
        boneData += [[vert.boneIndices, vert.boneWeights]]
        vertID += 1
    return (pos, norms, uvs, boneData)


def detach(faces):
    f = OpenMaya.MIntArray()
    fc = OpenMaya.MIntArray()
    for face in faces:
        for fp in face.points:
            f.append(fp)
        fc.append(len(face.points))
    return (f, fc)


def getBoneWeights(boneData):
    bw = {}
    for vindex in range(len(boneData)):
        boneIDlist, weights = boneData[vindex]
        # print ', '.join(map(str, boneIDlist))
        # print ', '.join(map(str, weights))

        for idx in range(len(boneIDlist)):
            index = boneIDlist[idx]
            weight = weights[idx]
            if weight != 0:
                name = getBoneName(index)
                if name is not None:
                    if (vindex not in bw):
                        bw[vindex] = {}
                    bw[vindex][name] = weight
                    # print ("Bone: %s, index: %s, weight: %s" %
                    #        (name, vindex, weight))
    return bw


def bindMaterials(meshes, data, materials):
    if materials is None:
        cmds.warning("No materials to bind!")
        return
    matType = type(materials)
    # print "materials Type: %s" % matType
    if (matType == TupleType):
        materials = materials[0]
    # print "materials: %s" % materials
    for i, obj in enumerate(meshes):
        meshData = data.meshes[i]
        if materials == "lambert1" or "CollisionPhysics" in materials:
            # print("Lambert or Collision")
            cmds.select("%sShape" % obj["name"], r=True)
            if "CollisionPhysics" in materials:
                cmds.sets(forceElement="CollisionPhysicsSG")
            else:
                cmds.sets(forceElement="initialShadingGroup")
        # elif materials.has_key(meshData.materialKey):
        elif meshData.materialKey in materials:
            # print ("Mat[key]: %s" % materials.get(meshData.materialKey))
            mat = materials.get(meshData.materialKey)
            shape = "%sShape" % obj["name"]
            cmds.select(shape, r=True)
            if (mat[-2:] != "SG"):
                mat = "%sSG" % mat
            # print ("Setting shape %s to mat %s" % (shape, mat))
            cmds.sets(forceElement=mat)
            imgList = cmds.ls(type='file')
            for img in imgList:
                try:
                    UVSetName = "%sShape.uvSet[1].uvSetName" % obj["name"]
                    # print ("UVSet: %s, Img: %s"%(UVSetName,img))
                    cmds.uvLink(make=True, uvSet=UVSetName, texture=img)
                except:
                    pass
        else:
            # print("else: Lambert")
            cmds.select("%sShape" % obj["name"], r=True)
            cmds.sets(forceElement="initialShadingGroup")


def importMesh(rootName, armature, meshData):
    global settings
    global rootObject

    rdata = {}

    mfName = "submesh%s_%s" % (rootName, meshData.name.rsplit("_")[-1])
    mfName = MayaSafeName(mfName)
    mfName = mfName.rsplit("_", 1)[0]
    # print "name: %s"%mfName
    meshName = cmds.createNode("transform", n=mfName, p=rootObject)
    pos, norms, uvs, boneData = segregate(meshData.vertices)
    faces, fcounts = detach(meshData.indices)

    rdata["name"] = meshName
    rdata["materialKey"] = meshData.materialKey

    mesh = OpenMaya.MFnMesh()
    mesh.create(pos, fcounts, faces, parent=get_mobject(meshName))
    meshshapename = mesh.fullPathName().rsplit("|")[-1]
    # print "extracted shapename: %s" % meshshapename
    cmds.rename(meshshapename, "%sShape" % mfName)

    # Display a list of UV data
    # for uvID in range(len(uvs)):
    #    print "uvdata: %s"%uvs[uvID]

    # Build UV Data
    # print "UVCount: %s" % meshData.uvCount
    for UVSet in range(meshData.uvCount):
        # if meshData.uvCount == 1:
        if UVSet == 0:
            uvSetNode = "map1"
        else:
            UVSetName = "UVSet_%s" % UVSet
            # print "UVSetname: %s, UVSet: %s"%(UVSetName,UVSet)
            uvSetNode = mesh.createUVSet(UVSetName)

        mesh.setCurrentUVSetName(uvSetNode)
        MeshUVIDs = OpenMaya.MIntArray()
        MeshUVCounts = OpenMaya.MIntArray()
        for fidx in range(0, len(faces), 3):
            MeshUVIDs.append(faces[fidx+0])
            MeshUVIDs.append(faces[fidx+1])
            MeshUVIDs.append(faces[fidx+2])
            MeshUVCounts.append(3)
            mesh.setUV(faces[fidx+0], uvs[faces[fidx+0]][UVSet][0],
                       1-uvs[faces[fidx+0]][UVSet][1], uvSetNode)
            mesh.setUV(faces[fidx+1], uvs[faces[fidx+1]][UVSet][0],
                       1-uvs[faces[fidx+1]][UVSet][1], uvSetNode)
            mesh.setUV(faces[fidx+2], uvs[faces[fidx+2]][UVSet][0],
                       1-uvs[faces[fidx+2]][UVSet][1], uvSetNode)

        if len(MeshUVCounts) > 0:
            mesh.assignUVs(MeshUVCounts, MeshUVIDs, uvSetNode)

    # Attach Bones
    if armature:
        bwd = getBoneWeights(boneData)
        if len(bwd) > 0:
            cmds.select(rootObject, r=True)
            jointList = cmds.ls(dag=True, type='joint', sl=True)
            clusterName = cmds.skinCluster(meshName, tuple(jointList),
                                           skinMethod=1)
            cmds.select(clusterName, r=True)
            for index, weightdata in bwd.items():
                skinData = []
                sumWeights = 0
                for boneName, weight in weightdata.items():
                    # The weights in the mesh are rounded by Maya, and as a
                    # result can occasionally overflow. We compensate for this
                    # by arbitrarily removing weight from the last joint. This
                    # doesn't change things appreciably since we're subtracting
                    # out rounding error.
                    if sumWeights + weight > 1.0:
                        weight = 1.0 - sumWeights
                    skinData += [(boneName, weight)]
                    sumWeights += weight
                vertexNum = "%s.vtx[%i]" % (meshName, index)
                # print ("Skinning v#: ", vertexNum, " skinData: ", skinData)
                cmds.skinPercent("%s" % tuple(clusterName),
                                 vertexNum, transformValue=skinData)

    return rdata


def importMeshes(rootName, armature):
    global data
    meshes = [importMesh(rootName, armature, meshData)
              for meshData in data.meshes]
    return meshes


# def importEmpties():
#     global data
#     global settings
#     global rootObject
#
#     if not settings.ModelImportEmpties:
#         return []
#
#     att = bpy.data.objects.new('Empties', None)
#     att.parent = rootObject
#     att.hide = att.hide_render = True
#     bpy.context.scene.objects.link(att)
#     bpy.context.scene.update()
#
#     e = []
#     for emp in data.empties:
#         empty = bpy.data.objects.new(emp.name, None)
#         bpy.context.scene.objects.link(empty)
#         bpy.context.scene.update()
#         empty.parent = att
#         empty.location = adjustAxis(emp.position)
#         empty.rotation_euler = Quaternion(
#             wadjustAxis(emp.rotation)).to_euler('XYZ')
#         empty.select = True
#         bpy.context.scene.update()
#         e += [empty]
#     return e


# def boneTailMiddleObject(armature):
#     bpy.context.scene.objects.active = armature
#     bpy.ops.object.mode_set(mode='EDIT', toggle=False)
#     eb = armature.data.edit_bones
#     boneTailMiddle(eb)
#     bpy.ops.object.mode_set(mode='OBJECT', toggle=False)


def boneTailMiddle(eb):
    for bone in eb:
        if len(bone.children) > 0:
            l = len(bone.children)
            bone.tail = Vector(map(sum, zip(*(
                child.head.xyz for child in bone.children))))/l
        else:
            if bone.parent is not None:
                if bone.head.xyz != bone.parent.tail.xyz:
                    delta = bone.head.xyz - bone.parent.tail.xyz
                else:
                    delta = bone.parent.tail.xyz - bone.parent.head.xyz
                bone.tail = bone.head.xyz + delta
    for bone in eb:
        fixLength(bone)
        if bone.parent:
            if bone.head == bone.parent.tail:
                bone.use_connect = True


def readmdl(materials=None, instanceCount=0):
    global root
    global data
    global rootObject

    currentlinear = cmds.currentUnit(query=True, linear=True)
    currentangle = cmds.currentUnit(query=True, angle=True)
    cmds.currentUnit(linear="inch", angle="deg")
    root, file = os.path.split(settings.filename)

    data = read_owmdl.read(settings.filename)
    if not data:
        return None

    rootName = os.path.splitext(file)[0]
    if len(data.header.name) > 0:
        rootName = data.header.name
    rootName = MayaSafeName(rootName)
    if instanceCount > 0:
        rootName = "%s_%s" % (rootName, instanceCount)
    rootGroupName = ("root_%s" % rootName)

    if not cmds.objExists(rootGroupName):
        rootObject = cmds.group(em=True, name=rootGroupName, w=True)
    else:
        rootObject = rootGroupName

    armature = None
    if settings.ModelImportBones and data.header.boneCount > 0:
        armature = importArmature(rootName)

    meshes = importMeshes(rootName, armature)

    if materials is None and settings.ModelImportMaterials and len(
            data.header.material) > 0:
        matpath = data.header.material
        if not os.path.isabs(matpath):
            matpath = os.path.normpath('%s/%s' % (root, matpath))
        materials, texList = import_owmat.read(matpath)
        bindMaterials(meshes, data, materials)

    empties = []
    # if settings.ModelImportEmpties and data.header.emptyCount > 0:
    #    empties = importEmpties()

    # if armature:
    #    boneTailMiddleObject(armature)

    # if impMat:
    #    import_owmat.cleanUnusedMaterials(materials)

    cmds.currentUnit(linear=currentlinear, angle=currentangle)
    return (rootObject, armature, meshes, empties, data)


class DefSettings:
        def __init__(self,
                     MapImportModels=True,
                     MatImportTextures=True,
                     MapImportMaterials=True,
                     MapImportLights=True,
                     MapImportModelsAs=1,
                     MapImportObjectsLarge=True,
                     MapImportObjectsDetail=True,
                     MapImportObjectsPhysics=False,
                     ModelImportMaterials=True,
                     ModelImportBones=True,
                     ModelImportEmpties=False,
                     MapHideReferenceModels=True):
            self.MatImportTextures = int(MatImportTextures)

            self.MapImportModels = int(MapImportModels)
            self.MapImportMaterials = int(MapImportMaterials)
            self.MapImportLights = int(MapImportLights)
            self.MapImportModelsAs = int(MapImportModelsAs)

            self.MapImportObjectsLarge = int(MapImportObjectsLarge)
            self.MapImportObjectsDetail = int(MapImportObjectsDetail)
            self.MapImportObjectsPhysics = int(MapImportObjectsPhysics)

            self.ModelImportMaterials = int(ModelImportMaterials)
            self.ModelImportBones = int(ModelImportBones)
            self.ModelImportEmpties = int(ModelImportEmpties)

            self.MapHideReferenceModels = int(MapHideReferenceModels)


def read(aux, inputsettings, materials=None, instanceCount=0):
    global settings
    settings = inputsettings or DefSettings()

    settings.filename = aux

    status = readmdl(materials, instanceCount)
    return status
import os
import math
import time

from types import TupleType
import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya
import maya.api.OpenMayaAnim as OpenMayaAnim
from maya.api.OpenMaya import MVector as Vector
from maya.api.OpenMaya import MQuaternion as Quaternion

from OWMImporter.commonfuncs import get_mobject, adjustAxis
from OWMImporter.commonfuncs import MayaSafeName
from OWMImporter import read_owmdl
from OWMImporter import import_owmat

LOG_TIMING_STATS = False
LOG_DEBUG_STATS = False
LOG_SKIN_DETAILS = False


class Skeleton:
    def __init__(self):
        self.BoneNames = {}
        self.BoneIndexes = {}
        self.BoneObjects = {}

    def add(self, name, objname):
        idx = len(self.BoneNames)
        self.BoneNames[name] = idx
        self.BoneIndexes[idx] = name
        self.BoneObjects[name] = objname

    def getName(self, idx):
        return self.BoneIndexes.get(idx)

    def getIndex(self, name):
        return self.BoneNames.get(name)

    def getObjname(self, name):
        return self.BoneObjects.get(name)


class UVTarget:
    def __init__(self, iid=0, uvset="UVSet_0", ix=0, iy=0):
        self.id = iid
        self.uvset = uvset
        self.x = ix
        self.y = iy


def scopedSelect(root, name):
    cmds.select(root, hi=True)
    objname = cmds.ls(name, sl=True)[0]
    cmds.select(objname, r=True)
    return objname


def fixLength(bone):
    default_length = 0.005
    if bone.length == 0:
        bone.tail = bone.head - Vector((0, .001, 0))
    if bone.length < default_length:
        bone.length = default_length


def importArmature(data, parentName):
    start = time.time()
    bones = data.bones
    armature = None
    if len(bones) > 0:
        skeleton = Skeleton()

        armname = ("Skeleton_%s" % parentName)
        armname = ("Skeleton")
        parentRoot = parentName
        armature = cmds.group(em=True, name=armname, parent=parentRoot)

        # The bones are not topologically sorted, and I'm too lazy
        # to implement that. Therefore, we construct the skeleton in
        # two passes. The first pass instantiates all the joints and
        # the second pass parents bones to each other.
        for bone in bones:
            pos = adjustAxis(bone.pos)
            scale = adjustAxis(bone.scale)
            qrot = Quaternion(bone.rot[0], bone.rot[1],
                              bone.rot[2], bone.rot[3])
            erot = qrot.asEulerRotation()

            # We create each bone with the armature selected, so they
            # get it as the default parent. This allows us to then
            # parent the bones to their correct parents. Without
            # doing this select, each bone would be parented to the
            # previously created bone.
            cmds.select(armature)
            bbone = cmds.joint(name=bone.name,
                               rad=0.05,
                               p=(pos[0], pos[1], pos[2]),
                               s=(scale[0], scale[1], scale[2]),
                               o=tuple(math.degrees(x) for x in [
                                   erot[0], erot[1], erot[2]]),
                               angleX=0,
                               angleY=0,
                               angleZ=0)
            skeleton.add(bone.name, bbone)

        for bone in bones:
            parent = skeleton.getName(bone.parent)
            bbone = skeleton.getObjname(bone.name)

            if not parent:
                continue

            # Here, we account for multiple skeletons in the scene by
            # selecting in the scope of armature we've created. That
            # way, we find our 'local' bone.
            pbone = scopedSelect(armature, parent)

            # One immensely annoying attribute of the OWLib is that
            # the first bone resolves as its own parent.
            if parent is not None and parent != bone.name:
                cmds.connectJoint(bbone, pbone, pm=True)

    if LOG_TIMING_STATS:
        print "importArmature(): ", time.time() - start
    return armature, skeleton


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


def getBoneWeights(bones, boneData):
    bw = {}
    for vindex in range(len(boneData)):
        boneIDlist, weights = boneData[vindex]
        # print ', '.join(map(str, boneIDlist))
        # print ', '.join(map(str, weights))

        for idx in range(len(boneIDlist)):
            index = boneIDlist[idx]
            weight = weights[idx]
            if weight != 0:
                name = bones.getName(index)
                if name is not None:
                    if (vindex not in bw):
                        bw[vindex] = {}
                    bw[vindex][name] = weight
                    # print ("Bone: %s, index: %s, weight: %s" %
                    #        (name, vindex, weight))
    return bw


def bindMaterials(rootObject, meshes, data, materials):
    start = time.time()
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
            objname = scopedSelect(rootObject, shape)
            if (mat[-2:] != "SG"):
                mat = "%sSG" % mat
            # print ("Setting shape %s to mat %s" % (shape, mat))
            cmds.sets(forceElement=mat)
            imgList = cmds.ls(type='file')
            for img in imgList:
                try:
                    UVSetName = "%s.uvSet[0].uvSetName" % objname
                    # print ("UVSet: %s, Img: %s"%(UVSetName,img))
                    cmds.uvLink(make=True, uvSet=UVSetName, texture=img)
                except Exception as e:
                    print "Error binding uvset: ", e
                    pass
        else:
            # print("else: Lambert")
            scopedSelect(rootObject, "%sShape" % obj["name"])
            cmds.sets(forceElement="initialShadingGroup")
    if LOG_TIMING_STATS:
        print "bindMaterials(): ", time.time() - start


def importMesh(rootObject, armature, skeleton, meshData):
    start = time.time()
    rdata = {}

    mfName = "submesh%s_%s" % (
        rootObject[5:], meshData.name.rsplit("_")[-1])
    mfName = MayaSafeName(mfName)
    mfName = mfName.rsplit("_", 1)[0]
    meshName = cmds.createNode("transform", n=mfName, p=rootObject)
    pos, norms, uvs, boneData = segregate(meshData.vertices)
    faces, fcounts = detach(meshData.indices)

    rdata["name"] = meshName.rsplit("|")[-1]
    rdata["materialKey"] = meshData.materialKey

    mesh = OpenMaya.MFnMesh()
    mesh.create(pos, fcounts, faces, parent=get_mobject(meshName))
    meshshapename = mesh.fullPathName().rsplit("|")[-1]
    cmds.rename(meshshapename, "%sShape" % mfName)

    uvStart = time.time()
    uvRange = meshData.uvCount
    MeshUVCounts = OpenMaya.MIntArray(len(faces) / 3, 3)

    for UVSet in range(uvRange):
        uvSetStart = time.time()
        # Per https://goo.gl/UtXRmc we name the UV sets to match the default
        # names. This helps with handling the model later.
        if UVSet == 0:
            uvSetNode = "map1"
        else:
            UVSetName = "uvSet"
            uvSetNode = mesh.createUVSet(UVSetName)

        MeshUVIDs = OpenMaya.MIntArray(len(faces), 0)
        MeshUs = OpenMaya.MFloatArray(len(faces), 0)
        MeshVs = OpenMaya.MFloatArray(len(faces), 0)

        for fidx in range(0, len(faces), 3):
            for j in range(3):
                MeshUVIDs[fidx+j] = faces[fidx+j]
                MeshUs[faces[fidx+j]] = uvs[faces[fidx+j]][UVSet][0]
                MeshVs[faces[fidx+j]] = 1-uvs[faces[fidx+j]][UVSet][1]

        if len(MeshUVCounts) > 0:
            mesh.setUVs(MeshUs, MeshVs, uvSetNode)
            mesh.assignUVs(MeshUVCounts, MeshUVIDs, uvSetNode)

        if LOG_TIMING_STATS:
            print "UV Set ", UVSet, " #: ", len(MeshUVCounts),
            print " time: ", time.time() - uvSetStart
    if LOG_TIMING_STATS:
        print "UV build time: ", time.time() - uvStart

    # Attach Bones
    if armature:
        skinStart = time.time()
        bwd = getBoneWeights(skeleton, boneData)
        if len(bwd) > 0:
            cmds.select(rootObject, r=True)
            jointList = cmds.ls(dag=True, type='joint', sl=True)
            clusterName = cmds.skinCluster(meshName, tuple(jointList),
                                           skinMethod=1)
            # Build the bone indices from the skin's view of bones
            # since that ordering is used by the OpenMaya calls.
            mfnSkin = OpenMayaAnim.MFnSkinCluster(get_mobject(clusterName[0]))
            meshDag = toMDagPath(meshName)
            influences = influenceObjects(clusterName[0])
            jointLookup = dict((y.split('|')[-1], x)
                               for (x, y) in enumerate(influences))

            numVerts = cmds.polyEvaluate(meshName, v=True)
            numJoints = len(jointList)

            cmds.select(clusterName, r=True)
            apiVertices = OpenMaya.MIntArray(numVerts, 0)
            apiJointIndices = OpenMaya.MIntArray(numJoints, 0)
            for i in range(numJoints):
                apiJointIndices[i] = i

            apiWeights = OpenMaya.MDoubleArray(numVerts * numJoints, 0)

            for index, weightdata in bwd.items():
                apiVertices[index] = index
                skinData = []
                sumWeights = 0
                for boneName, weight in weightdata.items():
                    # The weights in the mesh are rounded by Maya, and as a
                    # result can occasionally overflow. We compensate for
                    # this by arbitrarily removing weight from the last
                    # joint. This doesn't change things appreciably since
                    # we're subtracting out rounding error.
                    if sumWeights + weight > 1.0:
                        weight = 1.0 - sumWeights
                    jidx = jointLookup[boneName.split("|")[-1]]
                    apiWeights[(index * numJoints) + jidx] = weight
                    sumWeights += weight
                vertexNum = "%s.vtx[%i]" % (meshName, index)
                if LOG_SKIN_DETAILS:
                    print "Skin v#: ", vertexNum, " skinData: ", skinData

            apiComponents = (OpenMaya.MFnSingleIndexedComponent()
                             .create(OpenMaya.MFn.kMeshVertComponent))
            (OpenMaya.MFnSingleIndexedComponent(apiComponents)
                .addElements(apiVertices))

            mfnSkin.setWeights(meshDag, apiComponents,
                               apiJointIndices, apiWeights, False)

            if LOG_TIMING_STATS:
                print "skinning time: ", time.time() - skinStart

    if LOG_TIMING_STATS:
        print "importMesh(): ", time.time() - start
    return rdata


def importMeshes(data, rootObject, armature, skeleton):
    meshes = [importMesh(rootObject, armature, skeleton, meshData)
              for meshData in data.meshes]
    return meshes


def toMDagPath(nodeName):
    """ Get an API MDagPAth to the node given the name of existing dag node """
    obj = get_mobject(nodeName)
    if obj:
        dagFn = OpenMaya.MFnDagNode(obj)
        # dagPath = OpenMaya.MDagPath()
        return dagFn.getPath()


def influenceObjects(skinCluster):
    mfnSkin = OpenMayaAnim.MFnSkinCluster(get_mobject(skinCluster))
    # dagPaths = OpenMaya.MDagPathArray()
    dagPaths = mfnSkin.influenceObjects()
    influences = []
    l = len(dagPaths)
    for i in range(l):
        influences.append(dagPaths[i].fullPathName())
    return influences


# TODO: the hardpoint importing code was removed. No idea what to do yet.

def readmdl(settings, filename, materials=None, instanceCount=0):
    currentlinear = cmds.currentUnit(query=True, linear=True)
    currentangle = cmds.currentUnit(query=True, angle=True)
    cmds.currentUnit(linear="cm", angle="deg")
    root, file = os.path.split(filename)

    readStart = time.time()
    data = read_owmdl.read(filename)
    if not data:
        print "Model read for %s failed" % filename
        return None
    if LOG_TIMING_STATS:
        print "read time: ", time.time() - readStart

    rootName = os.path.splitext(file)[0]
    if len(data.header.name) > 0:
        rootName = data.header.name
    rootName = MayaSafeName(rootName)
    rootGroupName = ("root_%s_0" % rootName)
    rootObject = cmds.group(em=True, name=rootGroupName, w=True)

    armature = None
    skeleton = None
    if settings.ModelImportBones and data.header.boneCount > 0:
        armature, skeleton = importArmature(data, rootObject)

    meshes = importMeshes(data, rootObject, armature, skeleton)

    if materials is None and settings.ModelImportMaterials and len(
            data.header.material) > 0:
        matpath = data.header.material
        if not os.path.isabs(matpath):
            matpath = os.path.normpath('%s/%s' % (root, matpath))
        materials, texList = import_owmat.read(matpath)
        bindMaterials(rootObject, meshes, data, materials)

    empties = []
    # if settings.ModelImportEmpties and data.header.emptyCount > 0:
    #    empties = importEmpties()

    # if impMat:
    #    import_owmat.cleanUnusedMaterials(materials)

    cmds.currentUnit(linear=currentlinear, angle=currentangle)
    return (rootObject, armature, meshes, empties, data)


def read(filename, settings, materials=None, instanceCount=0):
    start = time.time()
    status = readmdl(settings, filename, materials, instanceCount)
    if LOG_TIMING_STATS:
        print "loading time: ", time.time() - start
    cmds.select(d=True)
    return status

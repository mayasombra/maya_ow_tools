import os
import maya.cmds as cmds
from maya.api.OpenMaya import MVector as Vector
from maya.api.OpenMaya import MQuaternion as Quaternion
# from maya.api.OpenMaya import MEulerRotation as Euler

from OWMImporter.commonfuncs import get_NameFromLong
from OWMImporter import read_owanim

root = ''
settings = None
data = None


def checkNodeisOverwatch(mainNode=""):
    if mainNode == "":
            return 0
    errorCode = 0
    # selNode = get_NameFromLong(mainNode)

    subNodes = cmds.listRelatives(mainNode, children=True, type="dagNode")
    if len(subNodes) > 0:
        errorCode = checkNodeisOverwatch()
        if errorCode > 0:
            return errorCode

    subNodesJoints = cmds.listRelatives(mainNode, children=True, type="joint")
    if len(subNodesJoints) <= 0:
        errorCode = 2

    return errorCode


def readanim():
    global root
    global data
    root, file = os.path.split(settings.filename)
    roundPrecision = 9

    data = read_owanim.read(settings.filename)
    if not data:
        return None

    # See if the data we need is here
    errorCode = 0
    skeletonNode = ""
    nodes = cmds.ls(long=True, type='dagNode')
    # hasRootOrSkel = True
    for i, node in enumerate(nodes):
        selNode = get_NameFromLong(node)
        if selNode.find("Skeleton") > -1 and selNode.find("bone") == -1:
            skeletonNode = node
            break

    if skeletonNode == "":
        errorCode = 1
    else:
        print ("CheckNode: %s" % skeletonNode)
        errorCode = checkNodeisOverwatch(skeletonNode)

    # Output Errors
    if errorCode > 0:
        if errorCode == 1:
            print("// Error: No Overwatch model imported.")
        elif errorCode == 2:
            print("// Error: No Joints found in Overwatch model.")
        else:
            print("// Error: An unknown error occured while "
                  "importing the animation.")

        raise ImportError()
        return None

    # Find Root Joint
    currentNodeName = get_NameFromLong(skeletonNode)
    start = currentNodeName.find("_")+1
    charName = currentNodeName[start:]
    baseJointList = cmds.listRelatives(
        skeletonNode, children=True, type="joint")
    rootJoint = "%s|%s" % (skeletonNode, baseJointList[0])
    print "root Joint: %s" % rootJoint
    jointList = cmds.listRelatives(rootJoint, ad=True, f=True)

    print("Setting Time")
    # set the scene for this animation
    # Set to 30fps, (most animations use this) since we can't change the FPS
    # to anything we want.
    cmds.currentUnit(time="ntsc")
    fps = data.header.framesPerSecond
    endTime = data.header.duration * fps
    cmds.playbackOptions(ast=0, aet=endTime, minTime=0, maxTime=endTime)

    # print("Building original Bones")
    origBones = {}
    for joint in jointList:
        pos = cmds.joint(joint, q=True, p=True)
        scale = cmds.joint(joint, q=True, s=True)
        rot = cmds.joint(joint, q=True, o=True)
        origBones[joint] = [pos, rot, scale]
        # print ("Pre: %s"%origBones[joint])

    # Process List
    for key in range(data.header.numKeyframes):
        keyframe = data.KeyFrames[key]
        frameNum = round(keyframe.frameTime * fps, roundPrecision)
        cmds.currentTime(frameNum, edit=True, update=False)
        # print("Setting keyframe for frame: %s"%frameNum)

        for boneNum in range(keyframe.numAnimBones):
            bone = keyframe.AnimBoneList[boneNum]
            boneName = "Skeleton_%s%s" % (charName, bone.boneName)
            currentBone = ""
            for joint in jointList:
                testName = get_NameFromLong(joint)
                if testName.find(boneName) > -1:
                    currentBone = joint
                    break
            if currentBone == "":
                cmds.warning("Animated bone \"%s\" missing from Overwatch "
                             "model. Skipping..." % boneName)
                continue

            # Apply Animation
            # print ("Selecting joint: %s"%currentBone)
            cmds.select(currentBone, replace=True)

            hasPos = False
            hasRot = False
            hasScale = False
            Position = Vector()
            Scale = Vector()
            Rotation = Quaternion()
            for valNum in range(bone.valueCount):
                value = bone.values[valNum]
                if value.channelID == 0:
                    hasPos = True
                    Position.x = round(value.keyValue1, roundPrecision)
                    Position.y = round(value.keyValue2, roundPrecision)
                    Position.z = round(value.keyValue3, roundPrecision)
                    # print("Position Data: X:%s, Y:%s, Z:%s" %
                    #       (Position.x, Position.y, Position.z))
                elif value.channelID == 1:
                    hasScale = True
                    Scale.x = round(value.keyValue1, roundPrecision)
                    Scale.y = round(value.keyValue2, roundPrecision)
                    Scale.z = round(value.keyValue3, roundPrecision)
                    # print("Size Data: X:%s, Y:%s, Z:%s" %
                    #       (Scale.x, Scale.y, Scale.z))
                elif value.channelID == 2:
                    hasRot = True
                    Rotation.x = round(value.keyValue1, roundPrecision)
                    Rotation.y = round(value.keyValue2, roundPrecision)
                    Rotation.z = round(value.keyValue3, roundPrecision)
                else:
                    cmds.warning("Unknown channel ID: %s on frame %s, "
                                 "for joint %s, in animation %s" %
                                 (value.channelID, frameNum, currentBone,
                                  data.header.name))

            # assign values to bone
            if hasPos is True:
                cmds.setKeyframe(currentBone, v=Position.x, at='translateX')
                cmds.setKeyframe(currentBone, v=Position.y, at='translateY')
                cmds.setKeyframe(currentBone, v=Position.z, at='translateZ')
            if hasScale is True:
                cmds.setKeyframe(currentBone, v=Scale.x, at='scaleX')
                cmds.setKeyframe(currentBone, v=Scale.y, at='scaleY')
                cmds.setKeyframe(currentBone, v=Scale.z, at='scaleZ')
            if hasRot is True:
                # print ("Rotations: X: %s, Y: %s, Z: %s" %
                #        (Rotation.x, Rotation.y, Rotation.z))
                cmds.setKeyframe(currentBone, v=Rotation.x, at='rotateX')
                cmds.setKeyframe(currentBone, v=Rotation.y, at='rotateY')
                cmds.setKeyframe(currentBone, v=Rotation.z, at='rotateZ')

        cmds.currentTime(0, edit=True)


def read(aux, inputsettings):
    global settings
    settings = inputsettings

    settings.filename = aux

    status = readanim()
    return status

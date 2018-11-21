from OWMImporter import bin_ops
from OWMImporter import owm_types
import io


def openStream(filename):
    stream = None
    with open(filename, "rb") as f:
        stream = io.BytesIO(f.read())
    return stream


def read(filename):
    stream = openStream(filename)
    if stream is None:
        return False

    # print "Reading Header"
    (major, minor, name, duration,
     framesPerSecond, numKeyframes) = bin_ops.readFmtFlat(
         stream, owm_types.OWANIMHeader.structFormat)
    header = owm_types.OWANIMHeader(major, minor, name, duration,
                                    framesPerSecond, numKeyframes)

    # print "Looking for Bone Animation"
    keyframes = []
    for kf in range(numKeyframes):
        frameTime, boneCount = bin_ops.readFmtFlat(
            stream, owm_types.OWANIMKeyFrame.structFormat)
        BoneAnimations = []
        if boneCount > 0:
            # print "Anim has %s Bones"%boneCount
            for bc in range(boneCount):
                boneName, valueCount = bin_ops.readFmtFlat(
                    stream, owm_types.OWANIMBoneAnim.structFormat)
                # print "bone #%s, # Keyframes: %s" % (bc,numKeyframes)
                values = []
                if valueCount > 0:
                    # print "\tFrame %s Num Values: %s"%(kf, valueCount)
                    for v in range(valueCount):
                        channelID, kv1, kv2, kv3 = bin_ops.readFmtFlat(
                            stream, owm_types.OWANIMFrameValue.structFormat)
                        values += [owm_types.OWANIMFrameValue(
                            channelID, kv1, kv2, kv3)]
                BoneAnimations += [owm_types.OWANIMBoneAnim(
                    boneName, valueCount, values)]
            keyframes += [owm_types.OWANIMKeyFrame(
                frameTime, boneCount, BoneAnimations)]
    return owm_types.OWANIMFile(header, keyframes)

import os
import math
import maya.cmds as cmds
from maya.api.OpenMaya import MQuaternion as Quaternion
from maya.api.OpenMaya import MEulerRotation as Euler

from OWMImporter.commonfuncs import adjustAxis, wadjustAxis, MayaSafeName
from OWMImporter import read_owmap
from OWMImporter import import_owmdl
from OWMImporter import import_owmat


# Set to a non-zero value to limit reading objects. This helps
# debugging since a map takes several minutes to read.
DEBUG_DATA_SIZE = 0


def instance_with_prs(name, source, parent, position, rotation, scale):
    nobj = cmds.instance(source.rsplit("|")[-1], name=name, leaf=True)
    cmds.parent(nobj[0], parent)
    loc = adjustAxis(position)
    cmds.move(loc[0], loc[1], loc[2], nobj)
    quatrotate(nobj[0], wadjustAxis(rotation))
    cmds.scale(scale[0], scale[1], scale[2], nobj)


def importModel(settings, obfile, obn):
    try:
        if settings.MapImportModelsAs == 1:
            if obfile.endswith(".owentity"):
                print "OWEntity not yet supported. Filename: %s" % obfile
                return None
            else:
                return import_owmdl.read(obfile, settings)
        else:
            return (cmds.spaceLocator(name=obn), "None")

    except Exception as e:
        print "Error importing map object %s. Error: %s" % (obfile, e)
        return None


def normalizeColor(inCol):
    intensity = 1
    color = inCol

    if (inCol[0] > 1.0 or inCol[1] > 1.0 or inCol[2] > 1.0):
        theMax = max(inCol[0], inCol[1], inCol[2])
        theMin = min(inCol[0], inCol[1], inCol[2], 0)
        color[0] = (inCol[0]-theMin)/(theMax-theMin)
        color[1] = (inCol[1]-theMin)/(theMax-theMin)
        color[2] = (inCol[2]-theMin)/(theMax-theMin)
        intensity = theMax

    return (color, intensity)


def quat2euler(q):
    qe = q.asEulerRotation()

    return qe


# TODO: move this to commonfuncs simce import_owmdl does something
# similar now.
def quatrotate(inobj, quat):
    if not inobj:
        return
    q = Quaternion(quat[0], quat[1], quat[2], quat[3])
    qe = quat2euler(q)
    qed = Euler()
    qed.x = round(math.degrees(qe.x), 3)
    qed.y = round(math.degrees(qe.y), 3)
    qed.z = round(math.degrees(qe.z), 3)
    # print "Rotating X: %s, Y: %s, Z: %s"%(qed.x, qed.y, qed.z)

    cmds.rotate(qed.x, qed.y, qed.z, inobj)


def remove(obj):
    cmds.delete(obj)


def readmap(settings, filename):
    print "Reading Map..."
    root, file = os.path.split(filename)

    data = read_owmap.read(filename)
    if not data:
        return None

    rootName = data.header.name
    if len(rootName) == 0:
        rootName = os.path.splitext(file)[0]

    rootName = MayaSafeName(rootName)

    rootGroupName = MayaSafeName("r_%s" % rootName)
    rootObject = cmds.group(em=True, name=rootGroupName, w=True)
    collisionMat = import_owmat.buildCollision("CollisionPhysics")

    matCache = {}
    lightNum = 0

    if settings.MapImportModels and settings.MapImportObjectsLarge:
        # print "Exporting Large Objects"
        globObj = cmds.group(em=True, n="%s_Objects" % rootName, p=rootObject)
        refObj = cmds.group(em=True, n="%s_ObjectReferences" % rootName,
                            p=globObj)
        cmds.hide(refObj)

        objCache = {}

        if DEBUG_DATA_SIZE:
            data.objects = data.objects[0:DEBUG_DATA_SIZE]

        for ob in data.objects:
            obfile = ob.model
            obfile = obfile.replace('\\', os.sep)
            if not os.path.isabs(obfile):
                obfile = os.path.normpath('%s/%s' % (root, obfile))

            obn = "obj%s" % os.path.splitext(os.path.basename(obfile))[0]

            obji = 0
            if obn in objCache:
                objfound = True
                while objfound:
                    obji = obji + 1
                    if ("%s_%s" % (obn, obji) not in objCache):
                        objfound = False

            if obji > 0:
                obn = "%s_%s" % (obn, obji)

            # Either use the model or a placeholder object based on
            # the settings.
            if settings.MapImportModelsAs == 1:
                obj = import_owmdl.read(obfile, settings, None, obji)
            else:
                obj = (cmds.spaceLocator(name=obn), "None")
            objCache[obn] = obj

            rlist = cmds.listRelatives(obj[0], allParents=True)
            # print("rList: %s"%rlist)

            if (rlist is None) or (refObj not in rlist):
                cmds.parent(obj[0], refObj)

            for idx, ent in enumerate(ob.entities):
                material = None
                matpath = ent.material
                matpath = matpath.replace('\\', os.sep)
                if not os.path.isabs(matpath):
                    matpath = os.path.normpath('%s/%s' % (root, matpath))
                if settings.MapImportMaterials and len(ent.material) > 0:
                    if matpath not in matCache:
                        material = import_owmat.read(matpath)[0]
                        matCache[matpath] = material
                    else:
                        material = matCache[matpath]
                    if settings.MapImportModelsAs == 1:
                        # Only attempt to texture Models
                        import_owmdl.bindMaterials(obj[2], obj[4], material)
                else:
                    if settings.MapImportModelsAs == 1:
                        # Only attempt to texture Models
                        import_owmdl.bindMaterials(obj[2], obj[4], "lambert1")

                matID = os.path.splitext(os.path.basename(matpath))[0]
                matObjName = "mat%s" % (
                    os.path.splitext(os.path.basename(matpath))[0])
                matObj = cmds.group(
                    em=True, name=matObjName, parent=globObj)

                mrec = len(cmds.ls("obj%s_*" % matID))
                for idx2, rec in enumerate(ent.records):
                    name = "obj%s_%i" % (matID, mrec)
                    mrec += 1
                    instance_with_prs(name, obj[0], matObj,
                                      rec.position, rec.rotation, rec.scale)

    if settings.MapImportModels and settings.MapImportObjectsDetail:
        # print "Exporting Detail Objects"
        globDet = cmds.group(em=True, n="%s_Details" % rootName, p=rootObject)
        refDet = cmds.group(em=True, n="%s_DetailsReferences" % rootName,
                            p=globDet)
        cmds.hide(refDet)

        objCache = {}

        mrec = {}

        if DEBUG_DATA_SIZE:
            data.details = data.details[0:DEBUG_DATA_SIZE]

        for ob in data.details:
            obfile = ob.model
            obfile = obfile.replace('\\', os.sep)
            if not os.path.isabs(obfile):
                obfile = os.path.normpath('%s/%s' % (root, obfile))

            obn = "detail%s" % os.path.splitext(os.path.basename(obfile))[0]

            if obn == 'detailphysics' and (
                settings.MapImportObjectsPhysics == 0 or
                    settings.MapImportModelsAs == 2):
                continue

            obj = None
            obji = 0
            if obn in objCache:
                objfound = True
                obj = objCache[obn]
                while objfound:
                    obji = obji + 1
                    if ("%s_%s" % (obn, obji) not in objCache):
                        objfound = False

            if obji > 0:
                obn = "%s_%s" % (obn, obji)

            if not obj:
                obj = importModel(settings, obfile, obn)
                if not obj:
                    print ("Bad/Invalid Object: (%s:%s:%s). "
                           "Skipping to next one..." % (obfile, obn, obji))
                    continue

                objCache[obn] = obj

            rlist = cmds.listRelatives(obj[0], allParents=True)

            if (rlist is None) or (refDet not in rlist):
                cmds.parent(obj[0], refDet)

            if settings.MapImportMaterials and len(ob.material) > 0:
                matpath = ob.material
                matpath = matpath.replace('\\', os.sep)
                if not os.path.isabs(matpath):
                    matpath = os.path.normpath('%s/%s' % (root, matpath))
                material = None
                if matpath not in matCache:
                    material = import_owmat.read(matpath)[0]
                    matCache[matpath] = material
                else:
                    material = matCache[matpath]
                if settings.MapImportModelsAs == 1:
                    # Only attempt to texture Models
                    import_owmdl.bindMaterials(obj[2], obj[4], material)
            if settings.MapImportMaterials and obn == 'detailphysics':
                import_owmdl.bindMaterials(obj[2], obj[4], collisionMat)
                # cmds.polyAutoProjection(
                # obj[0], lm=1, pb=True, ibd=True, cm=False,
                # l=0, sc=1, o=1, ps=0.2, ws=False)

            if obn not in mrec:
                mrec[obn] = 0

            name = "%s_%i" % (obn, mrec[obn])
            mrec[obn] = mrec[obn] + 1
            instance_with_prs(name, obj[0], globDet,
                              ob.position, ob.rotation, ob.scale)

    if settings.MapImportLights and len(data.lights) > 0:
        lightlist = [None] * len(data.lights)
        for light in data.lights:
            color, inten = normalizeColor(light.Color)
            if color == light.Color and inten != 1.0:
                inten = 1.0
            lightName = "%s_Light_%03i" % (rootName, lightNum)
            lightNum = lightNum + 1

            pos = adjustAxis(light.position)
            ca = light.LightFOV
            if light.LightType == 1 and ca == -1.0:
                print ("Light %s is a Spotlight with -1.0 cone angle. "
                       "Defaulting to 45 degrees..." % lightName)
                ca = 45

            # print "Name: %s\n    Position: %s\n    Rotation: %s\n    ",
            # print "Light Type: %s\n    Light FOV: %s, Cone Angle: %s\n    ",
            # print "Color: %s, Normalized Color: %s, Normalized ",
            # print "Intensity: %s"%(lightName, light.position, light.rotation,
            # light.LightType, light.LightFOV, ca, light.Color, color, inten)

            if light.LightType == 0:
                LObjName = cmds.directionalLight(
                    name=lightName, intensity=inten, rgb=color)
            elif light.LightType == 1:
                LObjName = cmds.spotLight(
                    name=lightName, intensity=inten, rgb=color, coneAngle=ca)
            elif light.LightType == 2:
                LObjName = cmds.pointLight(
                    name=lightName, intensity=inten, rgb=color)
            else:
                print "%s has an Unknown Light Type: %s" % (
                    lightName, light.LightType)
                pass

            cmds.move(pos[0], pos[1], pos[2], LObjName)
            quatrotate(LObjName, wadjustAxis(light.rotation))
            lightlist[lightNum-1] = LObjName

            # Research Data output

            # print "    uk1a: %s, uk1b: %s\n    uk2a: %s, uk2b: %s, uk2c: %s,"
            # uk2d: %s\n    uk3a: %s, uk3b: %s\n    ukPos1: %s, ukQuat1: %s\n
            # ukPos2: %s, ukQuat2: %s\n    ukPos3: %s\n    uk4a: %s\n    uk4b:
            # %s\n    uk8b: %s, uk8c: %s\n    uk9: %s\n    uk10a: %s, uk10b:
            # %s\n    uk11a: %s, uk11b: %s\n"%(light.uk1a, light.uk1b,
            # light.uk2a, light.uk2b, light.uk2c, light.uk2d, light.uk3a,
            # light.uk3b, light.ukp1, light.ukq1, light.ukp2, light.ukq2,
            # light.ukp3, light.uk4a, light.uk4b, light.uk8b, light.uk8c,
            # light.uk9, light.uk10a, light.uk10b, light.uk11a, light.uk11b)

        cmds.group(tuple(lightlist), n="%s_Lights" % rootName,
                   p=rootObject)


def read(infilename, inputsettings):
    settings = inputsettings

    status = readmap(settings, infilename)
    cmds.select(d=True)
    return status

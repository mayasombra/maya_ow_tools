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

    major, minor, name, objectCount, detailCount, lightCount = bin_ops.readFmtFlat(stream, owm_types.OWMAPHeader.structFormat)
    header = owm_types.OWMAPHeader(major, minor, name, objectCount, detailCount, lightCount)

    objects = []
    for i in range(objectCount):
        model, entityCount = bin_ops.readFmtFlat(stream, owm_types.OWMAPObject.structFormat)

        entities = []
        for j in range(entityCount):
            material, recordCount = bin_ops.readFmtFlat(stream, owm_types.OWMAPEntity.structFormat)

            records = []
            for k in range(recordCount):
                position, scale, rotation = bin_ops.readFmt(stream, owm_types.OWMAPRecord.structFormat)
                records += [owm_types.OWMAPRecord(position, scale, rotation)]
            entities += [owm_types.OWMAPEntity(material, recordCount, records)]
        objects += [owm_types.OWMAPObject(model, entityCount, entities)]
    details = []
    for i in range(detailCount):
        model, material = bin_ops.readFmtFlat(stream, owm_types.OWMAPDetail.structFormat)
        position, scale, rotation = bin_ops.readFmt(stream, owm_types.OWMAPDetail.exFormat)
        details += [owm_types.OWMAPDetail(model, material, position, scale, rotation)]
    
    lights = []
    for i in range(lightCount):
        position, rotation, LightType, LightFOV, Color, uk1a, uk1b, uk2a, uk2b, uk2c, uk2d, uk3a, uk3b, ukp1, ukq1, ukp2, ukq2, ukp3, uk4a, uk4b, uk8b, uk8c, uk9, uk10a, uk10b, uk11a, uk11b = bin_ops.readFmt(stream, owm_types.OWMAPLight.structFormat)
        lights += [owm_types.OWMAPLight(position, rotation, LightType, LightFOV, Color, uk1a, uk1b, uk2a, uk2b, uk2c, uk2d, uk3a, uk3b, ukp1, ukq1, ukp2, ukq2, ukp3, uk4a, uk4b, uk8b, uk8c, uk9, uk10a, uk10b, uk11a, uk11b)]
        
    return owm_types.OWMAPFile(header, objects, details, lights)

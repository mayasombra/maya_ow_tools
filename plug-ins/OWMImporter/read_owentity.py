from . import bin_ops
from . import owm_types
import io
import os


def openStream(filename):
    stream = None
    with open(filename, 'rb') as f:
        stream = io.BytesIO(f.read())
    return stream


def read(filename):
    filename = os.path.normpath(filename.replace('\\', os.sep))
    root, file = os.path.split(filename)

    stream = openStream(filename)
    if not stream:
        return None

    (magic, major, minor, guid, model_guid, effect_guid, idx, model_idx,
     effect_idx, child_count) = bin_ops.readFmtFlat(
         stream, owm_types.OWEntityHeader.structFormat)
    header = owm_types.OWEntityHeader(
        magic, major, minor, guid, model_guid, effect_guid, idx, model_idx,
        effect_idx, child_count)

    children = []
    for i in range(child_count):
        (child_file, child_hardpoint, child_variable, child_hp_index,
         child_var_index, child_attachment) = bin_ops.readFmtFlat(
            stream, owm_types.OWEntityChild.structFormat)
        children.append(
            owm_types.OWEntityChild(child_file, child_hardpoint,
                                    child_variable, child_hp_index,
                                    child_var_index, child_attachment))
    return owm_types.OWEntityFile(
        header, guid, model_guid, effect_guid, idx, model_idx, effect_idx,
        children)

import math

from PIL import Image

LZW = "lzw"
ZIP = "zip"
JPEG = "jpeg"
PACKBITS = "packbits"
G3 = "g3"
G4 = "g4"


def roughness(r, g, b, a):
    return (255-g, 255-g, 255-g)


def metal(r, g, b, a):
    rf = r/255.0
    rf -= .5
    if rf < 0:
        rf = 0
    rf *= 2
    return (delinearizeFunc(rf), delinearizeFunc(rf), delinearizeFunc(rf))


def sheen(r, g, b, a):
    return (b, b, b)


def specular(r, g, b, a):
    rf = r/255.0
    if rf > .5:
        return (delinearizeFunc(0), delinearizeFunc(0), delinearizeFunc(0))
    rf *= 2
    if rf > 1.0:
        rf = 1.0
    return (delinearizeFunc(rf), delinearizeFunc(rf), delinearizeFunc(rf))


def delinearizeFunc(xf):
    if xf <= 0.0031308:
        return int(12.92 * xf * 255)
    return int((1.055*math.pow(xf, 1.0/2.4) - 0.055) * 255)


def ao(r, g, b, a):
    return (a, a, a)


def transform(fname, xform, outname, unlink=False):
    # The new Widowmaker textures included some TIFF tags that
    # bomb out the Python TIFF coder. We work around this by
    # creating a new output image and writing to it.
    im = Image.open(fname)
    out = Image.new(im.mode, im.size)
    data = list(im.getdata())

    for i in range(len(data)):
        if len(data[i]) == 4:
            r, g, b, a = data[i]
            data[i] = xform(r, g, b, a)
        else:
            r, g, b = data[i]
            data[i] = xform(r, g, b, 255)

    out.putdata(data)
    out.save(outname)

if __name__ == "__main__":
    transform('/tmp/330.tif', roughness, '/tmp/330-rough.tif')

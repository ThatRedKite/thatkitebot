from io import BytesIO
import imageio
from wand.image import Image as WandImage
import numpy as np
from discord import File


# define filters which all take one argument (i) which is a numpy array:
def magik(i):
    with WandImage.from_array(i) as a:
        a.liquid_rescale(width=int(a.width / 2), height=int(a.height / 2), delta_x=1, rigidity=0)
        a.liquid_rescale(width=a.width * 2, height=a.height * 2, delta_x=2, rigidity=0)
        return np.array(a)


def wide(i):
    with WandImage.from_array(i) as a:
        a.resize(width=int(a.width * 3.3), height=int(a.height / 1.8))
        a.crop(left=int(a.width / 4), top=1, right=(a.width - (int(a.width / 4))), bottom=a.height)
        return np.array(a)


def deepfry(i):
    with WandImage.from_array(i) as a:
        a.modulate(saturation=600.00)
        a.noise("gaussian", attenuate=0.1)
        return np.array(a)


def do_gmagik(image: imageio.plugins.pillowmulti.GIFFormat.Reader):
    fps = image.get_meta_data()["duration"]
    # apply the magik filter to all frames
    io = list()
    for frame in image: io.append(magik(frame))

    # write the result to a BytesIO buffer and then tur
    # n it into a `discord.File` object and return it
    with BytesIO() as buffer:
        buffer.seek(0)
        imageio.mimwrite(buffer, io, fps=fps, format="gif")
        io.clear()
        buffer.seek(0)
        return File(buffer, filename="deepfried.gif")

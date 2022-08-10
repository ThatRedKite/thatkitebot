import re

from wand.image import Image as WandImage
from wand.color import Color
from wand.font import Font


def magik(buf, fn) -> (bytes, int):
    with WandImage(file=buf) as a:
        if a.width > 6000 or a.height > 6000:
            a.destroy()
            return None, -1
        a.sample(width=int(a.width * 0.5), height=int(a.height * 0.5))
        a.liquid_rescale(width=int(a.width / 2), height=int(a.height / 1.5), delta_x=1, rigidity=0)
        a.liquid_rescale(width=int(a.width * 2), height=int(a.height * 1.5), delta_x=2, rigidity=0)
        a.sample(width=int(a.width * 2), height=int(a.height * 2))
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def swirlmagik(buf, fn) -> (bytes, int):
    with WandImage(file=buf) as a:
        if a.width > 3000 or a.height > 3000:
            a.destroy()
            return None, -1
        a.sample(width=int(a.width * 0.5), height=int(a.height * 0.5))
        a.swirl(60)
        a.liquid_rescale(width=int(a.width / 2), height=int(a.height / 1.5), delta_x=1, rigidity=0)
        a.liquid_rescale(width=int(a.width * 2), height=int(a.height * 1.5), delta_x=2, rigidity=0)
        a.swirl(-60)
        a.sample(width=int(a.width * 2), height=int(a.height * 2))
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def swirl(buf, fn, angle: int = -60) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.swirl(degree=angle)
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def invert(buf, fn) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.negate()
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def implode(buf, fn) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.implode(0.6)
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def opacify(buf, fn) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.alpha_channel = "remove"
        a.background_color = Color("white")
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def explode(buf, fn) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.implode(-4.0)
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def reduce(buf, fn) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.posterize(levels=2)
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def caption(blob, fn, ct, path) -> (bytes, int):
    color_alias = {
        "piss": "#f9fc12",
        "cum": "#ededd5",
        "pickle": "#12a612",
        "white": "#ffffff",
    }
    in_str = str(ct)
    # find any emotes in the text
    x = re.findall(r"[<]:\w{2,}:\d{15,}[>]", in_str)
    for n in x: in_str = in_str.replace(str(n), re.findall(r":\w{2,}:", n)[0])
    # find any parameters in the command
    color = "white"
    x = re.findall(r"color:\d{1,3},\d{1,3},\d{1,3}", in_str)
    if len(x) > 0:
        color = x[0].lower().replace("color:", "rgb(") + ")"
        in_str = in_str.replace(x[0], "")
    x = re.findall(r"color:(?:\d{2}|[1-f]{2}){3}", in_str)
    if len(x) > 0:
        color = x[0].lower().replace("color:", "#")
        in_str = in_str.replace(x[0], "")
    x = re.findall(r"color:[\w]{3,30}", in_str)
    if len(x) > 0:
        color = x[0].lower().replace("color:", "")
        in_str = in_str.replace(x[0], "").rstrip()
        if color in color_alias:
            color = color_alias[color]
    try:
        with WandImage(file=blob) as image:
            # Calculate image parameters for the text to wrap and fit.
            txt_top = int(0.70 * image.height)  # add text to the bottom 25% of the image
            txt_left = int(0.10 * image.width)  # leave 10 % the image from the left
            txt_width = image.width - (
                        txt_left * 2)  # total width - 10% * 2 will leave 10% of with on the right side as well
            txt_height = image.height - txt_top  # use the whole 15% for text
            stroke_width = (txt_height * txt_width)/(10000 + (2500 * len(in_str)))
            if stroke_width < 1.5 or color != "white":
                font = Font(path + "OpenSansEmoji.ttf", color=color)
            else:
                font = Font(path + "OpenSansEmoji.ttf", color=color, stroke_color="black", stroke_width=stroke_width)
            image.caption(in_str, left=txt_left, top=txt_top, width=txt_width, height=txt_height, font=font,
                        gravity='center')
            image.format = 'png'
            b = image.make_blob()
            image.destroy()
    except:
        fn = -3  # probably wrong color
        b = None
    return b, fn


def wide(buf, fn) -> (bytes, int):
    with WandImage(file=buf) as a:
        if a.width > 6000 or a.height > 6000:
            a.destroy()
            return None, -1
        a.resize(width=int(a.width * 3.3), height=int(a.height / 1.8))
        a.crop(left=int(a.width / 4), top=1, right=(a.width - (int(a.width / 4))), bottom=a.height)
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def deepfry(buf, fn) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.modulate(saturation=600.00)
        a.noise("gaussian", attenuate=0.1)
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def rotate(buf, fn, angle: int = 90) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.rotate(degree=angle, )
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn


def blackwhite(buf, fn) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.transform_colorspace('gray')
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn

def makesepia(buf, fn, threshold: float = 0.8) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.sepia_tone(threshold)
        b = a.make_blob(format="png")
        a.destroy()
    return b, fn

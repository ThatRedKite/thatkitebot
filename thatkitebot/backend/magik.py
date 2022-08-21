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
        b = a.make_blob(format='png')
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
        b = a.make_blob(format='png')
    return b, fn


def swirl(buf, fn, angle: int = -60) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.swirl(degree=angle)
        b = a.make_blob(format='png')
    return b, fn


def invert(buf, fn) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.negate()
        b = a.make_blob(format='png')
    return b, fn


def implode(buf, fn) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.implode(0.6)
        b = a.make_blob(format='png')
    return b, fn


def opacify(buf, fn) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.alpha_channel = 'remove'
        a.background_color = Color('white')
        b = a.make_blob(format='png')
    return b, fn


def explode(buf, fn) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.implode(-4.0)
        b = a.make_blob(format='png')
    return b, fn


def reduce(buf, fn) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.posterize(levels=2)
        b = a.make_blob(format='png')
    return b, fn


def caption(blob, fn, ct, path) -> (bytes, int):
    color_alias = {
        'piss': '#f9fc12',
        'cum': '#ededd5',
        'pickle': '#12a612',
        'white': '#ffffff',
    }
    in_str = str(ct)
    # find any emotes in the text
    x = re.findall(r'[<]:\w{2,}:\d{15,}[>]', in_str)
    for n in x: in_str = in_str.replace(str(n), re.findall(r':\w{2,}:', n)[0])
    # find any parameters in the command
    color = 'white'
    x = re.findall(r'color:\d{1,3},\d{1,3},\d{1,3}', in_str)
    if len(x) > 0:
        color = x[0].lower().replace('color:', 'rgb(') + ')'
        in_str = in_str.replace(x[0], '')
    x = re.findall(r'color:(?:\d{2}|[1-f]{2}){3}', in_str)
    if len(x) > 0:
        color = x[0].lower().replace('color:', '#')
        in_str = in_str.replace(x[0], '')
    x = re.findall(r'color:\w{3,30}', in_str)
    if len(x) > 0:
        color = x[0].lower().replace('color:', '')
        in_str = in_str.replace(x[0], '').rstrip()
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
            stroke_width = (txt_height * txt_width) / (10000 + (2500 * len(in_str)))
            if stroke_width < 1.5 or color != 'white':
                font = Font(path + 'OpenSansEmoji.ttf', color=color)
            else:
                font = Font(path + 'OpenSansEmoji.ttf', color=color, stroke_color='black', stroke_width=stroke_width)
            image.caption(in_str, left=txt_left, top=txt_top, width=txt_width, height=txt_height, font=font,
                          gravity='center')
            image.format = 'png'
            b = image.make_blob()
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
        b = a.make_blob(format='png')
    return b, fn


def deepfry(buf, fn) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.modulate(saturation=600.00)
        a.noise('gaussian', attenuate=0.1)
        b = a.make_blob(format='png')
    return b, fn


def rotate(buf, fn, angle: int = 90) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.rotate(degree=angle, )
        b = a.make_blob(format='png')
    return b, fn


def black_white(buf, fn) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.transform_colorspace('gray')
        b = a.make_blob(format='png')
    return b, fn


def make_sepia(buf, fn, threshold: float = 0.8) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.sepia_tone(threshold)
        b = a.make_blob(format='png')
    return b, fn


def make_polaroid(buf, fn) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.polaroid()
        b = a.make_blob(format='png')
    return b, fn


def charcoal(buf, fn, radius: float = 1.5, sigma: float = 0.5) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.charcoal(radius, sigma)
        b = a.make_blob(format='png')
    return b, fn


def make_vignette(buf, fn, sigma: int = 3, x: int = 10, y: int = 10) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.vignette(sigma, x, y)
        b = a.make_blob(format='png')
    return b, fn


def bubble(buf, fn) -> (bytes, int):
    # grab the template files stored in the data directory
    negative = '/app/data/resources/bubble_negative.png'
    outline = '/app/data/resources/bubble_outline.png'

    # load in all the images
    with (
        WandImage(file=buf) as a,
        WandImage(filename=negative) as neg,
        WandImage(filename=outline) as out
    ):
        # ensure the input image does not exceed 1024 in either direction
        if a.width > 1024 or a.height > 1024:
            aspect_ratio = a.width / a.height
            # and yes kite, the elif won't work here as we rely on it to make sure both sides are within specs
            if a.width > 1024:
                a.resize(width=1024, height=int(1024 / aspect_ratio))
            if a.height > 1024:
                a.resize(width=int(1024 * aspect_ratio), height=1024)
        # resize the images accordingly
        neg.resize(width=a.width, height=a.height)
        out.resize(width=a.width, height=a.height)
        # compose the input image onto the negative
        neg.composite_channel(channel='default_channels', image=a, operator='src_in')
        # compose the outline image onto the composed negative
        neg.composite_channel(channel='default_channels', image=out, operator='over')
        # create a binary output for the upload
        b = neg.make_blob(format='png')

    return b, fn


def scale(buf, fn, factor: float = 0.5) -> (bytes, int):
    # input protection
    if 1 > factor < 0.1:
        factor = 0.5

    # load in the source image
    with WandImage(file=buf) as a:
        # resize the image and returns the binary
        a.resize(width=int(a.width * factor), height=int(a.height * factor))
        b = a.make_blob('png')

    return b, fn


def blur(buf, fn, radius: int = 0, sigma: int = 3) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.blur(radius, sigma)
        b = a.make_blob(format='png')
    return b, fn


def adaptive_blur(buf, fn, radius: int = 8, sigma: int = 4) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.adaptive_blur(radius, sigma)
        b = a.make_blob(format='png')
    return b, fn


def motion_blur(buf, fn, radius: int = 8, sigma: int = 4, angle: int = -45) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.motion_blur(radius, sigma, angle)
        b = a.make_blob(format='png')
    return b, fn


def edge(buf, fn, radius: int = 1) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.transform_colorspace('gray')
        a.edge(radius)
        b = a.make_blob(format='png')
    return b, fn


def emboss(buf, fn, radius: float = 3.0, sigma: float = 1.75) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.transform_colorspace('gray')
        a.emboss(radius, sigma)
        b = a.make_blob(format='png')
    return b, fn


def kuwahara(buf, fn, radius: int = 1, sigma: float = 1.5) -> (bytes, int):
    with WandImage(file=buf) as a:
        a.kuwahara(radius, sigma)
        b = a.make_blob(format='png')
    return b, fn


def shade(buf, fn, gray: bool = True, azimuth: float = 286.0, elevation: float = 45.0):
    with WandImage(file=buf) as a:
        a.shade(gray, azimuth, elevation)
        b = a.make_blob(format='png')
    return b, fn

import Image
import os, sys


def roll(image, delta):
    "Roll an image sideways"

    xsize, ysize = image.size

    delta = delta % xsize
    if delta == 0: return image

    part1 = image.crop((0, 0, delta, ysize))
    part2 = image.crop((delta, 0, xsize, ysize))
    image.paste(part2, (0, 0, xsize-delta, ysize))
    image.paste(part1, (xsize-delta, 0, xsize, ysize))

    return image

def main():
    image1 = Image.open("test1.jpg")
    image2 = Image.open("test2.jpg")
    outfile = "test1rotate.jpg"
    box = (100, 100, 300, 300)
    region = image1.crop(box)
    region = region.transpose(Image.ROTATE_180)
    image2.paste(region, box)
    image2.save(outfile)
    #roll_image.show()


if __name__ == '__main__':
    main()
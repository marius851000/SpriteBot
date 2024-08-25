#  Copyright 2020-2021 Parakoopa and the SkyTemple Contributors
#
#  This file is part of SkyTemple.
#
#  SkyTemple is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SkyTemple is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SkyTemple.  If not, see <https://www.gnu.org/licenses/>.
from typing import List, Set, Dict, Tuple, Optional

class MultipleOffsetError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def centerBounds(bounds: Tuple[int, int, int, int], center: Tuple[int, int]):
    minX = min(bounds[0] - center[0], center[0] - bounds[2])
    minY = min(bounds[1] - center[1], center[1] - bounds[3])

    maxX = max(center[0] - bounds[0], bounds[2] - center[0])
    maxY = max(center[1] - bounds[1], bounds[3] - center[1])
    return addToBounds((minX, minY, maxX, maxY), center, False)


def roundUpBox(minBox: Tuple[int, int, int, int]):
    width = minBox[2] - minBox[0]
    height = minBox[3] - minBox[1]
    newWidth = roundUpToMult(width, 8)
    newHeight = roundUpToMult(height, 8)
    startX = minBox[0] + (width - newWidth) // 2
    startY = minBox[1] + (height - newHeight) // 2
    return startX, startY, startX + newWidth, startY + newHeight


def addToBounds(bounds: Tuple[int, int, int, int], add: Tuple[int, int], sub: bool = False) -> Tuple[int, int, int, int]:
    mult = 1
    if sub:
        mult = -1
    return (bounds[0] + add[0] * mult, bounds[1] + add[1] * mult, bounds[2] + add[0] * mult, bounds[3] + add[1] * mult)


def addLoc(loc1: Tuple[int, int], loc2: Tuple[int, int], sub: bool = False):
    mult = 1
    if sub:
        mult = -1
    return (loc1[0] + loc2[0] * mult, loc1[1] + loc2[1] * mult)


def getCoveredBounds(inImg, max_box: Optional[Tuple[int, int, int, int]] = None):
    if max_box is None:
        max_box = (0, 0, inImg.size[0], inImg.size[1])
    minX, minY = inImg.size
    maxX = -1
    maxY = -1
    datas = inImg.getdata()
    for i in range(max_box[0], max_box[2]):
        for j in range(max_box[1], max_box[3]):
            if datas[i + j * inImg.size[0]][3] != 0:
                if i < minX:
                    minX = i
                if i > maxX:
                    maxX = i
                if j < minY:
                    minY = j
                if j > maxY:
                    maxY = j
    abs_bounds = (minX, minY, maxX + 1, maxY + 1)
    return addToBounds(abs_bounds, (max_box[0], max_box[1]), True)


def addToPalette(palette, img):
    data = img.getdata()
    for color in data:
        if color[3] == 255:
            palette[color] = True


def getOffsetFromRGB(img, bounds: Tuple[int, int, int, int], black: bool, r: bool, g: bool, b: bool, white: bool):
    datas = img.getdata()
    results: List[Optional[Tuple[int, int]]] = [None] * 5
    for i in range(bounds[0], bounds[2]):
        for j in range(bounds[1], bounds[3]):
            color = datas[i + j * img.size[0]]
            if color[3] == 255:
                if color[0] == 255 and color[1] == 255 and color[2] == 255:
                    if white:
                        if results[4] is None:
                            results[4] = (i - bounds[0], j - bounds[1])
                        else:
                            raise MultipleOffsetError("Second white pixel found at {0} when already found at {1} when searching for offsets!".format((i, j), (results[4][0] + bounds[0], results[4][1] + bounds[1])))
                    else:
                        if results[1] is None and results[2] is None and results[3] is None:
                            if results[0] is None:
                                results[0] = (i - bounds[0], j - bounds[1])
                            # otherwise, black may already be chosen.  and just leave it alone

                            results[1] = (i - bounds[0], j - bounds[1])
                            results[2] = (i - bounds[0], j - bounds[1])
                            results[3] = (i - bounds[0], j - bounds[1])
                        else:
                            existing_px = []
                            if results[0] is not None:
                                existing_px.append((results[0][0] + bounds[0], results[0][1] + bounds[1]))
                            if results[1] is not None:
                                existing_px.append((results[0][1] + bounds[0], results[1][1] + bounds[1]))
                            if results[2] is not None:
                                existing_px.append((results[0][2] + bounds[0], results[2][1] + bounds[1]))
                            if results[3] is not None:
                                existing_px.append((results[0][3] + bounds[0], results[3][1] + bounds[1]))
                            raise MultipleOffsetError("White pixel found at {0} when r/g/b pixel already found at {1} when searching for offsets!".format((i, j), existing_px))
                else:
                    if black and color[0] == 0 and color[1] == 0 and color[2] == 0:
                        # there is one exception: black and white can coexist
                        # so if black offset already exists, but it was read as part of a white pixel,
                        # correct it to this black pixel
                        if results[0] is None or results[0] == results[1] and results[1] == results[2] and results[2] == results[3]:
                            results[0] = (i - bounds[0], j - bounds[1])
                        else:
                            raise MultipleOffsetError("Multiple black pixels found when searching for offsets!")
                    if r and color[0] == 255:
                        if results[1] is None:
                            results[1] = (i - bounds[0], j - bounds[1])
                        else:
                            raise MultipleOffsetError("Multiple red pixels found found when searching for offsets!")
                    if g and color[1] == 255:
                        if results[2] is None:
                            results[2] = (i - bounds[0], j - bounds[1])
                        else:
                            raise MultipleOffsetError("Multiple green pixels found found when searching for offsets!")
                    if b and color[2] == 255:
                        if results[3] is None:
                            results[3] = (i - bounds[0], j - bounds[1])
                        else:
                            raise MultipleOffsetError("Multiple blue pixels found found when searching for offsets!")

    return results


def combineExtents(extent1: Tuple[int, int, int, int], extent2: Tuple[int, int, int, int]):
    return min(extent1[0], extent2[0]), min(extent1[1], extent2[1]), \
           max(extent1[2], extent2[2]), max(extent1[3], extent2[3])


def roundUpToMult(inInt: int, inMult: int):
    subInt = inInt - 1
    div = subInt // inMult
    return (div + 1) * inMult

def imgsEqual(img1, img2, flip: bool = False):
    if img1.size[0] != img2.size[0] or img1.size[1] != img2.size[1]:
        return False
    data_1 = img1.getdata()
    data_2 = img2.getdata()
    for xx in range(img1.size[0]):
        for yy in range(img1.size[1]):
            idx1 = xx + yy * img1.size[0]
            x2 = xx
            if flip:
                x2 = img1.size[0] - 1 - xx
            idx2 = x2 + yy * img1.size[0]
            if data_1[idx1] != data_2[idx2]:
                return False

    return True

def imgsLineartEqual(img1, img2, flip: bool = False):
    if img1.size[0] != img2.size[0] or img1.size[1] != img2.size[1]:
        return False
    data_1 = img1.getdata()
    data_2 = img2.getdata()
    for xx in range(img1.size[0]):
        for yy in range(img1.size[1]):
            idx1 = xx + yy * img1.size[0]
            x2 = xx
            if flip:
                x2 = img1.size[0] - 1 - xx
            idx2 = x2 + yy * img1.size[0]
            if (data_1[idx1] == (0, 0, 0, 255)) != (data_2[idx2] == (0, 0, 0, 255)):
                return False

    return True


def offsetsEqual(offset1, offset2, imgWidth: int, flip: bool = False):
    if flip:
        center = (imgWidth - offset2.center[0] - 1, offset2.center[1])
        head = (imgWidth - offset2.head[0] - 1, offset2.head[1])
        lhand = (imgWidth - offset2.lhand[0] - 1, offset2.lhand[1])
        rhand = (imgWidth - offset2.rhand[0] - 1, offset2.rhand[1])
    else:
        center = offset2.center
        head = offset2.head
        lhand = offset2.lhand
        rhand = offset2.rhand

    if offset1.center != center:
        return False
    if offset1.head != head:
        return False
    if offset1.lhand != lhand:
        return False
    if offset1.rhand != rhand:
        return False
    return True

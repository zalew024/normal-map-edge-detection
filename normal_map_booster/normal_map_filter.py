import logging
import math
from krita import *
import numpy as np
import numpy.typing as npt
from PyQt5.QtGui import QImage

from normal_map_booster.slope_filter_numpy import change_slope
from normal_map_booster.utils import convert_numpy_to_qimage, convert_qimage_to_numpy


class Filter:

    def __init__(self, normalMapProps):
        self.normalMapProps = normalMapProps
        self.filterProps = {
            "type": normalMapProps["type"],
            "blueSwizzle": 4,
            "greenSwizzle": 2,  # 3 inverted
            "redSwizzle": 0,  # 1 inverted
            "vertRadius": normalMapProps["width"],
            "horizRadius": normalMapProps["width"],
            "channelToConvert": 0,
        }

    def setFilterProps(self):
        shape = self.normalMapProps["shape"]
        format = self.normalMapProps["format"]
        if shape == "bump" and format == "OpenGL":
            self.filterProps.update({"greenSwizzle": 3, "redSwizzle": 1})
        elif shape == "bump" and format == "DirectX":
            self.filterProps.update({"greenSwizzle": 2, "redSwizzle": 1})
        elif shape == "hole" and format == "OpenGL":
            self.filterProps.update({"greenSwizzle": 2, "redSwizzle": 0})
        elif shape == "hole" and format == "DirectX":
            self.filterProps.update({"greenSwizzle": 3, "redSwizzle": 0})

        self.heightToNormalFilter = Krita.instance().filter("height to normal")
        heightToNormalFilterConfig = self.heightToNormalFilter.configuration()

        for prop, val in self.filterProps.items():
            heightToNormalFilterConfig.setProperty(prop, val)
        self.heightToNormalFilter.setConfiguration(heightToNormalFilterConfig)

    def changeSlope(self, image: QImage) -> QImage:
        array = convert_qimage_to_numpy(image)
        array = change_slope(array, self.normalMapProps["slope"])
        return convert_numpy_to_qimage(array, (image.width(), image.height()))
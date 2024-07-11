import logging
import math
from krita import *
import numpy as np
import numpy.typing as npt

from normal_map.slope_filter_numpy import change_slope


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

    def changeSlope(self, imageData: QImage, filterLayer):
        angle_deg = self.normalMapProps["slope"]

        # Get image dimensions
        width = imageData.width()
        height = imageData.height()
        logging.debug(f"Image shape (w|h): {width}x{height}")
        assert width > 0 and height > 0

        # Get the pointer to the image data
        ptr = imageData.bits()
        assert ptr is not None
        ptr.setsize(imageData.sizeInBytes())
        shape = (height * width, 4)

        # Convert the data to a numpy array
        array = np.array(ptr, copy=True, dtype=np.float32).reshape(*shape)
        array = change_slope(array, angle_deg)
        array = array.astype(np.uint8)
        logging.debug(f"Array: {array.shape} {array.dtype}")

        imageData = QImage(array.data, width, height, QImage.Format_RGBA8888)
        imageData = imageData.rgbSwapped()
        logging.info(f"{filterLayer}, {type(filterLayer)}")
        ptr = imageData.bits()
        ptr.setsize(imageData.sizeInBytes())
        filterLayer.setPixelData(
            QByteArray(ptr.asstring()), 0, 0, imageData.width(), imageData.height()
        )

    def normalize(self, rgb: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
        return ((2 * rgb) / 255) - 1

    def denormalize(self, N_rgb: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
        return (255 * (N_rgb + 1)) / 2

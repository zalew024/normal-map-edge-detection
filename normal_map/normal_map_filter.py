import logging
import math
from krita import *
import numpy as np
import numpy.typing as npt


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
        angle_rad = math.radians(angle_deg + 90)
        logging.debug(f"Slope: {angle_deg}")

        if angle_deg >= 25:
            thr_down_RG = 76
            thr_up_RG = 180
            thr_down_B = 240
            thr_up_B = 255

        elif 15 <= angle_deg <= 25:
            thr_down_RG = 96
            thr_up_RG = 160
            thr_down_B = 248
            thr_up_B = 255

        elif 5 <= angle_deg <= 15:
            thr_down_RG = 116
            thr_up_RG = 140
            thr_down_B = 252
            thr_up_B = 255

        else:
            thr_down_RG = thr_up_RG = thr_down_B = thr_up_B = False

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

        # Extract RGB channels
        R = array[:, 0].astype(np.float32)
        logging.debug(f"R: {R.shape} {R.dtype}")

        G = array[:, 1].astype(np.float32)
        logging.debug(f"G: {G.shape} {G.dtype}")

        B = array[:, 2].astype(np.float32)
        logging.debug(f"B: {B.shape} {B.dtype}")

        # Conditions to skip certain pixels
        condition: npt.NDArray[np.bool] = (
            (R == 0)
            | (G == 0)
            | ((R == 127) & (G == 127) & (B == 254))
            | ((R == 128) & (G == 128) & (B == 255))
            | (
                (B >= thr_down_B)
                & (B <= thr_up_B)
                & (R >= thr_down_RG)
                & (R <= thr_up_RG)
                & (G >= thr_down_RG)
                & (G <= thr_up_RG)
            )
        )
        logging.debug(f"Condition: {condition.shape} {condition.dtype}")

        # Mask out the pixels that need to be processed
        mask = ~condition
        logging.debug(f"Mask: {mask.shape} {mask.dtype}")

        # Normalizing RGB values
        N_R = self.normalize(R[mask])
        logging.debug(f"N_R: {N_R.shape} {N_R.dtype}")

        N_G = self.normalize(G[mask])
        logging.debug(f"N_G: {N_G.shape} {N_G.dtype}")
        N_B = self.normalize(B[mask])

        # New blue component
        N_newB = np.sin(np.full(N_B.shape, angle_rad))
        logging.debug(f"N_newB: {N_newB.shape} {N_newB.dtype}")

        # New red and green components
        N_newR = np.sqrt(1 - (N_newB**2)) / np.sqrt((N_G / N_R) ** 2 + 1)
        logging.debug(f"N_newR: {N_newR.shape} {N_newR.dtype}")

        N_newR[N_R < 0] = -N_newR[N_R < 0]
        logging.debug(f"N_newR: {N_newR.shape} {N_newR.dtype}")

        N_newG = (N_G * N_newR) / N_R
        logging.debug(f"N_newG: {N_newG.shape} {N_newG.dtype}")

        # Denormalize and assign back
        newR = np.floor(self.denormalize(N_newR)).astype(np.uint8)
        logging.debug(f"newR: {newR.shape} {newR.dtype}")

        newG = np.floor(self.denormalize(N_newG)).astype(np.uint8)
        logging.debug(f"newG: {newG.shape} {newG.dtype}")

        newB = np.floor(self.denormalize(N_newB)).astype(np.uint8)
        logging.debug(f"newB: {newB.shape} {newB.dtype}")

        newB[newB < 128] = 128

        array[mask, 0] = newR
        array[mask, 1] = newG
        array[mask, 2] = newB
        logging.debug(f"Array: {array.shape} {array.dtype}")

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

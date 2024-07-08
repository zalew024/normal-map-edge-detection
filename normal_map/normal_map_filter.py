from krita import *
from PyQt5 import QtGui
import math


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

    def changeSlope(self, imageData, filterLayer):

        for n in range(0, imageData.width()):
            for m in range(0, imageData.height()):
                self.pixel_color = imageData.pixelColor(n, m)

                angle_deg = self.normalMapProps["slope"]
                if angle_deg >= 25:
                    thr_down_RG = 76
                    thr_up_RG = 180
                    thr_down_B = 240
                    thr_up_B = 255
                elif angle_deg <= 25 and angle_deg >= 15:
                    thr_down_RG = 96
                    thr_up_RG = 160
                    thr_down_B = 248
                    thr_up_B = 255
                elif angle_deg <= 15 and angle_deg >= 5:
                    thr_down_RG = 116
                    thr_up_RG = 140
                    thr_down_B = 252
                    thr_up_B = 255
                else:
                    thr_down_RG = thr_up_RG = thr_down_B = thr_up_B = False
                angle_rad = math.radians(angle_deg + 90)

                R, G, B = (
                    self.pixel_color.red(),
                    self.pixel_color.green(),
                    self.pixel_color.blue(),
                )
                if R == 0 or G == 0:
                    continue
                if R == 127 and G == 127 and B == 254:
                    continue
                if R == 128 and G == 128 and B == 255:
                    continue
                if B >= thr_down_B and B <= thr_up_B:
                    if R >= thr_down_RG and R <= thr_up_RG:
                        if G >= thr_down_RG and G <= thr_up_RG:
                            continue

                N_R, N_G, N_B = self.normalize(R), self.normalize(G), self.normalize(B)
                N_newB = math.sin(angle_rad)
                N_newR = math.sqrt(1 - (N_newB**2)) / math.sqrt(((N_G / N_R) ** 2) + 1)
                if N_R < 0:
                    N_newR = -N_newR
                N_newG = N_G * N_newR / N_R

                newR, newG, newB = (
                    self.denormalize(N_newR),
                    self.denormalize(N_newG),
                    self.denormalize(N_newB),
                )
                if newB < 128:
                    newB = 128

                for i, val in enumerate([newR, newG, newB]):
                    [newR, newG, newB][i] = math.floor(val)

                self.value = qRgb(int(newR), int(newG), int(newB))
                imageData.setPixel(n, m, self.value)

        imageData = imageData.rgbSwapped()

        ptr = imageData.bits()
        ptr.setsize(imageData.sizeInBytes())
        filterLayer.setPixelData(
            QByteArray(ptr.asstring()), 0, 0, imageData.width(), imageData.height()
        )

    def normalize(self, rgb):
        N_rgb = 2 * rgb / 255 - 1
        return N_rgb

    def denormalize(self, N_rgb):
        rgb = (255 * (N_rgb + 1)) / 2
        return rgb

import urllib.request
import zipfile
from tempfile import TemporaryDirectory
from pathlib import Path


PIP_WHL_URL = "https://files.pythonhosted.org/packages/e7/54/0c1c068542cee73d8863336e974fc881e608d0170f3af15d0c0f28644531/pip-24.1.2-py3-none-any.whl"


def download_and_extract_zip(url: str, destination_file: Path) -> None:
    
    with TemporaryDirectory() as temp_dir:
        temporart_zip_file = Path(temp_dir) / destination_file.name
        urllib.request.urlretrieve(url, temporart_zip_file.as_posix())
    
        with zipfile.ZipFile(temporart_zip_file.as_posix(), 'r') as zip_ref:
            zip_ref.extractall(destination_file.as_posix())


DES_PATH = Path.cwd() / "packages"
DES_PATH.mkdir(exist_ok=True, parents=True)

FILE_NAME = "pip-24.1.2-py3-none-any.whl"

download_and_extract_zip(PIP_WHL_URL, DES_PATH / FILE_NAME)




#----------------------------------------------------------------------------------------------------------


import numpy as np
import math

def changeSlope(self, imageData, filterLayer):
    width = imageData.width()
    height = imageData.height()
    
    # Extract pixel data from imageData
    ptr = imageData.bits()
    ptr.setsize(imageData.sizeInBytes())
    arr = np.frombuffer(ptr.asstring(), dtype=np.uint8).reshape((height, width, 4))

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
        thr_down_RG = thr_up_RG = thr_down_B = thr_up_B = None
    angle_rad = math.radians(angle_deg + 90)

    # Normalize
    def normalize(rgb):
        return 2 * rgb / 255 - 1

    # Denormalize
    def denormalize(N_rgb):
        return (255 * (N_rgb + 1)) / 2

    # Extract RGB channels
    R = arr[:, :, 0].astype(np.float32)
    G = arr[:, :, 1].astype(np.float32)
    B = arr[:, :, 2].astype(np.float32)

    # Conditions to skip certain pixels
    condition = ((R == 0) | (G == 0) | 
                 ((R == 127) & (G == 127) & (B == 254)) | 
                 ((R == 128) & (G == 128) & (B == 255)) |
                 ((B >= thr_down_B) & (B <= thr_up_B) &
                  (R >= thr_down_RG) & (R <= thr_up_RG) &
                  (G >= thr_down_RG) & (G <= thr_up_RG)))
    
    # Mask out the pixels that need to be processed
    mask = ~condition

    # Normalizing RGB values
    N_R = normalize(R[mask])
    N_G = normalize(G[mask])
    N_B = normalize(B[mask])

    # New blue component
    N_newB = np.sin(angle_rad)
    
    # New red and green components
    N_newR = np.sqrt(1 - N_newB**2) / np.sqrt((N_G / N_R)**2 + 1)
    N_newR[N_R < 0] = -N_newR[N_R < 0]
    N_newG = N_G * N_newR / N_R

    # Denormalize and assign back
    newR = np.floor(denormalize(N_newR)).astype(np.uint8)
    newG = np.floor(denormalize(N_newG)).astype(np.uint8)
    newB = np.floor(denormalize(N_newB)).astype(np.uint8)
    newB[newB < 128] = 128

    arr[mask, 0] = newR
    arr[mask, 1] = newG
    arr[mask, 2] = newB

    # Re-assign pixel data back to imageData
    imageData = QImage(arr.data, width, height, QImage.Format_RGBA8888).rgbSwapped()

    filterLayer.setPixelData(
        QByteArray(imageData.bits().asstring()), 0, 0, width, height
    )


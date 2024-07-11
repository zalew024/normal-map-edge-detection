import logging
from PyQt5.QtGui import QImage

import numpy as np
import numpy.typing as npt


def convert_qimage_to_numpy(image: QImage) -> npt.NDArray[np.float32]:
    """Return a numpy array containing image data from a QImage.

    QImage must be in format Format_RGBA8888.
    Numpy array will have shape (height * width, 4) and values will be in range 0-255.
    Data is copied from QImage.
    """
    width = image.width()
    height = image.height()
    logging.debug(f"Image shape (w|h): {width}x{height}")

    assert width > 0 and height > 0

    ptr = image.bits()
    assert ptr is not None

    ptr.setsize(image.sizeInBytes())
    shape = (height * width, 4)

    return np.array(ptr, copy=True, dtype=np.float32).reshape(*shape)


def convert_numpy_to_qimage(array: npt.NDArray[np.float32], image_size: tuple[int, int]) -> QImage:
    """Return a QImage containing image data from a numpy array.

    QImage will be in format Format_RGBA8888.
    Numpy array has to have shape (height * width, 4).
    """
    array = np.floor(array).astype(np.uint8)
    return QImage(array.data, *image_size, QImage.Format_RGBA8888)


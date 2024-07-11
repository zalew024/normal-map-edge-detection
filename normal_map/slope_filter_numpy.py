import logging
import math
import numpy as np
import numpy.typing as npt


def change_slope(
    image_data: npt.NDArray[np.float32], slope_angle_degrees: float
) -> npt.NDArray[np.float32]:
    angle_radians = math.radians(slope_angle_degrees + 90)
    logging.debug(f"Slope: {slope_angle_degrees} degrees")

    if slope_angle_degrees >= 25:
        threshold_down_RG = 76
        threshold_up_RG = 180
        threshold_down_B = 240
        threshold_up_B = 255

    elif 15 <= slope_angle_degrees <= 25:
        threshold_down_RG = 96
        threshold_up_RG = 160
        threshold_down_B = 248
        threshold_up_B = 255

    elif 5 <= slope_angle_degrees <= 15:
        threshold_down_RG = 116
        threshold_up_RG = 140
        threshold_down_B = 252
        threshold_up_B = 255

    else:
        threshold_down_RG = threshold_up_RG = threshold_down_B = threshold_up_B = False

    # Extract RGB channels
    r = image_data[:, 0].astype(np.float32)
    logging.debug(f"R: {r.shape} {r.dtype}")

    g = image_data[:, 1].astype(np.float32)
    logging.debug(f"G: {g.shape} {g.dtype}")

    b = image_data[:, 2].astype(np.float32)
    logging.debug(f"B: {b.shape} {b.dtype}")

    # Conditions to skip certain pixels
    condition: npt.NDArray[np.bool] = (
        (r == 0)
        | (g == 0)
        | ((r == 127) & (g == 127) & (b == 254))
        | ((r == 128) & (g == 128) & (b == 255))
        | (
            (b >= threshold_down_B)
            & (b <= threshold_up_B)
            & (r >= threshold_down_RG)
            & (r <= threshold_up_RG)
            & (g >= threshold_down_RG)
            & (g <= threshold_up_RG)
        )
    )
    logging.debug(f"Condition: {condition.shape} {condition.dtype}")

    # Mask out the pixels that need to be processed
    mask = ~condition
    logging.debug(f"Mask: {mask.shape} {mask.dtype}")

    # Normalizing RGB values
    normalized_r = normalize(r[mask])
    logging.debug(f"N_R: {normalized_r.shape} {normalized_r.dtype}")

    normalized_g = normalize(g[mask])
    logging.debug(f"N_G: {normalized_g.shape} {normalized_g.dtype}")
    normalized_b = normalize(b[mask])

    # New blue component
    new_normalized_b = np.sin(np.full(normalized_b.shape, angle_radians))
    logging.debug(f"N_newB: {new_normalized_b.shape} {new_normalized_b.dtype}")

    # New red and green components
    new_normalized_r = np.sqrt(1 - (new_normalized_b**2)) / np.sqrt(
        ((normalized_g / normalized_r) ** 2) + 1
    )
    logging.debug(f"N_newR: {new_normalized_r.shape} {new_normalized_r.dtype}")

    new_normalized_r[normalized_r < 0] = -new_normalized_r[normalized_r < 0]
    logging.debug(f"N_newR: {new_normalized_r.shape} {new_normalized_r.dtype}")

    new_normalized_g = (normalized_g * new_normalized_r) / normalized_r
    logging.debug(f"N_newG: {new_normalized_g.shape} {new_normalized_g.dtype}")

    # Denormalize and assign back to corresponding channels.
    newR = np.floor(denormalize(new_normalized_r)).astype(np.uint8)
    logging.debug(f"newR: {newR.shape} {newR.dtype}")

    newG = np.floor(denormalize(new_normalized_g)).astype(np.uint8)
    logging.debug(f"newG: {newG.shape} {newG.dtype}")

    newB = np.floor(denormalize(new_normalized_b)).astype(np.uint8)
    logging.debug(f"newB: {newB.shape} {newB.dtype}")

    newB[newB < 128] = 128

    image_data[mask, 0] = newR
    image_data[mask, 1] = newG
    image_data[mask, 2] = newB

    return image_data


def normalize(channel: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
    return ((2 * channel) / 255) - 1


def denormalize(normalized_channel: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
    return (255 * (normalized_channel + 1)) / 2

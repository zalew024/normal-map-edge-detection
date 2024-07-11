from PIL import Image
import numpy as np

from normal_map.slope_filter_numpy import change_slope
from tests.assets import ASSETS_DIRECTORY_PATH

OUTPUT_DIR = ASSETS_DIRECTORY_PATH / ".output"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


def test_dot_slope_75() -> None:
    base_image = Image.open(ASSETS_DIRECTORY_PATH / "dot" / "45" / "bump_dx.png")
    base_image_data_2_axes = np.array(base_image).reshape(-1, 4)

    new_image_data_2_axes = change_slope(base_image_data_2_axes, 75)
    new_image_data = new_image_data_2_axes.reshape(base_image.height, base_image.width, 4)

    Image.fromarray(new_image_data, mode="RGBA").save(OUTPUT_DIR / "dot_bump_dx_75.png")

    reference_image = Image.open(ASSETS_DIRECTORY_PATH / "dot" / "75" / "bump_dx.png")
    reference_image_data = np.array(reference_image)

    assert new_image_data.shape == reference_image_data.shape
    assert new_image_data.dtype == reference_image_data.dtype

    diff = (new_image_data - reference_image_data)
    diff[:, :, 3] = 255

    Image.fromarray(diff, mode="RGBA").save(
        OUTPUT_DIR / "dot_bump_dx_75_diff.png"
    )

    assert np.array_equal(new_image_data, reference_image_data)

import importlib
import importlib.util
from pathlib import Path
import platform
import sys
import urllib.request
import zipfile
from tempfile import TemporaryDirectory
from pathlib import Path
from io import StringIO


__version__ = "0.1.0"


PIP_WHL_URL = "https://files.pythonhosted.org/packages/e7/54/0c1c068542cee73d8863336e974fc881e608d0170f3af15d0c0f28644531/pip-24.1.2-py3-none-any.whl"


if platform.system() == "Windows":
    CACHE_DIR = (
        Path.home() / "AppData" / "Local" / "cache" / "krita-normal-map" / __version__
    )
else:
    CACHE_DIR = Path.home() / ".cache" / "krita-normal-map" / __version__

CACHE_DIR.mkdir(parents=True, exist_ok=True)
SITE_PACKAGES = CACHE_DIR / "site-packages"


def install_dependencies():

    with TemporaryDirectory() as temp_dir:
        temporart_zip_file = Path(temp_dir) / "pip.whl"
        urllib.request.urlretrieve(PIP_WHL_URL, temporart_zip_file.as_posix())

        with zipfile.ZipFile(temporart_zip_file.as_posix(), 'r') as zip_ref:
            zip_ref.extractall(SITE_PACKAGES.as_posix())

    importlib.invalidate_caches()
    import pip

    sys.stderr = StringIO()

    pip.main(["install", "--target", SITE_PACKAGES.as_posix(), "numpy"])
    importlib.invalidate_caches()


sys.path.insert(0, SITE_PACKAGES.as_posix())

if SITE_PACKAGES.exists():
    try:
        importlib.util.find_spec("numpy")
    except ImportError:
        install_dependencies()
else:
    install_dependencies()


import numpy as np

print(np.array([1, 2, 3]))


from krita import DockWidgetFactory, DockWidgetFactoryBase
from .normal_map_docker import NormalMapDocker

DOCKER_ID = "Normal Map (Edge Detection)"
instance = Krita.instance()
dock_widget_factory = DockWidgetFactory(
    DOCKER_ID, DockWidgetFactoryBase.DockRight, NormalMapDocker
)

instance.addDockWidgetFactory(dock_widget_factory)

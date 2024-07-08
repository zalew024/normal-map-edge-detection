import importlib
import importlib.util
import os
from pathlib import Path
import platform
import pprint
import re
import shutil
import sys
import urllib.request
import zipfile
from tempfile import TemporaryDirectory
from io import StringIO
import logging


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
SITE_PACKAGES.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, SITE_PACKAGES.as_posix())

LOG_FILE_PATH = CACHE_DIR / "krita-normal-map.log"

if LOG_FILE_PATH.exists():
    if LOG_FILE_PATH.is_file():
        LOG_FILE_PATH.unlink()
    else:
        shutil.rmtree(LOG_FILE_PATH.as_posix())


def configure_logger() -> None:
    logger = logging.getLogger()
    logger.handlers.clear()

    handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    handler.setFormatter(
        logging.Formatter("[ %(asctime)s ][ %(levelname)s ]  %(message)s")
    )

    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


configure_logger()

logging.info(f"Cache directory: {CACHE_DIR.as_posix()!r}")
logging.info(f"Site packages directory: {SITE_PACKAGES.as_posix()!r}")
logging.info(f"Added {SITE_PACKAGES.as_posix()!r} to sys.path")
logging.info(f"sys.stdin: {sys.stdin}")
logging.info(f"sys.stdout: {sys.stdout}")
logging.info(f"sys.stderr: {sys.stderr}")
logging.info(f"sys.executable: {sys.executable}")
logging.info(f"sys.path: \n{pprint.pformat(sys.path)}")
logging.info(f"sys.argv: \n{pprint.pformat(sys.argv)}")
logging.info(f"os.environ: \n{pprint.pformat(dict(os.environ))}")


def get_library_name(library_name_like: str) -> str:
    if (re_match := re.match(r"[a-zA-Z0-9_-]+", library_name_like)) is None:
        raise ValueError(
            f"Couldn't recognize library name in string: {library_name_like}"
        )

    return re_match.group(0)


def is_library_available(library_name_like: str) -> bool:
    library_name = get_library_name(library_name_like)

    try:
        return importlib.util.find_spec(library_name) is not None
    except (ImportError, ValueError):
        return False


def install(library_name_like: str) -> None:
    library_name = get_library_name(library_name_like)

    if not is_library_available(library_name):
        logging.error(f"Not available: {library_name!r}")
        import pip._internal.cli.main as pip

        stderr = sys.stderr
        stdout = sys.stdout
        stdin = sys.stdin

        sys.stderr = StringIO()
        sys.stdout = StringIO()
        sys.stdin = StringIO()

        logging.info(f"Installing: {library_name!r}")
        pip.main(
            [
                "install",
                "--no-cache-dir",
                "--disable-pip-version-check",
                "--log",
                (CACHE_DIR / f"install-{library_name}.log").as_posix(),
                "--target",
                SITE_PACKAGES.as_posix(),
                library_name_like,
            ]
        )
        configure_logger()

        sys.stderr = stderr
        sys.stdout = stdout
        sys.stdin = stdin

        logging.info("Invalidating import caches.")
        importlib.invalidate_caches()

        logging.info(f"Trying to import {library_name!r}")
        try:
            importlib.import_module(library_name)
            logging.error(f"Installed {library_name!r}")
        except Exception as e:
            logging.exception(e)

    else:
        logging.info(f"Found {library_name!r}")


def ensure_dependencies():

    if not is_library_available("pip"):
        logging.info("pip is not available.")
        with TemporaryDirectory() as temp_dir:
            temporary_zip_file = Path(temp_dir) / "pip.whl"
            logging.info("Downloading pip.")
            urllib.request.urlretrieve(PIP_WHL_URL, temporary_zip_file.as_posix())

            with zipfile.ZipFile(temporary_zip_file.as_posix(), "r") as zip_ref:
                logging.info("Installing pip.")
                zip_ref.extractall(SITE_PACKAGES.as_posix())

        logging.info("Invalidating import caches.")
        importlib.invalidate_caches()

    install("numpy==2.0.0")


ensure_dependencies()


import numpy as np


logging.info(f"numpy version: {np.__version__}")


from krita import DockWidgetFactory, DockWidgetFactoryBase
from .normal_map_docker import NormalMapDocker

DOCKER_ID = "Normal Map (Edge Detection)"
instance = Krita.instance()
dock_widget_factory = DockWidgetFactory(
    DOCKER_ID, DockWidgetFactoryBase.DockRight, NormalMapDocker
)

instance.addDockWidgetFactory(dock_widget_factory)

logging.info("Normal Map plugin initialized.")

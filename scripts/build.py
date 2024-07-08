import tarfile
import zipfile
from tempfile import TemporaryDirectory
from pathlib import Path


def repack_tar_gz_to_zip(tar_gz_path: Path, zip_path: Path) -> None:
    # Define a temporary directory to extract the tar.gz contents
    with TemporaryDirectory() as temporary_directory_str:
        temporary_directory = Path(temporary_directory_str)

        # Extract the tar.gz file
        with tarfile.open(tar_gz_path.as_posix(), "r:gz") as tar_ref:
            tar_ref.extractall(temporary_directory.as_posix())


        # Create a zip file and add the extracted files
        with zipfile.ZipFile(
            zip_path.as_posix(),
            "w",
            compression=zipfile.ZIP_DEFLATED,
            strict_timestamps=False,
        ) as zip_ref:
            # Walk through the directory
            for file_path in temporary_directory.rglob("*"):
                arcname = file_path.relative_to(temporary_directory)
                zip_ref.write(file_path.as_posix(), arcname.as_posix())


ROOT_DIR = Path(__file__).parent.parent
DIST_DIR = ROOT_DIR / "dist"


for path_tar_gz in DIST_DIR.glob("*.tar.gz"):
    path_zip = path_tar_gz.with_suffix("").with_suffix(".zip")
    repack_tar_gz_to_zip(path_tar_gz, path_zip)
    print(
        f"Repacked {path_tar_gz.relative_to(DIST_DIR).as_posix()} "
        f"to {path_zip.relative_to(DIST_DIR).as_posix()}"
    )

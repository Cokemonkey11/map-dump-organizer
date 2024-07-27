import os
import shutil
import argparse
import hashlib
import uuid
import subprocess
import logging
import sys
from pathlib import Path

import sh

sevenz = sh.Command("7z")

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)

EXTENSION_MAP: dict[str, Path] = {
    "scm": Path("scm/"),
    "scx": Path("scx/"),
    "w3m": Path("w3m/"),
    "w3x": Path("w3x/"),
    "pud": Path("pud/"),
    "bac0": Path("bac/"),
    "bac1": Path("bac/"),
    "bac2": Path("bac/"),
    "bac3": Path("bac/"),
    "bac4": Path("bac/"),
    "bac5": Path("bac/"),
    "bac6": Path("bac/"),
    "bac7": Path("bac/"),
    "bac8": Path("bac/"),
    "bac9": Path("bac/"),
    "bac10": Path("bac/"),
    "bac11": Path("bac/"),
    "bac12": Path("bac/"),
    "bac13": Path("bac/"),
    "bac14": Path("bac/"),
    "bac15": Path("bac/"),
    "bac16": Path("bac/"),
    "bac17": Path("bac/"),
    "bac18": Path("bac/"),
    "bac19": Path("bac/"),
    "trg": Path("trg/"),
    "gif": Path("img/"),
    "jpg": Path("img/"),
    "pcx": Path("img/"),
    "png": Path("img/"),
    "mp3": Path("snd/"),
    "wav": Path("snd/"),
    "htm": Path("text/"),
    "lwp": Path("text/"),
    "rtf": Path("text/"),
    "txt": Path("text/"),
    "txt~": Path("text/"),
    "doc": Path("text/"),
    "docx": Path("text/"),
    "nfo": Path("text/"),
    "pdf": Path("text/"),
    "diz": Path("text/"),
    "dds": Path("dds/"),
    "bmp": Path("bmp/"),
    "scn": Path("scn/"),
    "tga": Path("tga/"),
    "mpq": Path("unknown-mpq/"),
    "autosave": Path("unknown-mpq/"),
}

ARCHIVE_EXTENSIONS = {".zip", ".7z", ".rar", ".001"}
SEVENZ_EXTENSIONS = {".7z", ".001"}

BLACKLISTED_DIRECTORIES = set(EXTENSION_MAP.values())

DELETE_FILETYPES = {
    ".1",
    ".bsp",
    ".db",
    ".exe",
    ".ex_",
    ".img",
    ".ini",
    ".ins",
    ".iss",
    ".lev",
    ".lft",
    ".lib",
    ".log",
    ".lpl",
    ".map",
    ".pkg",
    ".rep",
    ".reg",
    ".rmf",
    ".url",
    ".nif",
    ".dll",
    ".graal",
    ".sqlite",
    ".torrent",
    ".ttf",
    ".ico",
    ".esp",
    ".ocx",
    ".chk",
    ".unt",
    ".lst",
    ".ani",
    ".dat",
    ".chr",
    ".opt",
    ".snd",
    ".rsrc",
    ".bin",
    ".xml",
}

USELESS_EXTENSIONS = {".bak", ".part"}

def get_file_metadata(file_path: Path) -> str:
    """Get file metadata using the 'file' command."""
    try:
        result = subprocess.run(['file', '-b', str(file_path)], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        logging.error(f"Error getting metadata for {file_path}: {e}")
        return ""

def compute_sha256(file_path: Path) -> str:
    """Compute and return the SHA-256 hash of the file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def move_file(file_path: Path, target_dir: Path) -> None:
    """Move file to the specified target directory, handling potential duplicates."""
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = target_dir / file_path.name

    if file_path.resolve() == destination.resolve():
        logging.info(f"'{file_path}' is already in the target directory.")
        return

    if destination.exists():
        # Compute hashes to determine if the files are identical
        source_hash = compute_sha256(file_path)
        destination_hash = compute_sha256(destination)

        if source_hash == destination_hash:
            # If files are identical, delete the source file
            file_path.unlink()
            logging.info(f"Deleted '{file_path}' as an identical file already exists at '{destination}'.")
        else:
            # If not identical, append a UUID fragment to the filename to avoid collision
            unique_suffix = uuid.uuid4().hex[:6]
            new_destination = destination.with_name(destination.stem + f"_{unique_suffix}" + destination.suffix)
            shutil.move(str(file_path), str(new_destination))
            logging.info(f"Moved '{file_path}' to '{new_destination}' to avoid overwriting existing file.")
    else:
        # No existing file, proceed with normal move
        shutil.move(str(file_path), str(destination))
        logging.info(f"Moved '{file_path}' to '{destination}'.")

def extract_archive(archive_path: Path, target_dir_base: Path) -> None:
    """Extracts archive to the specified target directory using 'unar'."""
    target_dir = target_dir_base.parent / f"{target_dir_base.name}_{str(uuid.uuid4())[:6]}"
    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        logging.info(f"Processing {archive_path}...")
        if any(archive_path.name.endswith(ext) for ext in SEVENZ_EXTENSIONS):
            sevenz("x", str(archive_path), f"-o{target_dir}")
        else:
            sh.unar("-o", str(target_dir), str(archive_path))
        logging.info(f"...Done. Deleting {archive_path}.")
        archive_path.unlink()
    except Exception as e:
        logging.error(f"Failed to process {archive_path} ({e})")

def remove_empty_directories(directory: Path) -> None:
    """Recursively removes empty directories."""
    # Walk through all directories from bottom to top.
    for root, dirs, _ in os.walk(directory, topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name

            if not any(dir_path.iterdir()):
                dir_path.rmdir()
                logging.info(f"Removed empty directory: {dir_path}")

def get_useful_extension(file_path: Path) -> str:
    """
    Get the useful extension of a file, ignoring 'useless' extensions.
    """
    while file_path.suffix.lower() in USELESS_EXTENSIONS:
        file_path = file_path.with_suffix("")
    return file_path.suffix[1:].lower()  # Remove the dot from the suffix

def process_directory(directory: Path, max_steps: int) -> None:
    """Recursively process the directory to flatten its structure."""
    steps = 0
    for root, dirs, files in os.walk(directory, topdown=True):
        logging.info(f"Processing {root}")

        # Filter out blacklisted directories.
        root_path = Path(root)
        dirs[:] = [d for d in dirs if root_path / d not in BLACKLISTED_DIRECTORIES]

        for name in files:
            steps += 1
            if steps > max_steps:
                return
            file_path = root_path / name
            if file_path.suffix.lower() in ARCHIVE_EXTENSIONS:
                extract_archive(file_path, file_path.parent / file_path.stem)
                continue

            if file_path.suffix.lower() in DELETE_FILETYPES:
                file_path.unlink()
                logging.info(f"Immediately deleting {file_path}")
                continue

            ext = get_useful_extension(file_path)
            if not ext:
                # Handle files without extensions
                metadata = get_file_metadata(file_path)
                if metadata.lower() == "data":
                    file_path.unlink()
                    logging.info(f"Deleted binary blob: {file_path}")
                elif "Apple DiskCopy" in metadata:
                    file_path.unlink()
                    logging.info(f"Deleted apple diskcopy: {file_path}")
                elif "MoPaQ (MPQ) archive" in metadata:
                    move_file(file_path, Path("unknown-mpq/"))
                    logging.info(f"Moved MoPaQ archive to unknown-mpq: {file_path}")
                elif "ascii text" in metadata.lower():
                    move_file(file_path, Path("text/"))
                    logging.info(f"Moved ASCII text file to text/: {file_path}")
                else:
                    logging.info(f"Skipping file without extension: {file_path}. Metadata: {metadata}")
                continue

            target_dir = EXTENSION_MAP.get(ext, Path("./"))
            move_file(file_path, target_dir)

    remove_empty_directories(directory)
    if not any(directory.iterdir()):
        directory.rmdir()
        logging.info(f"Removed empty directory: {directory}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flatten a directory and organize files by extension.")
    parser.add_argument("--directory", type=Path, help="Directory to process", required=True)
    parser.add_argument("--max-steps", type=int, help="Maximum number of steps to process", required=True)

    args = parser.parse_args()
    process_directory(args.directory, args.max_steps)
    logging.info("Processing completed.")
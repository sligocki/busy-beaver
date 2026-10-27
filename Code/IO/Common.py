import gzip
import io
from pathlib import Path
import zipfile


# Error for being unable to locate a given record (ex: file to short).
class RecordLocateError(Exception):
  pass


class ZipTextFileWrapper(io.TextIOBase):
  """Wrapper around a TextIOWrapper and its parent ZipFile so closing closes both."""

  def __init__(self, stream: io.TextIOWrapper, zf: zipfile.ZipFile):
    self._stream = stream
    self._zf = zf

  def close(self) -> None:
    try:
      self._stream.close()
    finally:
      if self._zf:
        self._zf.close()

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self.close()

  def __iter__(self):
    return iter(self._stream)

  def readline(self, size: int = -1) -> str:
    return self._stream.readline(size)

  def read(self, size: int = -1) -> str:
    return self._stream.read(size)

  def write(self, s: str) -> int:
    return self._stream.write(s)

  def flush(self) -> None:
    self._stream.flush()

  def seek(self, offset: int, whence: int = 0) -> int:
    return self._stream.seek(offset, whence)

  def tell(self) -> int:
    return self._stream.tell()

  def seekable(self) -> bool:
    return self._stream.seekable()

  def readable(self) -> bool:
    return self._stream.readable()

  def writable(self) -> bool:
    return self._stream.writable()

  def __getattr__(self, name):
    return getattr(self._stream, name)


class ZipBinaryFileWrapper(io.BufferedIOBase):
  """Wrapper around a binary ZipExtFile and its parent ZipFile so closing closes both."""

  def __init__(self, stream, zf: zipfile.ZipFile):
    self._stream = stream
    self._zf = zf

  def close(self) -> None:
    try:
      self._stream.close()
    finally:
      if self._zf:
        self._zf.close()

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self.close()

  def __iter__(self):
    return iter(self._stream)

  def readline(self, size: int = -1) -> bytes:
    return self._stream.readline(size)

  def read(self, size: int = -1) -> bytes:
    return self._stream.read(size)

  def readinto(self, b) -> int:
    return self._stream.readinto(b)

  def write(self, b) -> int:
    return self._stream.write(b)

  def flush(self) -> None:
    self._stream.flush()

  def seek(self, offset: int, whence: int = 0) -> int:
    return self._stream.seek(offset, whence)

  def tell(self) -> int:
    return self._stream.tell()

  def seekable(self) -> bool:
    return self._stream.seekable()

  def readable(self) -> bool:
    return self._stream.readable()

  def writable(self) -> bool:
    return self._stream.writable()

  def __getattr__(self, name):
    return getattr(self._stream, name)


def is_ignored_zip_info(info: zipfile.ZipInfo) -> bool:
  """Ignore directory entries and OS metadata files (such as __MACOSX and ._ files)."""
  if info.is_dir() or info.filename.endswith("/"):
    return True
  if info.filename.startswith("__MACOSX/") or "/__MACOSX/" in info.filename:
    return True
  p = Path(info.filename)
  if p.name.startswith("._") or p.name == ".DS_Store":
    return True
  return False


def get_zip_member(zf: zipfile.ZipFile, archive_path: Path) -> str:
  """Find the main data member in a zip archive."""
  members = [info.filename for info in zf.infolist() if not is_ignored_zip_info(info)]
  if not members:
    raise FileNotFoundError(f"No valid files found in zip archive: {archive_path}")
  if len(members) == 1:
    return members[0]

  target_name = archive_path.name.removesuffix(".zip")
  if target_name in members:
    return target_name

  basename_matches = [m for m in members if Path(m).name == target_name]
  if len(basename_matches) == 1:
    return basename_matches[0]

  return members[0]


def get_zip_write_member(archive_path: Path) -> str:
  member = archive_path.name.removesuffix(".zip")
  return member if member else "data"


def open_file(filename: Path | str, mode: str):
  """
  Unified file opener supporting plain files, .gz (gzip), and .zip files.
  Normalizes text mode when 'b' is not present.
  """
  filename = Path(filename)
  is_binary = "b" in mode
  if not is_binary and "t" not in mode:
    mode_with_type = mode[0] + "t" + mode[1:]
  else:
    mode_with_type = mode

  if ".gz" in filename.suffixes:
    return gzip.open(filename, mode_with_type)
  elif ".zip" in filename.suffixes:
    if "r" in mode:
      zf = zipfile.ZipFile(filename, "r")
      member = get_zip_member(zf, filename)
      raw = zf.open(member, "r")
      if is_binary:
        return ZipBinaryFileWrapper(raw, zf)
      else:
        return ZipTextFileWrapper(io.TextIOWrapper(raw, encoding="utf-8"), zf)
    elif "w" in mode or "a" in mode:
      zf_mode = "w" if "w" in mode else "a"
      zf = zipfile.ZipFile(filename, zf_mode, compression=zipfile.ZIP_DEFLATED)
      member = get_zip_write_member(filename)
      raw = zf.open(member, "w")
      if is_binary:
        return ZipBinaryFileWrapper(raw, zf)
      else:
        return ZipTextFileWrapper(io.TextIOWrapper(raw, encoding="utf-8"), zf)
    else:
      raise ValueError(f"Unsupported mode: {mode}")
  else:
    return open(filename, mode_with_type)

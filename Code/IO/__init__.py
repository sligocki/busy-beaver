"""Tools for working with TM IO in various formats."""

# List of names we want available upon `import IO`
from IO import Text
from IO import Proto

from IO.Timer import Timer

# TODO: Remove this as we move everything to new way:
from IO.Text import ReaderWriter as IO
from IO.Text import parse_ttable, parse_tm, load_TTable_filename

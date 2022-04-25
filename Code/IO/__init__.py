"""Tools for working with TM IO in various formats."""

# List of names we want available upon `import IO`
from IO import Text
from IO import Proto

from IO.General import Reader #, Writer
from IO.Timer import Timer

# TODO: This is just to support old code which is looking for IO.IO().
from IO.Text import ReaderWriter as IO
from IO.Text import parse_ttable, parse_tm, load_TTable_filename

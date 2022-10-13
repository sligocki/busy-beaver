"""Tools for working with TM IO in various formats."""

# List of names we want available upon `import IO`
from IO import StdText, Proto, Text, BBC

from IO.General import Reader, load_tm
from IO.StdText import parse_tm
from IO.Timer import Timer

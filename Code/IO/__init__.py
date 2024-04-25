"""Tools for working with TM IO in various formats."""

# List of names we want available upon `import IO`
from IO import StdText, Proto, Morphett, OldText, BBC

from IO.General import Reader, load_tm, get_tm
from IO.TM_Record import parse_tm
from IO.Timer import Timer

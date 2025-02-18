"""Tools for working with TM IO in various formats."""

# List of names we want available upon `import IO`
from IO import StdText, Proto, Morphett, OldText, BBC

from IO.General import Reader, Writer, load_tm, get_tm, iter_tms
from IO.TM_Record import parse_tm
from IO.Timer import Timer

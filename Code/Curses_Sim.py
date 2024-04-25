#! /usr/bin/env python3
# Visual simulation of a Turing Machine in terminal using ncurses.

import argparse
import curses
import string

from Direct_Simulator import DirectSimulator
import IO
from Macro import Turing_Machine


STATES = string.ascii_uppercase
class VisSim:
  def __init__(self, stdscr,
               tm : Turing_Machine.Simple_Machine,
               buffer_size : int,
               logfile):
    assert tm.num_symbols <= 7
    # Options
    self.buffer_size = buffer_size

    self.tm = tm
    self.stdscr = stdscr
    self.logfile = logfile

  def log(self, *args):
    print(*args, file=self.logfile)

  def reset_sim(self):
    self.sim = DirectSimulator(self.tm)
    # Clear pad
    self.pad.clear()
    self.pad.bkgd(" ", curses.color_pair(1))
    self.pad.bkgdset(" ", curses.color_pair(1))

  def pad_width(self):
    pad_height, pad_width = self.pad.getmaxyx()
    return pad_width

  def pad_height(self):
    pad_height, pad_width = self.pad.getmaxyx()
    return pad_height

  def init_pad(self):
    # Turn off blinking cursor
    curses.curs_set(False)
    assert curses.has_colors()

    # Set default colors
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_RED)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_BLUE)
    curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_MAGENTA)
    curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_YELLOW)

    # `pad` contains the "whole" visual representation of the simulation (up to
    # some step limit)
    # Then we decide which part of the pad to show based on cursor controls.
    self.pad = curses.newpad(1, 1)
    # Set "background" (default cell) to have a space and white background.
    self.pad.bkgd(" ", curses.color_pair(1))
    self.pad.bkgdset(" ", curses.color_pair(1))
    self.expand_pad(pad_height = self.buffer_size,
                    pad_width = self.buffer_size)
    self.cur_line = 0
    self.cur_pos = 0
    self.draw()

  def draw(self):
    self.log(f"draw {self.cur_line} {self.cur_pos}")
    # TM tape position at left of screen.
    left_pos = self.cur_pos - curses.COLS // 2
    # Column number in `self.pad` of left side of screen.
    left_col = left_pos + self.pos_offset
    self.log(f"refresh({self.cur_line}, {left_col}, 0, 0, {curses.LINES - 1}, {curses.COLS - 1})")
    assert 0 <= self.cur_line <= self.pad_height()
    assert 0 <= left_col <= self.pad_width()
    self.pad.refresh(self.cur_line, left_col,
                     # Full screen
                     0, 0, curses.LINES - 1, curses.COLS - 1)

  def expand_pad(self, pad_height : int, pad_width : int = None):
    """Expand pad to `limit_line_num` and draw results in."""
    self.log(f"expand_pad({pad_height}, {pad_width})")
    old_pad_height = self.pad_height()
    old_pad_width = self.pad_width()
    if not pad_width:
      pad_width = old_pad_width
    self.log(f"pad.resize({pad_height}, {pad_width})")
    self.pad.resize(pad_height, pad_width)

    if old_pad_width != pad_width:
      self.reset_sim()
      self.pos_offset = pad_width // 2

    while not self.sim.halted and self.sim.step_num < pad_height:
      self.write_tape(self.sim.step_num,
                      self.sim.tape, self.sim.state)
      self.sim.step()

  def write_tape(self, line_num : int,
                 tape, state : int):
    pos_min = tape.position - tape.index
    pos_max = pos_min + len(tape.tape)
    col_min = max(pos_min + self.pos_offset, 0)
    col_max = min(pos_max + self.pos_offset, self.pad_width() - 1)
    self.log("write_tape", line_num, col_min, col_max)
    for col_num in range(col_min, col_max + 1):
      pos = col_num - self.pos_offset
      # Color based on the symbol at this position starting from color 1.
      attr = curses.color_pair(tape.read_pos(pos) + 1)
      if pos == tape.position:
        # Convert state from integer to letter.
        text = STATES[state]
      else:
        text = " "
      self.log("Writing", line_num, col_num, repr(text), attr)
      self.pad.addstr(line_num, col_num, text, attr)

  def move_vert(self, vert_offset):
    # TODO: if self.cur_line +
    self.cur_line += vert_offset
    if self.cur_line < 0:
      self.cur_line = 0
    while self.cur_line + curses.LINES > self.sim.step_num:
      self.expand_pad(self.pad_height() + self.buffer_size)
    self.draw()

  def move_hor(self, hor_offset):
    self.cur_pos += hor_offset
    while (self.cur_pos + self.pos_offset - curses.COLS < 0 or
           self.cur_pos + self.pos_offset + self.cur_pos > self.pad_width()):
      self.expand_pad(self.pad_height(), self.pad_width() + self.buffer_size)
    self.draw()

  def input_loop(self):
    while True:
      key = self.stdscr.getkey()
      if key in ["q", "KEY_ESC"]:
        return
      elif key in ["KEY_DOWN", "KEY_ENTER", "j"]:
        # Move down 1
        self.move_vert(1)
      elif key in ["KEY_UP", "k"]:
        # Move up 1
        self.move_vert(-1)
      elif key in ["KEY_NPAGE", " "]:
        # Move down one page
        self.move_vert(curses.LINES)
      elif key in ["KEY_PPAGE", "b"]:
        # Move up one page
        self.move_vert(-curses.LINES)
      elif key in ["<"]:
        # Back to top
        self.move_vert(-self.cur_line)

      elif key in ["KEY_RIGHT", "l"]:
        # Move right 1
        self.move_hor(1)
      elif key in ["KEY_LEFT", "h"]:
        # Move left 1
        self.move_hor(-1)
      elif key in ["."]:
        # Center horizontally
        self.move_hor(-self.cur_pos)

      # TODO: Support more features:
      #  * Show TM ttable
      #  * Goto line
      else:
        # Unsupported key
        # TODO: Notify user ...
        pass

def sim(stdscr, tm, buffer_size, logfile):
  vis_sim = VisSim(stdscr, tm, buffer_size, logfile)
  # Display initial view
  vis_sim.init_pad()
  # Wait for user input and display results
  vis_sim.input_loop()

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm", help="Turing Machine or file or file:record_num (0-indexed).")
  parser.add_argument("--buffer-size", type=int, default=1000,
                      help="Number of rows and columns to buffer out to incrementally.")
  parser.add_argument("--log-file", default="curses_log.txt")
  args = parser.parse_args()

  tm = IO.get_tm(args.tm)

  with open(args.log_file, "w") as logfile:
    curses.wrapper(sim, tm, args.buffer_size, logfile)

main()

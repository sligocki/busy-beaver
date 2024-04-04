// TM Tape and configuration.

use enum_map::{enum_map, EnumMap};
use regex::Regex;
use std::fmt;
use std::str::FromStr;

use crate::count_expr::{CountExpr, CountType};
use crate::tm::{Dir, State, Symbol, Transition, TM};

// A block of TM symbols with a repetition count. Ex:
//      110^13  or  10^{x+4}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RepBlock {
    // Block is ordered so that the last element is closest to the TM head.
    pub symbols: Vec<Symbol>,
    pub rep: CountExpr,
}

#[derive(Debug, Clone)]
pub struct HalfTape(Vec<RepBlock>);

pub type Tape = EnumMap<Dir, HalfTape>;

#[derive(Debug, Clone)]
pub struct Config {
    pub tape: Tape,
    pub state: State,
    pub dir: Dir,
}

impl RepBlock {
    pub fn to_string(&self, dir: Dir) -> String {
        let mut symbols_strs: Vec<String> = self.symbols.iter().map(|s| s.to_string()).collect();
        if dir == Dir::Right {
            symbols_strs.reverse();
        }
        format!("{}^{}", symbols_strs.concat(), self.rep)
    }

    fn from_str(s: &str, dir: Dir) -> Result<Self, String> {
        let re = Regex::new(r"^(?P<symbols>[0-9]+)\^(?P<rep>.+)$").unwrap();
        let caps = re
            .captures(s)
            .ok_or(format!("Invalid rep block string {}", s))?;
        let mut symbols: Vec<Symbol> = caps["symbols"]
            .chars()
            .map(|c| c.to_digit(10).unwrap() as Symbol)
            .collect();
        if dir == Dir::Right {
            symbols.reverse();
        }
        let rep = CountExpr::from_str(&caps["rep"])?;
        Ok(RepBlock { symbols, rep })
    }
}

impl HalfTape {
    // Push a symbol onto this half-tape.
    pub fn push_symbol(&mut self, symbol: Symbol) {
        // Keep this simple. Always push symbols as their own simple block.
        // If this was a simulator, we'd prefer to merge symbols into existing blocks.
        // But since the use case is for validation, we want to keep the code as simple as possible.
        self.0.push(RepBlock {
            symbols: vec![symbol],
            rep: CountExpr::Const(1),
        });
    }

    // Pop the top symbol from this half-tape if possible.
    // Returns None if the tape is empty or if the top symbol is ambiguous (based on variable assignments).
    pub fn pop_symbol(&mut self) -> Option<Symbol> {
        match &mut self.0[..] {
            [] => None, // Cannot pop from empty tape.
            [.., RepBlock { rep, symbols }] => {
                // Split off one repetition of the block and pop the first symbol.
                // Ex: 110^13 -> 10 110^12 and we return the removed "1".

                // Try to remove one repetition (decrement the rep count).
                // If decrement fails, this is because rep is not guaranteed to be >= 0.
                // And so we have an ambiguous situation where top symbol could be
                // different things depending on the value of variables.
                // So, fail pop_symbol().
                let decr_rep = rep.decrement()?;

                // New RepBlock
                let mut new_symbols = symbols.clone();
                // We assume the order here is always that last
                let symbol = new_symbols.pop().unwrap();

                // Update the tape with decr_rep.
                if decr_rep.is_zero() {
                    self.0.pop();
                } else {
                    *rep = decr_rep;
                }

                // If there are any symbols left after popping the top one,
                // we add a new RepBlock for them.
                if !new_symbols.is_empty() {
                    self.0.push(RepBlock {
                        symbols: new_symbols,
                        rep: CountExpr::Const(1),
                    });
                }

                Some(symbol)
            }
        }
    }

    // Compare two half tapes for represent the same symbols.
    // Two tapes may be equivalent even if they are not "structurally" equal.
    // May fail for complex tapes.
    pub fn eqivalent_to(&self, other: &HalfTape) -> Option<bool> {
        let mut left = self.clone();
        let mut right = other.clone();
        while !left.0.is_empty() && !right.0.is_empty() {
            // Skip over identical blocks.
            if left.0.last().unwrap() == right.0.last().unwrap() {
                left.0.pop();
                right.0.pop();
                continue;
            }
            match (left.pop_symbol(), right.pop_symbol()) {
                (Some(l), Some(r)) => {
                    if l != r {
                        // Tapes differ.
                        return Some(false);
                    }
                }
                _ => {
                    // If either pop_symbol() failed, we cannot tell if the tapes are equivalent.
                    return None;
                }
            }
        }
        // If we reach here, one tape is empty they are only equivalent if both are empty.
        return Some(left.0.is_empty() && right.0.is_empty());
    }

    // Display the tape in a human-readable format.
    pub fn to_string(&self, dir: Dir) -> String {
        let mut block_strs: Vec<String> = self.0.iter().map(|block| block.to_string(dir)).collect();
        if dir == Dir::Right {
            block_strs.reverse();
        }
        block_strs.join(" ")
    }

    fn from_str(s: &str, dir: Dir) -> Result<Self, String> {
        let mut blocks: Vec<&str> = s.split(' ').filter(|x| !x.is_empty()).collect();
        if dir == Dir::Right {
            blocks.reverse();
        }
        let mut tape = Vec::with_capacity(blocks.len());
        for block in blocks {
            tape.push(RepBlock::from_str(block, dir)?);
        }
        Ok(HalfTape(tape))
    }
}

impl Config {
    pub fn step(&mut self, tm: &TM) -> Result<(), String> {
        let read_symbol = self
            .front_tape()
            .pop_symbol()
            .ok_or("Cannot read from tape".to_string())?;
        if let State::Run(state_in) = self.state {
            if let Transition::Transition { symbol, dir, state } = tm.trans(state_in, read_symbol) {
                self.dir = dir;
                self.state = state;
                // We write the symbol before moving (so it goes behind us).
                self.back_tape().push_symbol(symbol);
                Ok(())
            } else {
                Err("Undefined transition".to_string())
            }
        } else {
            Err("Cannot step from halt state".to_string())
        }
    }

    pub fn run(&mut self, tm: &TM, max_steps: u64) -> Result<CountType, String> {
        for n in 0..max_steps {
            self.step(tm)?;
            if self.state == State::Halt {
                return Ok(n + 1);
            }
        }
        Err("Max steps exceeded".to_string())
    }

    pub fn equivalent_to(&self, other: &Config) -> Option<bool> {
        if self.state != other.state || self.dir != other.dir {
            return Some(false);
        }
        match (
            self.tape[Dir::Left].eqivalent_to(&other.tape[Dir::Left]),
            self.tape[Dir::Right].eqivalent_to(&other.tape[Dir::Right]),
        ) {
            (Some(a), Some(b)) => Some(a && b),
            _ => None,
        }
    }

    #[inline]
    fn front_tape(&mut self) -> &mut HalfTape {
        &mut self.tape[self.dir]
    }
    #[inline]
    fn back_tape(&mut self) -> &mut HalfTape {
        &mut self.tape[!self.dir]
    }
}

impl fmt::Display for Config {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.tape[Dir::Left].to_string(Dir::Left))?;
        if self.dir == Dir::Left {
            write!(f, " <{} ", self.state)?;
        } else {
            write!(f, " {}> ", self.state)?;
        }
        write!(f, "{}", self.tape[Dir::Right].to_string(Dir::Right))
    }
}

impl FromStr for Config {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let re = Regex::new(r"^((?P<tape_left>.*) +)?(<(?P<head_left>.)|(?P<head_right>.)>)( +(?P<tape_right>.*))?$").unwrap();
        let caps = re.captures(s).ok_or("Invalid config string")?;
        let dir: Dir;
        let state: State;
        if caps.name("head_left").is_some() {
            dir = Dir::Left;
            state = State::from_str(&caps["head_left"])?;
        } else {
            dir = Dir::Right;
            state = State::from_str(&caps["head_right"])?;
        }
        fn get_default(caps: &regex::Captures, name: &str) -> String {
            caps.name(name)
                .map_or("".to_string(), |m| m.as_str().to_string())
        }
        Ok(Config {
            tape: enum_map! {
                Dir::Left => HalfTape::from_str(&get_default(&caps, "tape_left"), Dir::Left)?,
                Dir::Right => HalfTape::from_str(&get_default(&caps, "tape_right"), Dir::Right)?,
            },
            state,
            dir,
        })
    }
}

#[cfg(test)]
mod tests {
    use crate::count_expr::VarIdType;

    use super::*;

    #[test]
    fn test_parse_display() {
        for s in [
            "0^inf 10^13 01^1 <A 43^8 21^1 0^inf",
            "10^8 F> 0^inf",
            "1^138 Z> 0^2",
            " A> ",
        ] {
            assert_eq!(Config::from_str(s).unwrap().to_string(), s.to_string());
        }
    }

    #[test]
    fn test_pop_constant() {
        let mut tape = HalfTape::from_str("01^2 011^1", Dir::Right).unwrap();

        // 01^2
        assert_eq!(tape.pop_symbol(), Some(0));
        assert_eq!(tape.pop_symbol(), Some(1));
        assert_eq!(tape.pop_symbol(), Some(0));
        assert_eq!(tape.pop_symbol(), Some(1));

        // 011
        assert_eq!(tape.pop_symbol(), Some(0));
        assert_eq!(tape.pop_symbol(), Some(1));
        assert_eq!(tape.pop_symbol(), Some(1));

        assert_eq!(tape.pop_symbol(), None);
    }

    #[test]
    fn test_pop_ambiguous() {
        // Tape: 01^{x+1}
        let x: VarIdType = 13;
        let mut tape = HalfTape(vec![RepBlock {
            symbols: vec![1, 0],
            rep: CountExpr::var_plus_const(x, 1),
        }]);

        assert_eq!(tape.pop_symbol(), Some(0)); // 0 ... 1 01^x
        assert_eq!(tape.pop_symbol(), Some(1)); // 1 ... 01^x
        assert_eq!(tape.pop_symbol(), None); // 01^x is ambiguous
    }

    #[test]
    fn test_push_pop() {
        let mut tape = HalfTape(vec![]);
        tape.push_symbol(13);
        tape.push_symbol(8);
        tape.push_symbol(30);

        assert_eq!(tape.pop_symbol(), Some(30));
        assert_eq!(tape.pop_symbol(), Some(8));
        assert_eq!(tape.pop_symbol(), Some(13));
        assert_eq!(tape.pop_symbol(), None);
    }

    #[test]
    fn test_equivalent_to() {
        let tape1 = HalfTape::from_str("1^2", Dir::Right).unwrap();
        let tape2 = HalfTape::from_str("11^1", Dir::Right).unwrap();
        let tape3 = HalfTape::from_str("1^1 1^1", Dir::Right).unwrap();

        assert_eq!(tape1.eqivalent_to(&tape2), Some(true));
        assert_eq!(tape1.eqivalent_to(&tape3), Some(true));
        assert_eq!(tape2.eqivalent_to(&tape3), Some(true));

        // TODO: Add some more tests.
    }

    #[test]
    fn test_run_bb2() {
        // BB(2) champion
        let tm = TM::from_str("1RB1LB_1LA1RZ").unwrap();
        let mut config = Config::from_str("0^inf A> 0^inf").unwrap();
        // BB2 runs for 6 steps.
        assert_eq!(config.run(&tm, 10), Ok(6));
        assert_eq!(
            config.equivalent_to(&Config::from_str("0^inf 1^2 Z> 1^2 0^inf").unwrap()),
            Some(true)
        );
    }

    #[test]
    fn test_run_bb4() {
        let tm = TM::from_str("1RB1LB_1LA0LC_1RZ1LD_1RD0RA").unwrap();
        let mut config = Config::from_str("0^inf A> 0^inf").unwrap();
        // BB4 runs for 107 steps.
        assert_eq!(config.run(&tm, 1000), Ok(107));
        assert_eq!(
            config.equivalent_to(&Config::from_str("0^inf 1^1 Z> 0^1 1^12 0^inf").unwrap()),
            Some(true)
        );
    }
}

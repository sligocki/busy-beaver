// TM Tape and configuration.

use enum_map::{enum_map, EnumMap};
use regex::Regex;
use std::fmt;
use std::str::FromStr;

use crate::base::*;
use crate::count_expr::{CountOrInf, VarSubst};
use crate::tm::{Dir, State, Symbol, Transition, BLANK_SYMBOL, START_STATE, TM};

// A block of TM symbols with a repetition count. Ex:
//      110^13  or  10^{x+4}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RepBlock {
    // Block is ordered so that the last element is closest to the TM head.
    pub symbols: Vec<Symbol>,
    pub rep: CountOrInf,
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
        let rep = CountOrInf::from_str(&caps["rep"])?;
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
            rep: 1.into(),
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
                        rep: 1.into(),
                    });
                }

                Some(symbol)
            }
        }
    }

    pub fn subst(&self, var_subst: &VarSubst) -> HalfTape {
        HalfTape(
            self.0
                .iter()
                .map(|block| RepBlock {
                    symbols: block.symbols.clone(),
                    rep: block.rep.subst(var_subst),
                })
                .collect(),
        )
    }

    fn remove_empty_blocks(&mut self) {
        self.0.retain(|block| !block.rep.is_zero());
    }

    // Try to replace a subset of this tape.
    pub fn replace(&self, old: &HalfTape, new: &HalfTape) -> Result<HalfTape, String> {
        let mut curr = self.clone();
        let mut sub = old.clone();
        curr.remove_empty_blocks();
        sub.remove_empty_blocks();
        while !sub.0.is_empty() {
            if curr.0.is_empty() {
                return Err(format!(
                    "Replacement subtape is longer than current tape: {} vs. {}",
                    self.to_string(Dir::Right),
                    old.to_string(Dir::Right)
                ));
            }
            // Skip over identical blocks.
            if curr.0.last().unwrap() == sub.0.last().unwrap() {
                curr.0.pop().unwrap();
                sub.0.pop();
                continue;
            }
            match (curr.pop_symbol(), sub.pop_symbol()) {
                (Some(l), Some(r)) => {
                    if l != r {
                        return Err(format!("Tapes differ: {} != {}", l, r));
                    }
                }
                _ => {
                    // If either pop_symbol() failed, we cannot compare the tapes.
                    return Err(format!(
                        "Tapes differ: {} vs. {}",
                        curr.to_string(Dir::Right),
                        sub.to_string(Dir::Right)
                    ));
                }
            }
        }
        // sub.0.is_empty()
        // Success, we have removed `old` from the front of `curr`. Now replace it with `new`.
        // Note: The order here is that `new` is closest to the TM head which is stored at the end of the Vec.
        Ok(HalfTape(
            curr.0
                .iter()
                .cloned()
                .chain(new.0.iter().cloned())
                .collect(),
        ))
    }

    pub fn equivalent_to(&self, other: &HalfTape) -> bool {
        let empty = HalfTape(vec![]);
        if let Ok(replaced_config) = self.replace(other, &empty) {
            // self == other iff self - other == empty.
            replaced_config.0.is_empty()
        } else {
            false
        }
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
    pub fn new() -> Self {
        Config {
            // Initialize with infinite blank tape.
            tape: enum_map! {
                Dir::Left => HalfTape(vec![
                    RepBlock {
                        symbols: vec![BLANK_SYMBOL],
                        rep: CountOrInf::Infinity,
                    }
                ]),
                Dir::Right => HalfTape(vec![
                    RepBlock {
                        symbols: vec![BLANK_SYMBOL],
                        rep: CountOrInf::Infinity,
                    }
                ]),
            },
            state: State::Run(START_STATE),
            dir: Dir::Right,
        }
    }

    // Advance the TM by one step.
    // Returns an error if the TM is in a halt/undefined state or if it fell off the tape.
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

    // Run the TM for `num_steps` steps.
    // Returns an error if attempting to step from a halt/undefined state or if it falls off the tape.
    pub fn step_n(&mut self, tm: &TM, num_steps: CountType) -> Result<(), String> {
        for _ in 0..num_steps {
            self.step(tm)?;
        }
        Ok(())
    }

    pub fn subst(&self, var_subst: &VarSubst) -> Config {
        Config {
            tape: enum_map! {
                Dir::Left => self.tape[Dir::Left].subst(var_subst),
                Dir::Right => self.tape[Dir::Right].subst(var_subst),
            },
            state: self.state,
            dir: self.dir,
        }
    }

    // Check if this config contains `old` (as a complete or subconfig).
    // If so, replace `old` with `new`.
    pub fn replace(&self, old: &Config, new: &Config) -> Result<Config, String> {
        if !(self.state == old.state && self.dir == old.dir) {
            return Err(format!("State does not match: {} vs. {}", self, old));
        }
        Ok(Config {
            tape: enum_map! {
                Dir::Left => self.tape[Dir::Left].replace(&old.tape[Dir::Left], &new.tape[Dir::Left])?,
                Dir::Right => self.tape[Dir::Right].replace(&old.tape[Dir::Right], &new.tape[Dir::Right])?,
            },
            state: new.state,
            dir: new.dir,
        })
    }

    pub fn equivalent_to(&self, other: &Config) -> bool {
        self.state == other.state
            && self.dir == other.dir
            && self.tape[Dir::Left].equivalent_to(&other.tape[Dir::Left])
            && self.tape[Dir::Right].equivalent_to(&other.tape[Dir::Right])
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
        let x1 = CountOrInf::from_str("x+1").unwrap();
        let mut tape = HalfTape(vec![RepBlock {
            symbols: vec![1, 0],
            rep: x1,
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

        assert!(tape1.equivalent_to(&tape2));
        assert!(tape1.equivalent_to(&tape3));
        assert!(tape2.equivalent_to(&tape3));

        // TODO: Add some more tests.
    }

    #[test]
    fn test_replace() {
        let config = Config::from_str("0^inf 2^8 1^13 <A 0^1 1^1 0^42 0^inf").unwrap();
        let old = Config::from_str("1^13 <A 0^1 1^1").unwrap();
        let new = Config::from_str("2^10 1^2 B> 2^4 0^1").unwrap();

        let updated = config.replace(&old, &new).unwrap();
        let expected = Config::from_str("0^inf 2^8 2^10 1^2 B> 2^4 0^1 0^42 0^inf").unwrap();
        assert!(updated.equivalent_to(&expected));
    }

    #[test]
    fn test_run_bb2() {
        // BB(2) champion
        let tm = TM::from_str("1RB1LB_1LA1RZ").unwrap();
        let mut config = Config::new();
        // BB2 runs for 6 steps.
        assert_eq!(config.step_n(&tm, 6), Ok(()));
        assert!(config.equivalent_to(&Config::from_str("0^inf 1^2 Z> 1^2 0^inf").unwrap()));
    }

    #[test]
    fn test_run_bb4() {
        let tm = TM::from_str("1RB1LB_1LA0LC_1RZ1LD_1RD0RA").unwrap();
        let mut config = Config::new();
        // BB4 runs for 107 steps.
        assert_eq!(config.step_n(&tm, 107), Ok(()));
        assert!(config.equivalent_to(&Config::from_str("0^inf 1^1 Z> 0^1 1^12 0^inf").unwrap()));
    }
}

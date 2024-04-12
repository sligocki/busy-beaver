use std::fmt;
use std::ops::Not;
use std::slice::Iter;
use std::str::FromStr;

use enum_map::Enum;

pub type Symbol = u8;
pub type RunState = u8;

pub const BLANK_SYMBOL: Symbol = 0;
pub const START_STATE: RunState = 0;

#[derive(Debug, PartialEq, Eq, Copy, Clone)]
pub enum State {
    Halt,
    Run(RunState),
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Enum)]
pub enum Dir {
    Left,
    Right,
}

#[derive(Debug, Clone, Copy)]
pub enum Transition {
    UndefinedTrans,
    Transition {
        symbol: Symbol,
        dir: Dir,
        state: State,
    },
}

#[derive(Debug)]
pub struct TM {
    transitions: Vec<Vec<Transition>>,
}

#[derive(Debug)]
pub enum ParseError {
    DirectionInvalid(String),
    StateInvalidSize(String),
    StateInvalidChar(char),
    TransInvalidSize(String),
}

impl Dir {
    pub fn iter() -> Iter<'static, Dir> {
        static DIRS: [Dir; 2] = [Dir::Left, Dir::Right];
        DIRS.iter()
    }

    pub fn delta(self) -> i64 {
        match self {
            Dir::Left => -1,
            Dir::Right => 1,
        }
    }
}

impl Not for Dir {
    type Output = Dir;

    fn not(self) -> Dir {
        match self {
            Dir::Left => Dir::Right,
            Dir::Right => Dir::Left,
        }
    }
}

impl TM {
    #[inline]
    pub fn num_states(&self) -> usize {
        self.transitions.len()
    }
    #[inline]
    pub fn num_symbols(&self) -> usize {
        self.transitions[0].len()
    }

    #[inline]
    pub fn trans(&self, state_in: RunState, symb_in: Symbol) -> Transition {
        self.transitions[state_in as usize][symb_in as usize]
    }
}

// Implement the Display trait for TM types.
impl fmt::Display for Dir {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Dir::Left => write!(f, "L"),
            Dir::Right => write!(f, "R"),
        }
    }
}

impl fmt::Display for State {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            State::Halt => write!(f, "Z"),
            State::Run(state) => write!(f, "{}", (b'A' + state) as char),
        }
    }
}

impl fmt::Display for Transition {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Transition::UndefinedTrans => write!(f, "---"),
            Transition::Transition { symbol, dir, state } => {
                write!(f, "{}{}{}", symbol, dir, state)
            }
        }
    }
}

impl fmt::Display for TM {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let rows: Vec<String> = self
            .transitions
            .iter()
            .map(|row| {
                let cells: Vec<String> = row.iter().map(|trans| trans.to_string()).collect();
                cells.join("")
            })
            .collect();

        write!(f, "{}", rows.join("_"))
    }
}

// Implement parsing for TM types.
impl FromStr for Dir {
    type Err = ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "L" => Ok(Dir::Left),
            "R" => Ok(Dir::Right),
            _ => Err(ParseError::DirectionInvalid(s.to_string())),
        }
    }
}

impl FromStr for State {
    type Err = ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        if s.len() != 1 {
            return Err(ParseError::StateInvalidSize(s.to_string()));
        }
        let c = s.chars().nth(0).unwrap();
        if c == 'Z' {
            Ok(State::Halt)
        } else {
            let state = c as u8 - b'A';
            // Note: Since state is a u8, it cannot be < 0.
            if state < 26 {
                Ok(State::Run(state))
            } else {
                return Err(ParseError::StateInvalidChar(c));
            }
        }
    }
}

impl FromStr for Transition {
    type Err = ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        if s.len() != 3 {
            return Err(ParseError::TransInvalidSize(s.to_string()));
        }
        if s == "---" {
            Ok(Transition::UndefinedTrans)
        } else {
            Ok(Transition::Transition {
                symbol: s[0..=0].parse().unwrap(), // TODO: Figure out how to propagate errors of different type.
                dir: s[1..=1].parse()?,
                state: s[2..=2].parse()?,
            })
        }
    }
}

impl FromStr for TM {
    type Err = ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        fn parse_row(row_str: &str) -> Result<Vec<Transition>, ParseError> {
            let chars: Vec<char> = row_str.chars().collect();
            chars
                .chunks(3)
                .map(|chunk| {
                    let trans_str: String = chunk.iter().collect();
                    trans_str.parse()
                })
                .collect::<Result<Vec<Transition>, ParseError>>()
        }
        Ok(TM {
            transitions: s
                .split('_')
                .map(parse_row)
                .collect::<Result<Vec<Vec<Transition>>, ParseError>>()?,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_state_display() {
        assert_eq!(format!("{}", State::Halt), "Z");
        assert_eq!(format!("{}", State::Run(1)), "B");
    }

    #[test]
    fn test_parse_tm() {
        for tm_str in &[
            "1RB1LB_1LA1RZ",                      // BB(2) champion
            "1RB1LC_1RC1RB_1RD0LE_1LA1LD_1RZ0LA", // BB(5) champion
            "1RB2RA1LC_2LC1RB2RB_---2LA1LA", // "Bigfoot": https://www.sligocki.com/2023/10/16/bb-3-3-is-hard.html
            "---------_---------",
        ] {
            let tm: TM = TM::from_str(tm_str).unwrap();
            assert_eq!(tm.to_string(), String::from(*tm_str));
        }
    }
}

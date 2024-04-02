use std::fmt;
use std::slice::Iter;

use enum_map::Enum;

pub type Symbol = u8;
pub type RunState = u8;

#[derive(Debug, PartialEq, Copy, Clone)]
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
pub struct Transition {
    pub symbol: Symbol,
    pub dir: Dir,
    pub state: State,
}

#[derive(Debug)]
pub struct TM {
    transitions: Vec<Vec<Option<Transition>>>,
}

impl Dir {
    pub fn iter() -> Iter<'static, Dir> {
        static DIRS: [Dir; 2] = [Dir::Left, Dir::Right];
        DIRS.iter()
    }

    pub fn opp(self) -> Dir {
        match self {
            Dir::Left => Dir::Right,
            Dir::Right => Dir::Left,
        }
    }

    pub fn delta(self) -> i64 {
        match self {
            Dir::Left => -1,
            Dir::Right => 1,
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
    pub fn trans(&self, state_in: RunState, symb_in: Symbol) -> Option<Transition> {
        self.transitions[state_in as usize][symb_in as usize]
    }

    pub fn parse(tm_str: &str) -> TM {
        fn parse_trans(trans_str: &[u8]) -> Option<Transition> {
            if trans_str == b"---" {
                return None;
            }
            let (symb_char, dir_char, state_char) =
                if let [symb_char, dir_char, state_char] = trans_str {
                    (symb_char, dir_char, state_char)
                } else {
                    unreachable!()
                };
            Some(Transition {
                symbol: (symb_char - b'0') as Symbol,
                dir: match dir_char {
                    b'L' => Dir::Left,
                    b'R' => Dir::Right,
                    _ => panic!(),
                },
                state: match state_char {
                    b'Z' | b'H' => State::Halt,
                    x => State::Run(x - b'A'),
                },
            })
        }

        fn parse_row(row_str: &str) -> Vec<Option<Transition>> {
            row_str.as_bytes().chunks(3).map(parse_trans).collect()
        }

        TM {
            transitions: tm_str.trim().split('_').map(parse_row).collect(),
        }
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
        write!(f, "{}{}{}", self.symbol, self.dir, self.state)
    }
}

impl fmt::Display for TM {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let rows: Vec<String> = self.transitions.iter().map(|row| {
            row.iter().map(|trans| {
                match *trans {
                    None => "---".to_string(),
                    Some(trans) => trans.to_string(),
                }
            }).collect::<Vec<String>>().join("")
        }).collect();

        write!(f, "{}", rows.join("_"))
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
            "1RB1LB_1LA1RZ",                        // BB(2) champion
            "1RB1LC_1RC1RB_1RD0LE_1LA1LD_1RZ0LA",   // BB(5) champion
            "1RB2RA1LC_2LC1RB2RB_---2LA1LA",        // "Bigfoot": https://www.sligocki.com/2023/10/16/bb-3-3-is-hard.html
            "---------_---------"
        ] {
            let tm = TM::parse(tm_str);
            assert_eq!(tm.to_string(), String::from(*tm_str));
        }
    }
}
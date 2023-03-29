use std::fmt;

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

impl fmt::Display for State {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            State::Halt => write!(f, "H"),
            State::Run(state) => write!(f, "{}", (b'A' + state) as char),
        }
    }
}

impl Dir {
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
            transitions: tm_str.trim().split("_").map(parse_row).collect(),
        }
    }
}

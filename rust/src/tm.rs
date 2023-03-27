pub type Symbol = u8;
pub type RunState = u8;

#[derive(Debug)]
pub enum State {
    Halt,
    Run(RunState),
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum Dir {
    Left,
    Right,
}

pub type TransFunc = fn(RunState, Symbol) -> (Symbol, Dir, State);


impl Dir {
    pub fn opp(self) -> Dir {
        match self {
            Dir::Left => Dir::Right,
            Dir::Right => Dir::Left,
        }
    }

    pub fn delta(self) -> i32 {
        match self {
            Dir::Left => -1,
            Dir::Right => 1,
        }
    }
}

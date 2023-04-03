use enum_map::EnumMap;

use crate::tm::{Dir, State, Symbol};


pub type Count = i64;

#[derive(Debug)]
pub enum Rep<RepT> {
    Finite(RepT),
    Infinite,
}

// A block of TM symbols with a repetition count. Ex:
//      110^13  or  10^{x+4}
#[derive(Debug)]
pub struct RepBlock<RepT> {
    pub block: Vec<Symbol>,
    pub rep: Rep<RepT>,
}

pub type HalfTape<RepT> = Vec<RepBlock<RepT>>;
pub type Tape<RepT> = EnumMap<Dir, HalfTape<RepT>>;

#[derive(Debug)]
pub struct RepConfig<RepT> {
    pub tape: Tape<RepT>,
    pub state: State,
    pub dir: Dir,
}

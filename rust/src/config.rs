use enum_map::EnumMap;

use crate::tm::{Dir, State, Symbol};

pub type Count = i64;

// A block of TM symbols with a repetition count. Ex:
//      110^13  or  10^{x+4}
#[derive(Debug)]
pub struct RepBlock<RepT> {
    pub block: Vec<Symbol>,
    pub rep: RepT,
}

#[derive(Debug)]
pub struct HalfTape<RepT> {
    pub data: Vec<RepBlock<RepT>>,
    // Is this HalfTape complete (implicitly extended by 0^inf) or only a
    // limited finite portion of the tape?
    pub is_complete: bool,
}
pub type Tape<RepT> = EnumMap<Dir, HalfTape<RepT>>;

#[derive(Debug)]
pub struct RepConfig<RepT> {
    pub tape: Tape<RepT>,
    pub state: State,
    pub dir: Dir,
}

pub type RepConfigConcrete = RepConfig<Count>;

// impl RepConfigConcrete {
//     // Read 1 symbol in front of the TM head.
//     pub fn pop_one_front(&mut self) -> Symbol {
//         let front = &self.tape[self.dir];
//         match front.last_mut() {
//             None => {
//                 if (front.is_complete) {
//
//                 }
//             }
//             Some(RepBlock {
//                 rep: Rep::Infinite, ..
//             }) => {}
//             Some(RepBlock {
//                 rep: Rep::Finite(1), ..
//             }) => {
//                 self.tape[self.dir].pop();
//             }
//             Some(RepBlock {
//                 rep: Rep::Finite(rep), ..
//             }) => {
//                 *rep -= 1;
//             }
//         }
//     }
//     // Write 1 symbol behind the TM head.
//     pub fn push_one_back(&mut self, write: Symbol) {
//
//     }
//
//     pub fn front_block(&self) -> Vec<Symbol> {
//         match self.tape[self.dir].last() {
//             None => todo!(),
//             Some(x) => x.block.clone(), // TODO: Make this more efficient.
//         }
//     }
// }

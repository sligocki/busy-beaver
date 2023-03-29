use std::{fmt, ops};

use enum_map::EnumMap;

use crate::tm::{Dir, State, Symbol};

// A block of TM symbols with a repetition count. Ex:
//      110^13  or  10^{x+4}
#[derive(Debug)]
pub struct RepBlock<RepT> {
    pub block: Vec<Symbol>,
    pub rep: RepT,
}

pub type HalfTape<RepT> = Vec<RepBlock<RepT>>;

#[derive(Debug)]
pub struct Config<RepT> {
    pub tape: EnumMap<Dir, HalfTape<RepT>>,
    pub state: State,
    pub dir: Dir,
}

// An implementation of RepT for concrete repetitions (not with variables).
#[derive(Debug, Copy, Clone)]
pub enum Rep {
    Int(u64),
    Infinite,
}

impl ops::Add<Rep> for Rep {
    type Output = Rep;
    fn add(self, rhs: Rep) -> Rep {
        match (self, rhs) {
            (Rep::Infinite, _) => Rep::Infinite,
            (_, Rep::Infinite) => Rep::Infinite,
            (Rep::Int(x), Rep::Int(y)) => Rep::Int(x + y),
        }
    }
}

impl ops::AddAssign<Rep> for Rep {
    fn add_assign(&mut self, rhs: Rep) {
        *self = *self + rhs;
    }
}

impl fmt::Display for Rep {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Rep::Infinite => write!(f, "inf"),
            Rep::Int(x) => write!(f, "{}", x),
        }
    }
}

// Config where all reptitions are fixed integer values.
// Used for simulating concrete TM configs.
pub type ConfigConcrete = Config<Rep>;

impl ConfigConcrete {
    pub fn front_block(&self) -> Vec<Symbol> {
        match self.tape[self.dir].last() {
            None => todo!(),
            Some(x) => x.block.clone(), // TODO: Make this more efficient.
        }
    }

    pub fn pop_rep_front(&mut self) -> RepBlock<Rep> {
        match self.tape[self.dir].pop() {
            None => todo!(),
            Some(x) => x,
        }
    }

    pub fn drop_one_front(&mut self) {
        match self.tape[self.dir].last_mut() {
            None => todo!(),
            Some(RepBlock {
                rep: Rep::Infinite, ..
            }) => {}
            Some(RepBlock {
                rep: Rep::Int(1), ..
            }) => {
                self.tape[self.dir].pop();
            }
            Some(RepBlock {
                rep: Rep::Int(rep), ..
            }) => {
                *rep -= 1;
            }
        }
    }

    pub fn push_rep_back(&mut self, x: RepBlock<Rep>) {
        if let Some(top) = self.tape[self.dir.opp()].last_mut() {
            if top.block == x.block {
                // Merge equal blocks
                top.rep += x.rep;
                return;
            }
        }
        self.tape[self.dir.opp()].push(x);
    }
}

impl fmt::Display for RepBlock<Rep> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let block_str = self.block.iter().map(|x| x.to_string()).collect::<String>();
        write!(f, "{}^{}", block_str, self.rep)
    }
}

impl fmt::Display for ConfigConcrete {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        for x in self.tape[Dir::Left].iter() {
            write!(f, "{} ", x)?;
        }
        match self.dir {
            Dir::Left => {
                write!(f, "<{} ", self.state)?;
            }
            Dir::Right => {
                write!(f, "{}> ", self.state)?;
            }
        };
        for x in self.tape[Dir::Right].iter().rev() {
            write!(f, "{} ", x)?;
        }
        return Ok(());
    }
}

// TODO:
// pub type VariableId = u64;
//
// // Expression which is a variable plus a constant.
// //      x + const
// pub struct ExprVarPlus {
//     var: VariableId,
//     constant: Const,
// }
//
// // Expression linear in one variable.
// //      coef * x + const
// pub struct ExprLinear {
//     var: VariableId,
//     coef: Const,
//     constant: Const,
// }
//
// // An implementaion of RepT for variable repetitions (ex: 10^{x+3}).
// pub enum RepVar {
//     Concrete(Const),
//     VarPlus(ExprVarPlus),
//     Linear(ExprLinear),
// }
//
// // Config where some repetition counts may be variable.
// // Used for proving general rules.
// pub type ConfigVar = Config<RepVar>;

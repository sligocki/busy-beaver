use std::fmt;

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
    pub tape: EnumMap::<Dir, HalfTape<RepT>>,
    pub state: State,
    pub dir: Dir,
}


// An implementation of RepT for concrete repetitions (not with variables).
// TODO: Allow more complex expressions here, something like:
// pub enum Const {
//     direct: u64;
//     expo_not {
//         base: u64,
//         power: RepConcrete,
//         coef: u64,
//         const: u64,
//         denom: u64,
//     }
// }
pub type Const = u64;

// Config where all reptitions are fixed integer values.
// Used for simulating concrete TM configs.
pub type ConfigConcrete = Config<Const>;

impl ConfigConcrete {
    pub fn front_block(&self) -> Vec<Symbol> {
        match  self.tape[self.dir].last() {
            None => todo!(),
            Some(x) => x.block.clone(),  // TODO: Make this more efficient.
        }
    }

    pub fn pop_rep_front(&mut self) -> RepBlock<Const> {
        match  self.tape[self.dir].pop() {
            None => todo!(),
            Some(x) => x,
        }
    }

    pub fn drop_one_front(&mut self) {
        match  self.tape[self.dir].last_mut() {
            None => todo!(),
            Some(RepBlock { rep: 0, .. }) => { self.tape[self.dir].pop(); },
            Some(RepBlock { rep, .. }) => { *rep -= 1; },
        }
    }

    pub fn push_rep_back(&mut self, x : RepBlock<Const>) {
        if let Some(mut top) = self.tape[self.dir.opp()].last_mut() {
            if top.block == x.block {
                // Merge equal blocks
                top.rep += x.rep;
                return;
            }
        }
        self.tape[self.dir.opp()].push(x);
    }
}

impl fmt::Display for RepBlock<Const> {
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
            Dir::Left  => { write!(f, "<{} ", self.state)?; },
            Dir::Right => { write!(f, "{}> ", self.state)?; },
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

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
    pub tape: [HalfTape<RepT>; 2],
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

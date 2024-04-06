use std::fmt;
use std::str::FromStr;

use crate::base::*;

pub type VarIdType = usize;
#[derive(Debug, Clone, Copy, Eq, PartialEq)]
pub struct Variable(VarIdType);

// Representation for a broad concept of count ranging from
// Concrete binary integers to formulas that may or may not contain variables.
#[derive(Debug, Clone, Eq, PartialEq)]
pub enum CountExpr {
    // Concrete integer count
    Const(CountType),

    // TODO: Allow more complex formulas.
    VarPlus(Variable, CountType),
}

// Count that can also be infinite (for TM block repetition counts).
#[derive(Debug, Clone, Eq, PartialEq)]
pub enum CountOrInf {
    Finite(CountExpr),
    Infinity,
}

// // General mathematical function (from N->N) built up using 3 primatives. Like the Grzegorczyk hierarchy.
// //  https://en.wikipedia.org/wiki/Grzegorczyk_hierarchy
// #[derive(Debug, Clone, Eq, PartialEq)]
// pub enum Function {
//     // Identity function: Maps values to themselves.
//     Identity,
//     // Take an existing function `func` and add a constant to the result.
//     PlusConst { func: Box<Function>, add: CountType },
//     // Take an existing function `func` and apply it repeatedly `rep` times.
//     IterateConst { func: Box<Function>, rep: CountType },
//     // TODO: Maybe allow non-const iteration to allow getting to Ackermann growth.
// }

// // A mathematical formula built up from constants, variables, and functions.
// #[derive(Debug, Clone, Eq, PartialEq)]
// pub enum Formula {
//     // A formula that is a constant.
//     Const(CountType),
//     // A formula that is a single variable.
//     Var(Variable),
//     // A formula that is a function applied to another formula.
//     Func(Function, Box<Formula>),
// }

// impl Function {
//     // f.compose(g) : x -> f(g(x))
//     pub fn compose(&self, other: Function) -> Function {
//         match self {
//             Function::Identity => other,
//             Function::PlusConst { func, add } => Function::PlusConst {
//                 func: Box::new(func.compose(other)),
//                 add: *add,
//             },
//             Function::IterateConst { func, rep } => Function::IterateConst {
//                 func: Box::new(func.compose(other)),
//                 rep: *rep,
//             },
//         }
//     }
// }

// impl Formula {
//     // Decrement the count by 1 returning the result.
//     // Fails if it cannot guarantee that result will be >= 0.
//     pub fn decrement(&self) -> Option<Formula> {
//         match self {
//             Formula::Const(0) => None,
//             Formula::Const(n) => Some(Formula::Const(n - 1)),
//             Formula::Var(_) => None, // We cannot decrement a raw variable because it could be 0.
//             Formula::Func(func, val) => {
//                 match func {
//                     Function::Identity => val.decrement(),

//                     Function::PlusConst { func, add: 0 } =>
//                     // If the constant is 0, we can just decrement the subformula.
//                     {
//                         Formula::Func(*func.clone(), val.clone()).decrement()
//                     }
//                     Function::PlusConst { func, add } => Some(Formula::Func(
//                         Function::PlusConst {
//                             func: func.clone(),
//                             add: add - 1,
//                         },
//                         val.clone(),
//                     )),

//                     // If we're applying 0 iterations, that's the identity function, decrement the value.
//                     Function::IterateConst {
//                         func: _func,
//                         rep: 0,
//                     } => val.decrement(),
//                     Function::IterateConst { func, rep } => {
//                         // Unfold the outermost layer of iteration.
//                         let sub_iter = Function::IterateConst {
//                             func: func.clone(),
//                             rep: rep - 1,
//                         };
//                         Formula::Func(func.compose(sub_iter), val.clone()).decrement()
//                     }
//                 }
//             }
//         }
//     }
// }

impl CountExpr {
    pub fn is_zero(&self) -> bool {
        match self {
            CountExpr::Const(0) => true,
            _ => false,
        }
    }

    pub fn decrement(&self) -> Option<CountExpr> {
        match self {
            CountExpr::Const(0) => None, // Can't decrement 0
            CountExpr::Const(n) => Some(CountExpr::Const(n - 1)),

            CountExpr::VarPlus(_var, 0) => None, // Can't decrement, this could be <= 0.
            CountExpr::VarPlus(var, n) => Some(CountExpr::VarPlus(*var, n - 1)),
        }
    }
}

impl CountOrInf {
    pub fn is_zero(&self) -> bool {
        match self {
            CountOrInf::Finite(expr) => expr.is_zero(),
            CountOrInf::Infinity => false,
        }
    }

    pub fn decrement(&self) -> Option<CountOrInf> {
        match self {
            CountOrInf::Finite(expr) => expr.decrement().map(CountOrInf::Finite),
            CountOrInf::Infinity => Some(CountOrInf::Infinity),
        }
    }
}

impl From<CountType> for CountExpr {
    fn from(n: CountType) -> Self {
        CountExpr::Const(n)
    }
}

impl From<CountExpr> for CountOrInf {
    fn from(expr: CountExpr) -> Self {
        CountOrInf::Finite(expr)
    }
}

impl From<CountType> for CountOrInf {
    fn from(n: CountType) -> Self {
        CountOrInf::Finite(n.into())
    }
}

// Canonical names for variables. Start with n (for induction variable) and then use the rest of the alphabet.
const VAR_NAMES: &str = "nabcdefghijklmopqrstuvwxyz";
impl fmt::Display for Variable {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        if let Some(c) = VAR_NAMES.chars().nth(self.0) {
            write!(f, "{}", c)
        } else {
            write!(f, "<x{}>", self.0)
        }
    }
}

impl fmt::Display for CountExpr {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CountExpr::Const(n) => write!(f, "{}", n),
            CountExpr::VarPlus(var, n) => write!(f, "{}+{}", var, n),
        }
    }
}

impl fmt::Display for CountOrInf {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CountOrInf::Finite(expr) => write!(f, "{}", expr),
            CountOrInf::Infinity => write!(f, "inf"),
        }
    }
}

impl FromStr for Variable {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        if s.len() != 1 {
            return Err(format!("Variable must be a single character: {}", s));
        }
        match VAR_NAMES.find(s) {
            Some(id) => Ok(Variable(id)),
            // TODO: Support <x138> style variables for more than 26 variables.
            None => Err(format!("Could not parse Variable from string: {}", s)),
        }
    }
}

impl FromStr for CountExpr {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let parts = s.split('+').collect::<Vec<&str>>();
        if parts.len() == 1 {
            let n = parts[0]
                .parse::<CountType>()
                .map_err(|s| format!("Error parsing CountExpr: {}", s))?;
            return Ok(CountExpr::Const(n));
        } else if parts.len() == 2 {
            let var = parts[0].parse::<Variable>()?;
            let n = parts[1]
                .parse::<CountType>()
                .map_err(|s| format!("Error parsing CountExpr: {}", s))?;
            return Ok(CountExpr::VarPlus(var, n));
        } else {
            return Err(format!("Could not parse CountExpr from string: {}", s));
        }
    }
}

impl FromStr for CountOrInf {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "inf" => Ok(CountOrInf::Infinity),
            _ => match s.parse::<CountExpr>() {
                Ok(expr) => Ok(CountOrInf::Finite(expr)),
                Err(_) => Err(format!("Could not parse CountOrInf from string: {}", s)),
            },
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_display() {
        for s in &["0", "13", "inf", "n+0", "x+13", "k+138"] {
            assert_eq!(CountOrInf::from_str(s).unwrap().to_string(), s.to_string());
        }
    }

    #[test]
    fn test_decrement() {
        let x = Variable(13);
        assert_eq!(CountOrInf::Infinity.decrement(), Some(CountOrInf::Infinity));

        assert_eq!(CountExpr::Const(0).decrement(), None);
        assert_eq!(CountExpr::Const(1).decrement(), Some(CountExpr::Const(0)));
        assert_eq!(CountExpr::Const(13).decrement(), Some(CountExpr::Const(12)));

        assert_eq!(CountExpr::VarPlus(x, 0).decrement(), None);
        assert_eq!(
            CountExpr::VarPlus(x, 1).decrement(),
            Some(CountExpr::VarPlus(x, 0))
        );
        assert_eq!(
            CountExpr::VarPlus(x, 138).decrement(),
            Some(CountExpr::VarPlus(x, 137))
        );
    }
}

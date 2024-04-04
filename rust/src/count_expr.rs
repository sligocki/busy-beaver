use std::fmt;
use std::str::FromStr;

// Type to use for all integer counts in the system.
pub type CountType = u64;

pub type VarIdType = usize;

// Representation for a broad concept of count ranging from
// Concrete binary integers to formulas that may or may not contain variables.
#[derive(Debug, Clone, Eq, PartialEq)]
pub enum CountExpr {
    // Concrete integer count
    Const(CountType),
    // Unbounded count
    Infinity,

    // Formula applied to either a constant or variable.
    Formula(Formula),
}

// General mathematical function (from N->N) built up using 3 primatives. Like the Grzegorczyk hierarchy.
//  https://en.wikipedia.org/wiki/Grzegorczyk_hierarchy
#[derive(Debug, Clone, Eq, PartialEq)]
pub enum Function {
    // Identity function: Maps values to themselves.
    Identity,
    // Take an existing function `func` and add a constant to the result.
    PlusConst { func: Box<Function>, add: CountType },
    // Take an existing function `func` and apply it repeatedly `rep` times.
    IterateConst { func: Box<Function>, rep: CountType },
    // TODO: Maybe allow non-const iteration to allow getting to Ackermann growth.
}

// A mathematical formula built up from constants, variables, and functions.
#[derive(Debug, Clone, Eq, PartialEq)]
pub enum Formula {
    // A formula that is a constant.
    Const(CountType),
    // A formula that is a single variable.
    Var(VarIdType),
    // A formula that is a function applied to another formula.
    Func(Function, Box<Formula>),
}

impl Function {
    // f.compose(g) : x -> f(g(x))
    pub fn compose(&self, other: Function) -> Function {
        match self {
            Function::Identity => other,
            Function::PlusConst { func, add } => Function::PlusConst {
                func: Box::new(func.compose(other)),
                add: *add,
            },
            Function::IterateConst { func, rep } => Function::IterateConst {
                func: Box::new(func.compose(other)),
                rep: *rep,
            },
        }
    }
}

impl Formula {
    // Decrement the count by 1 returning the result.
    // Fails if it cannot guarantee that result will be >= 0.
    pub fn decrement(&self) -> Option<Formula> {
        match self {
            Formula::Const(0) => None,
            Formula::Const(n) => Some(Formula::Const(n - 1)),
            Formula::Var(_) => None, // We cannot decrement a raw variable because it could be 0.
            Formula::Func(func, val) => {
                match func {
                    Function::Identity => val.decrement(),

                    Function::PlusConst { func, add: 0 } =>
                    // If the constant is 0, we can just decrement the subformula.
                    {
                        Formula::Func(*func.clone(), val.clone()).decrement()
                    }
                    Function::PlusConst { func, add } => Some(Formula::Func(
                        Function::PlusConst {
                            func: func.clone(),
                            add: add - 1,
                        },
                        val.clone(),
                    )),

                    // If we're applying 0 iterations, that's the identity function, decrement the value.
                    Function::IterateConst {
                        func: _func,
                        rep: 0,
                    } => val.decrement(),
                    Function::IterateConst { func, rep } => {
                        // Unfold the outermost layer of iteration.
                        let sub_iter = Function::IterateConst {
                            func: func.clone(),
                            rep: rep - 1,
                        };
                        Formula::Func(func.compose(sub_iter), val.clone()).decrement()
                    }
                }
            }
        }
    }
}

impl CountExpr {
    pub fn var_plus_const(var: VarIdType, add: CountType) -> CountExpr {
        let plus_const = Function::PlusConst {
            func: Box::new(Function::Identity),
            add: add,
        };
        CountExpr::Formula(Formula::Func(plus_const, Box::new(Formula::Var(var))))
    }

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
            CountExpr::Infinity => Some(CountExpr::Infinity),
            CountExpr::Formula(formula) => Some(CountExpr::Formula(formula.decrement()?)),
        }
    }
}

impl fmt::Display for CountExpr {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CountExpr::Const(n) => write!(f, "{}", n),
            CountExpr::Infinity => write!(f, "inf"),
            // TODO: Implement Display for Formula
            CountExpr::Formula(_) => write!(f, "<Formula>"),
        }
    }
}

impl FromStr for CountExpr {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "inf" => Ok(CountExpr::Infinity),
            _ => match s.parse::<CountType>() {
                Ok(n) => Ok(CountExpr::Const(n)),
                Err(_) => Err(format!("Could not parse CountExpr from string: {}", s)),
            },
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_display() {
        for s in &["0", "13", "inf"] {
            assert_eq!(CountExpr::from_str(s).unwrap().to_string(), s.to_string());
        }
    }

    #[test]
    fn test_decrement() {
        assert_eq!(CountExpr::Const(0).decrement(), None);
        assert_eq!(CountExpr::Const(1).decrement(), Some(CountExpr::Const(0)));
        assert_eq!(CountExpr::Const(13).decrement(), Some(CountExpr::Const(12)));
        assert_eq!(CountExpr::Infinity.decrement(), Some(CountExpr::Infinity));

        // TODO: Test Function examples!
        // assert_eq!(CountExpr::Formula(Function::PlusConst { func: Function::Identity, add: 13 }).decrement(),
        //            Ok(CountExpr::Formula(Function::PlusConst { func: Function::Identity, add: 12 })));
    }
}

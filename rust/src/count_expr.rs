use std::collections::{BTreeMap, HashMap};
use std::str::FromStr;

use crate::base::*;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct Variable(usize);
pub type VarSubst = HashMap<Variable, CountExpr>;

// Representation for a broad concept of count ranging from
// Concrete binary integers to formulas that may or may not contain variables.
#[derive(Debug, Clone, Eq, PartialEq)]
pub enum CountExpr {
    // Sum of variables and a constant.
    // VarSum({x: 2, y: 1}, 3) == 2x + y + 3
    VarSum {
        // Use an ordered map to ensure deterministic order of variables.
        var_counts: BTreeMap<Variable, CountType>,
        constant: CountType,
    },
    // TODO: Allow more complex formulas.
}

// Count that can also be infinite (for TM block repetition counts).
#[derive(Debug, Clone, Eq, PartialEq)]
pub enum CountOrInf {
    Finite(CountExpr),
    Infinity,
}

impl Variable {
    pub const fn new(id: usize) -> Variable {
        Variable(id)
    }
}

impl CountExpr {
    #[inline]
    pub fn is_zero(&self) -> bool {
        let CountExpr::VarSum {
            var_counts: _,
            constant,
        } = self;
        *constant == 0 && self.is_const()
    }

    #[inline]
    pub fn is_const(&self) -> bool {
        let CountExpr::VarSum {
            var_counts,
            constant: _,
        } = self;
        var_counts.is_empty()
    }

    pub fn decrement(&self) -> Option<CountExpr> {
        let CountExpr::VarSum {
            var_counts,
            constant,
        } = self;
        let new_constant = constant.checked_sub(1)?;
        Some(CountExpr::VarSum {
            var_counts: var_counts.clone(),
            constant: new_constant,
        })
    }

    pub fn subst(&self, var_subst: &VarSubst) -> CountExpr {
        let CountExpr::VarSum {
            var_counts,
            constant,
        } = self;
        let mut new_expr = CountExpr::from(*constant);
        for (x, count) in var_counts {
            // TODO: Implement scalar mult to avoid repeated addition.
            for _ in 0..*count {
                new_expr += match var_subst.get(x) {
                    Some(expr) => expr.clone(),
                    None => CountExpr::from(*x),
                };
            }
        }
        new_expr
    }

    // Attempt subtraction (self - other).
    // Return None if the result is not guaranteed >= 0.
    pub fn checked_sub(&self, other: &CountExpr) -> Option<CountExpr> {
        let CountExpr::VarSum {
            var_counts: xs1,
            constant: n1,
        } = self;
        let CountExpr::VarSum {
            var_counts: xs2,
            constant: n2,
        } = other;
        let n = n1.checked_sub(*n2)?;
        // Remove xs2 from xs1.
        let mut xs = xs1.clone();
        for (x, count2) in xs2 {
            let count1 = xs.remove(x)?;
            let diff = count1.checked_sub(*count2)?;
            if diff > 0 {
                xs.insert(*x, diff);
            }
        }
        Some(CountExpr::VarSum {
            var_counts: xs,
            constant: n,
        })
    }
}

impl CountOrInf {
    #[inline]
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

    pub fn subst(&self, var_subst: &VarSubst) -> CountOrInf {
        match self {
            CountOrInf::Finite(expr) => CountOrInf::Finite(expr.subst(var_subst)),
            CountOrInf::Infinity => CountOrInf::Infinity,
        }
    }

    // Attempt subtraction (self - other).
    // Return None if the result is not guaranteed >= 0.
    // Note: We consider n - n = 0 for all n (including inf - inf = 0).
    pub fn checked_sub(&self, other: &CountOrInf) -> Option<CountOrInf> {
        match (self, other) {
            (CountOrInf::Finite(expr), CountOrInf::Finite(other_expr)) => {
                expr.checked_sub(other_expr).map(CountOrInf::Finite)
            }
            // inf - finite == inf
            // This is even true for variables: inf - x == inf since these variables are always finite.
            (CountOrInf::Infinity, CountOrInf::Finite(_)) => Some(CountOrInf::Infinity),
            // inf - inf == 0
            (CountOrInf::Infinity, CountOrInf::Infinity) => Some(0.into()),
            // finite - inf  fails
            (CountOrInf::Finite(_), CountOrInf::Infinity) => None,
        }
    }
}

impl std::ops::AddAssign for CountExpr {
    fn add_assign(&mut self, other: CountExpr) {
        let CountExpr::VarSum {
            var_counts,
            constant,
        } = self;
        let CountExpr::VarSum {
            var_counts: other_var_counts,
            constant: other_constant,
        } = other;

        *constant += other_constant;
        for (x, count) in other_var_counts {
            var_counts
                .entry(x)
                .and_modify(|c| *c += count)
                .or_insert(count);
        }
    }
}

impl std::ops::Add for CountExpr {
    type Output = CountExpr;

    fn add(self, other: CountExpr) -> CountExpr {
        let mut new_expr = self.clone();
        new_expr += other;
        new_expr
    }
}

impl std::ops::Add for CountOrInf {
    type Output = CountOrInf;

    fn add(self, other: CountOrInf) -> CountOrInf {
        match (self, other) {
            (CountOrInf::Finite(expr), CountOrInf::Finite(other_expr)) => {
                CountOrInf::Finite(expr + other_expr)
            }
            _ => CountOrInf::Infinity,
        }
    }
}

impl std::ops::AddAssign for CountOrInf {
    fn add_assign(&mut self, other: CountOrInf) {
        *self = self.clone() + other;
    }
}

impl From<CountType> for CountExpr {
    fn from(n: CountType) -> Self {
        CountExpr::VarSum {
            var_counts: BTreeMap::new(),
            constant: n,
        }
    }
}

impl From<Variable> for CountExpr {
    fn from(var: Variable) -> Self {
        CountExpr::VarSum {
            var_counts: [(var, 1)].iter().cloned().collect(),
            constant: 0,
        }
    }
}

impl From<CountType> for CountOrInf {
    fn from(n: CountType) -> Self {
        CountOrInf::Finite(n.into())
    }
}

// Canonical names for variables. Start with n (for induction variable) and then use the rest of the alphabet.
const VAR_NAMES: &str = "nabcdefghijklmopqrstuvwxyz";
impl std::fmt::Display for Variable {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        if let Some(c) = VAR_NAMES.chars().nth(self.0) {
            write!(f, "{}", c)
        } else {
            write!(f, "<x{}>", self.0)
        }
    }
}

impl std::fmt::Display for CountExpr {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let CountExpr::VarSum {
            var_counts,
            constant,
        } = self;
        for (var, count) in var_counts {
            // TODO: Replace with scalar multiplication.
            for _ in 0..*count {
                write!(f, "{}+", var)?;
            }
        }
        write!(f, "{}", constant)
    }
}

impl std::fmt::Display for CountOrInf {
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
        let mut expr = CountExpr::from(0);
        let parts = s.split('+').collect::<Vec<&str>>();
        for part in parts {
            if let Ok(n) = part.parse::<CountType>() {
                expr += CountExpr::from(n);
            } else if let Ok(var) = part.parse::<Variable>() {
                expr += CountExpr::from(var);
            } else {
                return Err(format!(
                    "Could not parse Variable or integer from string: {}",
                    part
                ));
            }
        }
        Ok(expr)
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
        for s in ["0", "13", "inf", "n+0", "x+13", "k+138", "a+b+7"] {
            assert_eq!(CountOrInf::from_str(s).unwrap().to_string(), s.to_string());
        }
    }

    #[test]
    fn test_equal() {
        assert_eq!(CountOrInf::Infinity, CountOrInf::Infinity);
        assert_eq!(CountOrInf::from(13), CountOrInf::from(13));
        assert_eq!(
            CountOrInf::from_str("x").unwrap(),
            CountOrInf::from_str("x").unwrap()
        );
        assert_eq!(
            (CountOrInf::from_str("x").unwrap() + CountOrInf::from(13)),
            CountOrInf::from_str("x+13").unwrap()
        );
        assert_eq!(
            CountOrInf::from_str("s+n+l+8").unwrap(),
            CountOrInf::from_str("4+l+s+n+4").unwrap()
        );

        assert_ne!(CountOrInf::Infinity, CountOrInf::from(13));
        assert_ne!(CountOrInf::from(13), CountOrInf::from(14));
        assert_ne!(
            CountOrInf::from_str("x").unwrap(),
            CountOrInf::from_str("y").unwrap()
        );
        assert_ne!(
            CountOrInf::from_str("x+x").unwrap(),
            CountOrInf::from_str("x").unwrap()
        );
        assert_ne!(
            CountOrInf::from_str("x+13").unwrap(),
            CountOrInf::from_str("x+14").unwrap()
        );
    }

    #[test]
    fn test_decrement() {
        assert_eq!(CountOrInf::Infinity.decrement(), Some(CountOrInf::Infinity));

        assert_eq!(CountExpr::from(0).decrement(), None);
        assert_eq!(CountExpr::from(1).decrement(), Some(CountExpr::from(0)));
        assert_eq!(CountExpr::from(13).decrement(), Some(CountExpr::from(12)));

        assert_eq!(CountExpr::from_str("x").unwrap().decrement(), None);
        assert_eq!(
            CountExpr::from_str("x+1").unwrap().decrement(),
            Some(CountExpr::from_str("x").unwrap())
        );
        assert_eq!(
            CountExpr::from_str("x+138").unwrap().decrement(),
            Some(CountExpr::from_str("x+137").unwrap())
        );
    }

    #[test]
    fn test_checked_sub() {
        assert_eq!(
            CountOrInf::from(138).checked_sub(&CountOrInf::from(0)),
            Some(CountOrInf::from(138))
        );
        assert_eq!(
            CountOrInf::from(13).checked_sub(&CountOrInf::from(13)),
            Some(CountOrInf::from(0))
        );
        assert_eq!(
            CountOrInf::from(13).checked_sub(&CountOrInf::from(14)),
            None
        );
        assert_eq!(
            CountOrInf::from(13).checked_sub(&CountOrInf::Infinity),
            None
        );
        assert_eq!(
            CountOrInf::Infinity.checked_sub(&CountOrInf::from(13)),
            Some(CountOrInf::Infinity)
        );
        assert_eq!(
            CountOrInf::Infinity.checked_sub(&CountOrInf::from_str("n").unwrap()),
            Some(CountOrInf::Infinity)
        );
        assert_eq!(
            CountOrInf::Infinity.checked_sub(&CountOrInf::Infinity),
            Some(CountOrInf::from(0))
        );
        assert_eq!(
            CountOrInf::from_str("x+13")
                .unwrap()
                .checked_sub(&CountOrInf::from(13)),
            Some(CountOrInf::from_str("x").unwrap())
        );
        assert_eq!(
            CountOrInf::from_str("x+13")
                .unwrap()
                .checked_sub(&CountOrInf::from(14)),
            None
        );
        assert_eq!(
            CountOrInf::from_str("x+13")
                .unwrap()
                .checked_sub(&CountOrInf::from_str("x+11").unwrap()),
            Some(CountOrInf::from(2))
        );
        assert_eq!(
            CountOrInf::from_str("x+x+13")
                .unwrap()
                .checked_sub(&CountOrInf::from_str("x").unwrap()),
            Some(CountOrInf::from_str("x+13").unwrap())
        );
        assert_eq!(
            CountOrInf::from_str("x+x+13")
                .unwrap()
                .checked_sub(&CountOrInf::from_str("x+x").unwrap()),
            Some(CountOrInf::from(13))
        );
        assert_eq!(
            CountOrInf::from_str("a+d+n")
                .unwrap()
                .checked_sub(&CountOrInf::from_str("a+n").unwrap()),
            Some(CountOrInf::from_str("d").unwrap())
        );
        assert_eq!(
            CountOrInf::from_str("a+d+n")
                .unwrap()
                .checked_sub(&CountOrInf::from_str("a+f").unwrap()),
            None
        );
    }

    #[test]
    fn test_add_sub() {
        let expr_strs = [
            "0", "13", "x", "x+13", "x+138", "a+b+7", "n", "n+1", "a+n+1", "x+n", "b+x",
        ];
        let exprs: Vec<CountExpr> = expr_strs
            .iter()
            .map(|s| CountExpr::from_str(s).unwrap())
            .collect();
        for a in &exprs {
            for b in &exprs {
                // a + b - b == a
                assert_eq!(
                    (a.clone() + b.clone()).checked_sub(&b),
                    Some(a.clone()),
                    "a: {}, b: {}",
                    a,
                    b
                );
            }
        }
    }

    #[test]
    fn test_not_add_sub() {
        // It is *not* always true that a + b - b == a.
        // Ex: x + inf - inf == 0 !
        let x = CountOrInf::from_str("x").unwrap();
        assert_eq!(
            (x + CountOrInf::Infinity).checked_sub(&CountOrInf::Infinity),
            Some(CountOrInf::from(0))
        );
        assert_eq!(
            (CountOrInf::from(813) + CountOrInf::Infinity).checked_sub(&CountOrInf::Infinity),
            Some(CountOrInf::from(0))
        );
    }
}

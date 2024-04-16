use std::collections::{BTreeMap, HashMap};
use std::str::FromStr;

use regex::Regex;
use thiserror::Error;

use crate::base::CountType;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct Variable(usize);
pub type VarSubst = VarSubstGen<CountExpr>;
type VarSumSubst = VarSubstGen<VarSum>;

#[derive(Debug, Clone)]
pub struct VarSubstGen<T: Clone>(HashMap<Variable, T>);

// Simple algebraic expression which is just a sum of variables and constants.
#[derive(Debug, Clone, Eq, PartialEq)]
pub struct VarSum {
    // Implementation detail: {x: 2, y: 1}  -->  2x + y
    var_counts: BTreeMap<Variable, CountType>,
    constant: CountType,
}

// Function is represented by `bound_var` and `expr`.
// Value of `f(n)` is equivalent to `expr.subst({bound_var: n})`.
// TODO: Support function composition.
#[derive(Debug, Clone, Eq, PartialEq)]
pub struct Function {
    pub bound_var: Variable,
    pub expr: CountExpr,
}

// Complex algebraic expression represented as an unexpended formula.
// Specifically repeated application of a function.
// Value is `func^num_repeats(base)`.
#[derive(Debug, Clone, Eq, PartialEq)]
pub struct RecursiveExpr {
    pub func: Box<Function>,
    pub num_repeats: Box<CountExpr>,
    pub base: Box<CountExpr>,
}

// Representation for a broad concept of count ranging from
// Concrete binary integers to formulas that may or may not contain variables.
#[derive(Debug, Clone, Eq, PartialEq)]
pub enum CountExpr {
    // Simple sum of variables and constants.
    // We support addition and subtraction on these.
    VarSum(VarSum),
    // RecursiveExpr expression. We do not support addition or subtraction on these, ex.
    RecursiveExpr(RecursiveExpr),
}

// Count that can also be infinite (for TM block repetition counts).
#[derive(Debug, Clone, Eq, PartialEq)]
pub enum CountOrInf {
    Finite(CountExpr),
    Infinity,
}

#[derive(Error, Debug)]
pub enum VarSubstError {}

#[derive(Error, Debug)]
pub enum ParseError {
    #[error("Variable name must be exactly one character: {0}")]
    VariableInvalidSize(String),
    #[error("Invalid variable character: {0}")]
    VariableInvalidChar(char),
    #[error("Failed to parse count expression: {0}")]
    CountRegexFailed(String),
}

impl<T: Clone> VarSubstGen<T> {
    #[inline]
    pub fn single(x: Variable, expr: T) -> Self {
        let mut subst = Self::default();
        subst.insert(x, expr);
        subst
    }

    #[inline]
    pub fn get(&self, x: &Variable) -> Option<&T> {
        self.0.get(x)
    }

    #[inline]
    pub fn insert(&mut self, x: Variable, expr: T) {
        self.0.insert(x, expr);
    }

    // Return new substitution with x removed.
    // Useful for substituting inside a function where x is bound.
    pub fn without(&self, x: &Variable) -> Self {
        let mut new_subst: Self = self.clone();
        new_subst.0.remove(x);
        new_subst
    }
}

impl<T: Clone> Default for VarSubstGen<T> {
    fn default() -> Self {
        VarSubstGen(HashMap::new())
    }
}

impl TryFrom<&VarSubst> for VarSumSubst {
    type Error = ();

    fn try_from(var_subst: &VarSubst) -> Result<Self, Self::Error> {
        let mut new_subst = VarSumSubst::default();
        for (x, expr) in var_subst.0.iter() {
            if let CountExpr::VarSum(var_sum) = expr {
                new_subst.0.insert(*x, var_sum.clone());
            } else {
                return Err(());
            }
        }
        Ok(new_subst)
    }
}

impl Variable {
    pub const fn new(id: usize) -> Variable {
        Variable(id)
    }
}

impl Default for Variable {
    fn default() -> Variable {
        Variable(0)
    }
}

impl VarSum {
    #[inline]
    pub fn is_zero(&self) -> bool {
        self.constant == 0 && self.is_const()
    }

    #[inline]
    pub fn is_const(&self) -> bool {
        self.var_counts.is_empty()
    }

    pub fn decrement(&self) -> Option<VarSum> {
        let new_constant = self.constant.checked_sub(1)?;
        Some(VarSum {
            var_counts: self.var_counts.clone(),
            constant: new_constant,
        })
    }

    pub fn subst(&self, var_subst: &VarSubst) -> CountExpr {
        let mut new_var_sum = VarSum::from(self.constant);
        // Set of substitutions whose values are RecurisveExprs.
        // We must process those seperately below.
        let mut rec_subst: Vec<(Variable, u64, RecursiveExpr)> = Vec::new();
        for (x, count) in self.var_counts.iter() {
            match var_subst.0.get(&x) {
                // VarSums can be substituted directly.
                Some(CountExpr::VarSum(expr)) => {
                    new_var_sum += expr.clone() * *count;
                }
                // If variable is missing, we leave it as before.
                None => {
                    new_var_sum += VarSum::from(*x) * *count;
                }
                // RecursiveExprs are saved for later.
                Some(CountExpr::RecursiveExpr(expr)) => {
                    rec_subst.push((*x, *count, expr.clone()));
                }
            };
        }
        let mut expr = CountExpr::VarSum(new_var_sum);
        for (x, count, rec_expr) in rec_subst.iter() {
            unimplemented!("RecursiveExpr substitution not implemented yet.");
            // assert!(!expr.unbound_vars().contains(x));
        }
        expr
    }

    // Attempt subtraction (self - other).
    // Return None if the result is not guaranteed >= 0.
    pub fn checked_sub(&self, other: &VarSum) -> Option<VarSum> {
        let n = self.constant.checked_sub(other.constant)?;
        // Remove other.var_counts from self.var_counts
        let mut xs = self.var_counts.clone();
        for (x, count2) in other.var_counts.iter() {
            let count1 = xs.remove(&x)?;
            let diff = count1.checked_sub(*count2)?;
            if diff > 0 {
                xs.insert(*x, diff);
            }
        }
        Some(VarSum {
            var_counts: xs,
            constant: n,
        })
    }
}

impl Function {
    pub fn plus(n: CountType) -> Function {
        let var = Variable::default();
        Function {
            bound_var: var,
            expr: CountExpr::var_plus(var, n),
        }
    }

    pub fn affine(m: CountType, b: CountType) -> Function {
        let var = Variable::default();
        Function {
            bound_var: var,
            expr: CountExpr::VarSum(VarSum {
                var_counts: [(var, m)].iter().cloned().collect(),
                constant: b,
            }),
        }
    }

    pub fn apply(&self, val: CountExpr) -> CountExpr {
        // TODO: Deal with unwrap ...
        self.expr
            .subst(&VarSubst::single(self.bound_var, val))
            .unwrap()
    }

    // Compose two functions (applying the first, first).
    // f.compose(g): x -> g(f(x))
    pub fn compose(&self, g: &Function) -> Function {
        let f = self.clone();
        Function {
            // x
            bound_var: f.bound_var,
            // g(y)  with y <- f(x)
            expr: g.apply(f.expr),
        }
    }
}

impl RecursiveExpr {
    pub fn subst(&self, var_subst: &VarSubst) -> Result<RecursiveExpr, VarSubstError> {
        let new_func = Function {
            bound_var: self.func.bound_var,
            expr: self
                .func
                .expr
                // Ignore the bound variable in the substitution!
                .subst(&var_subst.without(&self.func.bound_var))?,
        };
        Ok(RecursiveExpr {
            func: Box::new(new_func),
            num_repeats: Box::new(self.num_repeats.subst(var_subst)?),
            base: Box::new(self.base.subst(var_subst)?),
        })
    }
}

impl CountExpr {
    // Convenience function for: x + n
    #[inline]
    pub fn var_plus(x: Variable, n: CountType) -> CountExpr {
        CountExpr::VarSum(VarSum {
            var_counts: [(x, 1)].iter().cloned().collect(),
            constant: n,
        })
    }

    pub fn is_zero(&self) -> bool {
        match self {
            CountExpr::VarSum(expr) => expr.is_zero(),
            CountExpr::RecursiveExpr(_) => false,
        }
    }

    pub fn decrement(&self) -> Option<CountExpr> {
        match self {
            CountExpr::VarSum(expr) => expr.decrement().map(CountExpr::VarSum),
            CountExpr::RecursiveExpr(_) => None,
        }
    }

    pub fn subst(&self, var_subst: &VarSubst) -> Result<CountExpr, VarSubstError> {
        match self {
            CountExpr::VarSum(expr) => Ok(expr.subst(var_subst)),
            CountExpr::RecursiveExpr(expr) => expr.subst(var_subst).map(CountExpr::RecursiveExpr),
        }
    }

    // Attempt to add (self + other). Fails if either is an opaque RecursiveExpr.
    pub fn checked_add(&self, other: &CountExpr) -> Option<CountExpr> {
        match (self, other) {
            (CountExpr::VarSum(expr), CountExpr::VarSum(other_expr)) => {
                Some(CountExpr::VarSum(expr.clone() + other_expr.clone()))
            }
            _ => None,
        }
    }

    // Attempt subtraction (self - other).
    // Return None if the result is not guaranteed >= 0 (or if working with opaque RecursiveExpr).
    pub fn checked_sub(&self, other: &CountExpr) -> Option<CountExpr> {
        // n - n = 0 for all n (even opaque RecursiveExpr).
        if self == other {
            return Some(CountExpr::from(0));
        }

        match (self, other) {
            (CountExpr::VarSum(expr), CountExpr::VarSum(other_expr)) => {
                expr.checked_sub(other_expr).map(CountExpr::VarSum)
            }
            _ => None,
        }
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

    pub fn subst(&self, var_subst: &VarSubst) -> Result<CountOrInf, VarSubstError> {
        match self {
            CountOrInf::Finite(expr) => expr.subst(var_subst).map(CountOrInf::Finite),
            CountOrInf::Infinity => Ok(CountOrInf::Infinity),
        }
    }

    pub fn checked_add(&self, other: &CountOrInf) -> Option<CountOrInf> {
        match (self, other) {
            (CountOrInf::Finite(expr), CountOrInf::Finite(other_expr)) => {
                expr.checked_add(other_expr).map(CountOrInf::Finite)
            }
            // inf + x = x + inf = inf + inf = inf
            _ => Some(CountOrInf::Infinity),
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

impl std::ops::AddAssign for VarSum {
    fn add_assign(&mut self, other: VarSum) {
        self.constant += other.constant;
        for (x, count) in other.var_counts {
            self.var_counts
                .entry(x)
                .and_modify(|c| *c += count)
                .or_insert(count);
        }
    }
}

impl std::ops::Add for VarSum {
    type Output = VarSum;

    fn add(self, other: VarSum) -> VarSum {
        let mut new_expr = self.clone();
        new_expr += other;
        new_expr
    }
}

impl std::ops::Mul<CountType> for VarSum {
    type Output = VarSum;

    fn mul(self, n: CountType) -> VarSum {
        match n {
            0 => VarSum::from(0),
            1 => self,
            _ => VarSum {
                var_counts: self
                    .var_counts
                    .into_iter()
                    .map(|(x, c)| (x, c * n))
                    .collect(),
                constant: self.constant * n,
            },
        }
    }
}

impl From<CountType> for VarSum {
    #[inline]
    fn from(n: CountType) -> Self {
        VarSum {
            var_counts: BTreeMap::new(),
            constant: n,
        }
    }
}

impl From<Variable> for VarSum {
    #[inline]
    fn from(var: Variable) -> Self {
        VarSum {
            var_counts: [(var, 1)].iter().cloned().collect(),
            constant: 0,
        }
    }
}

impl From<CountType> for CountExpr {
    #[inline]
    fn from(n: CountType) -> Self {
        CountExpr::VarSum(VarSum::from(n))
    }
}

impl From<Variable> for CountExpr {
    #[inline]
    fn from(var: Variable) -> Self {
        CountExpr::VarSum(VarSum::from(var))
    }
}

impl From<CountType> for CountOrInf {
    #[inline]
    fn from(n: CountType) -> Self {
        CountOrInf::Finite(n.into())
    }
}

impl From<Variable> for CountOrInf {
    #[inline]
    fn from(var: Variable) -> Self {
        CountOrInf::Finite(var.into())
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

impl std::fmt::Display for VarSum {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let mut terms: Vec<String> = self
            .var_counts
            .iter()
            .map(|(var, count)| {
                if *count != 1 {
                    format!("{}{}", count, var)
                } else {
                    format!("{}", var)
                }
            })
            .collect();
        if self.constant != 0 {
            terms.push(self.constant.to_string());
        }
        if terms.is_empty() {
            write!(f, "0")
        } else {
            write!(f, "{}", terms.join("+"))
        }
    }
}

impl std::fmt::Display for RecursiveExpr {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        // TODO: Implement this.
        write!(f, "???")
    }
}

impl std::fmt::Display for CountExpr {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CountExpr::VarSum(expr) => write!(f, "{}", expr),
            CountExpr::RecursiveExpr(expr) => write!(f, "{}", expr),
        }
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
    type Err = ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        if s.len() != 1 {
            return Err(ParseError::VariableInvalidSize(s.to_string()));
        }
        let c = s.chars().nth(0).unwrap();
        match VAR_NAMES.find(c) {
            Some(id) => Ok(Variable(id)),
            // TODO: Support <x138> style variables for more than 26 variables.
            None => Err(ParseError::VariableInvalidChar(c)),
        }
    }
}

impl FromStr for VarSum {
    type Err = ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let mut expr = VarSum::from(0);
        let parts = s.split('+').collect::<Vec<&str>>();
        for part in parts {
            // Parse things like "12", "x", "2n", "4a" using regular expressions:
            let re = Regex::new(r"^(?P<coef>\d+)?(?P<var>[a-z])|(?P<const>\d+)$").unwrap();
            let caps = re
                .captures(part)
                .ok_or(ParseError::CountRegexFailed(part.to_string()))?;

            if let Some(var) = caps.name("var") {
                let var_expr = VarSum::from(Variable::from_str(var.as_str())?);
                // coefficient defaults to 1 if not present.
                let coef: CountType = caps.name("coef").map_or(1, |f| f.as_str().parse().unwrap());
                expr += var_expr * coef;
            } else {
                let constant: CountType = caps.name("const").unwrap().as_str().parse().unwrap();
                expr += VarSum::from(constant);
            }
        }
        Ok(expr)
    }
}

impl FromStr for CountExpr {
    type Err = ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        //  TODO: Support parsing recursive expressions.
        VarSum::from_str(s).map(CountExpr::VarSum)
    }
}

impl FromStr for CountOrInf {
    type Err = ParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "inf" => Ok(CountOrInf::Infinity),
            _ => CountExpr::from_str(s).map(CountOrInf::Finite),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_display() {
        for s in [
            "0", "13", "inf", "n", "x+13", "k+138", "a+b+7", "2x+5", "13j",
        ] {
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
            (VarSum::from_str("x").unwrap() + VarSum::from(13)),
            VarSum::from_str("x+13").unwrap()
        );
        assert_eq!(
            CountOrInf::from_str("x+13").unwrap(),
            CountOrInf::from_str("13+x").unwrap()
        );
        assert_eq!(
            CountOrInf::from_str("s+n+l+8").unwrap(),
            CountOrInf::from_str("4+l+s+n+4").unwrap()
        );

        assert_eq!(
            CountOrInf::from_str("3x").unwrap(),
            CountOrInf::from_str("x+x+x").unwrap()
        );
        assert_eq!(CountOrInf::from_str("0x").unwrap(), CountOrInf::from(0));
        assert_eq!(
            CountOrInf::from_str("1x").unwrap(),
            CountOrInf::from_str("x").unwrap()
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
    fn test_subst_mult() {
        let x = Variable::from_str("x").unwrap();
        let y = Variable::from_str("y").unwrap();
        let xe: VarSum = x.into();
        let ye: VarSum = y.into();

        // x -> 2y + 8
        let mut subst = VarSubst::default();
        subst.insert(x, CountExpr::VarSum(ye.clone() * 2 + 8.into()));

        // 3x + 13 -> 6y + (8*3 + 13)
        let start = xe * 3 + 13.into();
        let expected = ye * 6 + (8 * 3 + 13).into();
        assert_eq!(start.subst(&subst), CountExpr::VarSum(expected));
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
            CountOrInf::from_str("2x+13")
                .unwrap()
                .checked_sub(&CountOrInf::from_str("x").unwrap()),
            Some(CountOrInf::from_str("x+13").unwrap())
        );
        assert_eq!(
            CountOrInf::from_str("2x+13")
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
            "0", "13", "x", "x+13", "5x+138", "a+b+7", "n", "n+1", "a+n+1", "x+n", "2b+x",
        ];
        let exprs: Vec<VarSum> = expr_strs
            .iter()
            .map(|s| VarSum::from_str(s).unwrap())
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
            x.checked_add(&CountOrInf::Infinity)
                .unwrap()
                .checked_sub(&CountOrInf::Infinity),
            Some(CountOrInf::from(0))
        );
        assert_eq!(
            CountOrInf::from(813)
                .checked_add(&CountOrInf::Infinity)
                .unwrap()
                .checked_sub(&CountOrInf::Infinity),
            Some(CountOrInf::from(0))
        );
        assert_eq!(
            CountOrInf::Infinity
                .checked_add(&x)
                .unwrap()
                .checked_sub(&CountOrInf::Infinity),
            Some(CountOrInf::from(0))
        );
        assert_eq!(
            CountOrInf::Infinity
                .checked_add(&CountOrInf::from(813))
                .unwrap()
                .checked_sub(&CountOrInf::Infinity),
            Some(CountOrInf::from(0))
        );
    }

    #[test]
    fn test_function_compose() {
        // f(x) = 2x + 8
        let f = Function::affine(2, 8);

        // g(x) = 3x + 13
        let g = Function::affine(3, 13);

        // f#g: x -> g(f(x)) = 6x + (8*3 + 13)
        let fg = f.compose(&g);
        assert_eq!(fg.apply(5.into()), (5 * 6 + (8 * 3 + 13)).into());
    }

    #[test]
    fn test_subst_var_sum_recursive() {
        let outer_expr: CountExpr = "2n+8".parse().unwrap();

        // rep(\x -> 3x + 13, 2)(3)
        let inner_expr = CountExpr::RecursiveExpr(RecursiveExpr {
            func: Box::new(Function::affine(3, 13)),
            num_repeats: Box::new(2.into()),
            base: Box::new(3.into()),
        });

        // Substitute: n -> inner_expr
        let subst = VarSubst::single("n".parse().unwrap(), inner_expr);
        assert!(outer_expr.subst(&subst).is_ok());

        // let combined_expr = outer_expr.subst(&subst).unwrap();
        // TODO: assert_eq!(combined_expr, "6x+34".parse().unwrap());
    }
}

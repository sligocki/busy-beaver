// Library supporting (limited) algebraic expressions for use in proving
// general Busy Beaver rules.

use std::collections::HashMap;
use std::ops;

use crate::config::Count;

pub type VarId = u32;
pub type VarSubst = HashMap<VarId, Expr>;

// Algebraic Expression type
// Currently only supports simple linear equations of one variable, but intended to be extended to support other expressions over time as needed.
#[derive(Debug)]
pub enum Expr {
    Const(Count),
    Linear { var: VarId, m: Count, b: Count },
}

impl Expr {
    pub fn subst(&self, subs: &VarSubst) -> Option<Expr> {
        match self {
            Expr::Const(n) => Some(Expr::Const(*n)),
            Expr::Linear { var, m, b } => {
                match subs.get(var)? {
                    Expr::Const(n) => Some(Expr::Const(m * n + b)),
                    // m (m_in var_in + b_in) + b = (m m_in) var_in + (b + m b_in)
                    Expr::Linear {
                        var: var_in,
                        m: m_in,
                        b: b_in,
                    } => Some(Expr::Linear {
                        var: *var_in,
                        m: m * m_in,
                        b: b + m * b_in,
                    }),
                }
            }
        }
    }
}

// Implementing some basic arithmetic

impl ops::AddAssign<Count> for Expr {
    fn add_assign(&mut self, rhs: Count) {
        match self {
            Expr::Const(n) => *n += rhs,
            Expr::Linear { b, .. } => *b += rhs,
        }
    }
}

impl ops::SubAssign<Count> for Expr {
    fn sub_assign(&mut self, rhs: Count) {
        match self {
            Expr::Const(n) => *n -= rhs,
            Expr::Linear { b, .. } => *b -= rhs,
        }
    }
}

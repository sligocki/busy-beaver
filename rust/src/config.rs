// TM Tape and configuration.

use enum_map::{enum_map, EnumMap};
use std::fmt;

use crate::count_expr::CountExpr;
use crate::tm::{Dir, State, Symbol};

// A block of TM symbols with a repetition count. Ex:
//      110^13  or  10^{x+4}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RepBlock {
    // Block is ordered so that the last element is closest to the TM head.
    pub symbols: Vec<Symbol>,
    pub rep: CountExpr,
}

#[derive(Debug, Clone)]
pub struct HalfTape(Vec<RepBlock>);

pub type Tape = EnumMap<Dir, HalfTape>;

#[derive(Debug, Clone)]
pub struct Config {
    pub tape: Tape,
    pub state: State,
    pub dir: Dir,
}

impl RepBlock {
    pub fn to_string(&self, dir: Dir) -> String {
        let mut symbols_strs: Vec<String> = self.symbols.iter().map(|s| s.to_string()).collect();
        if dir == Dir::Right {
            symbols_strs.reverse();
        }
        format!("{}^{}", symbols_strs.concat(), self.rep)
    }
}

impl HalfTape {
    // Push a symbol onto this half-tape.
    pub fn push_symbol(&mut self, symbol: Symbol) {
        // Keep this simple. Always push symbols as their own simple block.
        // If this was a simulator, we'd prefer to merge symbols into existing blocks.
        // But since the use case is for validation, we want to keep the code as simple as possible.
        self.0.push(RepBlock {
            symbols: vec![symbol],
            rep: CountExpr::Const(1),
        });
    }

    // Pop the top symbol from this half-tape if possible.
    // Returns None if the tape is empty or if the top symbol is ambiguous (based on variable assignments).
    pub fn pop_symbol(&mut self) -> Option<Symbol> {
        match &mut self.0[..] {
            [] => None, // Cannot pop from empty tape.
            [.., RepBlock { rep, symbols }] => {
                // Split off one repetition of the block and pop the first symbol.
                // Ex: 110^13 -> 10 110^12 and we return the removed "1".

                // Try to remove one repetition (decrement the rep count).
                // If decrement fails, this is because rep is not guaranteed to be >= 0.
                // And so we have an ambiguous situation where top symbol could be
                // different things depending on the value of variables.
                // So, fail pop_symbol().
                let decr_rep = rep.decrement()?;

                // New RepBlock
                let mut new_symbols = symbols.clone();
                // We assume the order here is always that last
                let symbol = new_symbols.pop().unwrap();

                // Update the tape with decr_rep.
                if decr_rep.is_zero() {
                    self.0.pop();
                } else {
                    *rep = decr_rep;
                }

                // If there are any symbols left after popping the top one,
                // we add a new RepBlock for them.
                if !new_symbols.is_empty() {
                    self.0.push(RepBlock {
                        symbols: new_symbols,
                        rep: CountExpr::Const(1),
                    });
                }

                Some(symbol)
            }
        }
    }

    // Compare two half tapes for represent the same symbols.
    // Two tapes may be equivalent even if they are not "structurally" equal.
    // May fail for complex tapes.
    pub fn eqivalent_to(&self, other: &HalfTape) -> Option<bool> {
        let mut left = self.clone();
        let mut right = other.clone();
        while !left.0.is_empty() && !right.0.is_empty() {
            // Skip over identical blocks.
            if left.0.last().unwrap() == right.0.last().unwrap() {
                left.0.pop();
                right.0.pop();
                continue;
            }
            match (left.pop_symbol(), right.pop_symbol()) {
                (Some(l), Some(r)) => {
                    if l != r {
                        // Tapes differ.
                        return Some(false);
                    }
                }
                _ => {
                    // If either pop_symbol() failed, we cannot tell if the tapes are equivalent.
                    return None;
                }
            }
        }
        // If we reach here, one tape is empty they are only equivalent if both are empty.
        return Some(left.0.is_empty() && right.0.is_empty());
    }

    // Display the tape in a human-readable format.
    pub fn to_string(&self, dir: Dir) -> String {
        let mut block_strs: Vec<String> = self.0.iter().map(|block| block.to_string(dir)).collect();
        if dir == Dir::Right {
            block_strs.reverse();
        }
        block_strs.join(" ")
    }
}

impl fmt::Display for Config {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.tape[Dir::Left].to_string(Dir::Left))?;
        if self.dir == Dir::Left {
            write!(f, " <{} ", self.state)?;
        } else {
            write!(f, " {}> ", self.state)?;
        }
        write!(f, "{}", self.tape[Dir::Right].to_string(Dir::Right))
    }
}

#[cfg(test)]
mod tests {
    use crate::count_expr::VarIdType;

    use super::*;

    #[test]
    fn test_config_display() {
        let config = Config {
            tape: enum_map! {
                Dir::Left => HalfTape(vec![
                    RepBlock {
                        symbols: vec![0],
                        rep: CountExpr::Infinity,
                    },
                    RepBlock {
                        symbols: vec![1, 0],
                        rep: CountExpr::Const(13),
                    },
                    RepBlock {
                        symbols: vec![0, 1],
                        rep: CountExpr::Const(1),
                    },
                ]),
                Dir::Right => HalfTape(vec![
                    RepBlock {
                        symbols: vec![1, 2],
                        rep: CountExpr::Const(1),
                    },
                    RepBlock {
                        symbols: vec![3, 4],
                        rep: CountExpr::Const(8),
                    },
                ]),
            },
            state: State::Run(0),
            dir: Dir::Left,
        };

        assert_eq!(format!("{}", config), "0^inf 10^13 01^1 <A 43^8 21^1");
    }

    #[test]
    fn test_pop_constant() {
        // Tape: 01^2 011
        let mut tape = HalfTape(vec![
            RepBlock {
                symbols: vec![1, 1, 0],
                rep: CountExpr::Const(1),
            },
            RepBlock {
                symbols: vec![1, 0],
                rep: CountExpr::Const(2),
            },
        ]);

        // 01^2
        assert_eq!(tape.pop_symbol(), Some(0));
        assert_eq!(tape.pop_symbol(), Some(1));
        assert_eq!(tape.pop_symbol(), Some(0));
        assert_eq!(tape.pop_symbol(), Some(1));

        // 011
        assert_eq!(tape.pop_symbol(), Some(0));
        assert_eq!(tape.pop_symbol(), Some(1));
        assert_eq!(tape.pop_symbol(), Some(1));

        assert_eq!(tape.pop_symbol(), None);
    }

    #[test]
    fn test_pop_ambiguous() {
        // Tape: 01^{x+1}
        let x: VarIdType = 13;
        let mut tape = HalfTape(vec![RepBlock {
            symbols: vec![1, 0],
            rep: CountExpr::var_plus_const(x, 1),
        }]);

        assert_eq!(tape.pop_symbol(), Some(0)); // 0 ... 1 01^x
        assert_eq!(tape.pop_symbol(), Some(1)); // 1 ... 01^x
        assert_eq!(tape.pop_symbol(), None); // 01^x is ambiguous
    }

    #[test]
    fn test_push_pop() {
        let mut tape = HalfTape(vec![]);
        tape.push_symbol(13);
        tape.push_symbol(8);
        tape.push_symbol(30);

        assert_eq!(tape.pop_symbol(), Some(30));
        assert_eq!(tape.pop_symbol(), Some(8));
        assert_eq!(tape.pop_symbol(), Some(13));
        assert_eq!(tape.pop_symbol(), None);
    }

    #[test]
    fn test_equivalent_to() {
        let tape1 = HalfTape(vec![RepBlock {
            symbols: vec![1],
            rep: CountExpr::Const(2),
        }]);

        let tape2 = HalfTape(vec![RepBlock {
            symbols: vec![1, 1],
            rep: CountExpr::Const(1),
        }]);

        let tape3 = HalfTape(vec![
            RepBlock {
                symbols: vec![1],
                rep: CountExpr::Const(1),
            },
            RepBlock {
                symbols: vec![1],
                rep: CountExpr::Const(1),
            },
        ]);

        assert_eq!(tape1.eqivalent_to(&tape2), Some(true));
        assert_eq!(tape1.eqivalent_to(&tape3), Some(true));
        assert_eq!(tape2.eqivalent_to(&tape3), Some(true));
    }
}

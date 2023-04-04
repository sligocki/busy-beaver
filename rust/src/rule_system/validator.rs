// Library for validating rules.

use std::iter::zip;

use enum_map::enum_map;

use crate::config::{Count, Rep, RepBlock, RepConfig, Tape};
use crate::rule_system::algebra::{Expr, VarId, VarSubst};
use crate::tm::Dir;

type RuleId = u32;

#[derive(Debug)]
enum SimStep {
    Base(Count),
    Rule(RuleId),
}

// Repetition counts for a rule's initial configuration can either be constant values
// or general integer values (with specified minimum).
// TODO: Maybe also support Collatz-style remainder restriction?
#[derive(Debug)]
enum RuleInitRep {
    Const(Count),
    Var { var: VarId, min: Count },
}

#[derive(Debug)]
struct Rule {
    init_config: RepConfig<RuleInitRep>,
    final_config: RepConfig<Expr>,
    algorithm: Vec<SimStep>,
}

// Try to match rule to this config and save variable assignments if it does match.
fn try_match(config: &RepConfig<Expr>, rule: &Rule) -> Option<VarSubst> {
    if config.state != rule.init_config.state || config.dir != rule.init_config.dir {
        return None;
    }
    let mut assignment = VarSubst::new();
    for &dir in Dir::iter() {
        if config.tape[dir].len() < rule.init_config.tape[dir].len() {
            // Config is too small for rule. Rule cannot match config.
            // TODO: Maybe deal with different representations of same config?
            return None;
        }
        for (
            RepBlock {
                block: c_block,
                rep: c_rep,
            },
            RepBlock {
                block: r_block,
                rep: r_rep,
            },
        ) in zip(&config.tape[dir], &rule.init_config.tape[dir])
        {
            if c_block != r_block {
                return None;
            }
            match r_rep {
                Rep::Infinite => {
                    if let Rep::Infinite = c_rep {
                    } else {
                        return None;
                    }
                }
                Rep::Finite(RuleInitRep::Const(r_n)) => {
                    if let Rep::Finite(Expr::Const(c_n)) = c_rep {
                        if c_n != r_n {
                            return None;
                        }
                    } else {
                        // Constant in rule cannot match Inf or Expr on config.
                        return None;
                    }
                }
                Rep::Finite(RuleInitRep::Var { var, min: r_min }) => {
                    match c_rep {
                        Rep::Finite(Expr::Const(c_n)) => {
                            // Only apply rule if tape rep is >= min
                            if c_n < r_min {
                                return None;
                            }
                            assignment.insert(*var, Expr::Const(*c_n));
                        }
                        Rep::Finite(_expr) => {
                            todo!("Make sure expr cannot be below r_min!");
                            // assignment.insert(var, expr);
                        }
                        Rep::Infinite => return None,
                    }
                }
            }
        }
    }
    Some(assignment)
}

fn update_rep(rep: &Rep<Expr>, subs: &VarSubst) -> Rep<Expr> {
    match rep {
        Rep::Infinite => Rep::Infinite,
        Rep::Finite(expr) => {
            // We should have assignments for all variables used in expr, so this
            // should never fail (for valid rules).
            Rep::Finite(expr.subst(subs).unwrap())
        }
    }
}

fn update_rep_block(rep_block: &RepBlock<Expr>, subs: &VarSubst) -> RepBlock<Expr> {
    RepBlock {
        block: rep_block.block.clone(),
        rep: update_rep(&rep_block.rep, subs),
    }
}

fn update_tape_rep(tape: &Tape<Expr>, subs: &VarSubst) -> Tape<Expr> {
    enum_map! {
        Dir::Left => tape[Dir::Left].iter().map(|x| update_rep_block(x, subs)).collect(),
        Dir::Right => tape[Dir::Right].iter().map(|x| update_rep_block(x, subs)).collect(),
    }
}

fn try_apply(config: &RepConfig<Expr>, rule: &Rule) -> Option<RepConfig<Expr>> {
    let subs = try_match(config, rule)?;
    Some(RepConfig {
        tape: update_tape_rep(&rule.final_config.tape, &subs),
        state: rule.final_config.state,
        dir: rule.final_config.dir,
    })
}

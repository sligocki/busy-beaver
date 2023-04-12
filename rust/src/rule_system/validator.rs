// Library for validating rules.

use std::iter::zip;
use std::result::Result;

use enum_map::enum_map;

use crate::config::{Count, HalfTape, RepBlock, RepConfig, Tape};
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
// Currently we require the configs to have the exact same compression.
fn try_match(config: &RepConfig<Expr>, rule: &Rule) -> Result<VarSubst, String> {
    if config.state != rule.init_config.state || config.dir != rule.init_config.dir {
        return Err("State or direction do not match rule".to_string());
    }
    let mut assignment = VarSubst::new();
    for &dir in Dir::iter() {
        let rule_htape = &rule.init_config.tape[dir];
        let config_htape = &config.tape[dir];
        if rule_htape.is_complete {
            // Complete rule
            if !config_htape.is_complete {
                return Err("Cannot apply complete rule to limited config".to_string());
            }
            if config_htape.data.len() != rule_htape.data.len() {
                return Err("Complete config is not same length as complete rule".to_string());
            }
        } else {
            // Limited rule
            if config_htape.data.len() < rule_htape.data.len() {
                return Err("Complete config is smaller than limited rule".to_string());
            }
        }
        // This zip is guaranteed to iterate over entire rule_htape b/c of the two
        // htape.data.len() checks above.
        for (
            RepBlock {
                block: c_block,
                rep: c_rep,
            },
            RepBlock {
                block: r_block,
                rep: r_rep,
            },
        ) in zip(&config_htape.data, &rule_htape.data)
        {
            if c_block != r_block {
                return Err("Block mismatch".to_string());
            }
            match r_rep {
                RuleInitRep::Const(r_n) => {
                    if let Expr::Const(c_n) = c_rep {
                        if c_n != r_n {
                            return Err("Constant rep-count mismatch".to_string());
                        }
                    } else {
                        return Err(
                            "Constant rule rep-count cannot apply to variable config rep-count"
                                .to_string(),
                        );
                    }
                }
                RuleInitRep::Var { var, min: r_min } => {
                    match c_rep {
                        Expr::Const(c_n) => {
                            // Only apply rule if tape rep is >= min
                            if c_n < r_min {
                                return Err("Config rep-count below rule minimum".to_string());
                            }
                            assignment.insert(*var, Expr::Const(*c_n));
                        }
                        _expr => {
                            todo!("Make sure expr cannot be below r_min!");
                            // assignment.insert(var, expr);
                        }
                    }
                }
            }
        }
    }
    Ok(assignment)
}

fn update_rep_block(rep_block: &RepBlock<Expr>, subs: &VarSubst) -> RepBlock<Expr> {
    RepBlock {
        block: rep_block.block.clone(),
        rep: rep_block.rep.subst(subs).unwrap(),
    }
}

fn update_half_tape_rep(half_tape: &HalfTape<Expr>, subs: &VarSubst) -> HalfTape<Expr> {
    HalfTape {
        data: half_tape
            .data
            .iter()
            .map(|x| update_rep_block(x, subs))
            .collect(),
        is_complete: half_tape.is_complete,
    }
}

fn update_tape_rep(tape: &Tape<Expr>, subs: &VarSubst) -> Tape<Expr> {
    enum_map! {
        Dir::Left => update_half_tape_rep(&tape[Dir::Left], subs),
        Dir::Right => update_half_tape_rep(&tape[Dir::Right], subs),
    }
}

fn try_apply(config: &RepConfig<Expr>, rule: &Rule) -> Result<RepConfig<Expr>, String> {
    let subs = try_match(config, rule)?;
    if !rule.final_config.tape[Dir::Left].is_complete
        || rule.final_config.tape[Dir::Right].is_complete
    {
        // Limited rule
        todo!("Handle limited configs correctly");
    } else {
        // Complete rule
        Ok(RepConfig {
            tape: update_tape_rep(&rule.final_config.tape, &subs),
            state: rule.final_config.state,
            dir: rule.final_config.dir,
        })
    }
}

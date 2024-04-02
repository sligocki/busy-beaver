// Library for validating rules.

use std::iter::zip;
use std::result::Result;

use enum_map::enum_map;

use crate::config::{CountType, HalfTape, RepBlock, RepConfig, Tape};
use crate::rule_system::algebra::{Expr, VarIdType, VarSubst};
use crate::tm::{Dir, TM};

type RuleIdType = usize;
type ConfigExpr = RepConfig<Expr>;


fn subst_block(block: &RepBlock<Expr>, subs: &VarSubst) -> Result<RepBlock<Expr>, String> {
    Ok(RepBlock {
        block: block.block.clone(),
        rep: block.rep.subst(subs)?,
    })
}

impl HalfTape<Expr> {
    fn subst(&self, subs: &VarSubst) -> Result<HalfTape<Expr>, String> {
        let new_data : Result<Vec<RepBlock<Expr>>, String> = self.data
            .iter()
            .map(|block| subst_block(block, subs))
            .collect();
        Ok(HalfTape { data: new_data?, is_complete: self.is_complete })
    }
}

impl ConfigExpr {
    fn subst(&self, subs: &VarSubst) -> Result<ConfigExpr, String> {
        Ok(RepConfig {
            tape: enum_map! {
                Dir::Left => self.tape[Dir::Left].subst(subs)?,
                Dir::Right => self.tape[Dir::Right].subst(subs)?,
            },
            state: self.state,
            dir: self.dir,
        })
    }
}


#[derive(Debug)]
enum ProofStep {
    // Apply an integer count of base TM steps.
    BaseSteps(CountType),
    // Apply a rule with the given ID and variable assignments.
    Rule { rule_id: RuleIdType, var_assignment: VarSubst },
    // Apply this rule via induction.
    Induction(VarSubst),
}

#[derive(Debug)]
struct Rule {
    num_vars: VarIdType,
    init_config: ConfigExpr,
    final_config: ConfigExpr,
    proof: Vec<ProofStep>,
}

#[derive(Debug)]
struct RuleSet {
    tm: TM,
    // Mapping from rule ID to Rule.
    // Rule n may only use rules with id < n (or induction).
    rules: Vec<Rule>,
}


fn try_apply_rule(config: &ConfigExpr, rule: &Rule, var_assignment: &VarSubst) -> Result<ConfigExpr, String> {
    // TODO: Check that var_assignment are all guaranteed to be positive.
    // Currently, we only allow equality between rules if Tapes are specified identically.
    // TODO: Support equality even if compression is different.
    if config != &rule.init_config.subst(var_assignment)? {
        return Err("Initial config does not match rule".to_string());
    }
    rule.final_config.subst(var_assignment)
}

fn try_apply_step(config: &ConfigExpr, step: &ProofStep, this_rule: &Rule, prev_rules: &[Rule]) -> Result<ConfigExpr, String> {
    match step {
        ProofStep::BaseSteps(n) => {
            // Apply n base TM steps.
            unimplemented!()
        }
        ProofStep::Rule { rule_id, var_assignment } => {
            try_apply_rule(config, &prev_rules[*rule_id], var_assignment)
        }
        ProofStep::Induction(var_assignment) => {
            try_apply_rule(config, this_rule, var_assignment)
        }
    }
}

fn validate_rule(tm: &TM, rule: &Rule, prev_rules: &[Rule]) -> Result<(), String> {
    let mut config = &rule.init_config;
    // For memory management, we own the config only after the first step.
    let mut config_holder : ConfigExpr;
    for step in &rule.proof {
        config_holder = try_apply_step(&config, step, rule, prev_rules)?;
        config = &config_holder;
    }
    if *config == rule.final_config {
        // Success. Every step of every rule was valid and the final config matches.
        // This is a valid rule.
        return Ok(());
    } else {
        return Err("Final config does not match rule".to_string());
    }
}

// Validate a rule set.
fn validate_rule_set(rule_set: &RuleSet) -> Result<(), String> {
    rule_set.rules.iter().enumerate().map(|(rule_id, rule)|
        // This rule may only use previous rules: rule_set.rules[..rule_id]
        validate_rule(&rule_set.tm, rule, &rule_set.rules[..rule_id])).collect()
}


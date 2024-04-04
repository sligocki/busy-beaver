// Library for validating rules.

use std::result::Result;

use crate::config::Config;
use crate::count_expr::{VarIdType, CountType, CountExpr, VarSubst};
use crate::tm::TM;

pub type RuleIdType = usize;


#[derive(Debug)]
enum BaseProofStep {
    // Apply an integer count of base TM steps.
    TMSteps(CountType),
    // Apply a rule with the given ID and variable assignments.
    RuleStep { rule_id: RuleIdType, var_assignment: VarSubst },
}

#[derive(Debug)]
enum InductiveProofStep {
    BaseStep(BaseProofStep),
    // Apply this rule via induction.
    InductiveStep(VarSubst),
}

#[derive(Debug)]
struct Rule {
    num_vars: VarIdType,
    init_config: Config,
    final_config: Config,
    proof_base: Vec<BaseProofStep>,
    proof_inductive: Vec<InductiveProofStep>,
}

#[derive(Debug)]
struct RuleSet {
    tm: TM,
    // Mapping from rule ID to Rule.
    // Rule n may only use rules with id < n (or induction).
    rules: Vec<Rule>,
}


fn try_apply_rule(config: &Config, rule: &Rule, var_assignment: &VarSubst) -> Result<Config, String> {
    // TODO: Check that var_assignment are all guaranteed to be positive.
    // Currently, we only allow equality between rules if Tapes are specified identically.
    // TODO: Support equality even if compression is different.
    if config != &rule.init_config.subst(var_assignment)? {
        return Err("Initial config does not match rule".to_string());
    }
    rule.final_config.subst(var_assignment)
}

fn try_apply_step_base(tm: &TM, config: &Config, step: &BaseProofStep, prev_rules: &[Rule]) -> Result<Config, String> {
    match step {
        BaseProofStep::TMSteps(n) => {
            // Apply n base TM steps.
            let mut new_config = config.clone();
            new_config.run(tm, *n)?;
            Ok(new_config)
        }
        BaseProofStep::RuleStep { rule_id, var_assignment } => {
            if *rule_id >= prev_rules.len() {
                return Err("Rule ID out of bounds".to_string());
            }
            try_apply_rule(config, &prev_rules[*rule_id], var_assignment)
        }
    }
}

fn try_apply_step_inductive(tm: &TM, config: &Config, step: &InductiveProofStep, this_rule: &Rule, prev_rules: &[Rule]) -> Result<Config, String> {
    match step {
        InductiveProofStep::BaseStep(base_step) => {
            try_apply_step_base(tm, config, base_step, prev_rules)
        }
        InductiveProofStep::InductiveStep(var_assignment) => {
            // Ensure that the induction variable is decreasing.
            // Note: The induction variable must be the first variable.
            if var_assignment[0] != CountExpr::var_plus_const(0, -1) {
                // We only support simple induction: n -> n-1.
                return Err("Induction variable must be decrementing".to_string());
            }
            try_apply_rule(config, this_rule, var_assignment)
        }
    }
}

fn validate_rule(tm: &TM, rule: &Rule, prev_rules: &[Rule]) -> Result<(), String> {
    // TODO: Validate the rule.proof_base case.
    let mut config = &rule.init_config;
    // For memory management, we own the config only after the first step.
    let mut config_holder : Config;
    for step in &rule.proof_inductive {
        config_holder = try_apply_step_inductive(tm, &config, step, rule, prev_rules)?;
        config = &config_holder;
    }
    match config.equivalent_to(&rule.final_config) {
        Some(true) => {
            // Success. Every step of every rule was valid and the final config matches.
            // This is a valid rule.
            return Ok(());
        }
        Some(false) => {
            return Err("Final config does not match rule".to_string());
        }
        None => {
            return Err("Unable to compare final config".to_string());
        }
    }
}

// Validate a rule set.
fn validate_rule_set(rule_set: &RuleSet) -> Result<(), String> {
    rule_set.rules.iter().enumerate().map(|(rule_id, rule)|
        // This rule may only use previous rules: rule_set.rules[..rule_id]
        validate_rule(&rule_set.tm, rule, &rule_set.rules[..rule_id])).collect()
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_rule_simple() {
        // Validate a very simple rule that just performs a few steps on a tape with no variables.
        let tm = TM::from_str("AAB_BBA_BBB").unwrap();
        let rule = Rule {
            num_vars: 1,
            init_config: Config::from_str("A").unwrap(),
            final_config: Config::from_str("B").unwrap(),
            proof_base: vec![],
            proof_inductive: vec![],
        };
        let prev_rules = vec![];
        assert_eq!(validate_rule(&tm, &rule, &prev_rules), Ok(()));
    }
}
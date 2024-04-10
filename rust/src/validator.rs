// Library for validating rules.

use std::result::Result;

use crate::base::CountType;
use crate::config::Config;
use crate::count_expr::{CountExpr, VarSubst, Variable};
use crate::tm::TM;

type RuleIdType = usize;
const INDUCTION_VAR: Variable = Variable::new(0);

#[allow(dead_code)]
#[derive(Debug)]
enum BaseProofStep {
    // Apply an integer count of base TM steps.
    TMSteps(CountType),
    // Apply a rule with the given ID and variable assignments.
    RuleStep {
        rule_id: RuleIdType,
        var_assignment: VarSubst,
    },
}

#[allow(dead_code)]
#[derive(Debug)]
enum InductiveProofStep {
    BaseStep(BaseProofStep),
    // Apply this rule via induction.
    InductiveStep(VarSubst),
}

#[derive(Debug)]
struct Rule {
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

fn try_apply_rule(config: &Config, rule: &Rule, var_subst: &VarSubst) -> Result<Config, String> {
    // TODO: Check that var_subst are all guaranteed to be positive.
    // Currently, we only allow equality between rules if Tapes are specified identically.
    // TODO: Support equality even if compression is different.
    let init_config = rule.init_config.subst(var_subst);
    let final_config = rule.final_config.subst(var_subst);
    config.replace(&init_config, &final_config)
}

fn try_apply_step_base(
    tm: &TM,
    config: &Config,
    step: &BaseProofStep,
    prev_rules: &[Rule],
) -> Result<Config, String> {
    match step {
        BaseProofStep::TMSteps(n) => {
            // Apply n base TM steps.
            let mut new_config = config.clone();
            new_config.step_n(tm, *n)?;
            Ok(new_config)
        }
        BaseProofStep::RuleStep {
            rule_id,
            var_assignment,
        } => {
            if *rule_id >= prev_rules.len() {
                return Err("Rule ID out of bounds".to_string());
            }
            try_apply_rule(config, &prev_rules[*rule_id], var_assignment)
        }
    }
}

fn try_apply_step_inductive(
    tm: &TM,
    config: &Config,
    step: &InductiveProofStep,
    this_rule: &Rule,
    prev_rules: &[Rule],
) -> Result<Config, String> {
    match step {
        InductiveProofStep::BaseStep(base_step) => {
            try_apply_step_base(tm, config, base_step, prev_rules)
        }
        InductiveProofStep::InductiveStep(var_assignment) => {
            // Ensure that the induction variable is decreasing.
            // Note: When doing an inductive proof, we start by replacing n <- n+1 and
            // then only allow any uses of the rule itself with n <- n.
            if var_assignment[&INDUCTION_VAR] != INDUCTION_VAR.into() {
                return Err("Induction variable must be decrementing".to_string());
            }
            try_apply_rule(config, this_rule, var_assignment)
        }
    }
}

fn validate_rule_base(tm: &TM, rule: &Rule, prev_rules: &[Rule]) -> Result<(), String> {
    // In base case, we consider the case n <- 0.
    let base_subst = VarSubst::from([(INDUCTION_VAR, 0.into())]);
    let mut config = rule.init_config.subst(&base_subst);
    for step in &rule.proof_base {
        config = try_apply_step_base(tm, &config, step, prev_rules)?;
    }
    let expected_final = rule.final_config.subst(&base_subst);
    if config.equivalent_to(&expected_final) {
        // Success. Every step of every rule was valid and the final config matches.
        // This is a valid rule.
        Ok(())
    } else {
        Err(format!(
            "Unable to prove equivalence between with final config: {} != {}",
            config, expected_final
        ))
    }
}

fn validate_rule_inductive(tm: &TM, rule: &Rule, prev_rules: &[Rule]) -> Result<(), String> {
    // In inductive case, we consider the case n <- m+1 (and only allow use of this rule where n <- m).
    let ind_subst = VarSubst::from([(
        INDUCTION_VAR,
        CountExpr::from(INDUCTION_VAR) + CountExpr::from(1),
    )]);
    let mut config = rule.init_config.subst(&ind_subst);
    for step in &rule.proof_inductive {
        config = try_apply_step_inductive(tm, &config, step, rule, prev_rules)?;
    }
    let expected_final = rule.final_config.subst(&ind_subst);
    if config.equivalent_to(&expected_final) {
        // Success. Every step of every rule was valid and the final config matches.
        // This is a valid rule.
        Ok(())
    } else {
        Err(format!(
            "Unable to prove equivalence between with final config: {} != {}",
            config, expected_final
        ))
    }
}

fn validate_rule(tm: &TM, rule: &Rule, prev_rules: &[Rule]) -> Result<(), String> {
    // Validate base case (n <- 0) and inductive case (n <- m+1) seperately.
    validate_rule_base(tm, rule, prev_rules)?;
    validate_rule_inductive(tm, rule, prev_rules)
}

// Validate a rule set.
#[allow(dead_code)]
fn validate_rule_set(rule_set: &RuleSet) -> Result<(), String> {
    rule_set
        .rules
        .iter()
        .enumerate()
        // This rule may only use previous rules: rule_set.rules[..rule_id]
        .map(|(rule_id, rule)| validate_rule(&rule_set.tm, rule, &rule_set.rules[..rule_id]))
        .collect()
}

#[cfg(test)]
mod tests {
    use std::str::FromStr;

    use super::*;

    #[test]
    fn test_validate_rule_trivial() {
        // Validate a very trivial rule which does nothing.
        let tm = TM::from_str("1RB1LB_1LA1RZ").unwrap();
        let rule = Rule {
            init_config: Config::from_str("0^inf 1^138 B> 0^1 1^2 0^inf").unwrap(),
            final_config: Config::from_str("0^inf 1^138 B> 0^1 1^2 0^inf").unwrap(),
            proof_base: vec![],
            proof_inductive: vec![],
        };
        let prev_rules = vec![];
        assert_eq!(validate_rule(&tm, &rule, &prev_rules), Ok(()));
    }

    #[test]
    fn test_validate_rule_simple() {
        // Validate a very simple rule that just performs a few steps on a tape with no variables.
        // BB(2) champion
        let tm = TM::from_str("1RB1LB_1LA1RZ").unwrap();
        // BB2 runs for 6 steps.
        let rule = Rule {
            init_config: Config::new(),
            final_config: Config::from_str("0^inf 1^2 Z> 1^2 0^inf").unwrap(),
            proof_base: vec![BaseProofStep::TMSteps(6)],
            proof_inductive: vec![InductiveProofStep::BaseStep(BaseProofStep::TMSteps(6))],
        };
        let prev_rules = vec![];
        assert_eq!(validate_rule(&tm, &rule, &prev_rules), Ok(()));
    }

    #[test]
    fn test_validate_rule_chain() {
        // Validate a chain rule.
        //      https://www.sligocki.com/2021/07/17/bb-collatz.html#chain-step
        let tm = TM::from_str("1RB1LD_1RC1RB_1LC1LA_0RC0RD").unwrap();
        // 0^n <C  ->  <C 1^n
        let rule = Rule {
            init_config: Config::from_str("0^n <C").unwrap(),
            final_config: Config::from_str("<C 1^n").unwrap(),
            // Base case is trivial:  0^0 <C  ==  <C 1^0
            proof_base: vec![],
            proof_inductive: vec![
                // 0^n+1 <C  ->  0^n <C 1
                InductiveProofStep::BaseStep(BaseProofStep::TMSteps(1)),
                // 0^n <C 1  ->  <C 1^n 1  ==  <C 1^n+1
                InductiveProofStep::InductiveStep(VarSubst::from([(
                    INDUCTION_VAR,
                    INDUCTION_VAR.into(),
                )])),
            ],
        };
        let prev_rules = vec![];
        assert_eq!(validate_rule(&tm, &rule, &prev_rules), Ok(()));
    }

    // Helper function to create a simple chain rule for which:
    //    A) The base case is trivial.
    //    B) The inductive case is `steps` TM steps followed by the inductive step.
    fn simple_chain_rule(start: &str, end: &str, steps: CountType) -> Rule {
        Rule {
            init_config: Config::from_str(start).unwrap(),
            final_config: Config::from_str(end).unwrap(),
            proof_base: vec![],
            proof_inductive: vec![
                InductiveProofStep::BaseStep(BaseProofStep::TMSteps(steps)),
                InductiveProofStep::InductiveStep(VarSubst::from([(
                    INDUCTION_VAR,
                    INDUCTION_VAR.into(),
                )])),
            ],
        }
    }

    #[test]
    fn test_validate_rule_level1() {
        // Validate a "level 1" rule (rule built only on chain rules). This is Rule 1x from:
        //      https://www.sligocki.com/2022/02/27/bb-recurrence-relations.html
        let rule_set = RuleSet {
            tm: TM::from_str("1RB0LB1LA_2LC2LB2LB_2RC2RA0LC").unwrap(),
            rules: vec![
                simple_chain_rule("C> 0^n", "2^n C>", 1),
                simple_chain_rule("2^n <C", "<C 0^n", 1),
                // Rule 1x: 0^inf <C 0^a 2^n  ->  0^inf <C 0^a+2n
                Rule {
                    init_config: Config::from_str("0^inf <C 0^a 2^n").unwrap(),
                    final_config: Config::from_str("0^inf <C 0^a+n+n").unwrap(),
                    proof_base: vec![],
                    proof_inductive: vec![
                        // 0^inf <C 0^a 2^n+1  ->  0^inf 2 C> 0^a 2^n+1
                        InductiveProofStep::BaseStep(BaseProofStep::TMSteps(1)),
                        // 0^inf 2 C> 0^a 2^n+1  ->  0^inf 2^a+1 C> 2^n+1
                        InductiveProofStep::BaseStep(BaseProofStep::RuleStep {
                            rule_id: 0,
                            var_assignment: VarSubst::from([(
                                Variable::from_str("n").unwrap(),
                                CountExpr::from_str("a").unwrap(),
                            )]),
                        }),
                        // 0^inf 2^a+1 C> 2^n+1  ->  0^inf 2^a+1 <C 0 2^n
                        InductiveProofStep::BaseStep(BaseProofStep::TMSteps(1)),
                        // 0^inf 2^a+1 <C 0 2^n  ->  0^inf <C 0^a+2 2^n
                        InductiveProofStep::BaseStep(BaseProofStep::RuleStep {
                            rule_id: 1,
                            var_assignment: VarSubst::from([(
                                Variable::from_str("n").unwrap(),
                                CountExpr::from_str("a+1").unwrap(),
                            )]),
                        }),
                        // Induction: 0^inf <C 0^a+2 2^n  ->  0^inf <C 0^a+2n+2
                        InductiveProofStep::InductiveStep(VarSubst::from([
                            (
                                Variable::from_str("n").unwrap(),
                                CountExpr::from_str("n").unwrap(),
                            ),
                            (
                                Variable::from_str("a").unwrap(),
                                CountExpr::from_str("a+2").unwrap(),
                            ),
                        ])),
                    ],
                },
            ],
        };
        assert_eq!(validate_rule_set(&rule_set), Ok(()));
    }

    #[test]
    #[ignore = "broken: 0^n prefix of 0^n+1"]
    fn test_validate_rule_counter() {
        // Validate a binary counter rule which uses the inductive hypothesis twice!
        //      See: https://www.sligocki.com/2022/06/14/counter-induction.html
        let rule_set = RuleSet {
            tm: TM::from_str("1RB1LA_0LC0RB_0LD0LB_1RE---_1LE1LA").unwrap(),
            rules: vec![
                simple_chain_rule("1^n <A", "<A 1^n", 1),
                simple_chain_rule("B> 1^n", "0^n B>", 1),
                // Rule P(n): 0^n 1 00 B> 0  ->  1^n+1 00 B> 0
                Rule {
                    init_config: Config::from_str("0^n 1^1 00^1 B> 0^1").unwrap(),
                    final_config: Config::from_str("1^n+1 00^1 B> 0^1").unwrap(),
                    proof_base: vec![],
                    proof_inductive: vec![
                        // 0^n+1 1 00 B> 0  ->  0 1^n+1 00 B> 0
                        // TODO: Currently failing because we cannot detect that
                        //       ... 0^n 1 00 is a prefix of ... 0^n+1 1 00.
                        InductiveProofStep::InductiveStep(VarSubst::from([(
                            Variable::from_str("n").unwrap(),
                            CountExpr::from_str("n").unwrap(),
                        )])),
                        // 0 1^n+1 00 B> 0  --(5)-->  0 1^n+1 <A 110
                        InductiveProofStep::BaseStep(BaseProofStep::TMSteps(5)),
                        // 0 1^n+1 <A 110  -->  0 <A 1^n+3 0
                        InductiveProofStep::BaseStep(BaseProofStep::RuleStep {
                            rule_id: 0,
                            var_assignment: VarSubst::from([(
                                Variable::from_str("n").unwrap(),
                                CountExpr::from_str("n+1").unwrap(),
                            )]),
                        }),
                        // 0 <A 1^n+3 0  --(1)-->  1 B> 1^n+3 0
                        InductiveProofStep::BaseStep(BaseProofStep::TMSteps(1)),
                        // 1 B> 1^n+3 0  --(5)-->  0^n+3 B> 0
                        InductiveProofStep::BaseStep(BaseProofStep::RuleStep {
                            rule_id: 1,
                            var_assignment: VarSubst::from([(
                                Variable::from_str("n").unwrap(),
                                CountExpr::from_str("n+3").unwrap(),
                            )]),
                        }),
                        // 0^n+3 B> 0  --(8)-->  1 0^n 1 00 B> 0
                        InductiveProofStep::BaseStep(BaseProofStep::TMSteps(8)),
                        // 1 0^n 1 00 B> 0  -->  1^n+2 00 B> 0
                        InductiveProofStep::InductiveStep(VarSubst::from([(
                            Variable::from_str("n").unwrap(),
                            CountExpr::from_str("n").unwrap(),
                        )])),
                    ],
                },
            ],
        };
        assert_eq!(validate_rule_set(&rule_set), Ok(()));
    }
}

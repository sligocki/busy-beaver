// Library for validating rules.

use std::result::Result;

use crate::base::CountType;
use crate::config::Config;
use crate::count_expr::{CountExpr, VarSubst, VarSubstError, Variable, VAR_N};
use crate::tm::TM;

use thiserror::Error;

type RuleIdType = usize;
const INDUCTION_VAR: Variable = VAR_N;

#[derive(Debug, Clone)]
pub enum ProofStep {
    // Apply an integer count of base TM steps.
    TMSteps(CountType),
    // Apply a rule with the given ID and variable assignments.
    RuleStep {
        rule_id: RuleIdType,
        var_assignment: VarSubst,
    },
    // Apply this rule via induction.
    InductiveStep(VarSubst),
    // End proof early and treat it like a success. (For debugging.)
    Admit,
}

#[derive(Debug)]
pub enum Proof {
    // A simple non-inductive proof.
    Simple(Vec<ProofStep>),
    // An inductive proof (where we prove a base case, and then an induction step).
    Inductive {
        // TODO: Induction variable.
        // var: Variable,
        proof_base: Vec<ProofStep>,
        proof_inductive: Vec<ProofStep>,
    },
}

#[derive(Debug)]
pub struct Rule {
    init_config: Config,
    final_config: Config,
    proof: Proof,
}

#[derive(Debug)]
pub struct RuleSet {
    tm: TM,
    // Mapping from rule ID to Rule.
    // Rule n may only use rules with id < n (or induction).
    rules: Vec<Rule>,
}

// Errors while validating one step in a rule.
#[derive(Error, Debug)]
enum StepValidationError {
    #[error("Error applying {1} TM steps to config {0}: {2}")]
    TMStepError(Config, CountType, String),
    #[error("Rule {0} is not yet defined")]
    RuleNotYetDefined(RuleIdType),
    #[error("Induction variable must decrease correctly")]
    InductionVarNotDecreasing,
    #[error("Configuration does not match rule initial config {0} vs. {1}: {2}")]
    RuleConfigMismatch(Config, Config, String),
    #[error("Variable substitution error: {0}")]
    VarSubstError(#[from] VarSubstError),
    #[error("Inductive step in non-inductive proof")]
    InductiveStepInNonInductiveProof,
}

// Errors while evaluating a rule part (base or inductive).
#[derive(Error, Debug)]
enum ProofValidationError {
    #[error("Step {step_num}: {error}")]
    StepError {
        step_num: usize,
        error: StepValidationError,
    },
    #[error("Final configuration mismatch: {actual_config} != {expected_config}")]
    FinalConfigMismatch {
        actual_config: Config,
        expected_config: Config,
    },
}

// Errors while evaluating a rule.
#[derive(Error, Debug)]
enum RuleValidationError {
    // Failure in a Proof::Simple proof.
    #[error("{0}")]
    Simple(ProofValidationError),
    // Failure in a Proof::Inductive proof_base.
    #[error("Base: {0}")]
    Base(ProofValidationError),
    // Failure in a Proof::Inductive proof_inductive.
    #[error("Induction: {0}")]
    Induction(ProofValidationError),
}

#[allow(dead_code)]
#[derive(Error, Debug)]
#[error("Validation error: Rule {rule_id}: {error}")]
struct ValidationError {
    rule_id: RuleIdType,
    error: RuleValidationError,
}

fn try_apply_rule(
    config: &Config,
    rule: &Rule,
    var_subst: &VarSubst,
) -> Result<Config, StepValidationError> {
    let init_config = rule
        .init_config
        .subst(var_subst)
        .map_err(StepValidationError::VarSubstError)?;
    let final_config = rule
        .final_config
        .subst(var_subst)
        .map_err(StepValidationError::VarSubstError)?;
    config
        .replace(&init_config, &final_config)
        .map_err(|err| StepValidationError::RuleConfigMismatch(config.clone(), init_config, err))
}

fn apply_proof_step(
    tm: &TM,
    mut config: Config,
    proof_step: &ProofStep,
    prev_rules: &[Rule],
    // Only used in inductive proofs.
    // Should be set to None for non-inductive proofs (including induction base cases).
    induction_rule: Option<&Rule>,
) -> Result<Config, StepValidationError> {
    match proof_step {
        ProofStep::TMSteps(n) => {
            // Apply n base TM steps.
            config
                .step_n(tm, *n)
                .map_err(|err| StepValidationError::TMStepError(config.clone(), *n, err))?;
            Ok(config)
        }
        ProofStep::RuleStep {
            rule_id,
            var_assignment,
        } => {
            if *rule_id >= prev_rules.len() {
                return Err(StepValidationError::RuleNotYetDefined(*rule_id));
            }
            try_apply_rule(&config, &prev_rules[*rule_id], var_assignment)
        }
        ProofStep::InductiveStep(var_assignment) => {
            // Only allow induction rules in inductive proofs.
            let Some(this_rule) = induction_rule else {
                return Err(StepValidationError::InductiveStepInNonInductiveProof);
            };

            // Ensure that the induction variable is decreasing.
            // Note: When doing an inductive proof, we start by replacing n <- n+1 and
            // then only allow any uses of the rule itself with n <- n.
            if var_assignment.get(&INDUCTION_VAR) != Some(&CountExpr::var_plus(INDUCTION_VAR, 0)) {
                return Err(StepValidationError::InductionVarNotDecreasing);
            }
            try_apply_rule(&config, this_rule, var_assignment)
        }
        ProofStep::Admit => Ok(config),
    }
}

// Apply all steps in a proof and validate that the final config is correct.
fn validate_proof(
    tm: &TM,
    init_config: Config,
    proof_steps: &Vec<ProofStep>,
    final_config: Config,
    prev_rules: &[Rule],
    // Only used in inductive proofs.
    // Should be set to None for non-inductive proofs (including induction base cases).
    induction_rule: Option<&Rule>,
) -> Result<(), ProofValidationError> {
    let mut config = init_config;
    for (step_num, step) in proof_steps.iter().enumerate() {
        if matches!(step, ProofStep::Admit) {
            return Ok(());
        }
        config = apply_proof_step(tm, config, step, prev_rules, induction_rule)
            .map_err(|error| ProofValidationError::StepError { step_num, error })?;
    }
    if config.equivalent_to(&final_config) {
        Ok(())
    } else {
        Err(ProofValidationError::FinalConfigMismatch {
            actual_config: config,
            expected_config: final_config,
        })
    }
}

fn validate_rule(tm: &TM, rule: &Rule, prev_rules: &[Rule]) -> Result<(), RuleValidationError> {
    match &rule.proof {
        Proof::Simple(proof) => validate_proof(
            tm,
            rule.init_config.clone(),
            &proof,
            rule.final_config.clone(),
            prev_rules,
            None,
        )
        .map_err(RuleValidationError::Simple),
        Proof::Inductive {
            proof_base,
            proof_inductive,
        } => {
            // Validate the base case (n <- 0).
            let base_subst = VarSubst::single(INDUCTION_VAR, 0.into());
            validate_proof(
                tm,
                rule.init_config.subst(&base_subst).unwrap(),
                &proof_base,
                rule.final_config.subst(&base_subst).unwrap(),
                prev_rules,
                None,
            )
            .map_err(RuleValidationError::Base)?;

            // Validate the inductive case (n <- m+1).
            let induct_subst =
                VarSubst::single(INDUCTION_VAR, CountExpr::var_plus(INDUCTION_VAR, 1));
            validate_proof(
                tm,
                rule.init_config.subst(&induct_subst).unwrap(),
                &proof_inductive,
                rule.final_config.subst(&induct_subst).unwrap(),
                prev_rules,
                Some(rule),
            )
            .map_err(RuleValidationError::Induction)
        }
    }
}

// Validate a rule set.
#[allow(dead_code)]
fn validate_rule_set(rule_set: &RuleSet) -> Result<(), ValidationError> {
    for (rule_id, rule) in rule_set.rules.iter().enumerate() {
        validate_rule(&rule_set.tm, rule, &rule_set.rules[..rule_id])
            .map_err(|error| ValidationError { rule_id, error })?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use std::{str::FromStr, vec};

    use crate::count_expr::{Function, RecursiveExpr};

    use super::*;

    // Helper functions to create proof steps of various kinds.
    fn base_step(num_steps: CountType) -> ProofStep {
        ProofStep::TMSteps(num_steps)
    }

    fn load_vars(var_assign: &[(&str, &str)]) -> VarSubst {
        let mut var_subst = VarSubst::default();
        for (var, count) in var_assign {
            var_subst.insert(
                Variable::from_str(var).unwrap(),
                CountExpr::from_str(count).unwrap(),
            );
        }
        var_subst
    }

    fn rule_step(rule_num: RuleIdType, var_assign: &[(&str, &str)]) -> ProofStep {
        ProofStep::RuleStep {
            rule_id: rule_num,
            var_assignment: load_vars(var_assign),
        }
    }

    fn chain_step(rule_num: RuleIdType, num_reps: &str) -> ProofStep {
        rule_step(rule_num, &[("n", num_reps)])
    }

    fn induction_step(var_assign: &[(&str, &str)]) -> ProofStep {
        let mut var_subst = load_vars(var_assign);
        // Add default n->n inductive bit.
        var_subst.insert(INDUCTION_VAR, INDUCTION_VAR.into());
        ProofStep::InductiveStep(var_subst)
    }

    fn induction_step_expr(var_assign: &[(Variable, CountExpr)]) -> ProofStep {
        let mut var_subst = VarSubst::default();
        for (var, expr) in var_assign {
            var_subst.insert(var.clone(), expr.clone());
        }
        // Add default n->n inductive bit.
        var_subst.insert(INDUCTION_VAR, INDUCTION_VAR.into());
        ProofStep::InductiveStep(var_subst)
    }

    fn simple_rule(start: &str, end: &str, steps: CountType) -> Rule {
        Rule {
            init_config: Config::from_str(start).unwrap(),
            final_config: Config::from_str(end).unwrap(),
            proof: Proof::Simple(vec![base_step(steps)]),
        }
    }

    // Helper function to create a simple chain rule for which:
    //    A) The base case is trivial.
    //    B) The inductive case is simple inductive step + `steps` TM steps.
    // Note: We currently need to do induction step first in order to work
    // around fragile tape comparison issues for blocks. Specifically, the fact that
    //      0^1 1^1 01^n  ==  01^n+1
    // which our current tape comparison cannot equate.
    fn chain_rule(start: &str, end: &str, steps: CountType) -> Rule {
        Rule {
            init_config: Config::from_str(start).unwrap(),
            final_config: Config::from_str(end).unwrap(),
            proof: Proof::Inductive {
                proof_base: vec![],
                proof_inductive: vec![induction_step(&[]), base_step(steps)],
            },
        }
    }

    #[test]
    fn test_validate_rule_trivial() {
        // Validate a very trivial rule which does nothing.
        let tm = TM::from_str("1RB1LB_1LA1RZ").unwrap();
        let rule = Rule {
            init_config: Config::from_str("0^inf 1^138 B> 0 1^2 0^inf").unwrap(),
            final_config: Config::from_str("0^inf 1^138 B> 0 1^2 0^inf").unwrap(),
            proof: Proof::Simple(vec![]),
        };
        let prev_rules = vec![];
        validate_rule(&tm, &rule, &prev_rules).unwrap();
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
            proof: Proof::Simple(vec![base_step(6)]),
        };
        let prev_rules = vec![];
        validate_rule(&tm, &rule, &prev_rules).unwrap();
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
            proof: Proof::Inductive {
                // Base case is trivial:  0^0 <C  ==  <C 1^0
                proof_base: vec![],
                proof_inductive: vec![
                    // 0^n+1 <C  ->  0^n <C 1
                    base_step(1),
                    // 0^n <C 1  ->  <C 1^n 1  ==  <C 1^n+1
                    induction_step(&[]),
                ],
            },
        };
        let prev_rules = vec![];
        validate_rule(&tm, &rule, &prev_rules).unwrap();
    }

    #[test]
    fn test_validate_rule_level1() {
        // Validate a "level 1" rule (rule built only on chain rules). This is Rule 1x from:
        //      https://www.sligocki.com/2022/02/27/bb-recurrence-relations.html
        let rule_set = RuleSet {
            tm: TM::from_str("1RB0LB1LA_2LC2LB2LB_2RC2RA0LC").unwrap(),
            rules: vec![
                chain_rule("C> 0^n", "2^n C>", 1),
                chain_rule("2^n <C", "<C 0^n", 1),
                // Rule 1x: 0^inf <C 0^a 2^n  ->  0^inf <C 0^a+2n
                Rule {
                    init_config: Config::from_str("0^inf <C 0^a 2^n").unwrap(),
                    final_config: Config::from_str("0^inf <C 0^a+2n").unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 0^inf <C 0^a 2^n+1  ->  0^inf 2 C> 0^a 2^n+1
                            base_step(1),
                            // 0^inf 2 C> 0^a 2^n+1  ->  0^inf 2^a+1 C> 2^n+1
                            chain_step(0, "a"),
                            // 0^inf 2^a+1 C> 2^n+1  ->  0^inf 2^a+1 <C 0 2^n
                            base_step(1),
                            // 0^inf 2^a+1 <C 0 2^n  ->  0^inf <C 0^a+2 2^n
                            chain_step(1, "a+1"),
                            // Induction: 0^inf <C 0^a+2 2^n  ->  0^inf <C 0^a+2n+2
                            induction_step(&[("a", "a+2")]),
                        ],
                    },
                },
            ],
        };
        validate_rule_set(&rule_set).unwrap();
    }

    #[test]
    fn test_validate_rule_counter() {
        // Validate a binary counter rule which uses the inductive hypothesis twice!
        //      See: https://www.sligocki.com/2022/06/14/counter-induction.html
        let rule_set = RuleSet {
            tm: TM::from_str("1RB1LA_0LC0RB_0LD0LB_1RE---_1LE1LA").unwrap(),
            rules: vec![
                chain_rule("1^n <A", "<A 1^n", 1),
                chain_rule("B> 1^n", "0^n B>", 1),
                // Rule P(n): 0^n 1 00 B> 0  ->  1^n+1 00 B> 0
                Rule {
                    init_config: Config::from_str("0^n 1 0 0 B> 0").unwrap(),
                    final_config: Config::from_str("1^n+1 0 0 B> 0").unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 0^n+1 1 00 B> 0  ->  0 1^n+1 00 B> 0
                            induction_step(&[]),
                            // 0 1^n+1 00 B> 0  --(5)-->  0 1^n+1 <A 110
                            base_step(5),
                            // 0 1^n+1 <A 110  -->  0 <A 1^n+3 0
                            chain_step(0, "n+1"),
                            // 0 <A 1^n+3 0  --(1)-->  1 B> 1^n+3 0
                            base_step(1),
                            // 1 B> 1^n+3 0  --(5)-->  0^n+3 B> 0
                            chain_step(1, "n+3"),
                            // 0^n+3 B> 0  --(8)-->  1 0^n 1 00 B> 0
                            base_step(8),
                            // 1 0^n 1 00 B> 0  -->  1^n+2 00 B> 0
                            induction_step(&[]),
                        ],
                    },
                },
                // Infinite Rule: 0^inf 1 00 B> 0  ->  0^inf 1^n+1 00 B> 0
                Rule {
                    init_config: Config::from_str("0^inf 1 0 0 B> 0").unwrap(),
                    final_config: Config::from_str("0^inf 1^n+1 0 0 B> 0").unwrap(),
                    proof: Proof::Simple(vec![
                        // 0^inf 1 00 B> 0  ->  0^inf 1^n+2 00 B> 0
                        rule_step(2, &[("n", "n")]),
                    ]),
                },
            ],
        };
        if let Err(err) = validate_rule_set(&rule_set) {
            panic!("{}", err);
        }
    }

    #[test]
    fn test_bouncer() {
        // Simple Bouncer
        // 1RB0RC_0LC---_1RD1RC_0LE1RA_1RD1LE

        fn f(n: CountExpr) -> CountExpr {
            CountExpr::RecursiveExpr(RecursiveExpr {
                func: Box::new(Function {
                    bound_var: "z".parse().unwrap(),
                    expr: "2z+4".parse().unwrap(),
                }),
                num_repeats: Box::new(n),
                base: Box::new(0.into()),
            })
        }

        let rule_set = RuleSet {
            tm: TM::from_str("1RB0RC_0LC---_1RD1RC_0LE1RA_1RD1LE").unwrap(),
            rules: vec![
                chain_rule("C> 1^n", "1^n C>", 1), // 0
                chain_rule("1^n <E", "<E 1^n", 1), // 1
                // 2: 0^inf 1^a A> 1^b 0^inf  -->  0^inf 1^{a+2} A> 1^{b-1} 0^inf  in 2b+4 steps
                Rule {
                    init_config: Config::from_str("0^inf 1^a A> 1^n 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 1^a+2n A> 0^inf").unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 0^inf 1^a A> 1^n+1 0^inf
                            base_step(1),
                            // 0^inf 1^a 0 C> 1^n 0^inf
                            chain_step(0, "n"),
                            // 0^inf 1^a 0 1^n C> 0^inf
                            base_step(2),
                            // 0^inf 1^a 0 1^n+1 <E 0^inf
                            chain_step(1, "n+1"),
                            // 0^inf 1^a 0 <E 1^n+1 0^inf
                            base_step(2),
                            // 0^inf 1^a+2 A> 1^n 0^inf
                            induction_step(&[("a", "a+2")]),
                        ],
                    },
                },
                // 3: 0^inf 1^a A> 0^inf  -->  0^inf 1^{2a + 6} A> 0^inf    in a^2 + 12a + 35 steps
                Rule {
                    init_config: Config::from_str("0^inf 1^a A> 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 1^2a+4 A> 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        // 0^inf 1^a A> 0^inf
                        base_step(5),
                        // 0^inf 1^a+2 <E 0^inf
                        chain_step(1, "a+2"),
                        // 0^inf <E 1^a+2 0^inf
                        base_step(2),
                        // 0^inf 1^2 A> 1^a+1 0^inf
                        rule_step(2, &[("a", "2"), ("n", "a+1")]),
                        // 0^inf 1^2f+4 A> 0^inf
                    ]),
                },
                // Infinite Rule
                Rule {
                    init_config: Config::new(),
                    final_config: Config::from_str("0^inf 1^x A> 0^inf")
                        .unwrap()
                        .subst(&VarSubst::single(
                            Variable::from_str("x").unwrap(),
                            f("n".parse().unwrap()),
                        ))
                        .unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![
                            // TODO: Need 0^inf 1^{(λz.2z+4)^0 0} A> == 0^inf 1^0 A> == 0^inf A>
                            ProofStep::Admit,
                        ],
                        proof_inductive: vec![
                            induction_step_expr(&[]),
                            // 0^inf 1^{f^n(0)} A> 0^inf
                            ProofStep::RuleStep {
                                rule_id: 3,
                                var_assignment: VarSubst::single(
                                    Variable::from_str("a").unwrap(),
                                    f("n".parse().unwrap()),
                                ),
                            },
                            // 0^inf 1^{f^n+1(0)} A> 0^inf
                        ],
                    },
                },
            ],
        };
        if let Err(err) = validate_rule_set(&rule_set) {
            panic!("{}", err);
        }
    }

    #[test]
    fn test_hydra() {
        // https://www.sligocki.com/2024/05/10/bb-2-5-is-hard.html
        // 1RB3RB---3LA1RA_2LA3RA4LB0LB0LA
        // Let A(a, b) = 0^inf <B 0^a 3^b 2 0^inf

        let rule_set = RuleSet {
            tm: TM::from_str("1RB3RB1RZ3LA1RA_2LA3RA4LB0LB0LA").unwrap(),
            rules: vec![
                chain_rule("3^n <A", "<A 3^n", 1),     // 0
                chain_rule("3^n <B", "<B 0^n", 1),     // 1
                chain_rule("1 B> 3^n", "3^n 1 B>", 3), // 2
                // 3:  0^inf 3^a 1 A> 00  -->  0^inf 3^a+3 1 A>
                Rule {
                    init_config: Config::from_str("0^inf 3^a 1 A> 0^2n").unwrap(),
                    final_config: Config::from_str("0^inf 3^3n+a 1 A>").unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 0^inf 3^a 1 A> 00
                            base_step(12),
                            // 0^inf 3^a <A 332
                            chain_step(0, "a"),
                            // 0^inf <A 3^a+2 2
                            base_step(1),
                            // 0^inf 1 B> 3^a+2 2
                            chain_step(2, "a+2"),
                            // 0^inf 3^a+2 1 B> 2
                            base_step(3),
                            // 0^inf 3^a+3 1 A>
                            induction_step(&[("a", "a+3")]),
                        ],
                    },
                },
                // Collatz rules
                // A(2n, 0)  -->  Halt(3n+3)
                Rule {
                    init_config: Config::from_str("0^inf <B 0^2n 3^0 2 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 3^3n+1 11 Z> 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        // 0^inf <B 0^2n 2 0^inf
                        base_step(5),
                        // 0^inf 3 1 A> 0^2n 2 0^inf
                        rule_step(3, &[("a", "1"), ("n", "n")]),
                        // 0^inf 3^3n+1 1 A> 2 0^inf
                        base_step(1),
                        // 0^inf 3^3n+1 11 Z> 0^inf
                    ]),
                },
                // A(2n, b+1)  -->  A(3n+3, b)
                Rule {
                    init_config: Config::from_str("0^inf <B 0^2n 3^b+1 2 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf <B 0^3n+3 3^b 2 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        // 0^inf <B 0^2n 3^b+1 2 0^inf
                        base_step(5),
                        // 0^inf 3 1 A> 0^2n 3^b+1 2 0^inf
                        rule_step(3, &[("a", "1"), ("n", "n")]),
                        // 0^inf 3^3n+1 1 A> 3^b+1 2 0^inf
                        base_step(3),
                        // 0^inf 3^3n+2 <B 0 3^b 2 0^inf
                        chain_step(1, "3n+2"),
                        // 0^inf <B 0^3n+3 3^b 2 0^inf
                    ]),
                },
                // A(2n+1, b)  -->  A(3n+3, b+2)
                Rule {
                    init_config: Config::from_str("0^inf <B 0^2n+1 3^b 2 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf <B 0^3n+3 3^b+2 2 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        // 0^inf <B 0^2n+1 3^b 2 0^inf
                        base_step(5),
                        // 0^inf 3 1 A> 0^2n+1 3^b 2 0^inf
                        rule_step(3, &[("a", "1"), ("n", "n")]),
                        // 0^inf 3^3n+1 1 A> 0 3^b 2 0^inf
                        base_step(1),
                        // 0^inf 3^3n+1 1 1 B> 3^b 2 0^inf
                        chain_step(2, "b"),
                        // 0^inf 3^3n+1 1 3^b 1 B> 2 0^inf
                        base_step(13),
                        // 0^inf 3^3n+1 1 3^b+3 <A 2 0^inf
                        chain_step(0, "b+3"),
                        // 0^inf 3^3n+1 1 <A 3^b+3 2 0^inf
                        base_step(2),
                        // 0^inf 3^3n+2 <B 0 3^b+3 2 0^inf
                        chain_step(1, "3n+2"),
                        // 0^inf <B 0^3n+3 3^b+2 2 0^inf
                    ]),
                },
                // 0^inf A> 0^inf  --(19)-->  A(3, 0)
                Rule {
                    init_config: Config::new(),
                    final_config: Config::from_str("0^inf <B 0^3 3^0 2 0^inf").unwrap(),
                    proof: Proof::Simple(vec![base_step(19)]),
                },
            ],
        };
        if let Err(err) = validate_rule_set(&rule_set) {
            panic!("{}", err);
        }
    }

    #[test]
    fn test_hydra2() {
        // Hydra compiled into 2 states by @dyuan01
        // https://discord.com/channels/960643023006490684/1084047886494470185/1247560072427474955
        //      0RE1RG_1RH0LD_0LA0LF_0LB1LJ_1RB1RA_1RE1LC_0LF---_1LF0LI_0LD0LC_1RE0RH
        //
        // Left:
        //   0: 00
        //   1: 01
        //   3: 11
        // Right:
        //   0: 00
        //   2: 11
        //   3: 10
        //   4: 01
        // States:
        //   A>: A>
        //   B>: B>
        //   <A: <C
        //   <B: <D

        let rule_set = RuleSet {
            tm: TM::from_str(
                "0RE1RG_1RH0LD_0LA0LF_0LB1LJ_1RB1RA_1RE1LC_0LF1RZ_1LF0LI_0LD0LC_1RE0RH",
            )
            .unwrap(),
            rules: vec![
                chain_rule("11^n <C", "<C 10^n", 2),       // 0
                chain_rule("11^n <D", "<D 00^n", 4),       // 1
                chain_rule("01 B> 10^n", "11^n 01 B>", 6), // 2
                // 3:  0^inf 3^a 1 A> 00  -->  0^inf 3^a+3 1 A>
                Rule {
                    init_config: Config::from_str("0^inf 11^a 01 A> 00^2n").unwrap(),
                    final_config: Config::from_str("0^inf 11^3n+a 01 A>").unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 0^inf 3^a 1 A> 00
                            base_step(31),
                            // 0^inf 3^a <A 332
                            chain_step(0, "a"),
                            // 0^inf <A 3^a+2 2
                            base_step(3),
                            // 0^inf 1 B> 3^a+2 2
                            chain_step(2, "a"),
                            chain_step(2, "2"),
                            // 0^inf 3^a+2 1 B> 2
                            base_step(6),
                            // 0^inf 3^a+3 1 A>
                            induction_step(&[("a", "a+3")]),
                        ],
                    },
                },
                // Collatz rules
                // 4: A(2n, 0)  -->  Halt(3n+3)
                Rule {
                    init_config: Config::from_str("0^inf <D 00^2n 10^0 11 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 11^3n+1 01 11 Z> 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        // 0^inf <B 0^2n 2 0^inf
                        base_step(13),
                        // 0^inf 3 1 A> 0^2n 2 0^inf
                        rule_step(3, &[("a", "1"), ("n", "n")]),
                        // 0^inf 3^3n+1 1 A> 2 0^inf
                        base_step(2),
                        // 0^inf 3^3n+1 11 Z> 0^inf
                    ]),
                },
                simple_rule("<D 00", "<D 00", 0), // 5
                // 6: A(2n, b+1)  -->  A(3n+3, b)
                Rule {
                    init_config: Config::from_str("0^inf <D 00^2n 10^b+1 11 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf <D 00^3n+3 10^b 11 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        // 0^inf <B 0^2n 3^b+1 2 0^inf
                        base_step(13),
                        // 0^inf 3 1 A> 0^2n 3^b+1 2 0^inf
                        rule_step(3, &[("a", "1"), ("n", "n")]),
                        // 0^inf 3^3n+1 1 A> 3^b+1 2 0^inf
                        base_step(7),
                        rule_step(5, &[]),
                        // 0^inf 3^3n+2 <B 0 3^b 2 0^inf
                        chain_step(1, "3n+2"),
                        // 0^inf <B 0^3n+3 3^b 2 0^inf
                    ]),
                },
                // 7: A(2n+1, b)  -->  A(3n+3, b+2)
                Rule {
                    init_config: Config::from_str("0^inf <D 00^2n+1 10^b 11 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf <D 00^3n+3 10^b+2 11 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        // 0^inf <B 0^2n+1 3^b 2 0^inf
                        base_step(13),
                        // 0^inf 3 1 A> 0^2n+1 3^b 2 0^inf
                        rule_step(3, &[("a", "1"), ("n", "n")]),
                        // 0^inf 3^3n+1 1 A> 0 3^b 2 0^inf
                        base_step(2),
                        // 0^inf 3^3n+1 1 1 B> 3^b 2 0^inf
                        chain_step(2, "b"),
                        // 0^inf 3^3n+1 1 3^b 1 B> 2 0^inf
                        base_step(33),
                        // 0^inf 3^3n+1 1 3^b+3 <A 2 0^inf
                        chain_step(0, "b+3"),
                        // 0^inf 3^3n+1 1 <A 3^b+3 2 0^inf
                        base_step(4),
                        rule_step(5, &[]),
                        // 0^inf 3^3n+2 <B 0 3^b+3 2 0^inf
                        chain_step(1, "3n+2"),
                        // 0^inf <B 0^3n+3 3^b+2 2 0^inf
                    ]),
                },
                // 0^inf A> 0^inf  -->  A(3, 0)
                Rule {
                    init_config: Config::new(),
                    final_config: Config::from_str("0^inf <D 00^3 10^0 11 0^inf").unwrap(),
                    proof: Proof::Simple(vec![base_step(51)]),
                },
            ],
        };
        if let Err(err) = validate_rule_set(&rule_set) {
            panic!("{}", err);
        }
    }

    #[test]
    fn test_antihydra() {
        // https://wiki.bbchallenge.org/wiki/Antihydra
        // 1RB1RA_0LC1LE_1LD1LC_1LA0LB_1LF1RE_---0RA
        // Let A(a+4, b) = 0^inf 1^b 0 1^a E> 0^inf

        let rule_set = RuleSet {
            tm: TM::from_str("1RB1RA_0LC1LE_1LD1LC_1LA0LB_1LF1RE_1RZ0RA").unwrap(),
            rules: vec![
                chain_rule("A> 1^n", "1^n A>", 1), // 0
                chain_rule("1^n <C", "<C 1^n", 1), // 1
                chain_rule("E> 1^n", "1^n E>", 1), // 2
                // 3: 11 <B 0 1^c 0^inf -> <B 0 1^c+3 0^inf
                Rule {
                    init_config: Config::from_str("1^2n <B 0 1^c 0^inf").unwrap(),
                    final_config: Config::from_str("<B 0 1^c+3n 0^inf").unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 11 <B 0 1^c $
                            base_step(6),
                            // 101 A> 1^c $
                            chain_step(0, "c"),
                            base_step(2),
                            // 1 0 1^c+2 <C $
                            chain_step(1, "c+2"),
                            base_step(2),
                            // <B 0 1^c+3
                            induction_step(&[("c", "c+3")]),
                        ],
                    },
                },
                // 4: A(2a, b) -> A(3a, b+2)
                Rule {
                    init_config: Config::from_str("0^inf 1^b 0 1^2a+2 E> 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 1^b+2 0 1^3a+5 E> 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        base_step(9),
                        // $ 1^b 0 1^2a <B 0 111 $
                        rule_step(3, &[("n", "a"), ("c", "3")]),
                        // $ 1^b 0 <B 0 1^3a+3 $
                        base_step(1),
                        chain_step(1, "b"),
                        base_step(5),
                        // $ 1 E> 1^b+2 00 1^3a+3 $
                        chain_step(2, "b+2"),
                        base_step(6),
                        chain_step(2, "3a+3"),
                    ]),
                },
                // 5: A(2a+1, 0) -> Halt
                Rule {
                    init_config: Config::from_str("0^inf 1^0 0 1^2a+3 E> 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 1 Z> 110 1^3a+3 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        base_step(9),
                        // $ 1^2a+1 <B 0 111 $
                        rule_step(3, &[("n", "a"), ("c", "3")]),
                        // $ 1 <B 0 1^3a+3 $
                        base_step(3),
                    ]),
                },
                // 6: A(2a+1, b+1) -> A(3a+1, b)
                Rule {
                    init_config: Config::from_str("10 1^2a+3 E> 0^inf").unwrap(),
                    final_config: Config::from_str("0 1^3a+6 E> 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        base_step(9),
                        // 10 1^2a+1 <B 0 111 $
                        rule_step(3, &[("n", "a"), ("c", "3")]),
                        // 101 <B 0 1^3a+3 $
                        base_step(8),
                        // 0 111 E> 1^3a+3 $
                        chain_step(2, "3a+3"),
                    ]),
                },
                // 0^inf A> 0^inf  -->  A(8, 0)  --->  A(202, 10)
                Rule {
                    init_config: Config::new(),
                    final_config: Config::from_str("0^inf 1^10 0 1^198 E> 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        base_step(11),
                        // A(8, 0)
                        rule_step(4, &[("a", "1"), ("b", "0")]),
                        // A(12, 2)
                        rule_step(4, &[("a", "3"), ("b", "2")]),
                        // A(18, 4)
                        rule_step(4, &[("a", "6"), ("b", "4")]),
                        // A(27, 6)
                        rule_step(6, &[("a", "10"), ("b", "6")]),
                        // A(40, 5)
                        rule_step(4, &[("a", "17"), ("b", "5")]),
                        // A(60, 7)
                        rule_step(4, &[("a", "27"), ("b", "7")]),
                        // A(90, 9)
                        rule_step(4, &[("a", "42"), ("b", "9")]),
                        // A(135, 11)
                        rule_step(6, &[("a", "64"), ("b", "11")]),
                        // A(202, 10)
                    ]),
                },
            ],
        };
        if let Err(err) = validate_rule_set(&rule_set) {
            panic!("{}", err);
        }
    }

    #[test]
    fn test_bigfoot() {
        // https://www.sligocki.com/2023/10/16/bb-3-3-is-hard.html
        // 1RB2RA1LC_2LC1RB2RB_---2LA1LA
        // Let A(a, b, c) = 0^inf 12^a 11^b <A 11^c 0^inf

        let rule_set = RuleSet {
            tm: TM::from_str("1RB2RA1LC_2LC1RB2RB_1RZ2LA1LA").unwrap(),
            rules: vec![
                chain_rule("A> 1^n", "2^n A>", 1),   // 0
                chain_rule("2^2n <A", "<A 1^2n", 2), // 1
                // 2: 1^n <A 1^2c 2^n  -->  <A 1^2c+2n
                Rule {
                    init_config: Config::from_str("1^n <A 1^2c 2^n").unwrap(),
                    final_config: Config::from_str("<A 1^2c+2n").unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 1 <A 1^2c 2
                            base_step(1),
                            // 2 A> 1^2c 2
                            chain_step(0, "2c"),
                            // 2^2c+1 A> 2
                            base_step(2),
                            chain_step(1, "c"),
                            // <A 1^2c+2
                            induction_step(&[("c", "c+1")]),
                        ],
                    },
                },
                // 3: 1^3n <A 1^2c+1 2^n  -->  <A 1^2c+1+4n
                Rule {
                    init_config: Config::from_str("1^3n <A 1^2c+1 2^n").unwrap(),
                    final_config: Config::from_str("<A 1^2c+1+4n").unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 111 <A 1^2c+1 2
                            base_step(1),
                            // 11 2 A> 1^2c+1 2
                            chain_step(0, "2c+1"),
                            // 11 2^2c+2 A> 2
                            base_step(2),
                            chain_step(1, "c"),
                            // 11 2 <A 1^2c+2
                            base_step(5),
                            // <A 1^2c+5
                            induction_step(&[("c", "c+2")]),
                        ],
                    },
                },
                // 4:  1^12 <A 1^2c 0^inf  -->  <A 1^2c+16 0^inf
                Rule {
                    init_config: Config::from_str("1^12n <A 1^2c 0^inf").unwrap(),
                    final_config: Config::from_str("<A 1^2c+16n 0^inf").unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 1^12 <A 1^2c 0^inf
                            base_step(1),
                            chain_step(0, "2c"),
                            // 1^11 2^2c+1 A> 0^inf
                            base_step(3),
                            // 1^11 2^2c+1 <A 22 0^inf
                            chain_step(1, "c"),
                            // 1^11 2 <A 1^2c 22 0^inf
                            base_step(5),
                            // 1^9 <A 1^2c+3 22 0^inf
                            rule_step(3, &[("n", "2"), ("c", "c+1")]),
                            // 1^3 <A 1^2c+11 0^inf
                            base_step(1),
                            chain_step(0, "2c+11"),
                            // 1^2 2^2c+12 A> 0^inf
                            base_step(3),
                            // 1^2 2^2c+12 <A 22 0^inf
                            chain_step(1, "c+6"),
                            // 1^2 <A 1^2c+12 22 0^inf
                            rule_step(2, &[("n", "2"), ("c", "c+6")]),
                            // <A 1^2c+16 0^inf
                            induction_step(&[("c", "c+8")]),
                        ],
                    },
                },
                // 5:  0^inf 12^n <A  -->  0^inf 12^n 1 B>
                Rule {
                    init_config: Config::from_str("0^inf 12^n <A").unwrap(),
                    final_config: Config::from_str("0^inf 12^n 1 B>").unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![base_step(1)],
                        proof_inductive: vec![
                            // 0^inf 12^n+1 <A
                            base_step(2),
                            // 0^inf 12^n <A 21
                            induction_step(&[]),
                            // 0^inf 12^n 1 B> 21
                            base_step(2),
                        ],
                    },
                },
                chain_rule("B> 1^n", "1^n B>", 1), // 6
                // Collatz rules
                // A(a, 6k, c+1)  -->  A(a, 8k+c, 2)
                Rule {
                    init_config: Config::from_str("0^inf 12^a 1^12k <A 1^2c+2 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 12^a 1^16k+2c <A 1^4 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        // 0^inf 12^a 1^12k <A 1^2c+2 0^inf
                        rule_step(4, &[("n", "k"), ("c", "c+1")]),
                        // 0^inf 12^a <A 1^2c+2+16k 0^inf
                        rule_step(5, &[("n", "a")]),
                        // 0^inf 12^a 1 B> 1^2c+2+16k 0^inf
                        chain_step(6, "2c+2+16k"),
                        // 0^inf 12^a 1^16k+2c+3 B> 0^inf
                        base_step(12),
                        // 0^inf 12^a 1^16k+2c <A 1^4 0^inf
                    ]),
                },
                // A(a, 6k+1, c+1)  -->  A(a, 8k+c, 2)
                Rule {
                    init_config: Config::from_str("0^inf 12^a 1^12k+2 <A 1^2c+2 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 12^a+1 1^16k+2c <A 1^6 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        // 0^inf 12^a 1^12k+2 <A 1^2c+2 0^inf
                        rule_step(4, &[("n", "k"), ("c", "c+1")]),
                        // 0^inf 12^a 11 <A 1^2c+2+16k 0^inf
                        ProofStep::Admit, // TODO
                    ]),
                },
                // TODO: Rest of rules:
                // ...
                // 0^inf A> 0^inf  --(69)-->  A(2, 1, 2)
                Rule {
                    init_config: Config::new(),
                    final_config: Config::from_str("0^inf 12^2 1^2 <A 1^4 0^inf").unwrap(),
                    proof: Proof::Simple(vec![base_step(69)]),
                },
            ],
        };
        if let Err(err) = validate_rule_set(&rule_set) {
            panic!("{}", err);
        }
    }

    #[test]
    fn test_62_halt_cryptid1() {
        // https://wiki.bbchallenge.org/wiki/1RB1RA_0RC1RC_1LD0LF_0LE1LE_1RA0LB_---0LC
        // Probviously halting BB(6) Cryptid
        // C(a, b, c) = $ 1^2a+1 C> 0^2b 1^c 01 $

        let rule_set = RuleSet {
            tm: TM::from_str("1RB1RA_0RC1RC_1LD0LF_0LE1LE_1RA1LD_1RZ0LC").unwrap(),
            rules: vec![
                chain_rule("1^2n <E", "<E 1^2n", 2), // 0
                chain_rule("A> 1^n", "1^n A>", 1),   // 1
                // 2: 0 1^2a+1 C> 0 -> 1^2a+3 A>
                Rule {
                    init_config: Config::from_str("0 1^2a+1 C> 0").unwrap(),
                    final_config: Config::from_str("1^2a+3 A>").unwrap(),
                    proof: Proof::Simple(vec![
                        // 0 1^2a+1 C> 0
                        base_step(2),
                        // 0 1^2a <E 11
                        chain_step(0, "a"),
                        // 0^ <E 1^2a+2
                        base_step(1),
                        chain_step(1, "2a+2"),
                        // 1^2a+3 A>
                    ]),
                },
                // 3: C(a, b+2, c)  ->  C(a+3, b, c)
                Rule {
                    init_config: Config::from_str("0^inf 1^2a+1 C> 0^4n").unwrap(),
                    final_config: Config::from_str("0^inf 1^2a+6n+1 C>").unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 0^inf 1^2a+1 C> 0^4
                            rule_step(2, &[("a", "a")]),
                            // 0^inf 1^2a+3 A> 0^3
                            base_step(4),
                            // 0^inf 1^2a+4 <E 01
                            chain_step(0, "a+2"),
                            // 0^inf <E 1^2a+4 01
                            base_step(1),
                            chain_step(1, "2a+4"),
                            // 0^inf 1^2a+5 A> 01
                            base_step(2),
                            // 0^inf 1^2a+7 C>
                            induction_step(&[("a", "a+3")]),
                        ],
                    },
                },
                chain_rule("1^2n <C", "<C 0^2n", 2), // 4
                // 5: C(1, 2b, c+1) -> C(1, 3b+2, c)
                Rule {
                    init_config: Config::from_str("0^inf 1^3 C> 0^4n 1").unwrap(),
                    final_config: Config::from_str("0^inf 1^3 C> 0^6n+4").unwrap(),
                    proof: Proof::Simple(vec![
                        rule_step(3, &[("a", "1"), ("n", "n")]),
                        // 0^inf 1^6n+3 C> 1
                        base_step(2),
                        chain_step(4, "3n+1"),
                        // 0^inf <C 0^6n+4
                        base_step(5),
                    ]),
                },
                // 6: C(1, 2b+1, c+2) -> C(1, 3b+4, c)
                Rule {
                    init_config: Config::from_str("0^inf 1^3 C> 0^4n+2 11").unwrap(),
                    final_config: Config::from_str("0^inf 1^3 C> 0^6n+8").unwrap(),
                    proof: Proof::Simple(vec![
                        rule_step(3, &[("a", "1"), ("n", "n")]),
                        // 0^inf 1^6n+3 C> 0011
                        rule_step(2, &[("a", "3n+1")]),
                        // 0^inf 1^6n+5 A> 011
                        base_step(4),
                        chain_step(4, "3n+3"),
                        // 0^inf <C 0^6n+8
                        base_step(5),
                    ]),
                },
                // 7: C(1, 2b, 0) -> C(1, 2, 6b+5)
                Rule {
                    init_config: Config::from_str("0^inf 1^3 C> 0^4n 01 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 1^3 C> 0^4 1^6n+5 01 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        rule_step(3, &[("a", "1"), ("n", "n")]),
                        // 0^inf 1^6n+3 C> 01 0^inf
                        rule_step(2, &[("a", "3n+1")]),
                        // 0^inf 1^6n+5 A> 1 0^inf
                        base_step(5),
                        // 0^inf 1^6n+7 <E 01 0^inf
                        chain_step(0, "3n+3"),
                        // 0^inf 1 <E 1^6n+6 01 0^inf
                        base_step(14),
                        // 0^inf 1^3 C> 0^4 1^6n+5 01 0^inf
                    ]),
                },
                // 8: 0^inf 1^2a+1 A> 1 0^inf -> 0^inf 1^3 C> 0^4 1^2a+1 01 0^inf
                Rule {
                    init_config: Config::from_str("0^inf 1^2a+1 A> 1 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 1^3 C> 0^4 1^2a+1 01 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        // 0^inf 1^2a+1 A> 1 0^inf
                        base_step(5),
                        // 0^inf 1^2a+3 <E 01 0^inf
                        chain_step(0, "a+1"),
                        // 0^inf 1 <E 1^2a+2 01 0^inf
                        base_step(14),
                    ]),
                },
                // 9: C(1, 2b, 0) -> C(1, 2, 6b+5)
                Rule {
                    init_config: Config::from_str("0^inf 1^3 C> 0^4b 01 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 1^3 C> 0^4 1^6b+5 01 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        rule_step(3, &[("a", "1"), ("n", "b")]),
                        // 0^inf 1^6b+3 C> 01 0^inf
                        rule_step(2, &[("a", "3b+1")]),
                        // 0^inf 1^6b+5 A> 1 0^inf
                        rule_step(8, &[("a", "3b+2")]),
                        // 0^inf 1^3 C> 0^4 1^6b+5 01 0^inf
                    ]),
                },
                // 10: C(1, 2b+1, 1) -> C(1, 2, 6b+9)
                Rule {
                    init_config: Config::from_str("0^inf 1^3 C> 0^4b+2 1 01 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 1^3 C> 0^4 1^6b+9 01 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        rule_step(3, &[("a", "1"), ("n", "b")]),
                        // 0^inf 1^6b+3 C> 00101 0^inf
                        rule_step(2, &[("a", "3b+1")]),
                        // 0^inf 1^6b+5 A> 0101 0^inf
                        base_step(2),
                        // 0^inf 1^6b+7 C> 01 0^inf
                        rule_step(2, &[("a", "3b+3")]),
                        // 0^inf 1^6b+9 A> 1 0^inf
                        rule_step(8, &[("a", "3b+4")]),
                        // 0^inf 1^3 C> 0^4 1^6b+9 01 0^inf
                    ]),
                },
                // 11: C(1, 2b+1, 0) -> Halt(6b+7)
                Rule {
                    init_config: Config::from_str("0^inf 1^3 C> 0^4b+2 01").unwrap(),
                    final_config: Config::from_str("0^inf 1^6b+7 Z> 0").unwrap(),
                    proof: Proof::Simple(vec![
                        rule_step(3, &[("a", "1"), ("n", "b")]),
                        // 0^inf 1^6b+3 C> 0001 0^inf
                        rule_step(2, &[("a", "3b+1")]),
                        // 0^inf 1^6b+5 A> 001 0^inf
                        base_step(4),
                    ]),
                },
                // Trajectory
                // Start --(43)--> C(1, 2, 5)
                Rule {
                    init_config: Config::new(),
                    final_config: Config::from_str("0^inf 1^3 C> 0^4 1^5 01 0^inf").unwrap(),
                    proof: Proof::Simple(vec![base_step(43)]),
                },
            ],
        };
        if let Err(err) = validate_rule_set(&rule_set) {
            panic!("{}", err);
        }
    }

    #[test]
    fn test_62_halt_cryptid2() {
        // Variation of test_62_halt_cryptid1
        // Probviously halting BB(6) Cryptid
        // C(a, b, c) = $ 1^2a+1 F> 0^2b 1^c 01 $

        let rule_set = RuleSet {
            tm: TM::from_str("1RB1RA_0RC1RF_1LD1RZ_0LE1LE_1RA1LD_1LD0LF").unwrap(),
            rules: vec![
                chain_rule("1^2n <E", "<E 1^2n", 2), // 0
                chain_rule("A> 1^n", "1^n A>", 1),   // 1
                // 2: 0 1^2a+1 C> 0 -> 1^2a+3 A>
                Rule {
                    init_config: Config::from_str("0 1^2a+1 F> 0").unwrap(),
                    final_config: Config::from_str("1^2a+3 A>").unwrap(),
                    proof: Proof::Simple(vec![
                        // 0 1^2a+1 F> 0
                        base_step(2),
                        // 0 1^2a <E 11
                        chain_step(0, "a"),
                        // 0^ <E 1^2a+2
                        base_step(1),
                        chain_step(1, "2a+2"),
                        // 1^2a+3 A>
                    ]),
                },
                // 3: C(a, b+2, c)  ->  C(a+3, b, c)
                Rule {
                    init_config: Config::from_str("0^inf 1^2a+1 F> 0^4n").unwrap(),
                    final_config: Config::from_str("0^inf 1^2a+6n+1 F>").unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 0^inf 1^2a+1 F> 0^4
                            rule_step(2, &[("a", "a")]),
                            // 0^inf 1^2a+3 A> 0^3
                            base_step(4),
                            // 0^inf 1^2a+4 <E 01
                            chain_step(0, "a+2"),
                            // 0^inf <E 1^2a+4 01
                            base_step(1),
                            chain_step(1, "2a+4"),
                            // 0^inf 1^2a+5 A> 01
                            base_step(2),
                            // 0^inf 1^2a+7 F>
                            induction_step(&[("a", "a+3")]),
                        ],
                    },
                },
                chain_rule("1^2n <F", "<F 0^2n", 2), // 4
                // 5: C(1, 2b, c+1) -> C(1, 3b+2, c)
                Rule {
                    init_config: Config::from_str("0^inf 1^3 F> 0^4n 1").unwrap(),
                    final_config: Config::from_str("0^inf 1^3 F> 0^6n+4").unwrap(),
                    proof: Proof::Simple(vec![
                        rule_step(3, &[("a", "1"), ("n", "n")]),
                        // 0^inf 1^6n+3 F> 1
                        base_step(2),
                        chain_step(4, "3n+1"),
                        // 0^inf <C 0^6n+4
                        base_step(5),
                    ]),
                },
                // 6: C(1, 2b+1, c+2) -> C(1, 3b+4, c)
                Rule {
                    init_config: Config::from_str("0^inf 1^3 F> 0^4n+2 11").unwrap(),
                    final_config: Config::from_str("0^inf 1^3 F> 0^6n+8").unwrap(),
                    proof: Proof::Simple(vec![
                        rule_step(3, &[("a", "1"), ("n", "n")]),
                        // 0^inf 1^6n+3 F> 0011
                        rule_step(2, &[("a", "3n+1")]),
                        // 0^inf 1^6n+5 A> 011
                        base_step(4),
                        chain_step(4, "3n+3"),
                        // 0^inf <C 0^6n+8
                        base_step(5),
                    ]),
                },
                // 7: C(1, 2b, 0) -> C(1, 2, 6b+5)
                Rule {
                    init_config: Config::from_str("0^inf 1^3 F> 0^4n 01 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 1^3 F> 0^4 1^6n+5 01 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        rule_step(3, &[("a", "1"), ("n", "n")]),
                        // 0^inf 1^6n+3 F> 01 0^inf
                        rule_step(2, &[("a", "3n+1")]),
                        // 0^inf 1^6n+5 A> 1 0^inf
                        base_step(5),
                        // 0^inf 1^6n+7 <E 01 0^inf
                        chain_step(0, "3n+3"),
                        // 0^inf 1 <E 1^6n+6 01 0^inf
                        base_step(14),
                        // 0^inf 1^3 F> 0^4 1^6n+5 01 0^inf
                    ]),
                },
                // 8: 0^inf 1^2a+1 A> 1 0^inf -> 0^inf 1^3 F> 0^4 1^2a+1 01 0^inf
                Rule {
                    init_config: Config::from_str("0^inf 1^2a+1 A> 1 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 1^3 F> 0^4 1^2a+1 01 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        // 0^inf 1^2a+1 A> 1 0^inf
                        base_step(5),
                        // 0^inf 1^2a+3 <E 01 0^inf
                        chain_step(0, "a+1"),
                        // 0^inf 1 <E 1^2a+2 01 0^inf
                        base_step(14),
                    ]),
                },
                // 9: C(1, 2b, 0) -> C(1, 2, 6b+5)
                Rule {
                    init_config: Config::from_str("0^inf 1^3 F> 0^4b 01 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 1^3 F> 0^4 1^6b+5 01 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        rule_step(3, &[("a", "1"), ("n", "b")]),
                        // 0^inf 1^6b+3 F> 01 0^inf
                        rule_step(2, &[("a", "3b+1")]),
                        // 0^inf 1^6b+5 A> 1 0^inf
                        rule_step(8, &[("a", "3b+2")]),
                        // 0^inf 1^3 F> 0^4 1^6b+5 01 0^inf
                    ]),
                },
                // 10: C(1, 2b+1, 1) -> C(1, 2, 6b+9)
                Rule {
                    init_config: Config::from_str("0^inf 1^3 F> 0^4b+2 1 01 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 1^3 F> 0^4 1^6b+9 01 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        rule_step(3, &[("a", "1"), ("n", "b")]),
                        // 0^inf 1^6b+3 F> 00101 0^inf
                        rule_step(2, &[("a", "3b+1")]),
                        // 0^inf 1^6b+5 A> 0101 0^inf
                        base_step(2),
                        // 0^inf 1^6b+7 F> 01 0^inf
                        rule_step(2, &[("a", "3b+3")]),
                        // 0^inf 1^6b+9 A> 1 0^inf
                        rule_step(8, &[("a", "3b+4")]),
                        // 0^inf 1^3 F> 0^4 1^6b+9 01 0^inf
                    ]),
                },
                // 11: C(1, 2b+1, 0) -> Halt(6b+7)
                Rule {
                    init_config: Config::from_str("0^inf 1^3 F> 0^4b+2 01").unwrap(),
                    final_config: Config::from_str("0^inf 1^6b+5 1 0 1 Z>").unwrap(),
                    proof: Proof::Simple(vec![
                        rule_step(3, &[("a", "1"), ("n", "b")]),
                        // 0^inf 1^6b+3 F> 0001 0^inf
                        rule_step(2, &[("a", "3b+1")]),
                        // 0^inf 1^6b+5 A> 001 0^inf
                        base_step(3),
                    ]),
                },
                // Trajectory
                // Start --(43)--> C(1, 2, 5)
                Rule {
                    init_config: Config::new(),
                    final_config: Config::from_str("0^inf 1^3 F> 0^4 1^5 01 0^inf").unwrap(),
                    proof: Proof::Simple(vec![base_step(43)]),
                },
            ],
        };
        if let Err(err) = validate_rule_set(&rule_set) {
            panic!("{}", err);
        }
    }

    #[test]
    fn test_34_uni() {
        // Analysis of Pavel's 3x4 TM shared 31 May 2023:
        //      https://discord.com/channels/960643023006490684/1095740122139480195/1113545691994783804
        // Common configs:
        //      C(a, b, c, d, e) = $ 1 2^a 1 3^b 1 01^c 1 2^d <A 2^e $
        // Rules:
        //    1)    C(a, b, c,  d+2, 2e+1)  ->  C(a, b, c, d, 2 (e+2) + 1)
        //          C(a, b, c, 2k+r, 2e+1)  ->  C(a, b, c, r, 2 (e+2k) + 1)
        //    2)    C(a, b, c+1, 1, 2e+1)  ->  C(a, b, c, 2e+5, 3)
        //                                 ->  C(a, b, c, 1, 2 (2e+5) + 1)
        //          C(a, b, c, 1, 2e+1)  ->  C(a, b, 0, 1, 2 f(c, e) + 1)
        //              where f(c, e) = rep(λx -> 2x+5, c)(e)  ~= 2^c
        //    3)    C(a, b+1, 0, 1, 2e+1)  ->  C(a, b, e+2, 1, 3)
        //                                 ->  C(a, b, 0, 1, 2 f(e+2, 1) + 1)
        //          C(a, b, 0, 1, 2e+1)  ->  C(a, 0, 0, 1, 2 g(b, e) + 1)
        //              where g(b, e) = rep(λx -> f(x+2, 1), b)(e)  ~= 2^^b
        //    4)    C(a+2, 0, 0, 1, 2e+1)  ->  C(a, 2e+7, 0, 1, 3)
        //                                 ->  C(a, 0, 0, 1, 2 g(2e+7, 1) + 1)
        //          C(2a+r, 0, 0, 1, 2e+1)  ->  C(r, 0, 0, 1, 2 h(a, e) + 1)
        //              where h(a, e) = rep(λx -> g(2x+7, 1), a)(e)  ~= 2^^^a
        //    5)    C(0, 0, 0, 1, 2e+1)  ->  C(0, 0, 0, 1, 2 h(4e+19, g(1, 1)) + 1)

        // f1(x) = 2x+5
        // f2(x, y) = f1^x(y)  ~= 2^x
        fn f2(x: CountExpr, y: CountExpr) -> CountExpr {
            CountExpr::RecursiveExpr(RecursiveExpr {
                func: Box::new(Function {
                    bound_var: "x".parse().unwrap(),
                    expr: "2x+5".parse().unwrap(),
                }),
                num_repeats: Box::new(x),
                base: Box::new(y),
            })
        }
        // f3(x, y) = rep(λz -> f2(z+2, 1), x)(y) ~= 2^^x
        fn f3(x: CountExpr, y: CountExpr) -> CountExpr {
            CountExpr::RecursiveExpr(RecursiveExpr {
                func: Box::new(Function {
                    bound_var: "z".parse().unwrap(),
                    expr: f2("z+2".parse().unwrap(), 1.into()),
                }),
                num_repeats: Box::new(x),
                base: Box::new(y),
            })
        }
        // f4(x, y) = rep(λz -> f3(2z+7, 1), x)(y) ~= 2^^^x
        fn f4(x: CountExpr, y: CountExpr) -> CountExpr {
            CountExpr::RecursiveExpr(RecursiveExpr {
                func: Box::new(Function {
                    bound_var: "z".parse().unwrap(),
                    expr: f3("2z+7".parse().unwrap(), 1.into()),
                }),
                num_repeats: Box::new(x),
                base: Box::new(y),
            })
        }
        // f5(x, y) = ((λz.f4(4z+19, f2(1, 1)))^x y) ~= 2^^^^x
        fn f5(x: CountExpr, y: CountExpr) -> CountExpr {
            CountExpr::RecursiveExpr(RecursiveExpr {
                func: Box::new(Function {
                    bound_var: "z".parse().unwrap(),
                    expr: f4("4z+19".parse().unwrap(), f3(1.into(), 1.into())),
                }),
                num_repeats: Box::new(x),
                base: Box::new(y),
            })
        }

        let rule_set = RuleSet {
            tm: TM::from_str("1RB2LA1RC3RA_1LA2RA2RB0RC_1RZ3LC1RA1RB").unwrap(),
            rules: vec![
                // Level 0: Basic chain rules
                chain_rule("A> 2^2n", "1^2n A>", 2),
                chain_rule("C> 2^2n", "1^2n C>", 2),
                chain_rule("1^n <A", "<A 2^n", 1),
                chain_rule("B> 2^n", "2^n B>", 1),
                chain_rule("1^n <C", "<C 3^n", 1),
                chain_rule("B> 3^2n", "01^n B>", 2),
                chain_rule("A> 3^n", "3^n A>", 1),
                // Level 1: C(a, b, c, 2k+r, 2e+1)  ->  C(a, b, c, r, 2 (e+2k) + 1)
                Rule {
                    init_config: Config::from_str("2^2n <A 2^2e+1 0^inf").unwrap(),
                    final_config: Config::from_str("<A 2^4n+2e+1 0^inf").unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 22^n+1 <A 2^2e+1  --(1)-->  22^n 21 C> 2^2e+1
                            base_step(1),
                            // 22^n 21 C> 2^2e+1  -->  22^n 21 11^e C> 2
                            chain_step(1, "e"),
                            // 22^n 21 11^e C> 200  --(3)-->  22^n 21 11^e 11 <A 1
                            base_step(3),
                            // 22^n 2 1^2e+3 <A 1  -->  22^n 2 <A 2^2e+3 1
                            chain_step(2, "2e+3"),
                            // 22^n 2 <A 2^2e+3 1  --(1)-->  22^n 1 C> 2^2e+3 1
                            base_step(1),
                            // 22^n 1 C> 2^2e+3 1  -->  22^n 1 11^e+1 C> 21
                            chain_step(1, "e+1"),
                            // 22^n 1 11^e+1 C> 21  --(3)-->  22^n 1 11^e+1 <A 22
                            base_step(3),
                            // 22^n 1 11^e+1 <A 22  -->  22^n <A 2^2e+5
                            chain_step(2, "2e+3"),
                            // 22^n <A 2^2(e+2)+1  -->  <A 2^2(e+2(n+1))+1
                            induction_step(&[("e", "e+2")]),
                        ],
                    },
                },
                // Level 2: C(a, b, c, 1, 2e+1)  ->  C(a, b, 0, 1, 2 f2(c, e) + 1)
                //   where f2(c, e) = rep(λx -> 2x+5, c)(e)  ~= 2^c
                Rule {
                    init_config: Config::from_str("01^n 1 2 <A 2^2e+1 0^inf").unwrap(),
                    final_config: Config::from_str("1 2 <A 2^2x+1 0^inf")
                        .unwrap()
                        .subst(&VarSubst::single(
                            Variable::from_str("x").unwrap(),
                            f2("n".parse().unwrap(), "e".parse().unwrap()),
                        ))
                        .unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![
                            // Note this requires RecursionExpr comparison supporting equality between:
                            //      2e+1  ==  λx.2x+1 ((λx.2x+5)^0 e)
                        ],
                        proof_inductive: vec![
                            // 01^n+1 12 <A 2^2e+1 00  -->  01^n+1 1 <A 2^2e+3 1
                            base_step(1),
                            chain_step(1, "e"),
                            base_step(3),
                            chain_step(2, "2e+3"),
                            // 01^n+1 1 <A 2^2e+3 1  --(3)-->  01^n 1 B> 22 2^2e+3 1
                            base_step(3),
                            chain_step(3, "2e+5"),
                            // 01^n 1 2^2e+5 B> 100  --(9)-->  01^n 1 2^2e+5 <A 222
                            base_step(9),
                            // Level 1: 01^n 1 2^2(e+2)+1 <A 2^3  -->  01^n 12 <A 2^2(2e+5)+1
                            rule_step(7, &[("n", "e+2"), ("e", "1")]),
                            // Induction: 01^n 12 <A 2^2(2e+5)+1  -->  12 <A 2^2x+1  for x = f2(n, 2e+5) = f2(n+1, e)
                            induction_step(&[("e", "2e+5")]),
                            // Note this requires RecursionExpr comparison supporting equality between:
                            //      λx.2x+1 ((λx.2x+5)^n 2e+5)
                            //      λx.2x+1 ((λx.2x+5)^n+1 e)
                        ],
                    },
                },
                // Level 3: C(a, b, 0, 1, 2e+1)  ->  C(a, 0, 0, 1, 2 f3(b, e) + 1)
                //   where f3(b, e) = rep(λx -> f2(x+2, 1), b)(e)  ~= 2^^b
                Rule {
                    init_config: Config::from_str("3^n 1 1 2 <A 2^2e+1 0^inf").unwrap(),
                    final_config: Config::from_str("1 1 2 <A 2^2x+1 0^inf")
                        .unwrap()
                        .subst(&VarSubst::single(
                            Variable::from_str("x").unwrap(),
                            f3("n".parse().unwrap(), "e".parse().unwrap()),
                        ))
                        .unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 3^n+1 112 <A 2^2e+1 00  -->  3^n+1 <A 2^2e+5 1
                            base_step(1),
                            chain_step(1, "e"),
                            base_step(3),
                            chain_step(2, "2e+5"),
                            // 3^n+1 <A 2^2e+5 1  --(1)-->  3^n 3 A> 2^2e+5 1
                            base_step(1),
                            // 3^n 3 A> 2^2e+5 1  -->  3^n 3 11^e+2 A> 21
                            chain_step(0, "e+2"),
                            base_step(2),
                            chain_step(4, "2e+5"),
                            // 3^n 3 <C 3^2e+6  --(1)-->  3^n 1 B> 3^2e+6
                            base_step(1),
                            // 3^n 1 B> 3^2e+6  -->  3^n 1 01^e+3 B>
                            chain_step(5, "e+3"),
                            // 3^n 1 01^e+3 B> 000  --(13)-->  3^n 1 01^e+2 12 <A 2^3
                            base_step(13),
                            // Level 2: 3^n 1 01^e+2 12 <A 2^3  -->  3^n 112 <A 2^{2 f2(e+2, 1) + 1}
                            rule_step(8, &[("n", "e+2"), ("e", "1")]),
                            // Induction: 3^n 112 <A 2^{2 f1(e+2, 1) + 1}  -->  112 <A 2^2x+1
                            //      for x = f3(n, f2(e+2, 1)) = f3(n+1, e)
                            induction_step_expr(&[(
                                "e".parse().unwrap(),
                                f2("e+2".parse().unwrap(), 1.into()),
                            )]),
                        ],
                    },
                },
                // Level 4: C(2a+r, 0, 0, 1, 2e+1)  ->  C(r, 0, 0, 1, 2 f4(a, e) + 1)
                //   where f4(a, e) = rep(λx -> f3(2x+7), a)(e)  ~= 2^^^a
                Rule {
                    init_config: Config::from_str("2^2n 1 1 1 2 <A 2^2e+1 0^inf").unwrap(),
                    final_config: Config::from_str("1 1 1 2 <A 2^2x+1 0^inf")
                        .unwrap()
                        .subst(&VarSubst::single(
                            Variable::from_str("x").unwrap(),
                            f4("n".parse().unwrap(), "e".parse().unwrap()),
                        ))
                        .unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 2^2n+2 1112 <A 2^2e+1 00  -->  2^2n+2 <A 2^2e+6 1
                            base_step(1),
                            chain_step(1, "e"),
                            base_step(3),
                            chain_step(2, "2e+6"),
                            // 2^2n+2 <A 2^2e+6 1  -->  2^2n+1 1^2e+7 C> 1
                            base_step(1),
                            chain_step(1, "e+3"),
                            // 2^2n+1 1^2e+7 C> 1  -->  2^2n+1 <C 3^2e+8
                            base_step(1),
                            chain_step(4, "2e+7"),
                            // 2^2n+1 <C 3^2e+8  -->  2^n 1 3^2e+8 A>
                            base_step(1),
                            chain_step(6, "2e+8"),
                            // 2^n 1 3^2e+8 A> 00  --(23)-->  2^n 1 3^2e+7 112 <A 2^3
                            base_step(23),
                            // Level 3: 2^n 1 3^2e+7 112 <A 2^3  -->  2^n 112 <A 2^{2 f3(2e+7, 1) + 1}
                            rule_step(9, &[("n", "2e+7"), ("e", "1")]),
                            // Induction: 2^n 112 <A 2^{2 f3(2e+7, 1) + 1}  -->  112 <A 2^2x+1
                            //      for x = f4(n, f3(2e+7, 1)) = f4(n+1, e)
                            induction_step_expr(&[(
                                "e".parse().unwrap(),
                                f3("2e+7".parse().unwrap(), 1.into()),
                            )]),
                        ],
                    },
                },
                // Level 5: C(0, 0, 0, 1, 2e+1)  ->  C(0, 0, 0, 1, 2 f4(4e+19, f3(1, 1)) + 1)
                // Infinite
                Rule {
                    init_config: Config::from_str("0^inf 1 1 1 1 2 <A 2^2e+1 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 1 1 1 1 2 <A 2^2x+1 0^inf")
                        .unwrap()
                        .subst(&VarSubst::single(
                            Variable::from_str("x").unwrap(),
                            f5("n".parse().unwrap(), "e".parse().unwrap()),
                        ))
                        .unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 11112 <A 2^2e+1 00  -->  <A 2^2e+7 1
                            base_step(1),
                            chain_step(1, "e"),
                            base_step(3),
                            chain_step(2, "2e+7"),
                            // 0 <A 2^2e+7 1  -->  1 2^2e+7 B> 1
                            base_step(1),
                            chain_step(3, "2e+7"),
                            // 1 2^2e+7 B> 100  --(9)-->  1 2^2e+7 <A 2^3
                            base_step(9),
                            // Level 1: 12 2^2e+6 <A 2^3  -->  12 <A 2^2(2e+6)+3
                            rule_step(7, &[("n", "e+3"), ("e", "1")]),
                            // 12 <A 2^4e+15 00  -->  <A 2^4e+18 1
                            base_step(1),
                            chain_step(1, "2e+7"),
                            base_step(3),
                            chain_step(2, "4e+18"),
                            // 0 <A 2^4e+18 1  -->  1 2^4e+18 B> 1
                            base_step(1),
                            chain_step(3, "4e+18"),
                            // 1 2^4e+18 B> 100  --(9)-->  1 2^4e+18 <A 2^3
                            base_step(9),
                            // Level 1: 1 2^4e+18 <A 2^3  -->  1 <A 2^2(4e+18)+3
                            rule_step(7, &[("n", "2e+9"), ("e", "1")]),
                            // 01 <A 2^8e+39  -->  1 2^8e+40 B>
                            base_step(2),
                            chain_step(3, "8e+40"),
                            // 1 2^8e+40 B> 0^6  --(30)--> 1 2^8e+38 1 3^1 112 <A 2^3
                            base_step(30),
                            // Level 3: 3^1 112 <A 2^3  -->  112 <A 2^{2 f3(1, 1) + 1}
                            //      f3(1, 1) = f2(3, 1)
                            rule_step(9, &[("n", "1"), ("e", "1")]),
                            // Level 4: 1 2^8e+38 1112 <A 2^{2 f3(1, 1) + 1}  -->  11112 <A 2^2x+1
                            //      for x = f4(4e+19, f3(1, 1))
                            ProofStep::RuleStep {
                                rule_id: 10,
                                var_assignment: VarSubst::from(&[
                                    (
                                        Variable::from_str("n").unwrap(),
                                        CountExpr::from_str("4e+19").unwrap(),
                                    ),
                                    (Variable::from_str("e").unwrap(), f3(1.into(), 1.into())),
                                ]),
                            },
                            induction_step_expr(&[(
                                "e".parse().unwrap(),
                                f4("4e+19".parse().unwrap(), f3(1.into(), 1.into())),
                            )]),
                        ],
                    },
                },
                // Proof that TM is infinite starting from blank tape.
                Rule {
                    init_config: Config::new(),
                    final_config: Config::from_str("0^inf 1 1 1 1 2 <A 2^2x+1 0^inf")
                        .unwrap()
                        .subst(&VarSubst::single(
                            Variable::from_str("x").unwrap(),
                            f5("n".parse().unwrap(), f4(7.into(), f3(1.into(), 1.into()))),
                        ))
                        .unwrap(),
                    proof: Proof::Simple(vec![
                        // <A --> 1 2^14 1 3 112 <A 2^3
                        ProofStep::TMSteps(210),
                        // Level 3: 1 2^14 1 3 112 <A 2^3  -->  1 2^14 1 112 <A 2^{2 f3(1, 1) + 1}
                        ProofStep::RuleStep {
                            rule_id: 9,
                            var_assignment: VarSubst::from(&[
                                ("n".parse().unwrap(), 1.into()),
                                ("e".parse().unwrap(), 1.into()),
                            ]),
                        },
                        // Level 4: 1 2^14 1112 <A 2^{2 f3(1, 1) + 1}  -->  1 112 <A 2^{2 f4(7, f3(1, 1)) + 1}
                        ProofStep::RuleStep {
                            rule_id: 10,
                            var_assignment: VarSubst::from(&[
                                ("n".parse().unwrap(), 7.into()),
                                ("e".parse().unwrap(), f3(1.into(), 1.into())),
                            ]),
                        },
                        // TODO: Apply Level 5
                        ProofStep::RuleStep {
                            rule_id: 11,
                            var_assignment: VarSubst::from(&[
                                ("n".parse().unwrap(), "n".parse().unwrap()),
                                ("e".parse().unwrap(), f4(7.into(), f3(1.into(), 1.into()))),
                            ]),
                        },
                    ]),
                },
            ],
        };
        if let Err(err) = validate_rule_set(&rule_set) {
            panic!("{}", err);
        }
    }

    #[ignore = "sum expression support needed"]
    #[test]
    fn test_25_dyuan() {
        // @dyuan01's halting 2x5 counter-bouncer.
        //      https://discord.com/channels/960643023006490684/1084047886494470185/1230916624626876529
        // Note: This proof is not complete, there are several Admits.

        let n = Variable::from_str("n").unwrap();
        let a = Variable::from_str("a").unwrap();
        let x = Variable::from_str("x").unwrap();

        // Repeat λx.2x+1 n times starting from 0.
        //   = 2^n - 1
        fn rep2n1(n: &CountExpr) -> CountExpr {
            CountExpr::RecursiveExpr(RecursiveExpr {
                func: Box::new(Function::affine(2, 1)),
                num_repeats: Box::new(n.clone()),
                base: Box::new(0.into()),
            })
        }

        // a_2n1 = a + rep2n1(n) = a + 2^n - 1
        let a_2n1 = CountExpr::from_str("a+x")
            .unwrap()
            .subst(&VarSubst::single(x, rep2n1(&n.into())))
            .unwrap();

        // e6 = 2^6 - 1 = 63
        let e6 = rep2n1(&6.into());
        // e7 = 2^7 - 1 = 127
        // Note: e7 = rep2n1(7) ... but our system cannot detect that equivalence.
        let e7 = CountExpr::from_str("a+x")
            .unwrap()
            .subst(&VarSubst::from(&[
                (a, e6.checked_add(&1.into()).unwrap()),
                (x, e6.clone()),
            ]))
            .unwrap();
        // ee7 = 2^e7 - 1 = 2^127 - 1
        let ee7 = rep2n1(&e7);

        let rule_set = RuleSet {
            tm: TM::from_str("1RB0LB---4RA0LA_2LA3LA3LB0RA2LA").unwrap(),
            rules: vec![
                chain_rule("A> 033^n", "104^n A>", 3),
                chain_rule("104^n <A", "<A 302^n", 5),
                chain_rule("104^n <B", "<B 033^n", 5),
                simple_rule("000 <B", "104 A>", 7),
                // 0^inf 104^a 1104 A> 302^n  -->  0^inf 104^{a + 2^n - 1} 1104 A> 033^n
                Rule {
                    init_config: Config::from_str("0^inf 104^a 1104 A> 302^n").unwrap(),
                    final_config: Config::from_str("0^inf 104^x 1104 A> 033^n")
                        .unwrap()
                        .subst(&VarSubst::single(x, a_2n1.clone()))
                        .unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // First Induction:  0^inf 104^a 1104 A> 302^n+1  -->  0^inf 104^a_2n1 1104 A> 033^n 302
                            induction_step(&[("a", "a")]),
                            // A> 033^n 302  -->  104^n A> 302  -->  104^n <A 033  -->  <A 302^n 033
                            chain_step(0, "n"),
                            base_step(5),
                            chain_step(1, "n"),
                            // 1104 <A  -->  <B 0302
                            base_step(6),
                            // 000 104^a_2n1 <B  -->  000 <B 033^a_2n1  --> 104 A> 033^a_2n1  -->  104 104^a_2n1 A>
                            ProofStep::RuleStep {
                                rule_id: 2,
                                var_assignment: VarSubst::from(&[(n, a_2n1.clone())]),
                            },
                            rule_step(3, &[]),
                            ProofStep::RuleStep {
                                rule_id: 0,
                                var_assignment: VarSubst::from(&[(n, a_2n1.clone())]),
                            },
                            // A> 0302  -->  1104 A>
                            base_step(8),
                            ProofStep::Admit,
                            // Second Induction:  0^inf 104^{a_2n1 + 1}         1104 A> 033^n 302
                            //               -->  0^inf 104^{a_2n1 + 1 + 2n1}   1104 A> 302^n 302
                            ProofStep::InductiveStep(VarSubst::from(&[
                                (n, n.into()),
                                // TODO: Cannot add 1 to a_2n1 (RecursionExpr).
                                // (a, a_2n1 + 1),
                            ])),
                            // TODO: This in order to prove the final config, we must equate:
                            //          λx.a+x ((λn.2n+1)^n+1 1)
                            //          λy.(λz.z+y (λx.a+x ((λn.2n+1)^n 1))) ((λn.2n+1)^n 1)   [+1]
                            // ie:   a + (2^n+1 - 1)  ==  a + (2^n - 1) + (2^n - 1) + 1
                            // One idea to support this would be to expand VarSum to support arbitrary
                            // RecursionExprs, not just simple variables ...
                        ],
                    },
                },
                Rule {
                    init_config: Config::from_str("0^inf 104 104^a 1104 A> 302^n").unwrap(),
                    final_config: Config::from_str("0^inf 104 104^x 1104 A> 033^n")
                        .unwrap()
                        .subst(&VarSubst::single(x, a_2n1.clone()))
                        .unwrap(),
                    proof: Proof::Simple(vec![
                        ProofStep::RuleStep {
                            rule_id: 4,
                            var_assignment: VarSubst::from(&[
                                (a, CountExpr::var_plus(a, 1)),
                                (n, n.into()),
                            ]),
                        },
                        ProofStep::Admit,
                    ]),
                },
                // Halt Proof
                Rule {
                    init_config: Config::new(),
                    final_config: Config::from_str(
                        "0^inf 104^x 1104 104^126 1 Z> 033^7 0302 302 033 3303 02^3 0^inf",
                    )
                    .unwrap()
                    .subst(&VarSubst::single(x, ee7.clone()))
                    .unwrap(),
                    proof: Proof::Simple(vec![
                        base_step(642),
                        // [1104] A> [302]6 [3033] [033]2 [0302] [00] [02] [02]
                        ProofStep::RuleStep {
                            rule_id: 4,
                            var_assignment: VarSubst::from(&[(a, 0.into()), (n, 6.into())]),
                        },
                        // [104]63 [1104] A> [033]6 [3033] [033]2 [0302] [00] [02] [02]
                        base_step(97),
                        // [104]63 <B [0302] [302]6 [0302] [302]2 [3303] [02] [02] [02]
                        ProofStep::RuleStep {
                            rule_id: 2,
                            var_assignment: VarSubst::from(&[(n, e6.clone())]),
                        },
                        rule_step(3, &[]),
                        ProofStep::RuleStep {
                            rule_id: 0,
                            var_assignment: VarSubst::from(&[(n, e6.clone())]),
                        },
                        base_step(8),
                        // [104]64 [1104] A> [302]6 [0302] [302]2 [3303] [02] [02] [02]
                        ProofStep::RuleStep {
                            rule_id: 5,
                            var_assignment: VarSubst::from(&[(a, e6.clone()), (n, 6.into())]),
                        },
                        // [104]127 [1104] A> [033]6 [0302] [302]2 [3303] [02] [02] [02]
                        base_step(73),
                        // [104]127 <A [3033] [033]6 [0302] [033][302] [3303] [02] [02] [02]
                        ProofStep::RuleStep {
                            rule_id: 1,
                            var_assignment: VarSubst::from(&[(n, e7.clone())]),
                        },
                        rule_step(3, &[]),
                        ProofStep::RuleStep {
                            rule_id: 0,
                            var_assignment: VarSubst::from(&[(n, e7.clone())]),
                        },
                        // ...
                        // [1104] A> [302]126 [3033] [033]6 [0302] [033][302] [3303] [02] [02] [02]
                        // ...
                    ]),
                },
            ],
        };
        if let Err(err) = validate_rule_set(&rule_set) {
            panic!("{}", err);
        }
    }

    #[test]
    fn test_25_t4_dyuan() {
        // 1RB3LA4RB0RB2LA_1LB2LA3LA1RA1RZ
        //   @dyuan01's halting 2x5 counter-bouncer.
        //   https://discord.com/channels/960643023006490684/1084047886494470185/1254826217375273112
        //   Estimated score > (10↑)^4 6.5

        let a = (2_u64.pow(25) - 2_u64.pow(19) - 9) / 3;
        assert!(a == 11010045);
        //let b = (2^(a+27)-2^(a+2)-11)/3;

        let rule_set = RuleSet {
            tm: TM::from_str("1RB3LA4RB0RB2LA_1LB2LA3LA1RA1RZ").unwrap(),
            rules: vec![
                simple_rule("A>", "A>", 0), // Dummy rule so that numbers line up :P
                // Basic Rules
                simple_rule("01 <A", "11 A>", 3),          // 1
                chain_rule("11^n <A", "<A 33^n", 2),       // 2
                chain_rule("A> 33^n", "01^n A>", 2),       // 3
                simple_rule("01 <A 3", "11 0 B>", 4),      // 4
                chain_rule("11^n <A 3", "<A 3 33^n", 2),   // 5
                chain_rule("0 B> 33^n", "01^n 0 B>", 2),   // 6
                simple_rule("A> 21", "<A 22", 3),          // 7
                simple_rule("A> 22", "<A 23", 3),          // 8
                chain_rule("A> 23^n", "41^n A>", 2),       // 9
                simple_rule("A> 0^inf", "<A 21 0^inf", 3), // 10
                simple_rule("0 B> 21", "<A 3 33", 6),      // 11
                simple_rule("0 B> 22 0^inf", "11 1 Z> 1 0^inf", 6), // 12
                chain_rule("0 B> 23^n", "11^n 0 B>", 4),   // 13
                chain_rule("41^n <A", "<A 23^n", 2),       // 14
                simple_rule("0^inf 11 <A", "0^inf 11 0 B>", 5), // 15
                // Counter Rules
                // 16) Counter Rule (A)
                // 01 11^x <A -> 11 01^x A>
                Rule {
                    init_config: Config::from_str("01 11^x <A").unwrap(),
                    final_config: Config::from_str("11 01^x A>").unwrap(),
                    proof: Proof::Simple(vec![
                        chain_step(2, "x"),
                        rule_step(1, &[]),
                        chain_step(3, "x"),
                    ]),
                },
                // 17) Counter Rule (1)
                // 01 11^x <A 23^y 0^inf -> 11 01^x <A 23^y 21 0^inf
                Rule {
                    init_config: Config::from_str("01 11^x <A 23^y 0^inf").unwrap(),
                    final_config: Config::from_str("11 01^x <A 23^y 21 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        rule_step(16, &[("x", "x")]),
                        chain_step(9, "y"),
                        rule_step(10, &[]),
                        chain_step(14, "y"),
                    ]),
                },
                // 18) Counter Rule (2)
                // 01 11^x <A 23^y 21 -> 11 01^x <A 23^y 22
                Rule {
                    init_config: Config::from_str("01 11^x <A 23^y 21").unwrap(),
                    final_config: Config::from_str("11 01^x <A 23^y 22").unwrap(),
                    proof: Proof::Simple(vec![
                        rule_step(16, &[("x", "x")]),
                        chain_step(9, "y"),
                        rule_step(7, &[]),
                        chain_step(14, "y"),
                    ]),
                },
                // 19) Counter Rule (3)
                // 01 11^x <A 23^y 22 -> 11 01^x <A 23^y 23
                Rule {
                    init_config: Config::from_str("01 11^x <A 23^y 22").unwrap(),
                    final_config: Config::from_str("11 01^x <A 23^y+1").unwrap(),
                    proof: Proof::Simple(vec![
                        rule_step(16, &[("x", "x")]),
                        chain_step(9, "y"),
                        rule_step(8, &[]),
                        chain_step(14, "y"),
                    ]),
                },
                // 20) Counter Rule (4)
                // 0^inf 11^x+1 <A 3 -> 0^inf 11 01^x 0 B>
                Rule {
                    init_config: Config::from_str("0^inf 11^x+1 <A").unwrap(),
                    final_config: Config::from_str("0^inf 11 01^x 0 B>").unwrap(),
                    proof: Proof::Simple(vec![
                        chain_step(2, "x"),
                        rule_step(15, &[]),
                        chain_step(6, "x"),
                    ]),
                },
                // 21) Counter Rule (5)
                // 01 11^x <A 3 -> 11 01^x 0 B>
                Rule {
                    init_config: Config::from_str("01 11^x <A 3").unwrap(),
                    final_config: Config::from_str("11 01^x 0 B>").unwrap(),
                    proof: Proof::Simple(vec![rule_step(16, &[("x", "x")]), base_step(1)]),
                },
                // Advanced Rules
                // 22) Advanced Rule (1)
                // 01^3 0 B> 0^inf -> 11 01^3 <A 21 0^inf
                simple_rule("01^3 0 B> 0^inf", "11 01^3 <A 21 0^inf", 36),
                // 23) Advanced Rule (2)
                // 01 11^x+2 0 B> 0^inf -> 11 01^x 11^2 01 <A 21 0^inf
                Rule {
                    init_config: Config::from_str("01 11^x+2 0 B> 0^inf").unwrap(),
                    final_config: Config::from_str("11 01^x 11^2 01 <A 21 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        base_step(4),
                        chain_step(2, "x+1"),
                        rule_step(1, &[]),
                        chain_step(3, "x+1"),
                        base_step(25),
                    ]),
                },
                // Overflow Rules
                // 24) Overflow Rule (1)
                // 0^inf 11^x+2 <A 23^y+2 21 0^inf -> 0^inf 11 01^x 11 01^y 11 01^3 <A 21 0^inf
                Rule {
                    init_config: Config::from_str("0^inf 11^x+2 <A 23^y+2 21 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 11 01^x 11 01^y 11 01^3 <A 21 0^inf")
                        .unwrap(),
                    proof: Proof::Simple(vec![
                        rule_step(20, &[("x", "x+1")]),
                        chain_step(13, "y+2"),
                        rule_step(11, &[]),
                        rule_step(21, &[("x", "y+2")]),
                        chain_step(6, "1"),
                        rule_step(22, &[]),
                    ]),
                },
                // 25) Overflow Rule (2)
                // 0^inf 11^x+2 <A 23^y+2 0^inf -> 0^inf 11 01^x 11 01^y 11^2 01 <A 21 0^inf
                Rule {
                    init_config: Config::from_str("0^inf 11^x+2 <A 23^y+2 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 11 01^x 11 01^y 11^2 01 <A 21 0^inf")
                        .unwrap(),
                    proof: Proof::Simple(vec![
                        rule_step(20, &[("x", "x+1")]),
                        chain_step(13, "y+2"),
                        rule_step(23, &[("x", "y")]),
                    ]),
                },
                // 26) Overflow Rule (3)
                // 0^inf 11^x+1 <A 23^y+1 22 0^inf -> 0^inf 11 01^x 11^y+2 1 Z> 1 0^inf
                Rule {
                    init_config: Config::from_str("0^inf 11^x+1 <A 23^y+1 22 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 11 01^x 11^y+2 1 Z> 1 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        rule_step(20, &[("x", "x")]),
                        chain_step(13, "y+1"),
                        rule_step(12, &[]),
                    ]),
                },
                // Halt Proof
                Rule {
                    init_config: Config::new(),
                    final_config: Config::from_str("0^inf 11 01^a+b+c+31 11^d+1 1 Z> 1 0^inf")
                        .unwrap()
                        .subst(&VarSubst::from(&[
                            ("a".parse().unwrap(), a.into()),
                            // ("b".parse().unwrap(), b),
                            // ("c".parse().unwrap(), c),
                            // ("d".parse().unwrap(), d),
                        ]))
                        .unwrap(),
                    proof: Proof::Simple(vec![
                        base_step(2430),
                        // [11]^7 <A [23]^17 [21]
                        rule_step(24, &[("x", "5"), ("y", "15")]),
                        // [11] [01]^5 [11] [01]^15 [11] [01]^3 <A [21]
                        ProofStep::Admit,
                    ]),
                },
            ],
        };
        if let Err(err) = validate_rule_set(&rule_set) {
            panic!("{}", err);
        }
    }

    #[test]
    fn test_34_a14_uni() {
        // https://www.sligocki.com/2024/05/22/bb-3-4-a14.html
        //   1RB3LB1RZ2RA_2LC3RB1LC2RA_3RB1LB3LC2RC
        //     Discovered by @uni on 25 Apr 2024.
        //     Scores exactly 2{15}5 + 14 = (2 ↑^15 5) + 14 > Ack(14)

        // f(k, x, y) = g_k^x(y)
        //      g_0(y) = y + 1
        //      g_{k+1}(y) = g_k^{2y+2}(0)
        // By some strange coincidence:
        //      2 f(k, x, 0) + 4 = 2{k}(x+2) = 2 ↑^k (x+2)
        fn f(k: CountType, x: CountExpr, y: CountExpr) -> CountExpr {
            match k {
                0 => x,
                k => CountExpr::RecursiveExpr(RecursiveExpr {
                    func: Box::new(Function {
                        bound_var: "z".parse().unwrap(),
                        expr: f(k - 1, "2z+2".parse().unwrap(), 0.into()),
                    }),
                    num_repeats: Box::new(x),
                    base: Box::new(y),
                }),
            }
        }

        // This TM simulates an Ackermann level rule.
        // We cannot prove that rule generally in our system (because it depends on double induction).
        // But we can prove every level of it individually.
        // This function proves each level of the Ackermann rule sequentially and then we use it up to k == 15 below.
        //
        // General rule:
        //      0^inf 3^2e+1 2^k+1 A> 1^n  -->  0^inf 3^2x+1 2^k+1 A>  for x = f(k, n, e)
        // Steps (for e = 0):
        //      t_0(n) ~= 4 n^2
        //      t_k(n) ~= sum_{x=0}^{n-1} t_{k-1}(2 g_k^x(0) + 2)
        //
        //      t_1(n) = sum_{x=0}^{n-1} t_0(2 g_1^x(0) + 2)
        //                ~= sum 4 (2^{x+2} - 2)^2
        //                ~= 16/3 (g_1^n(0))^2
        //
        //      t_2(n) = sum_{x=0}^{n-1} t_1(2 g_2^x(0) + 2)
        //                  ~= sum 16/3 (g_2^{x+1}(0))^2
        //                  ~= 16/3 (g_2^n(0))^2
        //
        //      t_k(n) ~= 16/3 (g_k^n(0))^2
        fn rule_level(k: CountType, prev_rule_id: usize) -> Rule {
            if k < 1 {
                panic!("k must be >= 1");
            }
            Rule {
                init_config: Config::from_str("0^inf 3^2e+1 2^k+1 A> 1^n")
                    .unwrap()
                    .subst(&VarSubst::single("k".parse().unwrap(), k.into()))
                    .unwrap(),
                final_config: Config::from_str("0^inf 3^2x+1 2^k+1 A>")
                    .unwrap()
                    .subst(&VarSubst::from(&[
                        ("k".parse().unwrap(), k.into()),
                        (
                            "x".parse().unwrap(),
                            f(k, "n".parse().unwrap(), "e".parse().unwrap()),
                        ),
                    ]))
                    .unwrap(),

                proof: Proof::Inductive {
                    proof_base: vec![],
                    proof_inductive: vec![
                        // 0^inf 3^2e+1 2^k+1 A> 1^n+1
                        base_step(1),
                        // 0^inf 3^2e+1 2^k+1 <B 3 1^n
                        rule_step(4, &[("a", &k.to_string()), ("n", "2e+1")]),
                        // 0^inf 2^k+1 <B 1^2e+1 3 1^n
                        base_step(2 * k + 2),
                        // 0^inf 3 2^k A> 1^2e+2 3 1^n $
                        rule_step(prev_rule_id, &[("n", "2e+2"), ("e", "0")]),
                        // 0^inf 3^2x+1 2^k A> 3 1^n $
                        base_step(1),
                        // 0^inf 3^2x+1 2^k+1 A> 1^n $
                        induction_step_expr(&[(
                            "e".parse().unwrap(),
                            f(k - 1, "2e+2".parse().unwrap(), 0.into()),
                        )]),
                    ],
                },
            }
        }

        let rule_set = RuleSet {
            tm: TM::from_str("1RB3LB1RZ2RA_2LC3RB1LC2RA_3RB1LB3LC2RC").unwrap(),
            rules: vec![
                chain_rule("2^n <C", "<C 3^n", 1), // 0
                chain_rule("C> 3^n", "2^n C>", 1), // 1
                chain_rule("A> 3^n", "2^n A>", 1), // 2 [Unused]
                chain_rule("B> 1^n", "3^n B>", 1), // 3
                // 4: 3^n 2^a+1 <B  -->  2^a+1 <B 1^n
                //      in n(2a+3) steps
                Rule {
                    init_config: Config::from_str("3^n 2^a+1 <B").unwrap(),
                    final_config: Config::from_str("2^a+1 <B 1^n").unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            base_step(1),
                            chain_step(0, "a"),
                            base_step(1),
                            chain_step(1, "a"),
                            base_step(1),
                            induction_step(&[("a", "a")]),
                        ],
                    },
                },
                // 5: B(1, n, e)  -->  B(1, 0, e+n) = B(1, 0, g_0^n(e))
                //      in t_0(n, e) steps
                // Where:
                //      t_0(0, e) = 0
                //      t_0(n, e) = 8e+9 + t_0(n-1, e+1)
                // So,
                //      t_0(n, e) = 4n(n-1) + n(8e+9)
                //      t_0(n, 0) = 4 n^2 + 5n
                Rule {
                    init_config: Config::from_str("0^inf 3^2e+1 2 A> 1^n").unwrap(),
                    final_config: Config::from_str("0^inf 3^2n+2e+1 2 A>").unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 0^inf 3^2e+1 2 A> 1^n+1
                            base_step(1),
                            // 0^inf 3^2e+1 2 <B 3 1^n
                            rule_step(4, &[("a", "0"), ("n", "2e+1")]),
                            // 0^inf 2 <B 1^2e+1 3 1^n
                            base_step(2),
                            // 0^inf 3 B> 1^2e+2 3 1^n
                            chain_step(3, "2e+2"),
                            // 0^inf 3^2e+3 B> 3 1^n
                            base_step(1),
                            // 0^inf 3^2e+3 2 A> 1^n
                            induction_step(&[("e", "e+1")]),
                        ],
                    },
                },
                // 15 layers of Ackermann rules
                rule_level(1, 5),   // 6
                rule_level(2, 6),   // 7
                rule_level(3, 7),   // 8
                rule_level(4, 8),   // 9
                rule_level(5, 9),   // 10
                rule_level(6, 10),  // 11
                rule_level(7, 11),  // 12
                rule_level(8, 12),  // 13
                rule_level(9, 13),  // 14
                rule_level(10, 14), // 15
                rule_level(11, 15), // 16
                rule_level(12, 16), // 17
                rule_level(13, 17), // 18
                rule_level(14, 18), // 19
                rule_level(15, 19), // 20
                // Halt Proof
                Rule {
                    init_config: Config::new(),
                    final_config: Config::from_str("0^inf 3^2x+1 2^16 1 Z> 0^inf")
                        .unwrap()
                        .subst(&VarSubst::single(
                            "x".parse().unwrap(),
                            f(15, 3.into(), 0.into()),
                        ))
                        .unwrap(),
                    proof: Proof::Simple(vec![
                        base_step(241),
                        // $ 3 2^16 A> 1^3 2 $
                        rule_step(20, &[("n", "3"), ("e", "0")]),
                        // $ 3^2x+1 2^16 A> 2 $  with x = f(15, 3, 0)
                        base_step(1),
                    ]),
                },
                // Permutation Halt Proof
                // If you start in state B on a blank tape, this leads to a
                // slightly smaller giant score:  2{6}5 + 5
                //      TNF: 1RB3RB1LC2LA_2LA2RB1LB3RA_3LA1RZ1LC2RA
                Rule {
                    init_config: Config::from_str("0^inf B> 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 3^2x+1 2^7 1 Z> 0^inf")
                        .unwrap()
                        .subst(&VarSubst::single(
                            "x".parse().unwrap(),
                            f(6, 3.into(), 0.into()),
                        ))
                        .unwrap(),
                    proof: Proof::Simple(vec![
                        base_step(86),
                        // $ 3 2^7 A> 1^3 2 $
                        rule_step(11, &[("n", "3"), ("e", "0")]),
                        // $ 3^2x+1 2^7 A> 2 $  with x = f(6, 3, 0)
                        base_step(1),
                    ]),
                },
            ],
        };
        if let Err(err) = validate_rule_set(&rule_set) {
            panic!("{}", err);
        }
    }

    #[test]
    fn test_34_a11_uni() {
        // 1RB1RZ1LA2RB_1RC3RC1LA2LB_2LB2RC1LC3RB
        //      Shared by @uni on 23 May 2024.
        //      Halt(SuperPowers(10))
        //      https://discord.com/channels/960643023006490684/1026577255754903572/1243057809268932620
        //  Score: g_13^2(1) + 14 = 2{12}4 + 11 > Ack(11)

        // Common config: 3 <A 1^b 2^c 0^inf

        // f(k, x, y) = g_k^x(y)
        //      g_1(y) = y + 2
        //      g_{k+1}(y) = g_k^{y+1}(1)
        //
        //  g_1^x(y) = 2x + y
        //
        //  g_k(y) = 2{k-2}(y+3) - 3
        //  g_k^x(1) = g_{k+1}(x-1) = 2{k-1}(x+2) - 3
        fn f(k: CountType, x: CountExpr, y: CountExpr) -> CountExpr {
            match k {
                0 => unreachable!("k must be >= 1"),
                1 => CountExpr::from_str("2x+y")
                    .unwrap()
                    .subst(&VarSubst::from(&[
                        ("x".parse().unwrap(), x.clone()),
                        ("y".parse().unwrap(), y.clone()),
                    ]))
                    .unwrap(),
                k => CountExpr::RecursiveExpr(RecursiveExpr {
                    func: Box::new(Function {
                        bound_var: "z".parse().unwrap(),
                        expr: f(k - 1, "z+1".parse().unwrap(), 1.into()),
                    }),
                    num_repeats: Box::new(x),
                    base: Box::new(y),
                }),
            }
        }

        // Ackermann level rule.
        //
        // General rule:
        //      3^n <A 1^k 2^c 0^inf  -->  <A 1^k 2^x 0^inf  for x = f(k, n, c)
        fn rule_level(k: CountType, prev_rule_id: usize) -> Rule {
            if k < 2 {
                panic!("k must be >= 2");
            }
            Rule {
                init_config: Config::from_str("3^n <A 1^k 2^c 0^inf")
                    .unwrap()
                    .subst(&VarSubst::single("k".parse().unwrap(), k.into()))
                    .unwrap(),
                final_config: Config::from_str("<A 1^k 2^x 0^inf")
                    .unwrap()
                    .subst(&VarSubst::from(&[
                        ("k".parse().unwrap(), k.into()),
                        (
                            "x".parse().unwrap(),
                            f(k, "n".parse().unwrap(), "c".parse().unwrap()),
                        ),
                    ]))
                    .unwrap(),

                proof: Proof::Inductive {
                    proof_base: vec![],
                    proof_inductive: vec![
                        // 3^n+1 <A 1^k 2^c 0^inf
                        base_step(1),
                        // 3^n 2 B> 1^k 2^c 0^inf
                        rule_step(4, &[("b", &(k - 1).to_string()), ("n", "c")]),
                        // 3^n 2 3^c B> 1^k 0^inf
                        base_step(1),
                        // 3^n 2 3^c+1 C> 1^k-1 0^inf
                        chain_step(0, &(k - 1).to_string()),
                        // 3^n 2 3^c+1 2^k-1 C> 0^inf
                        base_step(2),
                        // 3^n 2 3^c+1 2^k-2 <A 12 0^inf
                        chain_step(3, &(k - 2).to_string()),
                        // 3^n 2 3^c+1 <A 1^k-1 2 0^inf
                        rule_step(prev_rule_id, &[("n", "c+1"), ("c", "1")]),
                        // 3^n 2 <A 1^k-1 2^x 0^inf   for x = f(k-1, c+1, 1)
                        base_step(1),
                        // 3^n <A 1^k 2^x 0^inf
                        induction_step_expr(&[(
                            "c".parse().unwrap(),
                            f(k - 1, "c+1".parse().unwrap(), 1.into()),
                        )]),
                        // <A 1^k 2^y 0^inf   for y = f(k, n, x)
                    ],
                },
            }
        }

        let rule_set = RuleSet {
            tm: TM::from_str("1RB1RZ1LA2RB_1RC3RC1LA2LB_2LB2RC1LC3RB").unwrap(),
            rules: vec![
                chain_rule("C> 1^n", "2^n C>", 1), // 0
                chain_rule("2^n <C", "<C 1^n", 1), // 1
                chain_rule("3^n <B", "<B 2^n", 1), // 2
                chain_rule("2^n <A", "<A 1^n", 1), // 3
                // 4
                Rule {
                    init_config: Config::from_str("B> 1^b+1 2^n").unwrap(),
                    final_config: Config::from_str("3^n B> 1^b+1").unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // B> 1^b+1 2^n+1
                            base_step(1),
                            // 3 C> 1^b 2^n+1
                            chain_step(0, "b"),
                            // 3 2^b C> 2^n+1
                            base_step(1),
                            // 3 2^b <C 1 2^n
                            chain_step(1, "b"),
                            // 3 <C 1^b+1 2^n
                            base_step(1),
                            // 3 B> 1^b+1 2^n
                            induction_step(&[("b", "b")]),
                        ],
                    },
                },
                // 5
                Rule {
                    init_config: Config::from_str("3^n <A 1 2^c 0^inf").unwrap(),
                    final_config: Config::from_str("<A 1 2^c+2n 0^inf").unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 3^n+1 <A 1 2^c 0^inf
                            base_step(1),
                            // 3^n 2 B> 1 2^c 0^inf
                            rule_step(4, &[("b", "0"), ("n", "c")]),
                            // 3^n 2 3^c B> 1 0^inf
                            base_step(2),
                            // 3^n 2 3^c+1 <B 2 0^inf
                            chain_step(2, "c+1"),
                            // 3^n 2 <B 2^c+2 0^inf
                            base_step(1),
                            // 3^n <A 1 2^c+2 0^inf
                            induction_step(&[("c", "c+2")]),
                        ],
                    },
                },
                // Ackermann rules
                rule_level(2, 5),   // 6
                rule_level(3, 6),   // 7
                rule_level(4, 7),   // 8
                rule_level(5, 8),   // 9
                rule_level(6, 9),   // 10
                rule_level(7, 10),  // 11
                rule_level(8, 11),  // 12
                rule_level(9, 12),  // 13
                rule_level(10, 13), // 14
                rule_level(11, 14), // 15
                rule_level(12, 15), // 16
                rule_level(13, 16), // 17
                // Halt Proof
                Rule {
                    init_config: Config::new(),
                    final_config: Config::from_str("0^inf 1 Z> 1^13 2^x 0^inf")
                        .unwrap()
                        .subst(&VarSubst::single(
                            "x".parse().unwrap(),
                            f(13, 2.into(), 1.into()),
                        ))
                        .unwrap(),
                    proof: Proof::Simple(vec![
                        base_step(182),
                        // 0^inf 1 3^2 <A 1^13 2 0^inf
                        rule_step(17, &[("n", "2"), ("c", "1")]),
                        // 0^inf 1 <A 1^13 2^x 0^inf   for x = f(13, 2, 1)
                        base_step(1),
                    ]),
                },
                // Permutation: Start State B.
                //      TNF: 1RB3RB1LC2LA_2LA2RB1LB3RA_1RA1RZ1LC2RA
                //      Score: g_7^2(1) + 8 = 2{6}4 + 5
                Rule {
                    init_config: Config::from_str("0^inf B> 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 1 Z> 1^7 2^x 0^inf")
                        .unwrap()
                        .subst(&VarSubst::single(
                            "x".parse().unwrap(),
                            f(7, 2.into(), 1.into()),
                        ))
                        .unwrap(),
                    proof: Proof::Simple(vec![
                        base_step(84),
                        // 0^inf 1 3^2 <A 1^7 2 0^inf
                        rule_step(11, &[("n", "2"), ("c", "1")]),
                        // 0^inf 1 <A 1^7 2^x 0^inf   for x = f(7, 2, 1)
                        base_step(1),
                    ]),
                },
            ],
        };
        if let Err(err) = validate_rule_set(&rule_set) {
            panic!("{}", err);
        }
    }

    #[test]
    fn test_43_a2_uni() {
        // 1RB1RD1LC_2LB1RB1LC_1RZ1LA1LD_0RB2RA2RD
        // SuperPowers(2)
        // Common config: 21^n 2^k <D 1^a 0^inf
        // Note: This proof is not complete, there are several Admits.

        fn f1(n: CountExpr, a: CountExpr) -> CountExpr {
            CountExpr::RecursiveExpr(RecursiveExpr {
                func: Box::new(Function {
                    bound_var: "z".parse().unwrap(),
                    expr: CountExpr::from_str("2z+4").unwrap(),
                }),
                num_repeats: Box::new(n),
                base: Box::new(a),
            })
        }
        fn f2(n: CountExpr, a: CountExpr) -> CountExpr {
            CountExpr::RecursiveExpr(RecursiveExpr {
                func: Box::new(Function {
                    bound_var: "z".parse().unwrap(),
                    expr: f1("z+2".parse().unwrap(), 2.into()),
                }),
                num_repeats: Box::new(n),
                base: Box::new(a),
            })
        }
        fn f3(n: CountExpr, a: CountExpr) -> CountExpr {
            CountExpr::RecursiveExpr(RecursiveExpr {
                func: Box::new(Function {
                    bound_var: "z".parse().unwrap(),
                    expr: f1(1.into(), f2("z+2".parse().unwrap(), 2.into())),
                }),
                num_repeats: Box::new(n),
                base: Box::new(a),
            })
        }

        let rule_set = RuleSet {
            tm: TM::from_str("1RB1RD1LC_2LB1RB1LC_1RZ1LA1LD_0RB2RA2RD").unwrap(),
            rules: vec![
                chain_rule("A> 1^2n", "12^n A>", 2), // 0
                chain_rule("12^n <A", "<A 1^2n", 2), // 1
                // 2
                Rule {
                    init_config: Config::from_str("12^n <C 1^2a+1 0^inf").unwrap(),
                    final_config: Config::from_str("<C 1^2a+1+4n 0^inf").unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 12^n 12 <C 1^2a+1 0^inf
                            base_step(2),
                            // 12^n 2 A> 1^2a+2 0^inf
                            chain_step(0, "a+1"),
                            // 12^n 2 12^a+1 A> 0^inf
                            base_step(5),
                            // 12^n 2 12^a+1 <A 1^2 0^inf
                            chain_step(1, "a+1"),
                            // 12^n 2 <A 1^2a+4 0^inf
                            base_step(1),
                            // 12^n <C 1^2a+5 0^inf
                            induction_step(&[("a", "a+2")]),
                        ],
                    },
                },
                // 3
                Rule {
                    init_config: Config::from_str("12^n <D 1^2a+2 0^inf").unwrap(),
                    final_config: Config::from_str("<D 1^2x+2 0^inf")
                        .unwrap()
                        .subst(&VarSubst::from(&[(
                            "x".parse().unwrap(),
                            f1("n".parse().unwrap(), "a".parse().unwrap()),
                        )]))
                        .unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 12 <D 1^2a+2 0^inf
                            base_step(2),
                            // 12 2 A> 1^2a+1 0^inf
                            chain_step(0, "a"),
                            // 12 2 12^a A> 1 0^inf
                            base_step(7),
                            // 12 2 12^a <A 1^2 2 0^inf
                            chain_step(1, "a"),
                            // 12 2 <A 1^2a+2 2 0^inf
                            base_step(3),
                            // 2 A> 1^2a+4 2 0^inf
                            chain_step(0, "a+2"),
                            // 2 12^a+2 A> 2 0^inf
                            base_step(1),
                            // 2 12^a+2 <C 1 0^inf
                            rule_step(2, &[("n", "a+2"), ("a", "0")]),
                            // 2 <C 1^4a+9 0^inf
                            base_step(1),
                            // <D 1^4a+10 0^inf
                            induction_step(&[("a", "2a+4")]),
                        ],
                    },
                },
                // 4
                Rule {
                    init_config: Config::from_str("12^n 2 <D 1^2a+2 0^inf").unwrap(),
                    final_config: Config::from_str("2 <D 1^2x+2 0^inf")
                        .unwrap()
                        .subst(&VarSubst::from(&[(
                            "x".parse().unwrap(),
                            f2("n".parse().unwrap(), "a".parse().unwrap()),
                        )]))
                        .unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 122 <D 1^2a+2 0^inf
                            base_step(2),
                            // 1222 A> 1^2a+1 0^inf
                            chain_step(0, "a"),
                            // 1222 12^a A> 1 0^inf
                            base_step(7),
                            // 1222 12^a <A 1^2 2 0^inf
                            chain_step(1, "a"),
                            // 1222 <A 1^2a+2 2 0^inf
                            base_step(4),
                            // 122 A> 1^2a+3 2 0^inf
                            chain_step(0, "a+1"),
                            // 122 12^a+1 A> 12 0^inf
                            base_step(7),
                            // 122 12^a+1 <A 1^2 22 0^inf
                            chain_step(1, "a+1"),
                            // 122 <A 1^2a+4 22 0^inf
                            base_step(3),
                            // 2 A> 1^2a+6 22 0^inf
                            chain_step(0, "a+3"),
                            // 2 12^a+3 A> 22 0^inf
                            base_step(19),
                            // 2 12^a+2 <D 1^6 0^inf
                            rule_step(3, &[("n", "a+2"), ("a", "2")]),
                            // 2 <D 1^2x+2 0^inf   for x = f1(a+2, 2)
                            induction_step_expr(&[(
                                "a".parse().unwrap(),
                                f1("a+2".parse().unwrap(), 2.into()),
                            )]),
                        ],
                    },
                },
                // 5
                Rule {
                    init_config: Config::from_str("0^inf 1^6n <D 1^2a+2 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf <D 1^2x+2 0^inf")
                        .unwrap()
                        .subst(&VarSubst::from(&[(
                            "x".parse().unwrap(),
                            f3("n".parse().unwrap(), "a".parse().unwrap()),
                        )]))
                        .unwrap(),
                    proof: Proof::Inductive {
                        proof_base: vec![],
                        proof_inductive: vec![
                            // 1^6 <D 1^2a+2 0^inf
                            base_step(1),
                            // 1^4 12 A> 1^2a+2 0^inf
                            chain_step(0, "a+1"),
                            // 1^4 12^a+2 A> 0^inf
                            base_step(5),
                            // 1^4 12^a+2 <A 1^2 0^inf
                            chain_step(1, "a+1"),
                            // 1^4 12 <A 1^2a+4 0^inf
                            base_step(4),
                            // 1^3 12 A> 1^2a+5 0^inf
                            chain_step(0, "a+2"),
                            // 1^3 12^a+3 A> 1 0^inf
                            base_step(7),
                            // 1^3 12^a+3 <A 1^2 2 0^inf
                            chain_step(1, "a+2"),
                            // 1^3 12 <A 1^2a+6 2 0^inf
                            base_step(4),
                            // 1^2 12 A> 1^2a+7 2 0^inf
                            chain_step(0, "a+3"),
                            // 1^2 12^a+4 A> 12 0^inf
                            base_step(7),
                            // 1^2 12^a+4 <A 11 22 0^inf
                            chain_step(1, "a+3"),
                            // 1^2 12 <A 1^2a+8 22 0^inf
                            base_step(4),
                            // 1 12 A> 1^2a+9 22 0^inf
                            chain_step(0, "a+4"),
                            // 1 12^a+5 A> 122 0^inf
                            base_step(30),
                            // 1 12^a+5 2 <D 1^6 0^inf
                            ProofStep::Admit,
                            // This doesn't work yet, b/c the tape actually looks like:
                            //      0^inf 1^6n+2 2 12^a+4 2 <D 1^6 0^inf
                            // which cannot (yet) be normalized to:
                            //      0^inf 1^6n+1 12^a+5 2 <D 1^6 0^inf
                            rule_step(4, &[("n", "a+5"), ("a", "2")]),
                            // 12 <D 1^2x+2 0^inf  x = f2(a+5, 2)
                            ProofStep::RuleStep {
                                rule_id: 3,
                                var_assignment: VarSubst::from(&[
                                    ("n".parse().unwrap(), 1.into()),
                                    ("a".parse().unwrap(), f2("a+5".parse().unwrap(), 2.into())),
                                ]),
                            },
                            // <D 1^2y+2 0^inf  y = f1(1, x) = 2x+4
                        ],
                    },
                },
                chain_rule("B> 1^n", "1^n B>", 1), // 6
                // 7
                Rule {
                    init_config: Config::from_str("0^inf 11 <D 1^2a+2 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 1^2a+2 <D 1^2x+2 0^inf")
                        .unwrap()
                        .subst(&VarSubst::from(&[(
                            "x".parse().unwrap(),
                            f1(1.into(), f2(3.into(), 2.into())),
                        )]))
                        .unwrap(),
                    proof: Proof::Simple(vec![
                        // 0^inf 11 <D 1^2a+2 0^inf
                        base_step(1),
                        // 0^inf 12 A> 1^2a+2 0^inf
                        chain_step(0, "a+1"),
                        // 0^inf 12^a+2 A> 0^inf
                        base_step(5),
                        // 0^inf 12^a+2 <A 1^2 0^inf
                        chain_step(1, "a+1"),
                        // 0^inf 12 <A 1^2a+4 0^inf
                        base_step(3),
                        // 0^inf 1 B> 1^2a+6 0^inf
                        chain_step(6, "2a+6"),
                        // 0^inf 1 1^2a+6 B> 0^inf
                        base_step(66),
                        // 0^inf 1^2a+3 12^3 2 <D 1^6 0^inf
                        rule_step(4, &[("n", "3"), ("a", "2")]),
                        // 0^inf 1^2a+3 2 <D 1^2x+2 0^inf  x = f2(3, 2)
                        ProofStep::RuleStep {
                            rule_id: 3,
                            var_assignment: VarSubst::from(&[
                                ("n".parse().unwrap(), 1.into()),
                                ("a".parse().unwrap(), f2(3.into(), 2.into())),
                            ]),
                        },
                        // 0^inf 1^2a+2 <D 1^2y+2 0^inf  y = f1(1, x) = 2x+4
                    ]),
                },
                // 8
                Rule {
                    init_config: Config::from_str("0^inf 111 <D 1^2a+2 0^inf").unwrap(),
                    final_config: Config::from_str("0^inf 1^2a+4 <D 1^2x+2 0^inf")
                        .unwrap()
                        .subst(&VarSubst::from(&[(
                            "x".parse().unwrap(),
                            f1(1.into(), f2(3.into(), 2.into())),
                        )]))
                        .unwrap(),
                    proof: Proof::Simple(vec![
                        // 0^inf 111 <D 1^2a+2 0^inf
                        base_step(1),
                        // 0^inf 1 12 A> 1^2a+2 0^inf
                        chain_step(0, "a+1"),
                        // 0^inf 1 12^a+2 A> 0^inf
                        base_step(5),
                        // 0^inf 1 12^a+2 <A 1^2 0^inf
                        chain_step(1, "a+1"),
                        // 0^inf 112 <A 1^2a+4 0^inf
                        base_step(4),
                        // 0^inf 12 A> 1^2a+5 0^inf
                        chain_step(0, "a+2"),
                        // 0^inf 12^a+3 A> 1 0^inf
                        base_step(7),
                        // 0^inf 12^a+3 <A 1^2 2 0^inf
                        chain_step(1, "a+2"),
                        // 0^inf 12 <A 1^2a+6 2 0^inf
                        base_step(3),
                        // 0^inf 1 B> 1^2a+8 2 0^inf
                        chain_step(6, "2a+8"),
                        // 0^inf 1 1^2a+8 B> 2 0^inf
                        base_step(64),
                        // 0^inf 1^2a+5 12^3 2 <D 1^6 0^inf
                        rule_step(4, &[("n", "3"), ("a", "2")]),
                        // 0^inf 1^2a+5 2 <D 1^2x+2 0^inf  x = f2(3, 2)
                        ProofStep::RuleStep {
                            rule_id: 3,
                            var_assignment: VarSubst::from(&[
                                ("n".parse().unwrap(), 1.into()),
                                ("a".parse().unwrap(), f2(3.into(), 2.into())),
                            ]),
                        },
                        // 0^inf 1^2a+4 <D 1^2y+2 0^inf  y = f1(1, x) = 2x+4
                    ]),
                },
                // Halt Proof
                Rule {
                    init_config: Config::new(),
                    final_config: Config::from_str("0^inf Z> 0^inf").unwrap(),
                    proof: Proof::Simple(vec![
                        base_step(92),
                        // 0^inf 1^4 12^2 2 <D 1^6 0^inf
                        rule_step(4, &[("n", "2"), ("a", "2")]),
                        // 0^inf 1^4 2 <D 1^2x+2 0^inf  x = f2(2, 2)
                        ProofStep::RuleStep {
                            rule_id: 3,
                            var_assignment: VarSubst::from(&[
                                ("n".parse().unwrap(), 1.into()),
                                ("a".parse().unwrap(), f2(2.into(), 2.into())),
                            ]),
                        },
                        // 0^inf 1^3 <D 1^2y+2 0^inf    y = f1(1, x) = 2x+4
                        ProofStep::RuleStep {
                            rule_id: 8,
                            var_assignment: VarSubst::from(&[(
                                "a".parse().unwrap(),
                                f1(1.into(), f2(2.into(), 2.into())),
                            )]),
                        },
                        // 0^inf 1^4x+12 <D 1^2a+2 0^inf    a = f1(1, f2(3, 2))
                        //
                        ProofStep::Admit, // TODO
                        //
                        // At this point we need to calculate the remainder of
                        // 4x+12 % 6 where x = f2(2, 2) = f1(f1(4, 2)+2, 2)
                        //                   = f1(6 2^2 - 2, 2) = f1(22, 2)
                        //                   = 6 2^22 - 4
                        // so x % 6 = 2 and 4x+12 % 6 = 2
                        // ... but we cannot yet prove this in our system ...
                        //
                        // TODO: In this case this number can fit in memory,
                        // so we could implement a way to evaluate functions ...
                        //
                        // Longer term, we will want to create a way to get
                        // remainders even for formulas that cannot be evaluated.
                        ProofStep::RuleStep {
                            rule_id: 5,
                            var_assignment: VarSubst::from(&[(
                                "n".parse().unwrap(),
                                (2_u64.pow(24) + 1).into(),
                            )]),
                        },
                        // 0^inf 1^2 <D 1^2b+2 0^inf    b = f3(2^24 + 1, a)
                        ProofStep::RuleStep {
                            rule_id: 7,
                            var_assignment: VarSubst::from(&[(
                                "a".parse().unwrap(),
                                f3(
                                    (2_u64.pow(24) + 1).into(),
                                    f1(1.into(), f2(3.into(), 2.into())),
                                ),
                            )]),
                        },
                        // 0^inf 1^2b+2 <D 1^2a+2 0^inf
                    ]),
                },
            ],
        };
        if let Err(err) = validate_rule_set(&rule_set) {
            panic!("{}", err);
        }
    }
}

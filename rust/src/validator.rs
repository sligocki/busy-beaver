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
    use std::str::FromStr;

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
    fn test_34_a14_uni() {
        // http://sligocki.com/2024/05/22/bb-2-5-a14.html
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
                // 4
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
                            induction_step(&[("n", "n+1")]),
                        ],
                    },
                },
                // 5
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
}

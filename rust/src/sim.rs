use std::convert::From;
use std::{fmt, ops};

use enum_map::enum_map;

use crate::config::*;
use crate::tm::*;

// Simulate on ConfigConcrete
#[derive(Debug)]
pub struct Simulator {
    pub tm: TM,
    pub tm_config: ConfigConcrete,
    pub status: SimStatus,

    // Stats
    pub num_sim_steps: u64,
    pub num_base_steps: u64,
}

impl Simulator {
    fn next_trans(&self) -> Step {
        let read_block = self.tm_config.front_block();
        let in_state = self.tm_config.state;
        let in_dir = self.tm_config.dir;
        let in_conf = BlockConfig {
            state: in_state,
            dir: in_dir,
            block: read_block,
        };
        // println!(" Debug: In: {:?}", in_conf);
        let out = sim_block(&self.tm, in_conf);
        // println!(" Debug: Out: {:?}", out);
        if let SimStatus::Running = out.status {
            if out.config.state == in_state && out.config.dir == in_dir {
                return Step::Chain {
                    write_block: out.config.block,
                    num_base_steps_per_rep: out.num_base_steps,
                };
            } else {
                return Step::Macro {
                    trans: out.config,
                    num_base_steps: out.num_base_steps,
                };
            }
        } else {
            // TM is no longer running
            return Step::Terminate(out);
        }
    }

    fn apply(&mut self, step: Step) {
        match step {
            Step::Macro {
                trans,
                num_base_steps,
            } => {
                self.tm_config.drop_one_front();
                self.tm_config.dir = trans.dir;
                self.tm_config.state = trans.state;
                self.tm_config.push_rep_back(RepBlock {
                    block: trans.block,
                    rep: Rep::Finite(1),
                });
                self.num_base_steps += num_base_steps;
            }
            Step::Chain {
                write_block,
                num_base_steps_per_rep,
            } => {
                let read_rep_block = self.tm_config.pop_rep_front();
                self.tm_config.push_rep_back(RepBlock {
                    block: write_block,
                    rep: read_rep_block.rep,
                });
                match read_rep_block.rep {
                    Rep::Finite(read_rep) => {
                        self.num_base_steps += num_base_steps_per_rep * read_rep;
                    }
                    Rep::Infinite => {
                        // Chain step over 0^inf => TM will never halt!
                        self.status = SimStatus::Infinite;
                    }
                }
            }
            Step::Terminate(res) => {
                self.status = res.status;
                todo!();
            }
        }
    }

    pub fn step(&mut self) {
        if let SimStatus::Running = self.status {
            let step = self.next_trans();
            self.apply(step);
            self.num_sim_steps += 1;
        }
    }

    pub fn run(&mut self, max_steps: u64) {
        while self.status == SimStatus::Running && self.num_sim_steps < max_steps {
            self.step();
        }
    }
}


fn sim_test() {
    let mut sim = Simulator {
        // BB(6) champ
        // tm: TM::parse("1RB0LD_1RC0RF_1LC1LA_0LE1RZ_1LF0RB_0RC0RE"),
        tm: TM::parse("1RB1LD_1RC1RB_1LC1LA_0RC0RD"),
        tm_config: ConfigConcrete {
            tape: enum_map! {
                Dir::Left =>  vec![ RepBlock{ block: vec![0], rep: Rep::Infinite }, ],
                Dir::Right => vec![ RepBlock{ block: vec![0], rep: Rep::Infinite }, ],
            },
            state: State::Run(0),
            dir: Dir::Right,
        },
        status: SimStatus::Running,
        num_sim_steps: 0,
        num_base_steps: 0,
    };
    println!("{} {:?} {}", sim.num_sim_steps, sim.status, sim.tm_config);
    sim.run(100_000);
    println!("{} {:?} {}", sim.num_sim_steps, sim.status, sim.tm_config);
    println!("Status: {:?}", sim.status);
    println!("Num Steps: {}", sim.num_base_steps);
}

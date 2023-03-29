use std::convert::From;

use crate::config::*;
use crate::tm::*;

// Simulate on fixed sized block
#[derive(Debug)]
struct SimFixedConfig {
    state: State,
    tape: Vec<Symbol>,
    pos: i64,
}
#[derive(Debug, PartialEq, Copy, Clone)]
pub enum SimStatus {
    Running,
    Halted,
    UndefinedTrans,
    Infinite,
    OverSteps,
}
#[derive(Debug)]
struct SimFixedResult {
    status: SimStatus,
    config: SimFixedConfig,
    num_steps: u64,
}

const MAX_STEPS: u64 = 1_000_000;
fn sim_fixed(tm: &TM, start_config: SimFixedConfig) -> SimFixedResult {
    let mut config = start_config;
    let mut num_steps = 0;
    while let State::Run(state_in) = config.state {
        if config.pos < 0 || config.pos >= config.tape.len().try_into().unwrap() {
            return SimFixedResult {
                status: SimStatus::Running,
                config,
                num_steps,
            };
        }
        if num_steps >= MAX_STEPS {
            return SimFixedResult {
                status: SimStatus::OverSteps,
                config,
                num_steps,
            };
        }
        let symb_in = config.tape[config.pos as usize];
        num_steps += 1;
        if let Some(trans) = tm.trans(state_in, symb_in) {
            // println!("({:?}, {:?}) -> ({:?}, {:?}, {:?})", state_in, symb_in, symb_out, dir_out, state_out);
            // Write, move, state change
            config.tape[config.pos as usize] = trans.symbol;
            config.pos += trans.dir.delta();
            config.state = trans.state;
        } else {
            return SimFixedResult {
                status: SimStatus::UndefinedTrans,
                config,
                num_steps,
            };
        }
    }
    return SimFixedResult {
        status: SimStatus::Halted,
        config,
        num_steps,
    };
}

#[derive(Debug)]
struct BlockConfig {
    state: State,
    dir: Dir,
    block: Vec<Symbol>,
}

#[derive(Debug)]
struct BlockResult {
    status: SimStatus,
    config: BlockConfig,
    num_base_steps: u64,
}

impl From<SimFixedConfig> for BlockConfig {
    fn from(c: SimFixedConfig) -> Self {
        let dir = if c.pos < 0 { Dir::Left } else { Dir::Right };
        BlockConfig {
            state: c.state,
            dir,
            block: c.tape,
        }
    }
}

impl From<SimFixedResult> for BlockResult {
    fn from(res: SimFixedResult) -> Self {
        BlockResult {
            status: res.status,
            config: res.config.into(),
            num_base_steps: res.num_steps,
        }
    }
}

impl From<BlockConfig> for SimFixedConfig {
    fn from(c: BlockConfig) -> Self {
        let pos: i64 = match c.dir {
            Dir::Right => 0,
            Dir::Left => (c.block.len() - 1) as i64,
        };
        SimFixedConfig {
            state: c.state,
            tape: c.block,
            pos,
        }
    }
}

fn sim_block(tm: &TM, c: BlockConfig) -> BlockResult {
    BlockResult::from(sim_fixed(tm, c.into()))
}

#[derive(Debug)]
enum StepType {
    // Single step in macro machine A> 1010 -> <D 1101
    MacroStep {
        trans: BlockConfig,
        num_base_steps: u64,
    },
    // Chainable step: A> 1101 -> 0101 A>
    ChainStep {
        write_block: Vec<Symbol>,
        num_base_steps_per_rep: u64,
    },

    // Step leading to TM not running (Halting, Infinite, etc.)
    TerminateStep(BlockResult),
}

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
    fn next_trans(&self) -> StepType {
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
                return StepType::ChainStep {
                    write_block: out.config.block,
                    num_base_steps_per_rep: out.num_base_steps,
                };
            } else {
                return StepType::MacroStep {
                    trans: out.config,
                    num_base_steps: out.num_base_steps,
                };
            }
        } else {
            // TM is no longer running
            return StepType::TerminateStep(out);
        }
    }

    fn apply(&mut self, step: StepType) {
        match step {
            StepType::MacroStep {
                trans,
                num_base_steps,
            } => {
                self.tm_config.drop_one_front();
                self.tm_config.dir = trans.dir;
                self.tm_config.state = trans.state;
                self.tm_config.push_rep_back(RepBlock {
                    block: trans.block,
                    rep: Rep::Int(1),
                });
                self.num_base_steps += num_base_steps;
            }
            StepType::ChainStep {
                write_block,
                num_base_steps_per_rep,
            } => {
                let read_rep_block = self.tm_config.pop_rep_front();
                self.tm_config.push_rep_back(RepBlock {
                    block: write_block,
                    rep: read_rep_block.rep,
                });
                match read_rep_block.rep {
                    Rep::Int(read_rep) => {
                        self.num_base_steps += num_base_steps_per_rep * read_rep;
                    }
                    Rep::Infinite => {
                        // Chain step over 0^inf => TM will never halt!
                        self.status = SimStatus::Infinite;
                    }
                }
            }
            StepType::TerminateStep(res) => {
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

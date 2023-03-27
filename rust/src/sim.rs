use std::convert::From;

use crate::tm::*;
use crate::config::*;

// Simulate on fixed sized block
#[derive(Debug)]
struct SimFixedConfig {
    state: State,
    tape: Vec<Symbol>,
    pos: i64,
}
#[derive(Debug)]
enum SimFixedStatus {
    Running,
    Halted,
    UndefinedTrans,
    // TODO: Infinite,
    OverSteps,
}
#[derive(Debug)]
struct SimFixedResult {
    status: SimFixedStatus,
    config: SimFixedConfig,
    num_steps: Const,
}

const MAX_STEPS : u64 = 1_000_000;
fn sim_fixed(tm : &TM, start_config: SimFixedConfig) -> SimFixedResult {
    let mut config = start_config;
    let mut num_steps = 0;
    while let State::Run(state_in) = config.state {
        if config.pos < 0 || config.pos >= config.tape.len().try_into().unwrap() {
            return SimFixedResult { status: SimFixedStatus::Running, config, num_steps };
        }
        if num_steps >= MAX_STEPS {
            return SimFixedResult { status: SimFixedStatus::OverSteps, config, num_steps };
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
            return SimFixedResult { status: SimFixedStatus::UndefinedTrans, config, num_steps };
        }
    }
    return SimFixedResult { status: SimFixedStatus::Halted, config, num_steps };
}

pub fn test_sim() {
    let tm = TM::parse("1RB1RZ_0RC1RB_1LC1LA");
    let start_config = SimFixedConfig {
        state: State::Run(0),
        tape: [0; 20].to_vec(),
        pos: 10,
    };
    let result = sim_fixed(&tm, start_config);
    println!("Result: {:?}", result);
    println!("{:?}", result.status);
    println!("{:?}", result.config);
    println!("{:?}", result.num_steps);
}

#[derive(Debug)]
struct BlockConfig {
    state: State,
    dir: Dir,
    block: Vec<Symbol>,
}

#[derive(Debug)]
struct BlockResult {
    status: SimFixedStatus,
    config: BlockConfig,
    num_base_steps: Const,
}

impl From<SimFixedConfig> for BlockConfig {
    fn from(c : SimFixedConfig) -> Self {
        let dir = if c.pos < 0 {Dir::Left} else {Dir::Right};
        BlockConfig { state: c.state, dir, block: c.tape }
    }
}

impl From<SimFixedResult> for BlockResult {
    fn from(res : SimFixedResult) -> Self {
        BlockResult { status: res.status, config: res.config.into(), num_base_steps: res.num_steps }
    }
}

impl From<BlockConfig> for SimFixedConfig {
    fn from(c : BlockConfig) -> Self {
        let pos : i64 = match c.dir {
            Dir::Right => 0,
            Dir::Left => (c.block.len() - 1) as i64,
        };
        SimFixedConfig { state: c.state, tape: c.block, pos }
    }
}

fn sim_block(tm : &TM, c : BlockConfig) -> BlockResult {
    BlockResult::from(sim_fixed(tm, c.into()))
}

// Simulate on ConfigConcrete
#[derive(Debug)]
pub struct Simulator {
    pub tm: TM,
    pub tm_config: ConfigConcrete,
    // Stats
    pub num_sim_steps: u64,
    pub num_base_steps: Const,
}

impl Simulator {
    pub fn step(&mut self) {
        if let State::Run(_) = self.tm_config.state {
            let rep_block = self.tm_config.pop_front();
            let in_conf = BlockConfig { state: self.tm_config.state, dir: self.tm_config.dir, block: rep_block.block };
            println!(" Debug: In: {:?}", in_conf);
            let out = sim_block(&self.tm, in_conf);
            println!(" Debug: Out: {:?}", out);
            if let SimFixedStatus::Running = out.status {
                if out.config.state == self.tm_config.state &&
                   out.config.dir == self.tm_config.dir {
                    // Chain step
                    self.tm_config.push_back(RepBlock { block: out.config.block, rep: rep_block.rep });
                    self.num_sim_steps += 1;
                    self.num_base_steps += out.num_base_steps * rep_block.rep;
                } else {
                    todo!();
                }
            } else {
                todo!();
            }
        }
    }
}

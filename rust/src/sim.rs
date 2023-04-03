use std::convert::From;
use std::{fmt, ops};

use enum_map::enum_map;

use crate::config::*;
use crate::tm::*;

type ConcreteRep = Rep<Count>;

impl ops::Add<ConcreteRep> for ConcreteRep {
    type Output = ConcreteRep;
    fn add(self, rhs: ConcreteRep) -> ConcreteRep {
        match (self, rhs) {
            (Rep::Infinite, _) => Rep::Infinite,
            (_, Rep::Infinite) => Rep::Infinite,
            (Rep::Finite(x), Rep::Finite(y)) => Rep::Finite(x + y),
        }
    }
}

impl ops::AddAssign<ConcreteRep> for ConcreteRep {
    fn add_assign(&mut self, rhs: ConcreteRep) {
        *self = *self + rhs;
    }
}

impl fmt::Display for ConcreteRep {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Rep::Infinite => write!(f, "inf"),
            Rep::Finite(x) => write!(f, "{}", x),
        }
    }
}

// Config where all reptitions are fixed integer values.
// Used for simulating concrete TM configs.
pub type ConfigConcrete = RepConfig<ConcreteRep>;

impl ConfigConcrete {
    pub fn front_block(&self) -> Vec<Symbol> {
        match self.tape[self.dir].last() {
            None => todo!(),
            Some(x) => x.block.clone(), // TODO: Make this more efficient.
        }
    }

    pub fn pop_rep_front(&mut self) -> RepBlock<Count> {
        match self.tape[self.dir].pop() {
            None => todo!(),
            Some(x) => x,
        }
    }

    pub fn drop_one_front(&mut self) {
        match self.tape[self.dir].last_mut() {
            None => todo!(),
            Some(RepBlock {
                rep: Rep::Infinite, ..
            }) => {}
            Some(RepBlock {
                rep: Rep::Finite(1), ..
            }) => {
                self.tape[self.dir].pop();
            }
            Some(RepBlock {
                rep: Rep::Finite(rep), ..
            }) => {
                *rep -= 1;
            }
        }
    }

    pub fn push_rep_back(&mut self, x: RepBlock<Count>) {
        if let Some(top) = self.tape[self.dir.opp()].last_mut() {
            if top.block == x.block {
                // Merge equal blocks
                top.rep += x.rep;
                return;
            }
        }
        self.tape[self.dir.opp()].push(x);
    }
}

impl fmt::Display for RepBlock<Count> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let block_str = self.block.iter().map(|x| x.to_string()).collect::<String>();
        write!(f, "{}^{}", block_str, self.rep)
    }
}

impl fmt::Display for ConfigConcrete {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        for x in self.tape[Dir::Left].iter() {
            write!(f, "{} ", x)?;
        }
        match self.dir {
            Dir::Left => {
                write!(f, "<{} ", self.state)?;
            }
            Dir::Right => {
                write!(f, "{}> ", self.state)?;
            }
        };
        for x in self.tape[Dir::Right].iter().rev() {
            write!(f, "{} ", x)?;
        }
        Ok(())
    }
}

// TODO:
// pub type VariableId = u64;
//
// // Expression which is a variable plus a constant.
// //      x + const
// pub struct ExprVarPlus {
//     var: VariableId,
//     constant: Const,
// }
//
// // Expression linear in one variable.
// //      coef * x + const
// pub struct ExprLinear {
//     var: VariableId,
//     coef: Const,
//     constant: Const,
// }
//
// // An implementaion of RepT for variable repetitions (ex: 10^{x+3}).
// pub enum RepVar {
//     Concrete(Const),
//     VarPlus(ExprVarPlus),
//     Linear(ExprLinear),
// }
//
// // Config where some repetition counts may be variable.
// // Used for proving general rules.
// pub type ConfigVar = Config<RepVar>;


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
    SimFixedResult {
        status: SimStatus::Halted,
        config,
        num_steps,
    }
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
enum Step {
    // Single step in macro machine A> 1010 -> <D 1101
    Macro {
        trans: BlockConfig,
        num_base_steps: u64,
    },
    // Chainable step: A> 1101 -> 0101 A>
    Chain {
        write_block: Vec<Symbol>,
        num_base_steps_per_rep: u64,
    },

    // Step leading to TM not running (Halting, Infinite, etc.)
    Terminate(BlockResult),
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

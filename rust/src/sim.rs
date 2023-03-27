use crate::tm::*;

// Simulate on fixed sized block
#[derive(Debug)]
struct SimFixedConfig {
    state: State,
    tape: Vec<Symbol>,
    pos: i32,
}
#[derive(Debug)]
enum SimFixedStatus {
    Running,
    Halted,
    // TODO: Infinite,
    OverSteps,
}
#[derive(Debug)]
struct SimFixedResult {
    status: SimFixedStatus,
    config: SimFixedConfig,
    num_steps: u64,
}

const MAX_STEPS : u64 = 1_000_000;
fn sim_fixed(tm : TransFunc, start_config: SimFixedConfig) -> SimFixedResult {
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
        let (symb_out, dir_out, state_out) = tm(state_in, symb_in);
        // Write, move, state change
        config.tape[config.pos as usize] = symb_out;
        config.pos += dir_out.delta();
        config.state = state_out;
        num_steps += 1;
    }
    return SimFixedResult { status: SimFixedStatus::Halted, config, num_steps };
}

pub fn test_sim() {
    let tm : TransFunc = |state_in, symb_in| {
        match (state_in, symb_in) {
            (0, 0) => (1, Dir::Right, State::Run(1)),   // A0 -> 1RB
            (0, 1) => (1, Dir::Left,  State::Run(0)),   // A1 -> 1LA
            (1, 0) => (1, Dir::Left,  State::Run(1)),   // B0 -> 1LB
            (1, 1) => (1, Dir::Right, State::Halt),     // B1 -> 1RH
            (_, _) => unreachable!(),
        }
    };
    let start_config = SimFixedConfig {
        state: State::Run(0),
        tape: [0; 20].to_vec(),
        pos: 10,
    };
    let result = sim_fixed(tm, start_config);
    println!("Result: {:?}", result);
    println!("{:?}", result.status);
    println!("{:?}", result.config);
    println!("{:?}", result.num_steps);
}


// // Simulate on ConfigConcrete
// pub struct SimConfig {
//     tm: TransFunc,
//     tm_config: ConfigConcrete,
//     // Stats
//     num_sim_steps: u64,
// }
//
// impl SimConfig {
//     fn step(&self) -> SimConfig {
//         if tm_config.state == Halt { return self; }
//
//
//     }
// }

use busy_beaver::tm::*;
use busy_beaver::config::*;
use busy_beaver::sim::*;

use enum_map::enum_map;

fn main() {
    // test_sim();

    let mut sim = Simulator {
        // BB(6) champ
        // tm: TM::parse("1RB0LD_1RC0RF_1LC1LA_0LE1RZ_1LF0RB_0RC0RE"),
        tm : TM::parse("1RB1LD_1RC1RB_1LC1LA_0RC0RD"),
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
    while let SimStatus::Running = sim.status {
        sim.step();
        println!("{} {:?} {}", sim.num_sim_steps, sim.status, sim.tm_config);
    }
    println!("Status: {:?}", sim.status);
    println!("Num Steps: {}", sim.num_base_steps);
}

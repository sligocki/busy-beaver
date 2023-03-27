use busy_beaver::tm::*;
use busy_beaver::config::*;
use busy_beaver::sim::*;

use enum_map::enum_map;

fn main() {
    // test_sim();

    let mut sim = Simulator {
        // BB(6) champ
        tm: TM::parse("1RB0LD_1RC0RF_1LC1LA_0LE1RZ_1LF0RB_0RC0RE"),
        tm_config: ConfigConcrete {
            // 10^10 11 0^14 <C 1
            tape: enum_map! {
                Dir::Left => vec![
                    RepBlock{ block: vec![1, 0], rep: 10 },
                    RepBlock{ block: vec![1, 1], rep: 11 },
                    RepBlock{ block: vec![0], rep: 14},
                ],
                Dir::Right => vec![ RepBlock{ block: vec![1], rep: 1 } ],
            },
            state: State::Run(2),
            dir: Dir::Left,
        },
        num_sim_steps: 0,
        num_base_steps: 0,
    };
    loop {
        sim.step();
        println!("{:?}", sim.tm_config.tape);
    }
}

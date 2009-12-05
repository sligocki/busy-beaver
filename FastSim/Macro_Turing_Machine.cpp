#include "Macro_Turing_Machine.h"

Macro_Turing_Machine::Macro_Turing_Machine(shared_ptr<Turing_Machine> a_base_machine,
                                           const int                & a_block_size)
                                           // TODO: allow block offset.
{
  m_block_size = a_block_size;
  m_base_machine = a_base_machine;
  
  // Construct this machines start state, dir and blank symbol from base machine
  m_init_state = m_base_machine.m_init_state;
  m_init_dir   = m_base_machine.m_init_dir;
  
  // TODO: This probably isn't right.
  m_init_symbol = new BlockSymbol(m_block_size);
  for (int i = 0; i < m_block_size; i++)
  {
    m_init_symbol[i] = m_base_machine.m_init_symbol;
  }
  
  m_num_states  = m_base_machine.m_num_states;
  m_num_symbols = m_base_machine.m_num_symbols;
  // Maximum number of base-steps per macro-step evaluation w/o repeat
  // #positions * #states * #macro_symbols
  m_max_steps = m_block_size * m_num_states * m_num_symbols;
}

Macro_Turing_Machine::~Macro_Turing_Machine()
{
  delete m_init_symbol;
}

// The "sigma score" contribution from a symbol.
// Value of a block of symbols is the sum of the value of the symbols.
int Simple_Turing_Machine::eval_symbol(const SYMBOL & a_symbol);
{
  int sum = 0;
  for (int i = 0; i < m_block_size; i++)
  {
    sum += m_base_machine.eval_symbol(a_symbol[i]);
  }
  
  return sum;
};

// The "sigma score" contribution from the state.
// Block Macro Machines contribute nothing from state, but the base machine.
int Simple_Turing_Machine::eval_state(const STATE & a_state)
{
  return m_base_machine.eval_state(a_state);
};

void Macro_Turing_Machine::get_transition(RUN_STATE        & a_run_state,
                                          TRANSITION       & a_trans_out,
                                          INTEGER          & a_num_steps,
                                          const SYMBOL     & a_cur_symbol, // TODO: Why do we have cur_symbol and trans_in?
                                          const TRANSITION & a_trans_in)
{
  a_num_steps = 0;
  int num_macro_steps = 0;
  
  SYMBOL tape = /*copy*/ a_cur_symbol; // TODO: make it right.
  
  BASE_SYMBOL symbol; // The symbol for the base machine inside the "tape".
  STATE state = a_trans_in.m_state; // NOTE: this will mutate the state unless we copy.
  DIR dir = a_trans_in.m_dir;
  
  int pos;
  if (dir == RIGHT)
  {
    pos = 0;
  }
  else
  {
    pos = m_block_size - 1;
  }
  
  TRANSITION trans_out;
  INTEGER steps_in_trans;
  
  // Simulate the base machine on a finite tape until it falls off.
  while (0 <= pos && pos < m_block_size)
  {
    symbol = tape[pos];
    
    // Get base transition
    m_base_machine.get_transition(a_run_state, trans_out, steps_in_trans,
                                  symbol, new Transition(state, symbol, dir));
    a_num_steps += steps_in_trans;
    num_macro_steps++;
    
    tape[pos] = trans_out.m_symbol;
    state = trans_out.m_state;
    dir = trans_out.m_dir;
    
    if (dir == RIGHT)
    {
      pos++;
    }
    else
    {
      pos--;
    }
    
    // TM halted (or infinity) stop running.
    if (a_run_state != RUNNING)
    {
      a_trans_out = new Transition(state, tape, dir);
      return;
    }
    // Ran too long, it'll never halt.
    if (num_macro_steps > m_max_steps)
    {
      a_run_state = INFINITE;
      a_trans_out = new Transition(state, tape, dir);
      return;
    }
  }
  
  // Done, base TM fell off tape.
  a_trans_out = new Transition(state, tape, dir);
  return;
}

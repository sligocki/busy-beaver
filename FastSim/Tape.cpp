#include "Tape.h"

Tape::Tape()
{
  m_is_defined = false;
}

Tape::~Tape()
{
}

void Tape::define(const TRANSITION & a_init_trans)
{
  m_init_symbol = a_init_trans.m_symbol;

  m_dir = a_init_trans.m_dir;

  REPEATED_SYMBOL infinite_zero;
  infinite_zero.m_symbol = m_init_symbol;
  infinite_zero.m_number = INFINITY;

  m_tape[0].push_back(infinite_zero);
  m_tape[1].push_back(infinite_zero);
  
  m_displace = 0;

  m_is_defined = true;
}

INTEGER Tape::get_nonzeros(const INTEGER & a_state_value)
{
  INTEGER num;

  num = a_state_value;

  for (int dir = 0; dir < 2; dir++)
  {
    int n = m_tape[dir].size();

    for (int i = 0; i < n; i++)
    {
      if (m_tape[dir][i].m_number != INFINITY)
      {
        num += m_tape[dir][i].m_number;
      }
    }
  }

  return num;
}

REPEATED_SYMBOL Tape::get_top_block()
{
  return m_tape[m_dir][0];
}

SYMBOL Tape::get_top_symbol()
{
  return m_tape[m_dir][0].m_symbol;
}

void Tape::apply_single_move(const TRANSITION & a_trans)
{
  {
    vector<REPEATED_SYMBOL> & stack = m_tape[m_dir];
    REPEATED_SYMBOL & top = stack[0];
    if (top.m_number != INFINITY)
    {
      top.m_number--;

      if (top.m_number == 0)
      {
        stack.erase(stack.begin());
      }
    }
  }

  {
    vector<REPEATED_SYMBOL> & stack = m_tape[1 - a_trans.m_dir];
    REPEATED_SYMBOL & top = stack[0];
    if (top.m_symbol == a_trans.m_symbol)
    {
      if (top.m_number != INFINITY)
      {
        top.m_number++;
      }
    }
    else
    {
      REPEATED_SYMBOL new_repeat;
      new_repeat.m_symbol = a_trans.m_symbol;
      new_repeat.m_number = 1;

      stack.insert(stack.begin(),new_repeat);
    }
  }

  m_dir = a_trans.m_dir;

  if (m_dir == 0)
  {
    m_displace--;
  }
  else
  {
    m_displace++;
  }
}

INTEGER Tape::apply_chain_move(const SYMBOL & a_new_symbol)
{
  INTEGER num;

  vector<REPEATED_SYMBOL> & stack_dir = m_tape[m_dir];
  num = stack_dir[0].m_number;

  if (num != INFINITY)
  {
    stack_dir.erase(stack_dir.begin());

    vector<REPEATED_SYMBOL> & stack_not_dir = m_tape[1 - m_dir];
    REPEATED_SYMBOL & top = stack_not_dir[0];
    if (top.m_symbol == a_new_symbol)
    {
      if (top.m_number != INFINITY)
      {
        top.m_number += num;
      }
    }
    else
    {
      REPEATED_SYMBOL new_repeat;
      new_repeat.m_symbol = a_new_symbol;
      new_repeat.m_number = num;

      stack_not_dir.insert(stack_not_dir.begin(),new_repeat);
    }

    if (m_dir == 0)
    {
      m_displace -= num;
    }
    else
    {
      m_displace += num;
    }
  }

  return num;
}

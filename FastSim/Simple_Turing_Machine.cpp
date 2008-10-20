#include "Simple_Turing_Machine.h"

Simple_Turing_Machine::Simple_Turing_Machine(const TTable& a_ttable)
{
  m_ttable = a_ttable;

  m_init_state  = 0;
  m_init_symbol = 0;
  m_init_dir    = 1;
}

Simple_Turing_Machine::~Simple_Turing_Machine()
{
}

#include "TTable.h"

TTable::TTable()
{
  m_num_states  = 0;
  m_num_symbols = 0;

  m_transitions = NULL;

  m_is_defined = false;
}

TTable::~TTable()
{
  clear();
}
    
void TTable::clear()
{
  if (m_transitions != NULL)
  {
    for (int state = 0; state < m_num_states; state++)
    {
      if (m_transitions[state] != NULL)
      {
        delete[] m_transitions[state];
      }
    }

    delete[] m_transitions;

    m_num_states  = 0;
    m_num_symbols = 0;

    m_transitions = NULL;

    m_is_defined = false;
  }
}

void TTable::define(const int                        & a_num_states,
                    const int                        & a_num_symbols,
                    const vector<vector<TRANSITION> >& a_transitions)
{
  m_num_states  = a_num_states;
  m_num_symbols = a_num_symbols;

  m_transitions = new TRANSITION*[m_num_states];
  for (int state = 0; state < m_num_states; state++)
  {
    m_transitions[state] = new TRANSITION[m_num_symbols];
  }

  m_is_defined = true;
}

bool TTable::read(FILE* a_file)
{
}

#include "Tape.h"

ostream& operator<<(ostream             & a_ostream,
                    const Tape<INTEGER> & a_tape)
{
  for (int i = a_tape.m_tape[0].size()-1; i >= 0; i--)
  {
    a_ostream << "(" << a_tape.m_tape[0][i].m_symbol << ",";
    if (a_tape.m_tape[0][i].m_number != INFINITY)
    {
      a_ostream << a_tape.m_tape[0][i].m_number;
    }
    else
    {
      a_ostream << "inf";
    }
    a_ostream << ")";
  }

  a_ostream << " ";

  for (int i = 0; i < a_tape.m_tape[1].size(); i++)
  {
    a_ostream << "(" << a_tape.m_tape[1][i].m_symbol << ",";
    if (a_tape.m_tape[1][i].m_number != INFINITY)
    {
      a_ostream << a_tape.m_tape[1][i].m_number;
    }
    else
    {
      a_ostream << "inf";
    }
    a_ostream << ")";
  }

  a_ostream << endl;

  return a_ostream;
}

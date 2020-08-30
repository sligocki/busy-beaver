#ifndef Transition_Table_H
#define Transition_Table_H

#include <cstddef>

#include "Transition.h"

class Transition_Table
{
  public:
    inline Transition_Table(char a_num_states,
                            char a_num_symbols)
    {
      m_num_states  = a_num_states;
      m_num_symbols = a_num_symbols;

      m_table = new Transition* [m_num_states];

      for (int i = 0; i < m_num_states; i++)
      {
        m_table[i] = new Transition [m_num_symbols];
      }
    }

    inline Transition_Table(const Transition_Table& a_tt)
    {
      m_num_states  = a_tt.m_num_states;
      m_num_symbols = a_tt.m_num_symbols;

      m_table = new Transition* [m_num_states];

      for (int i = 0; i < m_num_states; i++)
      {
        m_table[i] = new Transition [m_num_symbols];

        for (int j = 0; j < m_num_symbols; j++)
        {
          m_table[i][j] = a_tt.m_table[i][j];
        }
      }
    }

    inline Transition_Table& operator=(const Transition_Table& a_tt)
    {
      if (this != &a_tt)
      {
        m_num_states  = a_tt.m_num_states;
        m_num_symbols = a_tt.m_num_symbols;

        m_table = new Transition* [m_num_states];

        for (int i = 0; i < m_num_states; i++)
        {
          m_table[i] = new Transition [m_num_symbols];

          for (int j = 0; j < m_num_symbols; j++)
          {
            m_table[i][j] = a_tt.m_table[i][j];
          }
        }
      }

      return *this;
    }

    inline ~Transition_Table()
    {
      for (int i = 0; i < m_num_states; i++)
      {
        delete [] m_table[i];
      }

      delete [] m_table;

      m_num_states  = 0;
      m_num_symbols = 0;

      m_table = NULL;
    }

    char m_num_states;
    char m_num_symbols;

    Transition **m_table;
};

#endif

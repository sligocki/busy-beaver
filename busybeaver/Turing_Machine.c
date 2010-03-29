#include <stdio.h>
#include <stdlib.h>

#include "Turing_Machine.h"

inline int step_TM(TM* m)
{
  m->new_symbol = m->machine[m->state].t[m->symbol].w;
  m->new_delta  = m->machine[m->state].t[m->symbol].d;
  m->new_state  = m->machine[m->state].t[m->symbol].s;

  m->total_steps++;

  if (m->new_symbol == -1)
  {
    if (m->symbol == 0) {
      m->total_symbols++;
    }

    return RESULT_UNDEFINED;
  }

  if (m->symbol == 0 && m->new_symbol != 0) {
    m->total_symbols++;
  }

  if (m->symbol != 0 && m->new_symbol == 0)
  {
    m->total_symbols--;
  }

  m->tape[m->position] = m->new_symbol;
  m->position += m->new_delta;

  if (m->new_state == -1)
  {
    return RESULT_HALTED;
  }

  if (m->position < 1 || m->position >= m->tape_length - 1)
  {
    return RESULT_NOTAPE;
  }

  if (m->position < m->max_left)
  {
    m->max_left = m->position;
  }
  
  if (m->position > m->max_right)
  {
    m->max_right = m->position;
  }
  
  m->symbol = m->tape[m->position];
  m->state = m->new_state;

  return RESULT_STEPPED;
}

inline void print_TM(TM* m)
{
  int state,symbol;

  fprintf(stderr,"Machine, (%d %4d)\n",
          m->num_states,m->num_symbols);
  for (state = 0; state < m->num_states; state++)
  {
    fprintf(stderr,"  State: %d\n",state);
    for (symbol = 0; symbol < m->num_symbols; symbol++)
    {
      fprintf(stderr,"    Symbol: %4d -> ",symbol);
      fprintf(stderr,"%4d ",m->machine[state].t[symbol].w);
      fprintf(stderr,"%2d ",m->machine[state].t[symbol].d);
      fprintf(stderr,"%2d\n",m->machine[state].t[symbol].s);
    }
  }
}

inline void free_TM(TM* m)
{
  if (m != NULL)
  {
    if (m->machine != NULL)
    {
      int state;
      for (state = 0; state < m->num_states; state++)
      {
        free(m->machine[state].t);
      }

      free(m->machine);
      m->machine = NULL;
    }

    if (m->tape != NULL)
    {
      free(m->tape);
      m->tape = NULL;
    }
  }
}

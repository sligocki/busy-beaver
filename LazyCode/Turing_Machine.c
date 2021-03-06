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

inline int step_recur_TM(TM* m, unsigned long long step_num)
{
  if (m->symbol == -1)
  {
#if 1
    int i;
    int* scanTape;
    int place = -1; 
    int prev_symbol = -2;
    int rep_count = 0;
#endif

#if 1
    printf("%7llu ",step_num);
#endif

#if 1
    scanTape = m->tape;
    for (i = 0; i < m->tape_length; i++)
    {
      int symbol = *(scanTape++);

#if 1
      if (i == m->position)
      {
        if (m->new_delta == 1)
        {
          if (place == -1)
          {
            printf(" 0^Inf");
            place = 0;
          }
          else
          {
            if (rep_count > 0)
            {
              printf(" %d^%d",prev_symbol,rep_count);
            }
          }

          printf(" %c>",m->state + 'A');

          if (symbol != -1)
          {
            prev_symbol = symbol;
            rep_count = 1;
          }
          else
          {
            if (place == 0) {
              printf(" 0^Inf");
              place = 1;
            }

            prev_symbol = -2;
            rep_count = 0;
          }
        }
        else if (m->new_delta == -1)
        {
          if (symbol != -1)
          {
            if (place == -1)
            {
              printf(" 0^Inf");
              place = 0;
            }

            if (symbol != prev_symbol)
            {
              if (prev_symbol != -2)
              {
                printf(" %d^%d",prev_symbol,rep_count);
              }

              prev_symbol = symbol;
              rep_count = 1;
            }
            else
            {
              rep_count++;
            }

            printf(" %d^%d",prev_symbol,rep_count);
          }
          else
          {
            if (place == -1)
            {
              printf(" 0^Inf");
              place = 0;
            }
          }

          printf(" <%c",m->state + 'A');

          prev_symbol = -2;
          rep_count = 0;
        }
        else
        {
          printf(" Unknown-delta");
        }
      }
      else
      {
        if (symbol != -1)
        {
          if (place == -1)
          {
            printf(" 0^Inf");
            place = 0;
          }

          if (symbol != prev_symbol)
          {
            if (rep_count > 0)
            {
              printf(" %1d^%d",prev_symbol,rep_count);
            }

            prev_symbol = symbol;
            rep_count = 1;
          }
          else
          {
            rep_count++;
          }
        }
        else
        {
          if (rep_count != 0)
          {
            printf(" %1d^%d",prev_symbol,rep_count);

            prev_symbol = -1;
            rep_count = 0;
          }

          if (place == 0) {
            printf(" 0^Inf");
            place = 1;
          }
        }
      }
#endif
    }
#endif

#if 1
    if (rep_count != 0)
    {
      printf(" %1d^%d",prev_symbol,rep_count);
    }

    if (step_num == 0)
    {
      printf("  (0, 0)");
    }
    else
    {
      printf("  (1, %llu)",step_num);
    }

    printf("\n");
#endif

    m->symbol = 0;
  }

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

  if (m->new_symbol == 0)
  {
    if ((m->new_delta == -1 && m->tape[m->position + 1] == -1) ||
        (m->new_delta ==  1 && m->tape[m->position - 1] == -1))
    {
      m->new_symbol = -1;
    }
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

inline int step_recur_2_4_054_TM(TM* m, unsigned long long step_num)
{
  if (m->symbol == -1)
  {
    int i;
    int* scanTape;
    int place;
    int prev_symbol;
    int rep_count1;
    int rep_count2;
    char good_tape;

    place = 0;

    scanTape = m->tape + m->max_left-1;
    prev_symbol = *(scanTape++);

    rep_count1 = 0;
    rep_count2 = 0;

    good_tape = 1;

    for (i = m->max_left; i <= m->max_right+1; i++)
    {
      int symbol = *(scanTape++);

      if (place == 0 && prev_symbol == -1 && symbol != -1)
      {
        if (i != m->position+1)
        {
          good_tape = 0;
          break;
        }

        place = 1;
      }

      if (place == 1)
      {
        if (symbol        != 3 ||
            *(scanTape+0) != 2 ||
            *(scanTape+1) != 0 ||
            *(scanTape+2) != 2 ||
            *(scanTape+3) != 0)
        {
          if (rep_count1 > 0)
          {
            place = 2;
          }
          else
          {
            good_tape = 0;
            break;
          }
        }
        else
        {
          i += 4;
          scanTape += 4;
          rep_count1++;
        }
      }

      if (place == 2)
      {
        if (symbol        != 2 ||
            *(scanTape+0) != 0)
        {
          place = 3;
        }
        else
        {
          i += 1;
          scanTape += 1;
          rep_count2++;
        }
      }

      if (place == 3)
      {
        if (symbol        ==  2 ||
            *(scanTape+0) == -1)
        {
          place = 4;
        }

        break;
      }

      prev_symbol = symbol;
    }

    if (place != 4) {
      good_tape = 0;
    }

    if (good_tape)
    {
      printf("%7llu ",step_num);

      printf(" 0^Inf");
      printf(" <A");
      printf(" (3,2,0,2,0)^%d",rep_count1);
      printf(" (2,0)^%d",rep_count2);
      printf(" 0^Inf");

      if (step_num == 0)
      {
        printf("  (0, 0)");
      }
      else
      {
        printf("  (1, %llu)",step_num);
      }

      printf("\n");
      fflush(stdout);
    }

    m->symbol = 0;
  }

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

  if (m->new_symbol == 0)
  {
    if ((m->new_delta == -1 && m->tape[m->position + 1] == -1) ||
        (m->new_delta ==  1 && m->tape[m->position - 1] == -1))
    {
      m->new_symbol = -1;
    }
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

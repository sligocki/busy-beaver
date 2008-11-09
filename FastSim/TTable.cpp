#include "TTable.h"

TTable::TTable()
{
  clear();
}

TTable::~TTable()
{
  clear();
}
    
void TTable::clear()
{
  m_num_states  = 0;
  m_num_symbols = 0;

  m_is_defined = false;
}

void TTable::define(const int                         & a_num_states,
                    const int                         & a_num_symbols,
                    const vector<vector<TRANSITION> > & a_transitions)
{
  m_num_states  = a_num_states;
  m_num_symbols = a_num_symbols;

  m_transitions = a_transitions;

  m_is_defined = true;
}

#define SKIP_WHITESPACE(a_char,a_file)             \
        while (isspace((a_char) = fgetc(a_file))); \

bool TTable::read(FILE* a_file)
{
  int cur_char;

  SKIP_WHITESPACE(cur_char,a_file);

  if (cur_char != '[')
  {
    Error("Unable to read initial '[' in TM");
  }

  SKIP_WHITESPACE(cur_char,a_file);

  int num_states = 0;
  int num_symbols;
  vector<vector<TRANSITION> > transitions;

  while (cur_char != ']')
  {
    num_states++;

    num_symbols = 0;

    if (cur_char != '[')
    {
      Error("Unable to read initial '[' for state transitions");
    }

    SKIP_WHITESPACE(cur_char,a_file);

    vector<TRANSITION> state_transitions;

    while (cur_char != ']')
    {
      TRANSITION cur_transition;

      if (cur_char != '(')
      {
        Error("Unable to read '(' for transition");
      }

      SKIP_WHITESPACE(cur_char,a_file);

      ungetc(cur_char,a_file);
      if (fscanf(a_file,"%d",&(cur_transition.m_state)) != 1)
      {
        Error("Unable to read new state for transition");
      }

      SKIP_WHITESPACE(cur_char,a_file);

      if (cur_char != ',')
      {
        Error("Unable to read first ',' in transition");
      }

      SKIP_WHITESPACE(cur_char,a_file);

      ungetc(cur_char,a_file);
      if (fscanf(a_file,"%d",&(cur_transition.m_symbol)) != 1)
      {
        Error("Unable to read new symbol for transition");
      }

      SKIP_WHITESPACE(cur_char,a_file);

      if (cur_char != ',')
      {
        Error("Unable to read first ',' in transition");
      }

      SKIP_WHITESPACE(cur_char,a_file);

      ungetc(cur_char,a_file);
      if (fscanf(a_file,"%d",&(cur_transition.m_dir)) != 1)
      {
        Error("Unable to read direction for transition");
      }

      SKIP_WHITESPACE(cur_char,a_file);

      if (cur_char != ')')
      {
        Error("Unable to read ')' in transition");
      }

      state_transitions.push_back(cur_transition);

      SKIP_WHITESPACE(cur_char,a_file);

      if (cur_char == ',')
      {
        SKIP_WHITESPACE(cur_char,a_file);
      }
    }

    transitions.push_back(state_transitions);
  }

  define(num_states,num_symbols,transitions);
}

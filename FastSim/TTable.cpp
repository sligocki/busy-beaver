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
      num_symbols++;

      TRANSITION cur_transition;

      if (cur_char != '(')
      {
        Error("Unable to read '(' for transition");
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

      if (cur_char != ',')
      {
        Error("Unable to read second ',' in transition");
      }

      SKIP_WHITESPACE(cur_char,a_file);

      ungetc(cur_char,a_file);
      if (fscanf(a_file,"%d",&(cur_transition.m_state)) != 1)
      {
        Error("Unable to read new state for transition");
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

    SKIP_WHITESPACE(cur_char,a_file);

    if (cur_char == ',')
      {
        SKIP_WHITESPACE(cur_char,a_file);
      }
  }

  define(num_states,num_symbols,transitions);

  return true;
}

ostream& operator<<(ostream      & a_ostream,
                    const TTable & a_ttable)
{
  a_ostream << "   ";
  for (int symbol = 0; symbol < a_ttable.m_num_symbols; symbol++)
  {
    a_ostream << "  " << symbol << "   ";
  }
  a_ostream << endl;

  a_ostream << "  +";
  for (int symbol = 0; symbol < a_ttable.m_num_symbols; symbol++)
  {
    a_ostream << "-----+";
  }
  a_ostream << endl;

  for (int state = 0; state < a_ttable.m_num_states; state++)
  {
    const vector<TRANSITION>& row = a_ttable.m_transitions[state];

    char state_char = 'A' + state;
    a_ostream << state_char << " |";

    for (int symbol = 0; symbol < a_ttable.m_num_symbols; symbol++)
    {
      const TRANSITION& cur_trans = row[symbol];

      a_ostream << " " << cur_trans.m_symbol;

      if (cur_trans.m_dir == 0)
      {
        a_ostream << 'L';
      }
      else
      {
        a_ostream << 'R';
      }

      if (cur_trans.m_state == -1)
      {
        a_ostream << "H |";
      }
      else
      {
        char new_state_char = 'A' + cur_trans.m_state;
        a_ostream << new_state_char << " |";
      }
    }

    a_ostream << endl;

    a_ostream << "  +";
    for (int symbol = 0; symbol < a_ttable.m_num_symbols; symbol++)
    {
      a_ostream << "-----+";
    }
    a_ostream << endl;
  }

  return a_ostream;
}

template <class T> inline Tape<T>::Tape()
{
  m_is_defined = false;
}

template <class T> inline Tape<T>::~Tape()
{
}

template <class T> inline void Tape<T>::define(const TRANSITION & a_init_trans)
{
  m_init_symbol = a_init_trans.m_symbol;

  m_dir = a_init_trans.m_dir;

  Repeated_Symbol<T> infinite_zero;
  infinite_zero.m_symbol = m_init_symbol;
  infinite_zero.m_number = INFINITY;

  m_half_tape[0].push_back(infinite_zero);
  m_half_tape[1].push_back(infinite_zero);
  
  m_displace = 0;

  m_is_defined = true;
}

template <class T> inline T Tape<T>::num_nonzero(shared_ptr<Turing_Machine> a_machine,
                                                 const STATE              & a_state)
{
  T num;

  num = a_machine->eval_state(a_state);

  for (int dir = 0; dir < 2; dir++)
  {
    int n = m_half_tape[dir].size();

    for (int i = 0; i < n; i++)
    {
      const SYMBOL & symbol = m_half_tape[dir][i].m_symbol;
      const T      & number = m_half_tape[dir][i].m_number;

      if (symbol != m_init_symbol && number != INFINITY)
      {
        num += a_machine->eval_symbol(symbol) * number;
      }
    }
  }

  return num;
}

template <class T> inline Repeated_Symbol<T> Tape<T>::get_top_block()
{
  return m_half_tape[m_dir][0];
}

template <class T> inline SYMBOL Tape<T>::get_top_symbol()
{
  return m_half_tape[m_dir][0].m_symbol;
}

template <class T> inline void Tape<T>::apply_single_move(const TRANSITION & a_trans)
{
  // Pop off the top symbol that we're reading.
  {
    vector<Repeated_Symbol<T> > & stack = m_half_tape[m_dir];
    Repeated_Symbol<T> & top = stack[0];
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
    vector<Repeated_Symbol<T> > & stack = m_half_tape[1 - a_trans.m_dir];
    Repeated_Symbol<T> & top = stack[0];
    if (top.m_symbol == a_trans.m_symbol)
    {
      if (top.m_number != INFINITY)
      {
        top.m_number++;
      }
    }
    else
    {
      Repeated_Symbol<T> new_repeat;
      new_repeat.m_symbol = a_trans.m_symbol;
      new_repeat.m_number = 1;

      stack.insert(stack.begin(),new_repeat);
    }
  }

  m_dir = a_trans.m_dir;

  if (m_dir == LEFT)
  {
    m_displace--;
  }
  else
  {
    m_displace++;
  }
}

template <class T> inline T Tape<T>::apply_chain_move(const SYMBOL & a_new_symbol)
{
  T num;

  vector<Repeated_Symbol<T> > & stack_dir = m_half_tape[m_dir];
  num = stack_dir[0].m_number;

  if (num != INFINITY)
  {
    stack_dir.erase(stack_dir.begin());

    vector<Repeated_Symbol<T> > & stack_not_dir = m_half_tape[1 - m_dir];
    Repeated_Symbol<T> & top = stack_not_dir[0];
    if (top.m_symbol == a_new_symbol)
    {
      if (top.m_number != INFINITY)
      {
        top.m_number += num;
      }
    }
    else
    {
      Repeated_Symbol<T> new_repeat;
      new_repeat.m_symbol = a_new_symbol;
      new_repeat.m_number = num;

      stack_not_dir.insert(stack_not_dir.begin(),new_repeat);
    }

    if (m_dir == LEFT)
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

template <class T> inline Tape<T> & Tape<T>::operator=(const Tape<T> & a_tape)
{
}

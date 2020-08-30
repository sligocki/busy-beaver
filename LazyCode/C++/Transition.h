#ifndef Transition_H
#define Transition_H

class Transition
{
  public:
    inline Transition()
    {
      // By default set to an illegal transition
      m_new_symbol = -1;
      m_new_state  = -1;
      m_inc        =  0;
    }

    inline ~Transition()
    {
    }

    inline bool isValid()
    {
      return ((m_inc == -1) || (m_inc == 1));
    }

    inline bool isInvalid()
    {
      return !isValid();
    }

    char m_new_symbol;
    char m_new_state;
    char m_inc;
};

#endif

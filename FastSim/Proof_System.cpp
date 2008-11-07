#include "Proof_System.h"

Proof_System::Proof_System()
{
  m_is_defined = false;
}

Proof_System::~Proof_System()
{
  m_is_defined = false;
}

void Proof_System::define(const Turing_Machine& a_machine,
                          const bool&           a_recursive)
{
  m_machine   = a_machine;
  m_recursive = a_recursive;

  m_is_defined = true;
}

void Proof_System::log(RUN_STATE&     a_cond,
                       Tape&          a_new_tape,
                       INTEGER&       a_num_steps,
                       const Tape&    a_old_tape,
                       const STATE&   a_old_state,
                       const INTEGER& a_step_num,
                       const INTEGER& a_loop_num)
{
  Error("Not implemented...");
}

bool Proof_System::compare()
{
  Error("Not implemented...");
}

bool Proof_System::applies()
{
  Error("Not implemented...");
}

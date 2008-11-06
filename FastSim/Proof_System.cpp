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

bool Proof_System::log()
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

#include "Exception.h"

void warning(const char* const a_warning)
{
  fprintf(stderr,"%s\n",a_warning);
}

void error(const char* const a_error)
{
  fprintf(stderr,"%s\n",a_error);
  abort();
}

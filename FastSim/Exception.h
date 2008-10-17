#ifndef _EXCEPTION_H_
#define _EXCEPTION_H_

#include "Define.h"

#define EXCEPTION_STR(s)  # s
#define EXCEPTION_XSTR(s) EXCEPTION_STR(s)

#define Warning(a_warning) \
        warning(__FILE__ ", line " EXCEPTION_XSTR(__LINE__) ": " a_warning);

#define Error(a_error) \
        error(__FILE__ ", line " EXCEPTION_XSTR(__LINE__) ": " a_error);

extern void warning(const char* const a_warning);

extern void error(const char* const a_error);

#endif

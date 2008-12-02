#include "Expression.h"

// Global variable ids bound, to assure we can distinguish variables
static VARIABLE g_num_variables = 0;

VARIABLE new_var()
{
  return g_num_variables++;
}

void Expression::add_new_variable()
{
  m_vars[new_var()] = 1;
}

void Expression::add(Expression a_other)
{
  // Iterate through a_other expression's variable list and add
  for (var_map::iterator it = a_other.m_vars.begin(); it != a_other.m_vars.end(); it++)
  {
    VARIABLE var = it->first;
    int coef = it->second;
    // TODO: I assume that m_vars[n] will initialize to 0 if not already set (is it safe?)
    m_vars[var] += coef;
  }
  
  // Add the constant
  m_constant += a_other.m_constant;
}

INTEGER Expression::eval(map<VARIABLE, INTEGER> a_assign)
{
  // result = constant + "evaluation of variables"
  INTEGER result = m_constant;
  
  // Iterate through expression's variable list and evaluate
  for (var_map::iterator it = m_vars.begin(); it != m_vars.end(); it++)
  {
    VARIABLE var = it->first;
    int coef = it->second;
    
    result += coef * a_assign[var];
  }
  
  // Add the constant
  return result;
}

VARIABLE Expression::get_var()
{
  // Must be only one variable
  assert(m_vars.size() == 1);
  
  // Must have coeficient of one
  var_map::iterator it = m_vars.begin();
  assert(it->second == 1);
  
  return it->first;
}

// return a string representation for a variable
char repr_variable(VARIABLE a_var)
{
  assert(a_var < 60);
  
  return a_var + 'A';
}

ostream& operator<<(ostream& a_stream, Expression a_expr)
{
  // Iterate through expression's variable list and print
  for (var_map::iterator it = a_expr.m_vars.begin(); it != a_expr.m_vars.end(); it++)
  {
    VARIABLE var = it->first;
    int coef = it->second;
    
    if (coef == 1)
    {
      a_stream << repr_variable(var) << " + ";
    }
    else if (coef == -1)
    {
      a_stream << "-" << repr_variable(var) << " + ";
    }
    else
    {
      a_stream << coef << repr_variable(var) << " + ";
    }
  }
  
  // Print the constant
  a_stream << a_expr.m_constant;
  
  return a_stream;
}

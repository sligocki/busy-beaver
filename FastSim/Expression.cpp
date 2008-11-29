#include "Expression.h"

// Global variable ids bound, to assure we can distinguish variables
VARIABLE num_variables = 0;

VARIABLE new_var()
{
  return num_variables++;
}

void Expression::add_new_variable()
{
  m_vars[new_var()] = 1;
}

void Expression::add(Expression other)
{
  // Iterate through other expression's variable list and add
  for (var_map::iterator it = other.m_vars.begin(); it != other.m_vars.end(); it++)
  {
    VARIABLE var = it->first;
    int coef = it->second;
    // TODO: I assume that m_vars[n] will initialize to 0 if not already set (is it safe?)
    m_vars[var] += coef;
  }
  
  // Add the constant
  m_constant += other.m_constant;
}

INTEGER Expression::eval(map<VARIABLE, INTEGER> assign)
{
  // result = constant + "evaluation of variables"
  INTEGER result = m_constant;
  
  // Iterate through expression's variable list and evaluate
  for (var_map::iterator it = m_vars.begin(); it != m_vars.end(); it++)
  {
    VARIABLE var = it->first;
    int coef = it->second;
    
    result += coef * assign[var];
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
char repr_variable(VARIABLE var)
{
  assert(var < 60);
  
  return var + 'A';
}

ostream& operator<<(ostream& stream, Expression expr)
{
  // Iterate through expression's variable list and print
  for (var_map::iterator it = expr.m_vars.begin(); it != expr.m_vars.end(); it++)
  {
    VARIABLE var = it->first;
    int coef = it->second;
    
    if (coef == 1)
    {
      stream << repr_variable(var) << " + ";
    }
    else if (coef == -1)
    {
      stream << "-" << repr_variable(var) << " + ";
    }
    else
    {
      stream << coef << repr_variable(var) << " + ";
    }
  }
  
  // Print the constant
  stream << expr.m_constant;
  
  return stream;
}

#include "Expression.h"

// Global variable ids bound, to assure we can distinguish variables
VARIABLE num_variables = 0;

VARIABLE new_var()
{
  return num_variables++;
}

void Expression::add_new_variable()
{
  vars[new_var()] = 1;
}

void Expression::add(Expression other)
{
  // Iterate through other expression's variable list and add
  for (var_map::iterator it = other.vars.begin(); it != other.vars.end(); it++)
  {
    VARIABLE var = it->first;
    int coef = it->second;
    // TODO: I assume that vars[n] will initialize to 0 if not already set (is it safe?)
    vars[var] += coef;
  }
  
  // Add the constant
  constant += other.constant;
}

INTEGER Expression::eval(map<VARIABLE, INTEGER> assign)
{
  // result = constant + "evaluation of variables"
  INTEGER result = constant;
  
  // Iterate through expression's variable list and evaluate
  for (var_map::iterator it = vars.begin(); it != vars.end(); it++)
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
  assert(vars.size() == 1);
  
  // Must have coeficient of one
  var_map::iterator it = vars.begin();
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
  for (var_map::iterator it = expr.vars.begin(); it != expr.vars.end(); it++)
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
  stream << expr.constant;
  
  return stream;
}


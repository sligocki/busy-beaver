#ifndef _GENERAL_INTEGER_H_
#define _GENERAL_INTEGER_H_

#include "Define.h"

// Variable labels
typedef int VARIABLE;
// Returns a new, distinct variable
VARIABLE new_var();

typedef map<VARIABLE, int> var_map; // TODO: should this be a diff type of int?

// A linear combination of variables and integers
class Expression
{
  public:
    // Set of variables and their coeficients.
    // e.g. if expr = 2x + 1, then vars[x] = 2 and vars[y] = 0
    var_map vars;
    
    // Integer constant. e.g. the 1 from above
    INTEGER constant; // TODO: should this be a diff type of int?
    
    // Cast an integer to an Expression type with no variables.
    Expression(INTEGER const_in=0)
    {
      constant = const_in;
    };
    
    // Create an expression from one variable + one constant.
    Expression(INTEGER const_in, VARIABLE var_in)
    {
      vars[var_in] = 1;
      constant = const_in;
    };
    
    virtual ~Expression()
    {
    };
    
    // Add a new variable to the expression: 2 -> x + 2
    void add_new_variable();
    
    // Arithmetic operations that mutate this object (like += and -=)
    void add(Expression other);
    //void sub(Expression other);
    void add_int(INTEGER other) { constant += other; };
    void sub_int(INTEGER other) { constant -= other; };
    
    // Evaluate this expression with a given variable assignment
    INTEGER eval(map<VARIABLE, INTEGER> assign);
    
    // Get the single variable from an expression.
    // TODO: This is ugly, can we find another way to do this?
    VARIABLE get_var();
    
    friend ostream& operator<<(ostream& stream, Expression ob);
};

#endif

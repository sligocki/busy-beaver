#ifndef _EXPRESSION_H_
#define _EXPRESSION_H_

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
    // e.g. if expr = 2x + 1, then m_vars[x] = 2 and m_vars[y] = 0
    var_map m_vars;
    
    // Integer constant. e.g. the 1 from above
    INTEGER m_constant; // TODO: should this be a diff type of int?
    
    // Cast an integer to an Expression type with no variables.
    Expression(INTEGER a_const_in=0)
    {
      m_constant = a_const_in;
    };
    
    // Create an expression from one variable + one constant.
    Expression(INTEGER a_const_in, VARIABLE a_var_in)
    {
      m_vars[a_var_in] = 1;
      m_constant = a_const_in;
    };
    
    virtual ~Expression()
    {
    };

    // Add a new variable to the expression: 2 -> x + 2
    void add_new_variable();
    
    // Arithmetic operations that mutate this object (like += and -=)
    void add(Expression a_other);
    //void sub(Expression a_other);
    void add_int(INTEGER a_other) { m_constant += a_other; };
    void sub_int(INTEGER a_other) { m_constant -= a_other; };
    
    // Evaluate this expression with a given variable assignment
    INTEGER eval(map<VARIABLE, INTEGER> a_assign);
    
    // Get the single variable from an expression.
    // TODO: This is ugly, can we find another way to do this?
    VARIABLE get_var();
    
    friend ostream& operator<<(ostream& a_stream, Expression a_expr);
};

#endif

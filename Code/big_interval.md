# BigInterval: Rigorous Interval Arithmetic for Large Numbers

## Motivation
When analyzing Busy Beaver machines, we encounter numbers so large that they cannot be stored directly in memory. For example, the current BB(6) champion has score > 10 ↑↑ 10 ↑↑ 10 ↑↑ 8. These numbers must be stored as unevaluated formula in our code. As the formula get more and more complex it becomes challenging to interpret and compare them.

This module provides a concise and readily comparible notation for large numbers. There are evidently too many large numbers to be able to specify all of them concisely, so instead we restrict ourselves to a specific subset expressed in a very precise way called `Knuth10` (similar to the use of floating point numbers to approximate reals).

In the same way that traditional interval arithmetic is built on top of the representable numbers in floating point arithmetic. This module also provides `BigInterval`, a rigorously bounded interval arithmetic system on top of `Knuth10` numbers.

By carefully restricting the canonical form of these grid points, we achieve fast lexicographical comparisons without ever suffering from floating-point imprecision or memory blowups.

## The Knuth10 Representation
A `Knuth10` object represents a number using Knuth's up-arrow notation with a fixed base of 10. Let 
   $$g_k(x) = 10 \uparrow^k x$$

A number is represented internally as a tuple of non-negative integers $A = (a_0, a_1, \dots, a_K)$, which evaluates to:
   $$ \text{Value}(A) = g_K^{a_K}( \dots g_2^{a_2}( g_1^{a_1}(a_0) ) \dots ) $$

The fundamental bridging identity between levels of the hierarchy is:
   $$ g_k(x) = g_{k-1}^x(1) $$

*(One application of $g_k$ is exactly $x$ applications of $g_{k-1}$ starting from a base of 1).*

## The Lexicographical Ordering Goal
One of the primary goals of our notation is that two numbers should be easily and efficiently comparible. Intuitively one `Knuth10` number is large than another if it has more iterations of the highest level functions. In other words, if its tuple is lexicographically larger (comparing highest index first).

However, this lexicographical ordering is not guaranteed to correspond to numeric ordering if we allow arbitrary values for $a_i$. For example, 
   $$(1, 0, 2) = 10 \uparrow\uparrow 10 < 10 \uparrow\uparrow 10^{10} = (10, 10, 1)$$

Therefor, we must provide some sort of restriction on which `Knuth10` values to accept in order to ensure that lexicographical ordering coincides with numeric ordering. A subset of `Knuth10` values will be said to have the "lexicolization property" if their lexicographical ordering coincides with numeric ordering. 

## The Greedy Bounding Algorithm
In fact, we can ensure exactly this property by using a greedy algorithm. Fix some constant cutoff $C \ge 10$ small enought that we don't mind storing $a_0 \approx 10^C$ (ex: $C = 100$). Consider any targe large number $A$. We can assign it a very tight lower bound via:

1. Find the max index $K$ such that $g_K(C) \le A$. 
2. Find the max coefficient $a_K$ such that $g_K^{a_K}(C) \le A$.
3. For each index $i$ from $K-1$ down to 1:
   - Let $F(x)$ represent the higher operations already assigned. 
   - Find max $a_i$ such that $F( g_i^{a_i}(C) ) \le A$.
   - Update $F(x) \leftarrow F(g_i^{a_i}(x))$
4. Find max base $a_0$ such that $F( a_0 ) \le A$.

It turns out that this algorith restricts us to coefficients:
1. $a_0 \in [C, 10^C)$ (Base must be reasonably large)
2. $a_i \in [0, C - 1)$ for all $i \ge 1$ (Coefficients must be reasonably small)

Directly thanks to this construction, all values produced this way will be guaranteed to have the lexicolization property. We directly chose the largest possible values for $K, a_K, a_{k-1}, \dots, a_0$ (each conditional on previous choices) therefore, if another `Knuth10` is lexicographically bigger, it must also be numerically bigger.

We can apply a similar algorithm to assign a canonical upper bound.

## Mathematical Harmony: Why the Greedy Algorithm is Perfect
### Proof for $a_i \le C - 3$
When we choose $a_i$, we maximize it such that $F( g_i^{a_i}(C) ) \le A$.
By the definition of the greedy algorithm from the *previous* step, we know we maximized $a_{i+1}$. That means adding one more application of $g_{i+1}$ would have strictly exceeded $A$.
Mathematically:
   $$ F( g_{i+1}(C) ) > A $$

Combining these gives:
   $$ F( g_i^{a_i}(C) ) \le A < F( g_{i+1}(C) ) $$
Since $F$ is strictly increasing, this strictly requires:
   $$ g_i^{a_i}(C) < g_{i+1}(C) $$

By the definition of the hierarchy, $g_{i+1}(C) = g_i^C(1) = g_i^{C-1}(10) \le g_i^{C-1}(C)$.
Substituting this in, the greedy algorithm guarantees:
   $$ g_i^{a_i}(C) < g_i^{C-1}(C) $$

**Thus $a_i < C - 1$.**

### Proof for $a_0 \in [C, 10^C)$
In the final step, we find max $a_0$ such that $F(a_0) \le A$. We know from the previous step that $F(C) \le A$, therefor $a_0 \ge C$.

By the same greedy logic from the $a_1$ step, we know that adding one more $g_1$ would exceed $A$. So $F( g_1(C) ) > A$. Since $g_1(C) = 10^C$ and $F$ is strictly increasing, $a_0 < 10^C$.

**Therefore, $C \le a_0 < 10^C$.**

## Conclusion
The greedy bounding algorithm flawlessly and natively constructs a bounding grid that strictly obeys the limits necessary for fast lexicographical ordering. 

Because `BigInterval` operates purely on this grid, arithmetic operations simply produce values that are greedily bounded back onto the grid, ensuring that all subsequent interval comparisons remain perfectly rigorous, fast, and immune to precision loss.

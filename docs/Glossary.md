# **GLOSSARY**

### **Algebraic Structure**:

* A collection of things together with a set of operations and rules defined
  on it, used to describe relationships between elements. Hornet's combinator
  functions form algebraic structures — in particular two [Monoids](#Monoid)
  and a [Distributive Lattice](#Distributive-Lattice).

### **Backtracking**:

* A technique employed in search and [Logic Programming](#Logic-Programming)
  to explore different possible outcomes. If a path does not lead to a
  solution, the program backtracks and tries an alternative. Backtracking can
  also generate an exhaustive list of solutions for a query.

### **Branch Pruning with the Cut**:

* In [Logic Programming](#Logic-Programming), *cut* (written *!* in Prolog) is
  an operator that succeeds once and then prevents backtracking beyond the
  point where it was invoked, effectively pruning branches in a search tree.

### **Choice Point**:

* In [Logic Programming](#Logic-Programming), a point where multiple
  alternatives are available. The program explores each in turn until a
  solution is found or all possibilities are exhausted.

### **Combinators**:

* Higher-order functions with no free variables that produce new functions as
  output. In Hornet, combinators are used to create and compose logical
  [Goals](#Goal).

### **Continuation**:

* A representation of the future of a computation, used to manage the flow of
  [Resolution](#Resolution) and [Backtracking](#Backtracking). In Hornet,
  there are at any point three possible futures: one in which the current
  [Goal](#Goal) succeeds, one in which it fails, and one in which it succeeds
  once and then curtails [Backtracking](#Backtracking) at the previous
  [Choice Point](#Choice-Point).

### **Continuation Monad**:

* A [Monad](#Monad) that encapsulates computations with
  [Continuations](#Continuation). Hornet employs the *Triple-Barrelled
  Continuation Monad* to manage [Resolution](#Resolution),
  [Backtracking](#Backtracking), and [Branch Pruning with the
  Cut](#Branch-Pruning-with-the-Cut).

### **Database**:

* A collection of [Horn Clauses](#Horn-Clauses) — facts and rules — that
  constitutes the knowledge base against which [Goals](#Goal) are
  [resolved](#Resolution). In Hornet, a `Database` is the central structure
  to which clauses are added and from which queries are run.

### **Distributive Lattice**:

* A mathematical structure where two binary operations — *meet* (infimum) and
  *join* (supremum) — satisfy certain distributive properties. The combinators
  `then` and `choice`, together with their respective identity elements `unit`
  and `fail`, form a Distributive Lattice.

### **Goal**:

* In [Logic Programming](#Logic-Programming), a resolvable logical statement
  or query. Goals define the tasks to be accomplished during
  [Resolution](#Resolution).

### **Horn Clauses**:
* A logical formula whose head and body consist entirely of positive (unnegated)
  atomic literals. The body is a conjunction of zero or more literals; the head
  holds at most one. There are three forms:

  *Fact*: a clause with a non-empty head and an empty body `(B)`. Asserts that `B` is
    unconditionally true. In Hornet: `db.tell(B)`.

  *Rule*: a clause with a non-empty head and a non-empty body `(A₁ ∧ … ∧ Aₙ → B)`.
    Asserts that `B` holds whenever all of `A₁ … Aₙ` hold. In Hornet:
    `db.tell(B.when(A₁, …, Aₙ))`.

  *Query* (or goal clause): a clause with an empty head and a non-empty body
    `(A₁ ∧ … ∧ Aₙ → ⊥)`. Asks whether `A₁ ∧ … ∧ Aₙ` can be derived. In Hornet:
    `db.ask(A₁, …, Aₙ)`.

  Horn clauses are the basis of [Logic Programming](#Logic-Programming). In Hornet,
  terms constructed with `.when()` are Horn rules, and `resolve()` interprets them
  via unification and backtracking.

### **Indicator**:

* A `(name, arity)` pair that uniquely identifies a [predicate](#Predicate).
  For example, a predicate `parent/2` has indicator `("parent", 2)`.

### **Logic Programming**:

* A programming paradigm in which computation is described via logic-based
  rules and statements. It relies on formal deductive reasoning to derive
  conclusions.

### **Logical Variables**:

* Variables that are automatically bound to values or other variables in the
  [Substitution Environment](#Substitution-Environment) during
  [Resolution](#Resolution). Like mathematical variables, they represent a
  fixed value and cannot be reassigned.

### **Monad**:

* A concept from Category Theory and a design pattern in Functional
  Programming, used to manage side effects and computations in a structured
  way. Hornet uses the *Triple-Barrelled Continuation Monad* to manage logical
  computations.

### **Monoid**:

* A mathematical structure consisting of a set, an associative binary
  operation, and an identity element. In Hornet, `then` and `unit` form a
  Monoid, as do `choice` and `fail`.

### **Negation as Failure**:

* A technique in [Logic Programming](#Logic-Programming) where the absence of
  a proof for a statement is treated as evidence of its negation.

### **Predicate**:

* A named relation of fixed arity defined by one or more [Horn
  Clauses](#Horn-Clauses) in the [Database](#Database). A predicate succeeds
  or fails when called with concrete arguments during
  [Resolution](#Resolution).

### **Resolution**:

* The fundamental process in [Logic Programming](#Logic-Programming) by which
  new facts or conclusions are derived from existing ones via logical rules and
  inference.

### **Substitution Environment**:

* A data structure mapping [Logical Variables](#Logical-Variables) to values
  — their *bindings* — constructed and maintained during
  [Resolution](#Resolution).

### **Tail Call Elimination**:

* A technique to optimize deeply chained function calls by avoiding the
  accumulation of stack frames.

### **Thunking**:

* Delaying a function's execution until its result is needed, typically by
  wrapping it in a parameter-less function (a *thunk*) that can be passed
  around and called at a later point. Hornet uses thunking to implement
  [Tail Call Elimination](#Tail-Call-Elimination).

### **Trailing**:

* The process of tracking bound [Logical Variables](#Logical-Variables).

### **Trampolining**:

* A technique for executing deeply chained function calls without consuming
  additional stack space, by converting them into a loop. Hornet uses this to
  implement [Tail Call Elimination](#Tail-Call-Elimination) in Python, which
  does not support it natively.

### **Unification**:

* The process of finding [substitutions](#Substitution-Environment) for
  [Logical Variables](#Logical-Variables) such that two terms become equal —
  the fundamental operation of [Logic Programming](#Logic-Programming).

### **Wildcard**:

* An anonymous [Logical Variable](#Logical-Variables), written `_`, that
  matches any term without creating a binding in the [Substitution
  Environment](#Substitution-Environment). Each occurrence of `_` is
  independent — no two wildcards are ever unified with each other.

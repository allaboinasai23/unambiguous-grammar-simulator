# Academic Project Report: Unambiguous Grammar Construction Simulator
**Course:** Formal Languages and Automata (FLA) / Theory of Computation  
**Project Title:** Unambiguous Grammar Construction Simulator  
**Domain:** Compiler Design, Formal Language Theory, Context-Free Grammars  

---

## Abstract
Context-Free Grammars (CFGs) are the foundational mathematical model utilized in compiler syntax analysis to formally define the syntax of programming languages. However, naive CFGs often suffer from grammatical ambiguity&mdash;a condition where a single terminal string yields multiple distinct parse trees and conflicting leftmost derivations. In computer systems, ambiguity is fatal because a compiler cannot deterministically generate target machine instructions without an unambiguous syntactic interpretation.

This project presents the design and implementation of an interactive, web-based academic simulator titled **“Unambiguous Grammar Construction Simulator.”** The application demonstrates the mathematical transition from an ambiguous arithmetic grammar ($G_1$) to a canonical, precedence-stratified unambiguous grammar ($G_2$). It features a recursive-descent parser, an exhaustive chart parser for ambiguity discovery, a dynamic SVG hierarchical parse tree layout engine, a step-by-step playback stepper, and a side-by-side comparative analysis workspace.

---

## 1. Introduction and Objectives

### 1.1 Background
In the Chomsky Hierarchy, Context-Free Grammars (Type-2) generate Context-Free Languages (CFLs). When a compiler parses a program, it constructs a concrete parse tree based on the language's grammar rules. If a grammar allows two or more structurally different parse trees for the same input string, the grammar is **ambiguous**.

Consider the arithmetic statement:
$$\text{result} = 2 + 3 \times 4$$
If addition is evaluated first, the result is $(2 + 3) \times 4 = 20$. If multiplication is evaluated first, the result is $2 + (3 \times 4) = 14$. If the underlying grammar is ambiguous, the compiler cannot guarantee mathematical correctness.

### 1.2 Project Objectives
1. **Visualizing Ambiguity:** Provide an intuitive platform where students can see how an ambiguous grammar allows both addition-first and multiplication-first parse trees for the benchmark string $\text{id} + \text{id} * \text{id}$.
2. **Demonstrating Disambiguation:** Illustrate the classical stratification technique that separates expressions ($E$), terms ($T$), and factors ($F$) to enforce mathematical operator precedence ($* > +$).
3. **Step-by-Step Introspection:** Enable students to step forward and backward through the parsing process, inspecting lookahead tokens, parser stack states, and sentential forms.
4. **Interactive Comparison:** Provide a side-by-side mode that directly contrasts both grammars on identical inputs.

---

## 2. Theoretical Foundations

### 2.1 Formal Definition of a Context-Free Grammar
A Context-Free Grammar $G$ is formally defined as a 4-tuple:
$$G = (V, \Sigma, R, S)$$
Where:
- $V$ is a finite set of **non-terminal variables** (syntactic categories).
- $\Sigma$ is a finite set of **terminal symbols** disjoint from $V$ ($V \cap \Sigma = \emptyset$), forming the alphabet of the language.
- $R$ is a finite relation $R \subseteq V \times (V \cup \Sigma)^*$, termed the set of **production rules**, denoted $A \to \alpha$.
- $S \in V$ is the distinguished **start symbol**.

### 2.2 Derivations and Parse Trees
- A **sentential form** is any string $\alpha \in (V \cup \Sigma)^*$ such that $S \Rightarrow^* \alpha$.
- A **Leftmost Derivation (LMD)** is a derivation sequence where the leftmost non-terminal variable is replaced at each step:
  $$S \Rightarrow_{lm} \alpha_1 \Rightarrow_{lm} \alpha_2 \Rightarrow_{lm} \dots \Rightarrow_{lm} w \quad (w \in \Sigma^*)$$
- A **Rightmost Derivation (RMD)** replaces the rightmost non-terminal variable at each step.
- A **Parse Tree** is an ordered, rooted tree representing the hierarchical syntactic structure of a derivation. The root is labeled $S$, interior nodes are labeled with variables in $V$, and leaves are labeled with terminals in $\Sigma \cup \{\epsilon\}$.

### 2.3 Definition of Grammatical Ambiguity
> **Definition:** A context-free grammar $G$ is called **ambiguous** if there exists at least one string $w \in L(G)$ that possesses two or more distinct parse trees (or equivalently, two or more distinct leftmost derivations). Otherwise, $G$ is **unambiguous**.

---

## 3. Mathematical Analysis of the Evaluated Grammars

### 3.1 Ambiguous Grammar ($G_1$)
$$G_1 = (\{E\}, \{+, *, (, ), \text{id}\}, R_1, E)$$
**Production Rules $R_1$:**
$$E \to E + E \mid E * E \mid (E) \mid \text{id}$$

#### Proof of Ambiguity for String $w = \text{id} + \text{id} * \text{id}$:
We demonstrate two distinct leftmost derivations for $w$:

**Derivation 1 (Addition at Root &mdash; Multiplication Evaluated First):**
$$E \Rightarrow_{lm} E + E \Rightarrow_{lm} \text{id} + E \Rightarrow_{lm} \text{id} + E * E \Rightarrow_{lm} \text{id} + \text{id} * E \Rightarrow_{lm} \text{id} + \text{id} * \text{id}$$
*Parse Tree 1 Semantic Grouping:* $\text{id} + (\text{id} * \text{id})$

**Derivation 2 (Multiplication at Root &mdash; Addition Evaluated First):**
$$E \Rightarrow_{lm} E * E \Rightarrow_{lm} E + E * E \Rightarrow_{lm} \text{id} + E * E \Rightarrow_{lm} \text{id} + \text{id} * E \Rightarrow_{lm} \text{id} + \text{id} * \text{id}$$
*Parse Tree 2 Semantic Grouping:* $(\text{id} + \text{id}) * \text{id}$

Since there exist two distinct leftmost derivations for the same string $w$, **$G_1$ is ambiguous by definition.** $\blacksquare$

---

### 3.2 Unambiguous Grammar ($G_2$)
$$G_2 = (\{E, T, F\}, \{+, *, (, ), \text{id}\}, R_2, E)$$
**Production Rules $R_2$:**
$$\begin{aligned}
E &\to E + T \mid T \\
T &\to T * F \mid F \\
F &\to (E) \mid \text{id}
\end{aligned}$$

#### Disambiguation Mechanics:
1. **Precedence Hierarchy (Stratification):**
   - $E$ represents Expressions (lowest precedence tier, handles addition $+$).
   - $T$ represents Terms (intermediate tier, handles multiplication $*$).
   - $F$ represents Factors (highest tier, handles atomic identifiers $\text{id}$ and parentheses $(E)$).
   Because an operation cannot be reduced until its operands are formed, operators in lower syntactic tiers ($T$ and $F$) are reduced before operators in higher tiers ($E$). Multiplication is thus guaranteed to bind tighter than addition.
2. **Associativity Enforcement:**
   - The production $E \to E + T$ is **left-recursive**, ensuring that $\text{id} + \text{id} + \text{id}$ is parsed left-to-right as $((\text{id} + \text{id}) + \text{id})$.
   - The production $T \to T * F$ is **left-recursive**, ensuring left-associativity for multiplication.

#### Uniqueness for String $w = \text{id} + \text{id} * \text{id}$:
Only ONE leftmost derivation exists under $G_2$:
$$\begin{aligned}
E &\Rightarrow_{lm} E + T \\
  &\Rightarrow_{lm} T + T \\
  &\Rightarrow_{lm} F + T \\
  &\Rightarrow_{lm} \text{id} + T \\
  &\Rightarrow_{lm} \text{id} + T * F \\
  &\Rightarrow_{lm} \text{id} + F * F \\
  &\Rightarrow_{lm} \text{id} + \text{id} * F \\
  &\Rightarrow_{lm} \text{id} + \text{id} * \text{id}
\end{aligned}$$
*Parse Tree Semantic Grouping:* $\text{id} + (\text{id} * \text{id})$ (Strictly Unique). $\blacksquare$

---

## 4. System Architecture & Implementation

```mermaid
graph TD
    Client[Web Browser / Interactive UI] -->|HTTP / JSON API| Flask[Flask Backend (app.py)]
    Flask --> Lexer[Tokenizer / Lexical Analysis]
    Lexer -->|Token Stream| Dispatcher{Grammar Selector}
    Dispatcher -->|Unambiguous G2| RDParser[Recursive-Descent Parser Engine]
    Dispatcher -->|Ambiguous G1| ChartParser[Dynamic Chart Multi-Tree Generator]
    RDParser --> TreeGen[Parse Tree & Derivations]
    ChartParser --> TreeGen
    TreeGen -->|JSON AST & Steps| Client
    Client --> SVGLayout[Interactive SVG Tree Layout Engine]
    Client --> Stepper[Simulation Stepper & Controls]
```

### 4.1 Module Breakdown
1. **`parser.py`**:
   - `tokenize(expression)`: Lexer supporting `id`, standard variables, integers, and operators.
   - `UnambiguousParser`: Recursive-descent parser for $G_2$ constructing left-associative ASTs while logging lookahead, stack states, and educational comments.
   - `AmbiguousParser`: Memoized dynamic-programming chart parser that spans sub-slices of tokens to discover and return **all structurally unique parse trees** for $G_1$.
   - `generate_leftmost_derivation()` & `generate_rightmost_derivation()`: Traverses generated parse trees to reconstruct full sentential form sequences.
2. **`app.py`**:
   - Web application controller serving HTML views and JSON REST API endpoints (`/api/simulate`, `/api/compare`, `/api/presets`).
3. **`static/js/simulator.js`**:
   - `TreeLayoutEngine`: Hierarchical layout algorithm assigning 2D coordinates $(x, y)$ using subtree bounding boxes and parent-centering.
   - `TreeSVGRenderer`: Interactive SVG renderer supporting pan, zoom, terminal/nonterminal styling, node tooltips, and vector export.
   - `SimulationController`: Playback engine managing step indices, progress bars, and execution speeds.

---

## 5. Experimental Testing & Results

The system was verified against both standard benchmarks and syntax error edge cases:

| Input String | Grammar Tested | Output & Trees Observed | Theoretical Evaluation |
| :--- | :--- | :--- | :--- |
| `id + id * id` | Ambiguous ($G_1$) | **2 Parse Trees** (`id+(id*id)` and `(id+id)*id`) | Proves ambiguity; demonstrates precedence conflict. |
| `id + id * id` | Unambiguous ($G_2$) | **1 Parse Tree** (`id+(id*id)`) | Successfully disambiguated; multiplication prioritized. |
| `id * id + id` | Unambiguous ($G_2$) | **1 Parse Tree** (`(id*id)+id`) | Verifies linear order independence for precedence. |
| `(id + id) * id` | Unambiguous ($G_2$) | **1 Parse Tree** (`((id+id)*id)`) | Verifies parenthesis overriding mechanism in $F \to (E)$. |
| `id + id + id` | Unambiguous ($G_2$) | **1 Parse Tree** (`((id+id)+id)`) | Verifies left-associativity enforcement. |
| `id + * id` | Both | **Rejected** with syntax error | Correctly identifies consecutive operators & missing operand. |
| `(id + id` | Both | **Rejected** with syntax error | Correctly flags unmatched opening parenthesis. |
| `id + id)` | Both | **Rejected** with syntax error | Correctly flags unexpected trailing closing parenthesis. |

---

## 6. Conclusion & Pedagogical Value

The **Unambiguous Grammar Construction Simulator** successfully provides a robust, scientifically accurate, and interactive medium for mastering Formal Languages and Automata concepts. By combining formal parsing algorithms with modern visual layout techniques, the simulator bridges the gap between abstract textbook mathematics and concrete compiler design implementation.

---
*Submitted for Formal Languages and Automata (FLA) Academic Evaluation.*

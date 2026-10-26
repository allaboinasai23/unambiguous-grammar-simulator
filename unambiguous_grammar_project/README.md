# Unambiguous Grammar Construction Simulator
### Formal Languages and Automata (FLA) Academic Web Application

An interactive, educational simulator that illustrates the formal principles of **Context-Free Grammars (CFGs)**, **Grammatical Ambiguity**, and **Disambiguation through Precedence Stratification**. Built with Python, Flask, HTML5, CSS3, and JavaScript with interactive SVG parse tree visualization.

---

## 1. Project Overview

In Formal Language Theory and Compiler Design, an **ambiguous grammar** permits more than one distinct leftmost derivation (or parse tree) for a single string in its language. In compilers, ambiguity is unacceptable because a single source statement could produce multiple conflicting machine code sequences with differing runtime semantics.

This application provides:
1. **Interactive Step-by-Step Simulation**: Observe recursive-descent parsing with lookahead tokens, parser stack, and leftmost/rightmost derivation sequences.
2. **Dynamic Parse Tree Generation**: SVG hierarchical parse tree renderer with pan, zoom, node tooltips, and image export.
3. **Ambiguity Demonstration**: Generates and visualizes **both valid parse trees** for expressions like `id + id * id` under the ambiguous grammar.
4. **Side-by-Side Grammar Comparison**: Directly contrasts ambiguous and unambiguous grammars on the same input string.
5. **Syntax Error Diagnostics**: Pinpoints missing operands, unmatched parentheses, and unexpected characters with actionable suggestions.

---

## 2. Formal Grammar Specifications

### A. The Ambiguous Grammar ($G_1$)
$$G_1 = (\{E\}, \{+, *, (, ), \text{id}\}, R_1, E)$$

**Production Rules:**
```text
E -> E + E | E * E | (E) | id
```
* **Why it is Ambiguous:** $G_1$ defines both addition (`+`) and multiplication (`*`) at the same non-terminal level $E$. It lacks operator precedence and associativity rules.
* **Result for `id + id * id`:**
  * **Parse Tree 1:** `id + (id * id)` &mdash; Addition at the root, multiplication grouped lower (standard).
  * **Parse Tree 2:** `(id + id) * id` &mdash; Multiplication at the root, addition grouped lower (non-standard).

---

### B. The Unambiguous Grammar ($G_2$)
$$G_2 = (\{E, T, F\}, \{+, *, (, ), \text{id}\}, R_2, E)$$

**Production Rules:**
```text
E -> E + T | T          (Level 1: Addition & Lowest Precedence)
T -> T * F | F          (Level 2: Multiplication & Higher Precedence)
F -> (E) | id           (Level 3: Atomic Operands & Highest Precedence)
```
* **Why it is Unambiguous:**
  1. **Precedence Stratification:** Operations with higher precedence appear deeper in the tree structure ($T \to T * F$) so they are reduced prior to lower precedence operations ($E \to E + T$).
  2. **Associativity via Left Recursion:** The productions $E \to E + T$ and $T \to T * F$ enforce left-to-right grouping, e.g. `(id + id) + id`.
* **Result for `id + id * id`:** Exactly **ONE** unique parse tree `id + (id * id)`.

---

## 3. Project Structure

```text
unambiguous_grammar_project/
├── app.py                     # Flask web server, API routes, and preset definitions
├── parser.py                  # Lexer, recursive-descent parser (G2), chart parser (G1), derivations
├── requirements.txt           # Python package dependencies (Flask)
├── README.md                  # System guide and documentation
├── PROJECT_REPORT.md          # Comprehensive academic project report
├── templates/
│   ├── index.html             # Academic dashboard and FLA theory guide
│   ├── simulator.html         # Interactive step-by-step simulator & SVG tree viewer
│   └── comparison.html        # Side-by-side dual grammar comparison tool
└── static/
    ├── css/
    │   └── style.css          # Modern academic theme, design tokens, responsive layout
    └── js/
        └── simulator.js       # Dynamic SVG tree layout engine & playback stepper
```

---

## 4. Installation & Local Setup

### Prerequisites
* **Python 3.9+** (Tested on Python 3.14)
* **pip** package manager

### Steps to Run

1. **Navigate to the project directory:**
   ```powershell
   cd "C:\Users\allab\.gemini\antigravity-ide\scratch\unambiguous_grammar_project"
   ```

2. **Install dependencies:**
   ```powershell
   python -m pip install -r requirements.txt
   ```

3. **Start the Flask development server:**
   ```powershell
   python app.py
   ```

4. **Open in your browser:**
   ```text
   http://127.0.0.1:5000
   ```

---

## 5. Verification Test Cases

| Expression | Ambiguous $G_1$ Result | Unambiguous $G_2$ Result | Semantic Meaning / Error |
| :--- | :--- | :--- | :--- |
| `id + id * id` | **2 Parse Trees** | **1 Unique Tree** | $G_1$ demonstrates ambiguity: `id + (id * id)` vs `(id + id) * id`. $G_2$ enforces `id + (id * id)`. |
| `id * id + id` | **2 Parse Trees** | **1 Unique Tree** | Multiplications binds tighter regardless of input position: `(id * id) + id`. |
| `(id + id) * id` | 1 Parse Tree | 1 Unique Tree | Parentheses in $F \to (E)$ elevate addition to highest priority: `((id + id) * id)`. |
| `id + id + id` | **2 Parse Trees** | **1 Unique Tree** | Left-associativity: $G_2$ produces `((id + id) + id)` via $E \to E + T$. |
| `id + id` | 1 Parse Tree | 1 Unique Tree | Minimal valid addition expression. |
| `id + * id` | **Rejected (Syntax Error)** | **Rejected (Syntax Error)** | Missing operand between consecutive operators `+` and `*`. |
| `(id + id` | **Rejected (Syntax Error)** | **Rejected (Syntax Error)** | Unmatched parenthesis: Missing closing `)`. |
| `id + id)` | **Rejected (Syntax Error)** | **Rejected (Syntax Error)** | Unmatched closing parenthesis `)`. |

---

## 6. Academic Credits
Developed for **Formal Languages and Automata (FLA)** academic curriculum. Designed for classroom demonstrations, laboratory assignments, and compiler design coursework.

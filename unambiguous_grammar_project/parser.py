"""
FLA Project: Unambiguous Grammar Construction Simulator
Module: parser.py
Description:
    Contains the Lexer, Recursive-Descent Parser for the Unambiguous Grammar,
    Chart/Memoized Parser for the Ambiguous Grammar (to find all parse trees),
    Derivation step generators (Leftmost & Rightmost), and detailed syntax error handling.
"""

from typing import List, Dict, Any, Optional, Tuple


class LexicalError(Exception):
    """Exception raised when an invalid token or character is encountered."""
    def __init__(self, message: str, position: int, character: str = ""):
        super().__init__(message)
        self.message = message
        self.position = position
        self.character = character


class ParseError(Exception):
    """Exception raised when an expression violates grammar syntax."""
    def __init__(self, message: str, position: int = 0, token: str = "", suggestion: str = ""):
        super().__init__(message)
        self.message = message
        self.position = position
        self.token = token
        self.suggestion = suggestion


class Token:
    """Represents a lexical token."""
    def __init__(self, type_: str, value: str, position: int):
        self.type = type_      # 'ID', 'PLUS', 'STAR', 'LPAREN', 'RPAREN', 'EOF'
        self.value = value    # e.g., 'id', '+', '*', '(', ')'
        self.position = position

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "value": self.value,
            "position": self.position
        }

    def __repr__(self) -> str:
        return f"Token({self.type}, '{self.value}', pos={self.position})"


def tokenize(expression: str) -> List[Token]:
    """
    Tokenizes the mathematical input expression into tokens:
    ID, PLUS (+), STAR (*), LPAREN ((), RPAREN ()), and EOF.
    Supports 'id', single letters (a, b, x, etc.), or integer numbers as identifiers.
    """
    tokens: List[Token] = []
    i = 0
    n = len(expression)

    while i < n:
        ch = expression[i]

        if ch.isspace():
            i += 1
            continue

        if ch == '+':
            tokens.append(Token("PLUS", "+", i))
            i += 1
        elif ch == '*':
            tokens.append(Token("STAR", "*", i))
            i += 1
        elif ch == '(':
            tokens.append(Token("LPAREN", "(", i))
            i += 1
        elif ch == ')':
            tokens.append(Token("RPAREN", ")", i))
            i += 1
        elif ch.isalpha() or ch == '_':
            # Identifier token (e.g. 'id' or variable names 'a', 'x', etc.)
            start = i
            while i < n and (expression[i].isalnum() or expression[i] == '_'):
                i += 1
            val = expression[start:i]
            tokens.append(Token("ID", val, start))
        elif ch.isdigit():
            # Numeric constant also treated as operand (id)
            start = i
            while i < n and expression[i].isdigit():
                i += 1
            val = expression[start:i]
            tokens.append(Token("ID", val, start))
        else:
            raise LexicalError(
                f"Invalid character '{ch}' at position {i}. Valid characters are 'id', '+', '*', '(', and ')'.",
                position=i,
                character=ch
            )

    tokens.append(Token("EOF", "$", n))
    return tokens


class ParseNode:
    """Represents a node in the Parse Tree."""
    _counter = 0

    def __init__(self, label: str, is_terminal: bool = False, rule: Optional[str] = None):
        ParseNode._counter += 1
        self.id = f"node_{ParseNode._counter}"
        self.label = label
        self.is_terminal = is_terminal
        self.rule = rule
        self.children: List['ParseNode'] = []

    def add_child(self, child: 'ParseNode') -> 'ParseNode':
        self.children.append(child)
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "is_terminal": self.is_terminal,
            "rule": self.rule,
            "children": [child.to_dict() for child in self.children]
        }

    def get_leaves(self) -> List[str]:
        if self.is_terminal or not self.children:
            return [self.label]
        res = []
        for c in self.children:
            res.extend(c.get_leaves())
        return res

    def get_semantic_grouping(self) -> str:
        """Returns fully parenthesized string indicating operator precedence grouping."""
        if self.is_terminal:
            return self.label
        if not self.children:
            return self.label
        if len(self.children) == 1:
            return self.children[0].get_semantic_grouping()
        if len(self.children) == 3:
            left = self.children[0].get_semantic_grouping()
            op = self.children[1].get_semantic_grouping()
            right = self.children[2].get_semantic_grouping()
            if op in ('+', '*'):
                return f"({left} {op} {right})"
            if self.children[0].label == '(':
                return f"({self.children[1].get_semantic_grouping()})"
        return " ".join(c.get_semantic_grouping() for c in self.children)


def generate_leftmost_derivation(root: ParseNode) -> List[Dict[str, Any]]:
    """
    Generates step-by-step Leftmost Derivation (LMD) sequence from a ParseTree root.
    Returns list of derivation states showing:
      - sentential_form: List of symbols (string)
      - production: Production rule used in this step
      - replaced_index: Index of the non-terminal symbol replaced
      - explanation: Pedagogical explanation
    """
    steps: List[Dict[str, Any]] = []

    # Current sentential form represented as a list of ParseNode references
    current_nodes: List[ParseNode] = [root]
    
    # Initial step: Start symbol S = E
    steps.append({
        "step_num": 1,
        "sentential_form": root.label,
        "rule_applied": "Initial Start Symbol",
        "symbol_replaced": "",
        "explanation": f"Begin derivation with the grammar start symbol '{root.label}'."
    })

    step_counter = 2

    while True:
        # Find the leftmost non-terminal
        target_idx = -1
        for idx, node in enumerate(current_nodes):
            if not node.is_terminal and node.children:
                target_idx = idx
                break

        if target_idx == -1:
            # All symbols are terminals; derivation complete
            break

        target_node = current_nodes[target_idx]
        production = target_node.rule or f"{target_node.label} -> {' '.join(c.label for c in target_node.children)}"

        # Replace the target non-terminal with its children
        new_nodes = current_nodes[:target_idx] + target_node.children + current_nodes[target_idx + 1:]
        current_nodes = new_nodes

        sentential_str = " ".join(node.label for node in current_nodes)
        steps.append({
            "step_num": step_counter,
            "sentential_form": sentential_str,
            "rule_applied": production,
            "symbol_replaced": target_node.label,
            "explanation": f"Replace leftmost non-terminal '{target_node.label}' using production: {production}"
        })
        step_counter += 1

    return steps


def generate_rightmost_derivation(root: ParseNode) -> List[Dict[str, Any]]:
    """
    Generates step-by-step Rightmost Derivation (RMD) sequence from a ParseTree root.
    """
    steps: List[Dict[str, Any]] = []
    current_nodes: List[ParseNode] = [root]

    steps.append({
        "step_num": 1,
        "sentential_form": root.label,
        "rule_applied": "Initial Start Symbol",
        "symbol_replaced": "",
        "explanation": f"Begin rightmost derivation with start symbol '{root.label}'."
    })

    step_counter = 2

    while True:
        # Find the rightmost non-terminal
        target_idx = -1
        for idx in range(len(current_nodes) - 1, -1, -1):
            node = current_nodes[idx]
            if not node.is_terminal and node.children:
                target_idx = idx
                break

        if target_idx == -1:
            break

        target_node = current_nodes[target_idx]
        production = target_node.rule or f"{target_node.label} -> {' '.join(c.label for c in target_node.children)}"

        new_nodes = current_nodes[:target_idx] + target_node.children + current_nodes[target_idx + 1:]
        current_nodes = new_nodes

        sentential_str = " ".join(node.label for node in current_nodes)
        steps.append({
            "step_num": step_counter,
            "sentential_form": sentential_str,
            "rule_applied": production,
            "symbol_replaced": target_node.label,
            "explanation": f"Replace rightmost non-terminal '{target_node.label}' using production: {production}"
        })
        step_counter += 1

    return steps


# ==============================================================================
# UNAMBIGUOUS GRAMMAR PARSER (Recursive Descent)
# Grammar G_2:
#   E -> E + T | T
#   T -> T * F | F
#   F -> (E) | id
#
# Eliminates left recursion for standard predictive / recursive-descent:
#   E  -> T E'
#   E' -> + T E' | epsilon
#   T  -> F T'
#   T' -> * F T' | epsilon
#   F  -> (E) | id
#
# Reconstructs the canonical Left-Associative Academic Parse Tree:
#   For T1 + T2:
#        E
#      / | \
#     E  +  T
#     |     |
#     T     ...
# ==============================================================================

class UnambiguousParser:
    """
    Recursive-descent parser for the unambiguous expression grammar.
    Tracks step-by-step actions, parser state, and builds the canonical parse tree.
    """
    def __init__(self, tokens: List[Token], original_expression: str):
        self.tokens = tokens
        self.expr = original_expression
        self.pos = 0
        self.steps: List[Dict[str, Any]] = []
        self.step_id = 0

    def current_token(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def _record_step(self, action: str, rule: str, explanation: str, stack_view: List[str]):
        self.step_id += 1
        rem_tokens = [t.value for t in self.tokens[self.pos:] if t.type != "EOF"]
        self.steps.append({
            "step_num": self.step_id,
            "action": action,
            "rule": rule,
            "lookahead": self.current_token().value,
            "remaining_input": " ".join(rem_tokens) if rem_tokens else "EOF",
            "stack": list(stack_view),
            "explanation": explanation
        })

    def match(self, expected_type: str, stack_view: List[str]) -> Token:
        token = self.current_token()
        if token.type == expected_type:
            self._record_step(
                action=f"Match terminal '{token.value}'",
                rule="",
                explanation=f"Successfully matched terminal symbol '{token.value}' from input stream.",
                stack_view=stack_view
            )
            self.pos += 1
            return token
        
        # Friendly syntax error message generator
        if expected_type == "ID":
            raise ParseError(
                f"Expected operand (id) at position {token.position}, but found '{token.value}'.",
                position=token.position,
                token=token.value,
                suggestion="Check for consecutive operators (e.g. '+ *') or missing operand."
            )
        elif expected_type == "RPAREN":
            raise ParseError(
                f"Unmatched parenthesis: Expected closing ')' at position {token.position}, but found '{token.value}'.",
                position=token.position,
                token=token.value,
                suggestion="Make sure every open parenthesis '(' has a matching closing ')'."
            )
        else:
            raise ParseError(
                f"Syntax error at position {token.position}: Expected '{expected_type}', found '{token.value}'.",
                position=token.position,
                token=token.value
            )

    def parse(self) -> Tuple[ParseNode, List[Dict[str, Any]]]:
        if not self.tokens or (len(self.tokens) == 1 and self.tokens[0].type == "EOF"):
            raise ParseError("Empty expression. Please enter an expression like 'id + id * id'.", position=0)

        stack_view = ["E"]
        self._record_step(
            action="Start Parser",
            rule="Start Symbol: E",
            explanation="Initializing recursive-descent parser with start symbol E (lowest precedence tier: addition).",
            stack_view=stack_view
        )

        tree = self.parse_E(stack_view)

        # Check for remaining unconsumed tokens
        if self.current_token().type != "EOF":
            tok = self.current_token()
            if tok.type in ("ID", "LPAREN"):
                raise ParseError(
                    f"Missing operator before '{tok.value}' at position {tok.position}.",
                    position=tok.position,
                    token=tok.value,
                    suggestion="Add an operator like '+' or '*' between operands."
                )
            elif tok.type == "RPAREN":
                raise ParseError(
                    f"Unexpected closing parenthesis ')' at position {tok.position} without matching '('.",
                    position=tok.position,
                    token=tok.value,
                    suggestion="Remove the extra ')' or add a matching '('."
                )
            else:
                raise ParseError(
                    f"Unexpected trailing token '{tok.value}' at position {tok.position}.",
                    position=tok.position,
                    token=tok.value
                )

        self._record_step(
            action="Accept Input",
            rule="E -> ... (Valid Parse)",
            explanation="All tokens consumed successfully. Input string is valid according to the unambiguous grammar.",
            stack_view=[]
        )

        return tree, self.steps

    def parse_E(self, stack_view: List[str]) -> ParseNode:
        """
        Parses E -> E + T | T.
        Enforces left-associativity: T1 + T2 + T3 forms (((T1) + T2) + T3).
        """
        self._record_step(
            action="Enter parse_E()",
            rule="E -> T (+ T)*",
            explanation="Evaluating Level 1 Expression (E). Invoking parse_T() for terms (multiplication tier).",
            stack_view=stack_view
        )

        # Parse first term T
        first_t = self.parse_T(stack_view + ["T"])

        # Create base E node: E -> T
        current_e = ParseNode("E", is_terminal=False, rule="E -> T")
        current_e.add_child(first_t)

        while self.current_token().type == "PLUS":
            plus_tok = self.match("PLUS", stack_view + ["+"])
            plus_node = ParseNode(plus_tok.value, is_terminal=True)

            self._record_step(
                action="Apply Rule: E -> E + T",
                rule="E -> E + T",
                explanation="Addition operator '+' matched. Grouping left subtree into new E node to preserve left-to-right associativity.",
                stack_view=stack_view + ["T"]
            )

            next_t = self.parse_T(stack_view + ["T"])

            # Left-associative tree construction:
            # New E node with children: [old_E, '+', next_T]
            new_e = ParseNode("E", is_terminal=False, rule="E -> E + T")
            new_e.add_child(current_e)
            new_e.add_child(plus_node)
            new_e.add_child(next_t)
            current_e = new_e

        return current_e

    def parse_T(self, stack_view: List[str]) -> ParseNode:
        """
        Parses T -> T * F | F.
        Enforces left-associativity and higher precedence than addition: F1 * F2 * F3.
        """
        self._record_step(
            action="Enter parse_T()",
            rule="T -> F (* F)*",
            explanation="Evaluating Level 2 Term (T). Invoking parse_F() for factors (atomic / paren tier).",
            stack_view=stack_view
        )

        first_f = self.parse_F(stack_view + ["F"])

        current_t = ParseNode("T", is_terminal=False, rule="T -> F")
        current_t.add_child(first_f)

        while self.current_token().type == "STAR":
            star_tok = self.match("STAR", stack_view + ["*"])
            star_node = ParseNode(star_tok.value, is_terminal=True)

            self._record_step(
                action="Apply Rule: T -> T * F",
                rule="T -> T * F",
                explanation="Multiplication operator '*' matched. Grouping into term node T to enforce higher precedence over addition.",
                stack_view=stack_view + ["F"]
            )

            next_f = self.parse_F(stack_view + ["F"])

            new_t = ParseNode("T", is_terminal=False, rule="T -> T * F")
            new_t.add_child(current_t)
            new_t.add_child(star_node)
            new_t.add_child(next_f)
            current_t = new_t

        return current_t

    def parse_F(self, stack_view: List[str]) -> ParseNode:
        """
        Parses F -> (E) | id.
        Enforces atomic evaluation or parenthesized subexpressions.
        """
        tok = self.current_token()

        if tok.type == "ID":
            id_tok = self.match("ID", stack_view + [tok.value])
            id_node = ParseNode(id_tok.value, is_terminal=True)
            f_node = ParseNode("F", is_terminal=False, rule="F -> id")
            f_node.add_child(id_node)

            self._record_step(
                action="Apply Rule: F -> id",
                rule="F -> id",
                explanation=f"Parsed atomic operand identifier '{id_tok.value}'.",
                stack_view=stack_view
            )
            return f_node

        elif tok.type == "LPAREN":
            lparen_tok = self.match("LPAREN", stack_view + ["("])
            lparen_node = ParseNode("(", is_terminal=True)

            self._record_step(
                action="Apply Rule: F -> ( E )",
                rule="F -> ( E )",
                explanation="Parenthesized subexpression found. Temporarily resetting to highest precedence tier inside parentheses.",
                stack_view=stack_view + ["E"]
            )

            e_node = self.parse_E(stack_view + ["E"])

            rparen_tok = self.match("RPAREN", stack_view + [")"])
            rparen_node = ParseNode(")", is_terminal=True)

            f_node = ParseNode("F", is_terminal=False, rule="F -> ( E )")
            f_node.add_child(lparen_node)
            f_node.add_child(e_node)
            f_node.add_child(rparen_node)
            return f_node

        elif tok.type in ("PLUS", "STAR"):
            raise ParseError(
                f"Missing operand before operator '{tok.value}' at position {tok.position}.",
                position=tok.position,
                token=tok.value,
                suggestion="Every binary operator requires operands on both sides (e.g. 'id + id')."
            )
        elif tok.type == "EOF":
            raise ParseError(
                "Unexpected end of expression: Missing trailing operand.",
                position=tok.position,
                token="EOF",
                suggestion="Add an operand like 'id' after the last operator."
            )
        else:
            raise ParseError(
                f"Unexpected token '{tok.value}' at position {tok.position}.",
                position=tok.position,
                token=tok.value
            )


# ==============================================================================
# AMBIGUOUS GRAMMAR PARSER (Complete Multi-Tree Generator)
# Grammar G_1:
#   E -> E + E | E * E | (E) | id
#
# Because G_1 does not encode precedence or associativity, an expression like
# 'id + id * id' admits MULTIPLE distinct parse trees.
# We implement a chart / memoized recursive search that discovers ALL valid
# distinct parse trees under G_1.
# ==============================================================================

class AmbiguousParser:
    """
    Parses expressions under the ambiguous grammar G_1:
      E -> E + E | E * E | (E) | id
    Discovers all structurally distinct parse trees and records why ambiguity occurs.
    """
    def __init__(self, tokens: List[Token], original_expression: str):
        # Exclude the EOF token for the chart parser
        self.raw_tokens = [t for t in tokens if t.type != "EOF"]
        self.expr = original_expression
        self.memo: Dict[Tuple[int, int], List[ParseNode]] = {}

    def parse_all_trees(self) -> List[ParseNode]:
        if not self.raw_tokens:
            raise ParseError("Empty expression. Please enter an expression like 'id + id * id'.", position=0)

        # Quick validation of balanced parentheses before branch search
        balance = 0
        for t in self.raw_tokens:
            if t.type == "LPAREN":
                balance += 1
            elif t.type == "RPAREN":
                balance -= 1
                if balance < 0:
                    raise ParseError(
                        f"Unmatched closing parenthesis ')' at position {t.position}.",
                        position=t.position,
                        token=")"
                    )
        if balance > 0:
            raise ParseError(
                "Unmatched opening parenthesis '(': Missing closing ')'.",
                position=len(self.expr) - 1,
                token="("
            )

        trees = self._parse_span(0, len(self.raw_tokens))
        if not trees:
            raise ParseError(
                "Invalid syntax under ambiguous grammar E -> E + E | E * E | (E) | id.",
                position=0
            )

        # Remove duplicate tree representations if any
        unique_trees: List[ParseNode] = []
        seen_structures = set()

        for tree in trees:
            struct_repr = tree.get_semantic_grouping()
            if struct_repr not in seen_structures:
                seen_structures.add(struct_repr)
                unique_trees.append(tree)

        return unique_trees

    def _parse_span(self, start: int, end: int) -> List[ParseNode]:
        """
        Returns all valid ParseNodes for the token slice tokens[start:end].
        Uses dynamic programming (memoization).
        """
        key = (start, end)
        if key in self.memo:
            return self.memo[key]

        length = end - start
        if length <= 0:
            return []

        results: List[ParseNode] = []

        # 1. Base case: single token -> E -> id
        if length == 1:
            tok = self.raw_tokens[start]
            if tok.type == "ID":
                id_leaf = ParseNode(tok.value, is_terminal=True)
                e_node = ParseNode("E", is_terminal=False, rule="E -> id")
                e_node.add_child(id_leaf)
                results.append(e_node)
            self.memo[key] = results
            return results

        # 2. Parenthesized rule: E -> ( E )
        if self.raw_tokens[start].type == "LPAREN" and self.raw_tokens[end - 1].type == "RPAREN":
            # Check if outer parens enclose the entire substring
            inner_trees = self._parse_span(start + 1, end - 1)
            for inner in inner_trees:
                lparen = ParseNode("(", is_terminal=True)
                rparen = ParseNode(")", is_terminal=True)
                e_node = ParseNode("E", is_terminal=False, rule="E -> ( E )")
                e_node.add_child(lparen)
                e_node.add_child(inner)
                e_node.add_child(rparen)
                results.append(e_node)

        # 3. Binary operators: E -> E + E | E * E
        # Split at operator positions where parentheses balance is 0
        paren_depth = 0
        for mid in range(start, end):
            tok = self.raw_tokens[mid]
            if tok.type == "LPAREN":
                paren_depth += 1
            elif tok.type == "RPAREN":
                paren_depth -= 1
            elif paren_depth == 0 and tok.type in ("PLUS", "STAR"):
                op_val = tok.value
                op_rule = f"E -> E {op_val} E"

                left_subtrees = self._parse_span(start, mid)
                if not left_subtrees:
                    continue

                right_subtrees = self._parse_span(mid + 1, end)
                if not right_subtrees:
                    continue

                for left in left_subtrees:
                    for right in right_subtrees:
                        op_node = ParseNode(op_val, is_terminal=True)
                        e_node = ParseNode("E", is_terminal=False, rule=op_rule)
                        e_node.add_child(left)
                        e_node.add_child(op_node)
                        e_node.add_child(right)
                        results.append(e_node)

        self.memo[key] = results
        return results


# ==============================================================================
# UNIFIED SIMULATION AND COMPARISON API
# ==============================================================================

def simulate_unambiguous(expression: str) -> Dict[str, Any]:
    """
    Executes full simulation for the Unambiguous Grammar G_2:
      E -> E + T | T
      T -> T * F | F
      F -> (E) | id
    """
    try:
        tokens = tokenize(expression)
        parser = UnambiguousParser(tokens, expression)
        parse_tree, steps = parser.parse()

        lmd = generate_leftmost_derivation(parse_tree)
        rmd = generate_rightmost_derivation(parse_tree)
        grouping = parse_tree.get_semantic_grouping()

        return {
            "success": True,
            "grammar_type": "unambiguous",
            "grammar_name": "Unambiguous Grammar (G2)",
            "rules": [
                "E -> E + T | T",
                "T -> T * F | F",
                "F -> (E) | id"
            ],
            "expression": expression,
            "tokens": [t.to_dict() for t in tokens if t.type != "EOF"],
            "tree": parse_tree.to_dict(),
            "tree_count": 1,
            "is_ambiguous": False,
            "grouping": grouping,
            "steps": steps,
            "leftmost_derivation": lmd,
            "rightmost_derivation": rmd,
            "explanation": (
                "The unambiguous grammar strictly enforces operator precedence and left-associativity. "
                "Multiplication (*) is located at a lower level (T) and is evaluated before addition (+) at level (E). "
                "Exactly ONE unique parse tree exists for this valid string."
            )
        }
    except (LexicalError, ParseError) as err:
        return {
            "success": False,
            "grammar_type": "unambiguous",
            "grammar_name": "Unambiguous Grammar (G2)",
            "expression": expression,
            "error": {
                "message": err.message,
                "position": getattr(err, "position", 0),
                "token": getattr(err, "token", ""),
                "suggestion": getattr(err, "suggestion", "Check your mathematical expression syntax.")
            }
        }
    except Exception as exc:
        return {
            "success": False,
            "grammar_type": "unambiguous",
            "expression": expression,
            "error": {
                "message": f"Syntax analysis failed: {str(exc)}",
                "position": 0,
                "suggestion": "Check the expression syntax."
            }
        }


def simulate_ambiguous(expression: str) -> Dict[str, Any]:
    """
    Executes full simulation for the Ambiguous Grammar G_1:
      E -> E + E | E * E | (E) | id
    """
    try:
        tokens = tokenize(expression)
        parser = AmbiguousParser(tokens, expression)
        trees = parser.parse_all_trees()

        serialized_trees = []
        for idx, tree in enumerate(trees, 1):
            lmd = generate_leftmost_derivation(tree)
            rmd = generate_rightmost_derivation(tree)
            grouping = tree.get_semantic_grouping()
            serialized_trees.append({
                "tree_id": idx,
                "tree_title": f"Parse Tree {idx}: {grouping}",
                "grouping": grouping,
                "tree": tree.to_dict(),
                "leftmost_derivation": lmd,
                "rightmost_derivation": rmd,
                "precedence_note": (
                    "Addition evaluated first (grouped lower)" if idx == 2 and "+" in grouping and "*" in grouping
                    else "Multiplication evaluated first (grouped lower)" if "+" in grouping and "*" in grouping
                    else "Associative branching variation"
                )
            })

        is_ambiguous = len(trees) > 1

        explanation = (
            f"The grammar generated {len(trees)} distinct parse trees for this expression! "
            "Because G1 allows E -> E + E and E -> E * E with no hierarchy, both addition-first "
            "and multiplication-first interpretations are accepted, proving the grammar is AMBIGUOUS."
            if is_ambiguous else
            "For this basic expression, 1 parse tree was found. However, G1 is inherently ambiguous "
            "because strings like 'id + id * id' permit multiple parse trees."
        )

        return {
            "success": True,
            "grammar_type": "ambiguous",
            "grammar_name": "Ambiguous Grammar (G1)",
            "rules": [
                "E -> E + E | E * E | (E) | id"
            ],
            "expression": expression,
            "tokens": [t.to_dict() for t in tokens if t.type != "EOF"],
            "trees": serialized_trees,
            "tree_count": len(trees),
            "is_ambiguous": is_ambiguous,
            "explanation": explanation
        }
    except (LexicalError, ParseError) as err:
        return {
            "success": False,
            "grammar_type": "ambiguous",
            "grammar_name": "Ambiguous Grammar (G1)",
            "expression": expression,
            "error": {
                "message": err.message,
                "position": getattr(err, "position", 0),
                "token": getattr(err, "token", ""),
                "suggestion": getattr(err, "suggestion", "Check your mathematical expression syntax.")
            }
        }
    except Exception as exc:
        return {
            "success": False,
            "grammar_type": "ambiguous",
            "expression": expression,
            "error": {
                "message": f"Syntax analysis failed: {str(exc)}",
                "position": 0,
                "suggestion": "Check the expression syntax."
            }
        }


def compare_grammars(expression: str) -> Dict[str, Any]:
    """
    Performs a side-by-side formal comparison of both grammars for the exact same input string.
    """
    amb_res = simulate_ambiguous(expression)
    unamb_res = simulate_unambiguous(expression)

    # Synthesis conclusion
    if not amb_res.get("success") or not unamb_res.get("success"):
        conclusion = {
            "valid_syntax": False,
            "summary": "The input expression contains syntax errors and could not be parsed by either grammar."
        }
    else:
        amb_trees = amb_res.get("tree_count", 0)
        unamb_trees = unamb_res.get("tree_count", 0)
        conclusion = {
            "valid_syntax": True,
            "ambiguous_tree_count": amb_trees,
            "unambiguous_tree_count": unamb_trees,
            "demonstrates_ambiguity": amb_trees > 1,
            "summary": (
                f"For the expression '{expression}', the Ambiguous Grammar yields {amb_trees} distinct parse trees "
                f"whereas the Unambiguous Grammar yields exactly {unamb_trees} parse tree. "
                "This conclusively illustrates the disambiguation property: introducing non-terminals (T, F) "
                "stratifies operators into strict precedence tiers, eliminating multiple syntactical interpretations."
            )
        }

    return {
        "expression": expression,
        "ambiguous": amb_res,
        "unambiguous": unamb_res,
        "conclusion": conclusion
    }

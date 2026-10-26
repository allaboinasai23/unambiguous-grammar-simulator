

"""
FLA Academic Project: Unambiguous Grammar Construction Simulator
Flask Web Application Entrypoint
"""

import os
from flask import Flask, render_template, request, jsonify
from parser import (
    simulate_unambiguous,
    simulate_ambiguous,
    compare_grammars,
    tokenize,
    LexicalError,
    ParseError
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fla-unambiguous-simulator-secret-2026'

# Predefined educational test cases and presets
PRESETS = [
    {
        "id": "classic_precedence",
        "name": "Classic Precedence (* vs +)",
        "expression": "id + id * id",
        "category": "Precedence Showcase",
        "description": "Demonstrates why G1 is ambiguous: allows both id+(id*id) and (id+id)*id, whereas G2 enforces id+(id*id).",
        "recommended_for": "comparison"
    },
    {
        "id": "precedence_reversed",
        "name": "Reversed Precedence (* before +)",
        "expression": "id * id + id",
        "category": "Precedence Showcase",
        "description": "Verifies that multiplication binds tighter than addition regardless of linear order in the input.",
        "recommended_for": "comparison"
    },
    {
        "id": "parentheses_override",
        "name": "Parentheses Overriding Precedence",
        "expression": "(id + id) * id",
        "category": "Grouping Showcase",
        "description": "Shows how parentheses in F -> (E) elevate addition to highest evaluation precedence.",
        "recommended_for": "simulator"
    },
    {
        "id": "associativity_addition",
        "name": "Left Associativity (+ and +)",
        "expression": "id + id + id",
        "category": "Associativity Showcase",
        "description": "Demonstrates that left recursion E -> E + T creates left-branching tree ((id + id) + id).",
        "recommended_for": "simulator"
    },
    {
        "id": "associativity_multiplication",
        "name": "Left Associativity (* and *)",
        "expression": "id * id * id",
        "category": "Associativity Showcase",
        "description": "Demonstrates that left recursion T -> T * F creates left-branching tree ((id * id) * id).",
        "recommended_for": "simulator"
    },
    {
        "id": "simple_addition",
        "name": "Basic Addition",
        "expression": "id + id",
        "category": "Basic",
        "description": "Minimal two-operand expression producing a single binary operation tree.",
        "recommended_for": "simulator"
    },
    {
        "id": "nested_parentheses",
        "name": "Complex Nested Expression",
        "expression": "(id + id * id) * (id + id)",
        "category": "Advanced",
        "description": "Combines precedence tiers, sub-expressions, and multiple operator levels.",
        "recommended_for": "simulator"
    },
    {
        "id": "error_consecutive_ops",
        "name": "Syntax Error: Consecutive Operators",
        "expression": "id + * id",
        "category": "Error Testing",
        "description": "Syntax error testing: Missing operand between '+' and '*'.",
        "recommended_for": "error_handling"
    },
    {
        "id": "error_unmatched_left",
        "name": "Syntax Error: Unmatched Left Parenthesis",
        "expression": "(id + id",
        "category": "Error Testing",
        "description": "Syntax error testing: Missing closing parenthesis ')'.",
        "recommended_for": "error_handling"
    },
    {
        "id": "error_unmatched_right",
        "name": "Syntax Error: Unmatched Right Parenthesis",
        "expression": "id + id)",
        "category": "Error Testing",
        "description": "Syntax error testing: Unexpected closing parenthesis without matching '('.",
        "recommended_for": "error_handling"
    }
]

# Educational formal grammar documentation
GRAMMAR_DETAILS = {
    "ambiguous": {
        "title": "Ambiguous Arithmetic Grammar (G1)",
        "tuple": "G1 = ({E}, {+, *, (, ), id}, R1, E)",
        "non_terminals": ["E"],
        "terminals": ["+", "*", "(", ")", "id"],
        "start_symbol": "E",
        "productions": [
            "E -> E + E",
            "E -> E * E",
            "E -> ( E )",
            "E -> id"
        ],
        "flaw": (
            "Because non-terminal E is used uniformly on both sides of '+' and '*', the grammar "
            "does NOT specify whether '*' has higher precedence than '+', nor does it specify "
            "left vs right associativity. Consequently, expressions like 'id + id * id' permit "
            "multiple distinct leftmost derivations and parse trees."
        ),
        "consequence": (
            "In compiler design, ambiguity is unacceptable because a source statement could compile "
            "into conflicting machine code instructions with completely different arithmetic results."
        )
    },
    "unambiguous": {
        "title": "Unambiguous Arithmetic Grammar (G2)",
        "tuple": "G2 = ({E, T, F}, {+, *, (, ), id}, R2, E)",
        "non_terminals": ["E", "T", "F"],
        "terminals": ["+", "*", "(", ")", "id"],
        "start_symbol": "E",
        "productions": [
            "E -> E + T | T",
            "T -> T * F | F",
            "F -> ( E ) | id"
        ],
        "precedence_tiers": [
            {"tier": "Level 1 (Lowest)", "non_terminal": "E", "operator": "+ (Addition)", "associativity": "Left-to-Right via E -> E + T"},
            {"tier": "Level 2 (Higher)", "non_terminal": "T", "operator": "* (Multiplication)", "associativity": "Left-to-Right via T -> T * F"},
            {"tier": "Level 3 (Highest)", "non_terminal": "F", "operator": "(E) and id (Atomic operands)", "associativity": "Enclosed Subexpressions"}
        ],
        "disambiguation_method": (
            "1. Stratification: Introducing non-terminals T (Terms) and F (Factors) creates a hierarchy. "
            "Multiplication appears deeper in the tree, ensuring it binds to its operands before addition. "
            "2. Left Recursion (E -> E + T and T -> T * F) forces operations of equal precedence to associate from left to right."
        )
    }
}


@app.route("/")
def home():
    """Renders the Home Page / Dashboard."""
    return render_template("index.html", presets=PRESETS, grammars=GRAMMAR_DETAILS)


@app.route("/simulator")
def simulator():
    """Renders the Interactive Step-by-Step Simulator page."""
    return render_template("simulator.html", presets=PRESETS, grammars=GRAMMAR_DETAILS)


@app.route("/comparison")
def comparison():
    """Renders the Side-by-Side Comparison page."""
    return render_template("comparison.html", presets=PRESETS, grammars=GRAMMAR_DETAILS)


# --- REST API Endpoints ---

@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    """
    Simulates parsing for the chosen grammar.
    JSON payload: { "expression": "id + id * id", "grammar": "unambiguous" | "ambiguous" }
    """
    data = request.get_json() or {}
    expr = (data.get("expression") or "").strip()
    grammar = (data.get("grammar") or "unambiguous").lower()

    if not expr:
        return jsonify({
            "success": False,
            "error": {
                "message": "Expression cannot be empty. Please enter an expression like 'id + id * id'.",
                "position": 0,
                "suggestion": "Select a preset above or type 'id + id * id'."
            }
        }), 400

    if grammar == "ambiguous":
        result = simulate_ambiguous(expr)
    else:
        result = simulate_unambiguous(expr)

    return jsonify(result)


@app.route("/api/compare", methods=["POST"])
def api_compare():
    """
    Compares ambiguous and unambiguous grammars side-by-side for an input expression.
    JSON payload: { "expression": "id + id * id" }
    """
    data = request.get_json() or {}
    expr = (data.get("expression") or "").strip()

    if not expr:
        return jsonify({
            "success": False,
            "error": {
                "message": "Expression cannot be empty.",
                "position": 0,
                "suggestion": "Enter an expression to compare."
            }
        }), 400

    result = compare_grammars(expr)
    return jsonify(result)


@app.route("/api/presets", methods=["GET"])
def api_presets():
    """Returns preset expressions."""
    return jsonify({"presets": PRESETS})


@app.route("/api/grammar-info", methods=["GET"])
def api_grammar_info():
    """Returns formal grammar educational details."""
    return jsonify(GRAMMAR_DETAILS)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Unambiguous Grammar Construction Simulator on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=True)

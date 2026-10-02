from typing import Dict, List, Tuple

Body = Tuple[str, ...]  # () representa ε
Grammar = Dict[str, List[Body]]


def parse(lines: List[str]) -> Grammar:
    """Convierte líneas ya validadas en gramática; conserva el orden de aparición."""
    grammar: Grammar = {}
    for line in lines:
        head, rhs = line.replace("->", "→").split("→", 1)
        bodies = grammar.setdefault(head.strip(), [])
        for alt in rhs.split("|"):
            alt = alt.strip()
            bodies.append(() if alt == "ε" else tuple(alt))
    return grammar


def format_body(body: Body) -> str:
    return "".join(body) if body else "ε"


def format_grammar(grammar: Grammar) -> List[str]:
    return [
        f"{head} → " + " | ".join(format_body(b) for b in bodies)
        for head, bodies in grammar.items()
        if bodies
    ]

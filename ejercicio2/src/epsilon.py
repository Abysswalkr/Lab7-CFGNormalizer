from dataclasses import dataclass, field
from itertools import product
from typing import List, Set, Tuple

from parser import Body, Grammar

Production = Tuple[str, Body]

ADDED = "agregada"
EMPTY = "descartada (vacía)"
DUPLICATE = "descartada (duplicada)"


def nullable_rounds(grammar: Grammar) -> List[List[Production]]:
    """Punto fijo: cada ronda agrega los no terminales con un cuerpo formado solo
    por anulables de rondas anteriores, junto con la producción que lo justifica."""
    nullable: Set[str] = set()
    rounds: List[List[Production]] = []
    while True:
        added = []
        for head, bodies in grammar.items():
            if head in nullable:
                continue
            body = next((b for b in bodies if all(s in nullable for s in b)), None)
            if body is not None:
                added.append((head, body))
        if not added:
            return rounds
        rounds.append(added)
        nullable |= {head for head, _ in added}


def nullable_productions(grammar: Grammar, nullable: Set[str]) -> List[Production]:
    return [
        (head, body)
        for head, bodies in grammar.items()
        for body in bodies
        if all(s in nullable for s in body)
    ]


@dataclass
class Expansion:
    head: str
    body: Body
    positions: List[int]  # índices de los símbolos anulables en el cuerpo
    cases: List[Tuple[Tuple[bool, ...], Body, str]] = field(default_factory=list)


def eliminate(grammar: Grammar, nullable: Set[str]) -> Tuple[Grammar, List[Expansion]]:
    """Genera, por cada producción, los 2^m casos de presencia/omisión de sus m
    símbolos anulables; descarta cuerpos vacíos y duplicados."""
    result: Grammar = {}
    expansions: List[Expansion] = []
    for head, bodies in grammar.items():
        new_bodies = result.setdefault(head, [])
        for body in bodies:
            exp = Expansion(head, body, [i for i, s in enumerate(body) if s in nullable])
            for mask in product((True, False), repeat=len(exp.positions)):
                omitted = {p for p, keep in zip(exp.positions, mask) if not keep}
                new_body = tuple(s for i, s in enumerate(body) if i not in omitted)
                if not new_body:
                    status = EMPTY
                elif new_body in new_bodies:
                    status = DUPLICATE
                else:
                    status = ADDED
                    new_bodies.append(new_body)
                exp.cases.append((mask, new_body, status))
            expansions.append(exp)
    return result, expansions

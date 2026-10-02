from dataclasses import dataclass, field
from typing import Dict, Set

from .ast_builder import ASTNode
from .expander import EPSILON


@dataclass
class NFA:
    start: int
    accept: int
    states: Set[int]
    transitions: Dict[int, Dict[str, Set[int]]] = field(default_factory=dict)


@dataclass
class _Fragment:
    start: int
    accept: int


class _ThompsonBuilder:
    def __init__(self) -> None:
        self._next_id = 0
        self.states: Set[int] = set()
        self.transitions: Dict[int, Dict[str, Set[int]]] = {}

    def new_state(self) -> int:
        state = self._next_id
        self._next_id += 1
        self.states.add(state)
        return state

    def add_transition(self, src: int, symbol: str, dst: int) -> None:
        self.transitions.setdefault(src, {}).setdefault(symbol, set()).add(dst)

    def build(self, node: ASTNode) -> _Fragment:
        if node.tipo == "literal":
            return self._build_literal(node.valor)
        if node.tipo == "epsilon":
            return self._build_epsilon()
        if node.tipo == "concat":
            return self._build_concat(node)
        if node.tipo == "union":
            return self._build_union(node)
        if node.tipo == "kleene":
            return self._build_kleene(node)
        raise ValueError(f"Tipo de nodo AST no soportado: {node.tipo}")

    def _build_literal(self, simbolo: str) -> _Fragment:
        start, accept = self.new_state(), self.new_state()
        self.add_transition(start, simbolo, accept)
        return _Fragment(start, accept)

    def _build_epsilon(self) -> _Fragment:
        start, accept = self.new_state(), self.new_state()
        self.add_transition(start, EPSILON, accept)
        return _Fragment(start, accept)

    def _build_concat(self, node: ASTNode) -> _Fragment:
        izq = self.build(node.izquierdo)
        der = self.build(node.derecho)
        self.add_transition(izq.accept, EPSILON, der.start)
        return _Fragment(izq.start, der.accept)

    def _build_union(self, node: ASTNode) -> _Fragment:
        izq = self.build(node.izquierdo)
        der = self.build(node.derecho)
        start, accept = self.new_state(), self.new_state()
        self.add_transition(start, EPSILON, izq.start)
        self.add_transition(start, EPSILON, der.start)
        self.add_transition(izq.accept, EPSILON, accept)
        self.add_transition(der.accept, EPSILON, accept)
        return _Fragment(start, accept)

    def _build_kleene(self, node: ASTNode) -> _Fragment:
        interno = self.build(node.izquierdo)
        start, accept = self.new_state(), self.new_state()
        self.add_transition(start, EPSILON, interno.start)
        self.add_transition(start, EPSILON, accept)
        self.add_transition(interno.accept, EPSILON, interno.start)
        self.add_transition(interno.accept, EPSILON, accept)
        return _Fragment(start, accept)


def build_nfa(root: ASTNode) -> NFA:
    builder = _ThompsonBuilder()
    fragment = builder.build(root)
    return NFA(
        start=fragment.start,
        accept=fragment.accept,
        states=builder.states,
        transitions=builder.transitions,
    )

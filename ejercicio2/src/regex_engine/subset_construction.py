from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Set

from .expander import EPSILON
from .thompson import NFA

# Nombre legible y determinista para el estado trampa (sink) que completa el AFD.
SINK_STATE = "SINK"


@dataclass
class DFA:
    start: str
    accepts: Set[str]
    states: Set[str]
    transitions: Dict[str, Dict[str, str]] = field(default_factory=dict)


def epsilon_closure(nfa: NFA, states: "Set[int] | FrozenSet[int]") -> FrozenSet[int]:
    """ε-closure de un conjunto de estados del AFN (no existía una versión previa
    para reutilizar; los módulos de minimización/simulación del compañero aún no
    están en el repo)."""
    stack = list(states)
    closure = set(states)
    while stack:
        state = stack.pop()
        for dest in nfa.transitions.get(state, {}).get(EPSILON, ()):
            if dest not in closure:
                closure.add(dest)
                stack.append(dest)
    return frozenset(closure)


def get_alphabet(nfa: NFA) -> Set[str]:
    """Alfabeto inferido del AFN: todos los símbolos usados en sus transiciones,
    excluyendo EPSILON."""
    alphabet: Set[str] = set()
    for symbol_map in nfa.transitions.values():
        alphabet.update(symbol for symbol in symbol_map if symbol != EPSILON)
    return alphabet


def _move(nfa: NFA, states: FrozenSet[int], symbol: str) -> Set[int]:
    result: Set[int] = set()
    for state in states:
        result.update(nfa.transitions.get(state, {}).get(symbol, ()))
    return result


def _state_name(subset: FrozenSet[int]) -> str:
    if not subset:
        return SINK_STATE
    return "{" + ",".join(str(s) for s in sorted(subset)) + "}"


def build_dfa(nfa: NFA) -> DFA:
    alphabet = sorted(get_alphabet(nfa))

    start_closure = epsilon_closure(nfa, {nfa.start})
    start_name = _state_name(start_closure)

    transitions: Dict[str, Dict[str, str]] = {}
    accepts: Set[str] = set()
    states: Set[str] = {start_name}
    pending: List[FrozenSet[int]] = [start_closure]

    sink_needed = False

    while pending:
        current = pending.pop()
        current_name = _state_name(current)
        if nfa.accept in current:
            accepts.add(current_name)

        current_transitions: Dict[str, str] = {}
        for symbol in alphabet:
            moved = _move(nfa, current, symbol)
            if not moved:
                sink_needed = True
                current_transitions[symbol] = SINK_STATE
                continue
            closure = epsilon_closure(nfa, moved)
            name = _state_name(closure)
            current_transitions[symbol] = name
            if name not in states:
                states.add(name)
                pending.append(closure)
        transitions[current_name] = current_transitions

    if sink_needed:
        states.add(SINK_STATE)
        transitions[SINK_STATE] = {symbol: SINK_STATE for symbol in alphabet}

    return DFA(start=start_name, accepts=accepts, states=states, transitions=transitions)

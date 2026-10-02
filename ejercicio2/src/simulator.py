from typing import Optional

from regex_engine.subset_construction import DFA, SINK_STATE


def reject_position(dfa: DFA, texto: str) -> Optional[int]:
    """Índice donde el AFD rechaza `texto` (len(texto) si termina en estado no
    aceptante); None si lo acepta."""
    state = dfa.start
    for i, symbol in enumerate(texto):
        state = dfa.transitions.get(state, {}).get(symbol)
        if state is None or state == SINK_STATE:
            return i
    return None if state in dfa.accepts else len(texto)


def accepts(dfa: DFA, texto: str) -> bool:
    return reject_position(dfa, texto) is None

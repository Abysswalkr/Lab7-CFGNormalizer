from typing import List, Tuple

from regex_engine.ast_builder import build_ast
from regex_engine.expander import expand
from regex_engine.shunting_yard import to_postfix
from regex_engine.subset_construction import DFA, build_dfa
from regex_engine.thompson import build_nfa
from simulator import reject_position

# `~` sustituye a ε en la línea, porque ε es el épsilon interno del motor.
PRODUCTION_REGEX = r"[A-Z] *(→|->) *([A-Za-z0-9]+|~)( *\| *([A-Za-z0-9]+|~))*"
EPSILON_PLACEHOLDER = "~"


class ValidationError(Exception):
    def __init__(self, line_number: int, line: str, reason: str) -> None:
        super().__init__(f"Línea {line_number}: '{line}' -> {reason}")
        self.line_number = line_number
        self.line = line
        self.reason = reason


def compile_regex(regex: str) -> DFA:
    postfix = to_postfix(expand(regex))[0]
    return build_dfa(build_nfa(build_ast(postfix)))


def _reason(dfa: DFA, line: str) -> str:
    if "→" not in line and "->" not in line:
        return "falta la flecha (→ o ->)"
    if not line[0].isupper():
        return f"el lado izquierdo '{line[0]}' debe ser una letra mayúscula (no terminal)"
    if EPSILON_PLACEHOLDER in line:
        return f"símbolo inválido '{EPSILON_PLACEHOLDER}' en la columna {line.index(EPSILON_PLACEHOLDER) + 1}"
    pos = reject_position(dfa, line.replace("ε", EPSILON_PLACEHOLDER))
    if pos == len(line):
        return "la línea termina incompleta (falta un cuerpo tras '|' o tras la flecha)"
    return f"símbolo inesperado '{line[pos]}' en la columna {pos + 1}"


def validate(lines: List[str], dfa: DFA) -> List[Tuple[int, str]]:
    """Devuelve las líneas no vacías (número, contenido) o lanza ValidationError
    en la primera inválida."""
    valid = []
    for number, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue
        if EPSILON_PLACEHOLDER in line or reject_position(
            dfa, line.replace("ε", EPSILON_PLACEHOLDER)
        ) is not None:
            raise ValidationError(number, line, _reason(dfa, line))
        valid.append((number, line))
    return valid

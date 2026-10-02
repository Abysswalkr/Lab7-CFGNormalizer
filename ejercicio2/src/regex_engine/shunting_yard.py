from dataclasses import dataclass, field
from typing import List, Optional

CONCAT_DISPLAY = "·"


class ShuntingYardError(Exception):
    pass


@dataclass
class Token:
    kind: str
    value: str = ""
    lo: Optional[int] = None
    hi: Optional[int] = None


PRECEDENCE = {"UNION": 1, "CONCAT": 2, "STAR": 3}
_OPERATORS = set(PRECEDENCE)


@dataclass
class TraceStep:
    token: str
    action: str
    stack: List[str] = field(default_factory=list)
    output: List[str] = field(default_factory=list)


def format_tokens(tokens: List[Token]) -> str:
    return "".join(t.value for t in tokens)


def to_postfix(tokens: List[Token]) -> "tuple[List[Token], List[TraceStep]]":
    output: List[Token] = []
    stack: List[Token] = []
    trace: List[TraceStep] = []

    def snapshot(token_repr: str, action: str) -> None:
        trace.append(
            TraceStep(
                token=token_repr,
                action=action,
                stack=[t.value for t in stack],
                output=[t.value for t in output],
            )
        )

    for tok in tokens:
        if tok.kind == "LITERAL":
            output.append(tok)
            snapshot(tok.value, "Agregar literal a la salida")
        elif tok.kind == "LPAREN":
            stack.append(tok)
            snapshot(tok.value, "Apilar '('")
        elif tok.kind == "RPAREN":
            while stack and stack[-1].kind != "LPAREN":
                output.append(stack.pop())
            if not stack:
                raise ShuntingYardError("Paréntesis desbalanceados: falta '(' correspondiente")
            stack.pop()
            snapshot(tok.value, "Vaciar pila hasta '(' y descartar el paréntesis")
        elif tok.kind in _OPERATORS:
            while (
                stack
                and stack[-1].kind in _OPERATORS
                and PRECEDENCE[stack[-1].kind] >= PRECEDENCE[tok.kind]
            ):
                output.append(stack.pop())
            stack.append(tok)
            snapshot(tok.value, f"Desapilar operadores de mayor/igual precedencia y apilar '{tok.value}'")
        else:
            raise ShuntingYardError(f"Token inesperado: {tok.kind}")

    while stack:
        top = stack.pop()
        if top.kind == "LPAREN":
            raise ShuntingYardError("Paréntesis desbalanceados: falta ')' correspondiente")
        output.append(top)

    snapshot("(fin)", "Vaciar el resto de la pila a la salida")
    return output, trace

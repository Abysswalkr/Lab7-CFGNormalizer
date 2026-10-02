from dataclasses import dataclass
from typing import List, Optional

from .expander import EPSILON
from .shunting_yard import ShuntingYardError, Token

UNARY_OPS = {"STAR": "kleene"}
BINARY_OPS = {"UNION": "union", "CONCAT": "concat"}


@dataclass
class ASTNode:
    tipo: str  # 'literal' | 'epsilon' | 'union' | 'concat' | 'kleene'
    valor: Optional[str] = None
    izquierdo: Optional["ASTNode"] = None
    derecho: Optional["ASTNode"] = None


def build_ast(postfix_tokens: List[Token]) -> ASTNode:
    stack: List[ASTNode] = []

    for tok in postfix_tokens:
        if tok.kind == "LITERAL":
            if tok.value == EPSILON:
                stack.append(ASTNode(tipo="epsilon"))
            else:
                stack.append(ASTNode(tipo="literal", valor=tok.value))
        elif tok.kind in UNARY_OPS:
            if not stack:
                raise ShuntingYardError(
                    f"Postfix inválido: operador unario '{tok.value}' sin operando"
                )
            hijo = stack.pop()
            stack.append(ASTNode(tipo=UNARY_OPS[tok.kind], izquierdo=hijo))
        elif tok.kind in BINARY_OPS:
            if len(stack) < 2:
                raise ShuntingYardError(
                    f"Postfix inválido: operador binario '{tok.value}' sin dos operandos"
                )
            derecho = stack.pop()
            izquierdo = stack.pop()
            stack.append(ASTNode(tipo=BINARY_OPS[tok.kind], izquierdo=izquierdo, derecho=derecho))
        else:
            raise ShuntingYardError(f"Token inesperado en postfix: {tok.kind}")

    if len(stack) != 1:
        raise ShuntingYardError(
            f"Postfix inválido: quedaron {len(stack)} nodos en la pila, se esperaba 1"
        )
    return stack[0]

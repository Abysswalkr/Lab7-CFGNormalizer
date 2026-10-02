from typing import List

from .shunting_yard import ShuntingYardError, Token

# Símbolo interno para epsilon (cadena vacía). Se usa "ε" (griega, U+03B5) porque
# no es un carácter ASCII imprimible común en los alfabetos de entrada de este
# proyecto, evitando colisión con símbolos literales de las expresiones regulares.
EPSILON = "ε"

SINGLE_CHAR_OPERATORS = {
    "(": "LPAREN",
    ")": "RPAREN",
    "|": "UNION",
    "*": "STAR",
    "+": "PLUS",
    "?": "QUESTION",
}


def _parse_repeat(regex: str, i: int) -> "tuple[Token, int]":
    end = regex.find("}", i)
    if end == -1:
        raise ShuntingYardError(f"Llave '{{' sin cerrar en posición {i}")
    body = regex[i + 1:end]
    if "," in body:
        lo_s, hi_s = body.split(",", 1)
        lo_s = lo_s.strip()
        hi_s = hi_s.strip()
        if not lo_s.isdigit():
            raise ShuntingYardError(f"Cuantificador '{{{body}}}' malformado")
        lo = int(lo_s)
        hi = int(hi_s) if hi_s.isdigit() else None
    else:
        if not body.strip().isdigit():
            raise ShuntingYardError(f"Cuantificador '{{{body}}}' malformado")
        lo = hi = int(body.strip())
    return Token("REPEAT", body, lo, hi), end + 1


def _parse_char_class(regex: str, i: int) -> "tuple[list, int]":
    chars: List[str] = []
    j = i + 1
    n = len(regex)
    while j < n and regex[j] != "]":
        c = regex[j]
        if c == "\\":
            if j + 1 >= n:
                raise ShuntingYardError("Escape '\\' al final de la expresión")
            chars.append(regex[j + 1])
            j += 2
            continue
        if j + 2 < n and regex[j + 1] == "-" and regex[j + 2] != "]":
            start_ord, end_ord = ord(c), ord(regex[j + 2])
            if end_ord < start_ord:
                raise ShuntingYardError(f"Rango de clase inválido '{c}-{regex[j + 2]}'")
            chars.extend(chr(o) for o in range(start_ord, end_ord + 1))
            j += 3
            continue
        chars.append(c)
        j += 1
    if j >= n:
        raise ShuntingYardError(f"Clase de caracteres '[' sin cerrar en posición {i}")
    if not chars:
        raise ShuntingYardError("Clase de caracteres vacía '[]'")
    return chars, j + 1


def tokenize(regex: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    n = len(regex)
    while i < n:
        c = regex[i]
        if c == "\\":
            if i + 1 >= n:
                raise ShuntingYardError("Escape '\\' al final de la expresión")
            tokens.append(Token("LITERAL", regex[i + 1]))
            i += 2
        elif c == "{":
            tok, i = _parse_repeat(regex, i)
            tokens.append(tok)
        elif c == "}":
            raise ShuntingYardError(f"'}}' inesperado sin '{{' previo en posición {i}")
        elif c == "[":
            chars, i = _parse_char_class(regex, i)
            tokens.append(Token("LPAREN", "("))
            for k, ch in enumerate(chars):
                if k > 0:
                    tokens.append(Token("UNION", "|"))
                tokens.append(Token("LITERAL", ch))
            tokens.append(Token("RPAREN", ")"))
        elif c == "]":
            raise ShuntingYardError(f"']' inesperado sin '[' previo en posición {i}")
        elif c in SINGLE_CHAR_OPERATORS:
            tokens.append(Token(SINGLE_CHAR_OPERATORS[c], c))
            i += 1
        else:
            tokens.append(Token("LITERAL", c))
            i += 1
    return tokens


def _find_operand_start(tokens: List[Token], quant_idx: int) -> int:
    j = quant_idx - 1
    if j < 0:
        raise ShuntingYardError("Cuantificador sin operando precedente")
    if tokens[j].kind == "RPAREN":
        depth = 1
        k = j - 1
        while k >= 0 and depth > 0:
            if tokens[k].kind == "RPAREN":
                depth += 1
            elif tokens[k].kind == "LPAREN":
                depth -= 1
            k -= 1
        if depth != 0:
            raise ShuntingYardError("Paréntesis desbalanceados")
        return k + 1
    if tokens[j].kind == "LITERAL":
        return j
    raise ShuntingYardError(
        f"Cuantificador aplicado a un token inválido: {tokens[j].kind}"
    )


def expand_repeats(tokens: List[Token]) -> List[Token]:
    tokens = list(tokens)
    while True:
        idx = next((i for i, t in enumerate(tokens) if t.kind == "REPEAT"), None)
        if idx is None:
            return tokens

        start = _find_operand_start(tokens, idx)
        operand = tokens[start:idx]
        quant = tokens[idx]

        lo, hi = quant.lo, quant.hi
        if lo is None:
            raise ShuntingYardError(f"Cuantificador '{{{quant.value}}}' malformado")
        replacement: List[Token] = []
        for _ in range(lo):
            replacement += operand
        if hi is None:
            replacement += operand + [Token("STAR", "*")]
        else:
            if hi < lo:
                raise ShuntingYardError(
                    f"Cuantificador {{{lo},{hi}}} inválido: límite superior < inferior"
                )
            for _ in range(hi - lo):
                replacement += operand + [Token("QUESTION", "?")]

        tokens = tokens[:start] + replacement + tokens[idx + 1:]


def expand_plus(tokens: List[Token]) -> List[Token]:
    tokens = list(tokens)
    while True:
        idx = next((i for i, t in enumerate(tokens) if t.kind == "PLUS"), None)
        if idx is None:
            return tokens

        start = _find_operand_start(tokens, idx)
        operand = tokens[start:idx]
        replacement = operand + operand + [Token("STAR", "*")]
        tokens = tokens[:start] + replacement + tokens[idx + 1:]


def expand_question(tokens: List[Token]) -> List[Token]:
    tokens = list(tokens)
    while True:
        idx = next((i for i, t in enumerate(tokens) if t.kind == "QUESTION"), None)
        if idx is None:
            return tokens

        start = _find_operand_start(tokens, idx)
        operand = tokens[start:idx]
        replacement = (
            [Token("LPAREN", "(")]
            + operand
            + [Token("UNION", "|"), Token("LITERAL", EPSILON), Token("RPAREN", ")")]
        )
        tokens = tokens[:start] + replacement + tokens[idx + 1:]


_CONCAT_STARTERS = {"LITERAL", "LPAREN"}
_CONCAT_ENDERS = {"LITERAL", "RPAREN", "STAR"}


def insert_concat(tokens: List[Token]) -> List[Token]:
    result: List[Token] = []
    for tok in tokens:
        if result and result[-1].kind in _CONCAT_ENDERS and tok.kind in _CONCAT_STARTERS:
            result.append(Token("CONCAT", "·"))
        result.append(tok)
    return result


def expand(regex: str) -> List[Token]:
    tokens = tokenize(regex)
    tokens = expand_repeats(tokens)
    tokens = expand_plus(tokens)
    tokens = expand_question(tokens)
    tokens = insert_concat(tokens)
    return tokens

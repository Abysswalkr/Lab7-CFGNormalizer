import argparse
import sys

from epsilon import eliminate, nullable_productions, nullable_rounds
from parser import format_body, format_grammar, parse
from regex_engine.shunting_yard import ShuntingYardError
from validator import PRODUCTION_REGEX, ValidationError, compile_regex, validate


def title(text: str) -> None:
    print(f"\n=== {text} ===")


def fmt_set(symbols) -> str:
    return "{" + ", ".join(sorted(symbols)) + "}"


def print_expansion(exp) -> None:
    production = f"{exp.head} → {format_body(exp.body)}"
    m = len(exp.positions)
    if m == 0:
        _, _, status = exp.cases[0]
        print(f"\n{production}  (m = 0, sin símbolos anulables): {status}")
        return
    print(f"\n{production}  (m = {m}, 2^{m} = {2 ** m} casos)")
    labels = [f"{exp.body[p]}({p + 1})" for p in exp.positions]
    width = max(len(format_body(exp.body)), len("Resultado"))
    print("  #  " + "  ".join(f"{l:<4}" for l in labels) + f"  {'Resultado':<{width}}  Estado")
    for n, (mask, new_body, status) in enumerate(exp.cases, start=1):
        flags = "  ".join(f"{'sí' if keep else 'no':<{max(4, len(l))}}" for keep, l in zip(mask, labels))
        print(f"  {n:<2} {flags}  {format_body(new_body):<{width}}  {status}")


def main() -> int:
    args = argparse.ArgumentParser(description="Eliminación de producciones-ε")
    args.add_argument("archivo")
    args.add_argument("--keep-start-epsilon", action="store_true",
                      help="conservar S → ε si el símbolo inicial es anulable")
    args = args.parse_args()

    try:
        with open(args.archivo, encoding="utf-8") as f:
            raw_lines = f.read().splitlines()
    except OSError as e:
        print(f"No se pudo leer '{args.archivo}': {e.strerror}", file=sys.stderr)
        return 1

    try:
        dfa = compile_regex(PRODUCTION_REGEX)
    except ShuntingYardError as e:
        print(f"Error al compilar la regex: {e}", file=sys.stderr)
        return 2

    try:
        lines = validate(raw_lines, dfa)
    except ValidationError as e:
        print(f"Línea {e.line_number} inválida: {e.line}", file=sys.stderr)
        print(f"Motivo: {e.reason}", file=sys.stderr)
        return 1
    if not lines:
        print("El archivo no contiene producciones.", file=sys.stderr)
        return 1
    title("0. Validación")
    for number, line in lines:
        print(f"Línea {number} válida: {line}")

    grammar = parse([line for _, line in lines])
    start = next(iter(grammar))

    title("1. Gramática original")
    print("\n".join(format_grammar(grammar)))

    title("2. Cálculo de anulables")
    nullable = set()
    for n, added in enumerate(nullable_rounds(grammar), start=1):
        print(f"Ronda {n}:")
        for head, body in added:
            why = f"  ({', '.join(sorted(set(body)))} ∈ anulables)" if body else ""
            print(f"  + {head}  por {head} → {format_body(body)}{why}")
        nullable |= {head for head, _ in added}
        print(f"  Anulables = {fmt_set(nullable)}")
    print("Sin cambios: punto fijo alcanzado.")
    print(f"Anulables = {fmt_set(nullable)}")

    title("3. Producciones anulables")
    for head, body in nullable_productions(grammar, nullable):
        print(f"{head} → {format_body(body)}")

    title("4. Generación de nuevas producciones")
    result, expansions = eliminate(grammar, nullable)
    for exp in expansions:
        print_expansion(exp)

    title("5. Gramática resultante")
    if start in nullable:
        if args.keep_start_epsilon:
            result[start].append(())
            print(f"Nota: {start} es anulable, ε ∈ L(G); se conserva {start} → ε (--keep-start-epsilon).")
        else:
            print(f"Nota: {start} es anulable, ε ∈ L(G); la gramática resultante genera L(G) \\ {{ε}}.")
    print("\n".join(format_grammar(result)))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())

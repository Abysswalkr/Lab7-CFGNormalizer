# Lab7-CFGNormalizer

Carga una gramática libre de contexto desde un `.txt`, valida cada línea con un motor de expresiones regulares propio (AFN → AFD) y elimina sus producciones-ε mostrando cada paso.
Solo se implementa la eliminación de producciones-ε (no unarias, no símbolos inútiles, no CNF).

## Estructura

- `ejercicio1/`: PDF con el procedimiento.
- `ejercicio2/`: código (`src/`) y gramáticas de entrada (`gramaticas/`).

## Requisitos y ejecución

Python 3.10+ sin dependencias externas. Desde la raíz del repositorio:

```bash
python ejercicio2/src/main.py ejercicio2/gramaticas/gramatica1.txt
```

```bash
python ejercicio2/src/main.py ejercicio2/gramaticas/gramatica2.txt --keep-start-epsilon
```

`--keep-start-epsilon` conserva `S → ε` cuando el símbolo inicial es anulable (desactivado por defecto). Si una línea es inválida, el programa indica número de línea, contenido y motivo, y termina con código 1. Los ejemplos inválidos están en `ejercicio2/gramaticas/errores/`.

## Formato de entrada

- Una producción por línea; alternativas separadas por `|`. Las líneas vacías se ignoran.
- Mayúscula individual = no terminal; minúscula individual o dígito = terminal.
- Flecha `→` o `->`; épsilon `ε`.
- El símbolo inicial es el lado izquierdo de la primera línea.

```
S → 0A0 | 1B1 | BB
```

## Video demostración

<link YouTube no listado>

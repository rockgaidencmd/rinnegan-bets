# Evaluations

Scripts ad-hoc para evaluar el modelo en escenarios concretos.

**No son tests automatizados** (eso vive en `backend/tests/`). Son corridas
humanas que producen output legible — sirven para entender qué hace el
modelo en partidos reales antes de confiar en él.

## Estructura

```
evaluations/
├── README.md              # Este archivo
├── compare_matchups.py    # Compara N partidos lado a lado
├── ecuador_classics.py    # Clásicos de Liga Pro Ecuador
├── premier_top6.py        # Choques del Big 6 de Premier
├── champions_picks.py     # Partidos de Champions League
└── runs/                  # Outputs (gitignored)
    └── 2026-05-19_*.txt
```

## Cuándo usar cada uno

| Script | Para qué |
|--------|----------|
| `compare_matchups.py` | Comparar varios partidos en una tabla resumen |
| `ecuador_classics.py` | Validar que el modelo Ecuador da resultados razonables |
| `premier_top6.py` | Ver cómo se comporta el modelo Europe con equipos top |
| `champions_picks.py` | Probar la lógica de matchups internacionales |

## Cómo correr

```bash
cd backend
source venv/bin/activate

# Output en pantalla
python evaluations/compare_matchups.py

# Guardar a archivo para revisar después
python evaluations/compare_matchups.py > evaluations/runs/$(date +%Y-%m-%d)_comparison.txt
```

## Diferencia con `tests/`

| | `tests/` | `evaluations/` |
|---|---|---|
| Propósito | Verificar que código no se rompe | Ver qué dice el modelo |
| Cuándo se corre | En CI, antes de cada commit | Cuando quieres entender el modelo |
| Output | "PASS" o "FAIL" | Predicciones legibles |
| Determinista | Sí | No (depende de la BD actual) |
| ¿Falla un commit? | Sí, si falla | No, son exploratorios |

## Reglas

1. **Scripts van al repo** (son código reutilizable).
2. **Outputs en `runs/` no van al repo** (gitignored). Cada uno corre
   sus propias evaluaciones y guarda lo que le interese.
3. Cada script debe poder correrse independiente, sin args complicados.
4. Output siempre human-readable (no JSON, no logs técnicos).

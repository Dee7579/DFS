# DFS Certified-Source Integrity Guard

## Purpose

The Babylon 5 ACTA platform modules and canonical `dfs.db` are certified source
inputs. Runtime features may read them but must never modify them. Tactical
Assistant battle state belongs in separate `*.dfs-game.json` files.

## Protected sources

- `Application/Python/platform_data/**/*.py`
- `Database/Data/dfs.db`

The committed manifest records every protected path, file size, SHA-256 digest,
and the canonical database table counts.

## Create the baseline

Run this only after the database validator passes and the project is deliberately
ready to certify:

```bat
cd /d D:\GitHub\DFS\Application\Python
certify_b5_acta_baseline.cmd
```

The command refuses to replace an existing manifest. Deliberate future
recertification requires:

```bat
python certify_sources.py --force
```

Never use `--force` merely to make a failing integrity test pass. First identify
and review every source change.

## Verify the baseline

```bat
python verify_certified_sources.py
```

The normal test suite also runs
`tests/test_certified_source_integrity.py`, so platform or database mutations
fail automatically.

## Runtime rule

Fleet Builder, Tactical Assistant, and future game modules must write only to
runtime databases, settings, logs, saved fleets, or saved game-state files.
They must not write to the protected source paths.

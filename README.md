# sprkkr2nomad

A [NOMAD](https://nomad-lab.eu/) parser for SPR-KKR calculations, using
[ASE2SPRKKR](https://github.com/ase2sprkkr/ase2sprkkr) to interpret SPR-KKR
output files and input parameters.

## Local development and testing

Use the project's virtual-environment Python to launch pytest:

```sh
uv sync --group dev
uv run --group dev python -m pytest -q
```

Do **not** rely on `uv run pytest` when a system-wide pytest executable is
also on `PATH`: if no `pytest` command is installed in the selected
environment, uv can invoke the external command, whose shebang selects its
**own** Python interpreter. This may produce `No module named 'nomad'`
even though uv installed the project dependencies.

To verify which environment is used:

```sh
uv run --group dev python -c 'import sys; print(sys.executable)'
uv run --group dev python -c 'import importlib.metadata as m; import nomad; print("ase2sprkkr:", m.version("ase2sprkkr")); print("nomad-lab:", m.version("nomad-lab"))'
```

The Python executable should be inside the project's `.venv` directory.
To reproduce the original bug report's Python 3.13 environment explicitly,
use `uv sync --python 3.13 --group dev` before running the tests.

This branch targets **ASE2SPRKKR 3.6.x**. Version 4 introduced a separate
`result_files` API and requires an explicit parser migration; its installation
is not equivalent to validating the 3.6 compatibility fixes.

## Exporting an index view

Once tests pass, generate a compact NOMAD data view without inlining large
HDF5 payloads:

```sh
uv run python scripts/nomad_data_view.py examples/Fe_Bsf/Fe_BSFEK.out --out index.json
```

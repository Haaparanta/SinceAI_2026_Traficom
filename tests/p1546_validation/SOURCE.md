# P.1546 validation suite (vendored, unmodified)

Copied on 6 Nov 2026 from `eeveetza/Py1546` at commit `e235629009ab1a12a33fc4a8fb5612f2883ecb5b`, the same commit pinned in
`pyproject.toml`. Py1546 is the Python implementation of Recommendation ITU-R P.1546-6 by Ivica Stevanovic (OFCOM/BAKOM),
corresponding to the reference code approved by ITU-R Working Party 3K. Licence: `LICENSE_Py1546` (use, modification and
redistribution allowed with acknowledgement).

| File | Upstream path |
|---|---|
| `validateP1546.py` | `tests/validateP1546.py` |
| `validation_profiles/*.csv` | `tests/validation_profiles/` (24 terrain profiles, 52 cases) |
| `reference_combined_results.csv` | `tests/validation_results/combined_results.csv` (published predictions) |

`tests/test_p1546.py` copies this folder to a temporary directory, runs the validation script with the NumPy 2 alias
`np.mat = np.asmatrix` (identical in NumPy 1.x), and requires every one of the 52 predictions to match the reference to
1e-6 dB. On 6 Nov 2026 the largest difference was 0.0 dB.

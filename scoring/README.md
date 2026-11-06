# scoring/

Deterministic relevance scoring for ITU BR IFIC notices against Finnish spectrum use.
It answers, for every notice item in a Space IFIC (API/A, CR/C, AP30/30A/30B, Part I/II/III-S)
or a Terrestrial IFIC (land-mobile T11/T12 notices): how much does this matter to Finland,
why, by when, and how sure are we. Read `DESIGN.md` for the reasoning; this file is the manual.

* Stdlib-only Python 3.10+. No model, no network call at scoring time, no randomness.
* Every factor carries evidence (SRS table and column, M4 row ID, RR provision, formula).
* Every calculated value is labelled indicative with its assumptions.
* All numbers that could be argued with live in `weights.json`.

## Quick start

```bash
# from the repository root
python -m unittest discover -s scoring/tests -t .

python -m scoring space scoring/examples/space_groups_example.json \
    --finnish-networks scoring/examples/finnish_space_networks_example.json \
    --out out/space.json --markdown out/space.md

python -m scoring terrestrial scoring/examples/terrestrial_notices_example.json \
    --previous scoring/examples/terrestrial_notices_previous_example.json \
    --stations scoring/examples/protected_stations_example.json \
    --out out/terrestrial.json --markdown out/terrestrial.md

python -m scoring explain out/space.json --id 126001001-1
python -m scoring evaluate out/space.json scoring/examples/labels_example.json
```

`examples/output/` holds the reports these commands produce, so the output format can be
reviewed without running anything.

## The score in one line

```
score = 100 x relevance x (0.65 x severity + 0.35 x urgency)        priority A >= 70, B >= 45, C >= 20, D below
relevance = freq_overlap x geography x direction                      a zero screens the item out, with the reason
```

Confidence (how much of the score rested on real inputs) is reported separately and never
mixed into the score. Suppressed and withdrawn notices are listed, not scored.

## Folder map

| Path | What it is |
|---|---|
| `DESIGN.md` | The thinking: expert questions, factor rationale, what is left out, what to verify, calibration plan. |
| `weights.json` | Every weight, threshold, bin and keyword rule. Versioned. |
| `models.py` | Dataclasses: `SpaceGroup`, `TerrestrialNotice`, `ProtectedStation`, `FinnishSpaceNetwork` (inputs); `Factor`, `Evidence`, `Finding`, `ScoredSubject` (outputs). Field names follow the SRS database and the T12 item keys. |
| `space_scoring.py` | Space factors and assembly: `score_group`, `rank_groups`, `aggregate_by_notice`. |
| `terrestrial_scoring.py` | Terrestrial factors, `diff_notices` (new/modified/withdrawn between IFICs), `trends`. |
| `finnish_table.py` | Loads the M4 table of frequency allocations (Traficom API snapshot), merges rows into allocation units, applies the sensitivity and primary/secondary rules. `python -m scoring.finnish_table fetch` refreshes the snapshot. |
| `pfd.py` | pfd at the ground and comparison with RR Article 21 Table 21-4. |
| `propagation.py` | Field-strength models (free space as upper bound, P.1546 hook) and the T/R 25-08 trigger lookup. |
| `geometry.py` | Distances, Finland and neighbour polygons, GSO elevation/slant range, NGSO coverage. |
| `adapters.py` | SRS tables to `SpaceGroup`, T12 items to `TerrestrialNotice`, JSON readers, special-interest XLS rows. |
| `explain.py` | Deterministic explanation text from the factors. |
| `evaluate.py` | Precision/recall sweep, ranking quality, priority agreement, ablation. |
| `cli.py` | Command-line entry points (`python -m scoring ...`). |
| `reference/` | Data: Finnish table snapshot (gzipped), Table 21-4 limits, T/R 25-08 thresholds, Finland region polygons (Natural Earth), ITU administration codes. |
| `examples/` | Synthetic golden cases for both sides, Finnish networks, protected stations, labels, and the generated reports. |
| `tests/` | 52 unit tests (`unittest`, no extra dependencies). |

## Inputs

**Space.** One `SpaceGroup` per frequency group of a notice. From the IFIC database, build it
with `adapters.groups_from_srs({"notice": rows, "grp": rows, "freq": rows, "s_beam": rows,
"emiss": rows, "geo": rows, "orbit": rows, "non_geo": rows, "srv_area": rows, "srv_cls": rows,
"provn": rows, "pub_ssn": rows})`, where each `rows` is a list of dicts exported from the
MDB (mdbtools, pyodbc, or a CSV dump). The minimum useful set is notice, grp, freq, geo or
orbit, s_beam and emiss. Optional `FinnishSpaceNetwork` entries (adm FIN networks from the
SRS) raise the relevance of uplink groups in the same band.

**Terrestrial.** One `TerrestrialNotice` per T11/T12 notice via `adapters.notice_from_t12(items)`
(item keys with or without the `t_` prefix) or `adapters.notices_from_rows(rows)` for
TerRaBase exports. Optional `ProtectedStation` entries from the special-interest XLS via
`adapters.protected_stations_from_rows(rows)`. Pass the previous IFIC to `diff_notices` to
set the novelty of each notice before scoring.

## Outputs

`ScoredSubject` per notice item: `score`, `priority`, `confidence`, `breadth`, `status`
(active, screened_out, withdrawn), `deadline`, `summary`, and `findings`. Each `Finding`
holds the eleven (space) or ten (terrestrial) factors with value, weight, availability,
reason and evidence, the screened-out reason when relevance is zero, the missing inputs,
and a fixed-template explanation. `to_dict()` gives JSON; the CLI also writes a Markdown
report with the top findings and their evidence lines.

## Integration

The pipeline step described in `pm_pack/06_AGENTS_Master_Context.md` (`backend/app/pipeline/score.py`)
can import this package directly: build the inputs with the adapters, call `rank_groups` or
`rank_notices`, and serialise `ScoredSubject.to_dict()`. The `Finding` shape already carries
`factors`, `score`, `evidence` and `indicative`, matching the frozen contracts in that document.

A propagation model is registered with `propagation.register_model("p1546", fn)` where
`fn(freq_mhz, erp_dbw, h_tx_m, d_km, path, time_pct, h_rx_m)` returns dB(uV/m). Until one is
registered, the terrestrial field-strength factor only screens out impossible cases and flags
the rest as needing a P.1546 run.

## Tuning

Change `weights.json` (or pass `--config my_weights.json`) and bump `version`. The config loader
rejects weights that do not sum to one and priority bands that are out of order.
`evaluate.py` reports what the change does against expert labels. Section 7 of `DESIGN.md`
says how to do this without fooling yourself.

## Known limitations

* Table 21-4 rows marked `verified: false` must be checked against RR 2024 before quoting.
* Satellite beam contours (GIMS) are not read: maximum gain towards Finland is assumed, which
  overstates pfd for beams that point elsewhere; the service-area multiplier partly compensates.
* The Finland region polygons are Natural Earth 1:50m: coastal cities can fall just outside
  the coastline, which only affects the land/sea classification of a path.
* Epfd (Article 22) and aggregate NGSO effects are out of scope.
* No P.1546 implementation is bundled yet.

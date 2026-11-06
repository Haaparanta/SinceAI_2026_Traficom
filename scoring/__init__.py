"""Deterministic relevance scoring for ITU BR IFIC notices against Finnish spectrum use.

Space side:        scoring.space_scoring   (API/A, CR/C, AP30/30A/30B, Part I/II/III-S)
Terrestrial side:  scoring.terrestrial_scoring (land-mobile notices, T/R 25-08 triggers, trends)
Shared:            scoring.models, scoring.common, scoring.geometry, scoring.pfd,
                   scoring.propagation, scoring.finnish_table, scoring.config

Everything here is stdlib-only and deterministic. No model, no network call, no randomness.
See README.md for the scoring philosophy and DESIGN.md for the factor rationale.
"""

__version__ = "0.1.0"

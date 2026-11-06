# Second check of the limit tables

**7 Nov 2026.** `pfd_limits.csv` (RR Article 21, Table 21-4) and `tr2508_thresholds.csv` (ECC/ERC T/R 25-08) were each typed in once. This is the second check: both source documents were transcribed again, independently, and compared value by value.

> [!IMPORTANT]
> This check was made by a second agent (Claude), not by a person. It shows that two separate readings of the source pages agree. The `review` column therefore still says "human sign-off pending". A spectrum specialist signs off by replacing that text with their name and the date.

## Method

1. **Sources.**
   - ITU Radio Regulations, Edition of 2024, Volume 1 (`2400594-RR-Vol 1-E-A5.pdf` from `R-REG-RR-2024-ZPF-E.zip`): Table 21-4 on printed pages 287 to 291 and its footnotes on pages 291 to 294.
   - ECC/ERC Recommendation T/R 25-08, Edition 6 June 2025, downloaded from `https://docdb.cept.org/download/4789`.
2. **Independent transcription.** A separate agent rendered the pages to images and transcribed them without opening the CSVs or any other repository file. The PDF text layer was used only to find the pages, because it drops some "+" and "δ" signs. Results:
   - [`rr_table21_4_transcription.json`](rr_table21_4_transcription.json): 38 printed rows, 64 band entries, with footnotes and doubts.
   - [`tr2508_transcription.json`](tr2508_transcription.json): 18 values from Annexes 1, 3 and 4.
3. **Numerical comparison.** [`tests/test_reference_review.py`](../../../tests/test_reference_review.py) evaluates every CSV limit and every printed limit expression at each angle from 0 to 90 degrees in 0.25 degree steps. Rows are matched on band, orbit and reference bandwidth. The test also checks that the CSV band is fully covered and that the cited page is right. It runs with `make test`, so a later edit to a limit is checked again.
4. **Spot checks by eye.** The cells that the first transcription had inferred, and every disagreement, were checked on the page images: T/R 25-08 page 6 and RR page 290.

## Result

| File | Rows | Values that agree | Corrected |
|---|---|---|---|
| `pfd_limits.csv` | 38 | 38 of 38, at every angle | page of `37500-40000_gso` and `40000-40500`: 291 changed to **290** (values unchanged) |
| `tr2508_thresholds.csv` | 5 | 5 of 5 (0, 6, 12, 18 and 20 dB(uV/m); 25 kHz, 10 m, 10 % time, 50 % locations, at the border line) | notes: the bandwidth correction applies only when the power is uniform across the channel |

Three slopes that the first transcription had reconstructed from continuity are now confirmed on the page images:
- 32.3-33 GHz: `-135 + (δ - 5)`
- 40.5-42 GHz GSO: `-120 + (δ - 5)` and `-110 + 0.5(δ - 15)`
- 42-42.5 GHz GSO: `-127 + (4/3)(δ - 5)` and `-107 + 0.4(δ - 20)`

None of the corrections changes a computed number. The page number appears only in the evidence text of the limit row.

## What the tables leave out, and whether it matters for 3074 and 3076

| Not in the CSV | Why | Effect on the results |
|---|---|---|
| RR rows for non-GSO and highly inclined orbits: 10.7-12.75 GHz (footnotes 24 and 25), 17.7-19.7 GHz (footnote 16), 27.5-30 GHz (footnote 26), and 37-38, 37.5-40, 40.5-42 and 42-42.5 GHz non-GSO | The pfd check (build step C1) covers GSO only; non-GSO is reported as "not evaluated" | none: those groups are "medium, non-GSO pfd not evaluated" |
| 9.9-10.4 GHz, Earth exploration-satellite (active), mean pfd (footnote 18) | Non-GSO radar; mean pfd is a different quantity | none: the 5 candidate groups in 3074 are all non-GSO |
| 12.2-12.75 GHz GSO (Region 3) and 12.5-12.75 GHz (Region 1 countries in Nos. 5.494 and 5.496) | Finland is in Region 1 and not listed in either provision | none: kept in the CSV with `applies_to_finland = no` |
| 31.0-31.3 and 34.7-35.2 GHz space research | The printed qualifier about Nos. 5.550 and 5.549 may cover only 34.7-35.2 GHz (a layout doubt) | none: no 3074 downlink in these bands |
| 1 518-1 525 MHz | United States territory only | none |
| T/R 25-08 Annex 3 (410-430 and 450-470 MHz, narrowband against wideband, preferential frequencies at 40 or 50 km) and Annex 4 (LTE, NR and CDMA at 3 m per 5 MHz) | Our check is co-channel at the border line (Annex 1) | none today: the 15 flagged 3076 notices in these bands are all narrowband (25 kHz or less). For a non-preferential frequency at 0 km, Annex 3 gives the same 20 dB(uV/m) as Annex 1 |
| T/R 25-08 above 470 MHz | The recommendation covers 29.7-470 MHz only | 3076 notices above 470 MHz get the field strength and "review" without a threshold (question Q12) |

## For the specialist who signs off

1. Footnote 13 (17.7-19.3 GHz, non-GSO FSS, `-115 - X`) and footnote 22 (`Y` for 3.4-4.2 GHz non-GSO; the CSV assumes `Y = 0`) only matter once non-GSO pfd is evaluated.
2. T/R 25-08 footnote 2 says the 1 % time curves "should be used" for digital systems in certain situations. We use 10 % time throughout. Should a digital notice also be checked at 1 %?
3. The T/R 25-08 band edges (47, 108, 380 and 400 MHz) are shared. The code assigns an edge frequency to the upper band (`f_min <= f < f_max`).
4. The RR row for 6 825-7 075 MHz has two limits that both apply (per 4 kHz and per 1 MHz). Both are in the CSV, and the pfd step uses the smaller margin.

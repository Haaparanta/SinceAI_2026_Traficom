# Scoring design: what makes an IFIC item matter to Finland

This document is the reasoning behind `scoring/`. It answers three questions: what an
expert at Traficom actually asks of a new notice, how those questions become numbers,
and what is deliberately left out. The code is the executable version of this text;
`weights.json` holds every tunable number.

The evaluation criteria of the challenge brief drive the design:

| Criterion | What the scorer does about it |
|---|---|
| A. Technical analysis, reproducibility (25 %) | Deterministic, stdlib-only. Every calculation prints its formula, inputs and assumptions. Same input, same output, byte for byte. |
| B. Extensibility, terrestrial side quest (25 %) | One score shape for both sides (`relevance x (severity, urgency)`); the terrestrial scorer reuses the Finnish table, geometry, evidence and explanation code and adds a propagation plug-in and an IFIC diff. |
| C. Prioritisation useful to an expert (20 %) | Priority bands A-D with a one-paragraph deterministic explanation per finding; filings roll up to notices; deadlines are computed. |
| D. Case recognition accuracy (15 %) | Hard relevance gates (frequency, geography, direction) screen out the bulk; `evaluate.py` measures precision/recall against expert labels on IFIC 3074/3076 and shows what each factor buys. |
| E. Auditability, evidence (15 %) | Every factor carries `Evidence(kind, source, excerpt)`: SRS table and column, M4 row ID, Radio Regulations provision, formula. |

## 1. The expert's questions

Reading a BR IFIC against Finnish use, a spectrum specialist asks, in this order:

1. **Does it touch a frequency Finland uses?** Co-channel first; adjacent band matters for passive services (radio astronomy, passive EESS) and for strong emitters.
2. **Can it physically reach Finland?** A GSO satellite must be above the Finnish horizon; an NGSO constellation must have an orbit that rises over 60-70 N; a terrestrial station must be within radio range of the border, and its antenna pointing matters.
3. **In which direction is the exposure?** A satellite downlink (space-to-Earth) lands on Finnish receivers. An uplink group exposes Finland only through the foreign earth stations (if close) or through Finnish satellites receiving in the band.
4. **How bad would it be?** The power flux-density at the ground compared with the Article 21 hard limit; for terrestrial, the field strength at the border compared with the T/R 25-08 trigger. Then: how important is the Finnish use (public safety, GNSS, passive science rank above amateur), whether Finland's allocation is primary, and how much bandwidth is involved.
5. **How urgent is it?** A coordination request (CR/C) where silence means agreement within four months is more urgent than an advance publication; if Finland is named as an affected administration a reply is mandatory; if it is not named but should be, a No. 9.41 request has the same four-month clock. New entries beat re-publications.
6. **Can I trust the numbers?** Missing inputs are common (no power density, no orbit, unknown service area). Those must not silently become "safe".

Questions 1-3 are gates: if any answer is "no", the item is not a Finnish case, however powerful or urgent it is. Questions 4-5 rank the cases that pass. Question 6 is reported separately as confidence, never folded into the score.

## 2. The score

```
score = 100 x relevance x (0.65 x severity + 0.35 x urgency)

relevance = freq_overlap x geography x direction            each in [0, 1]; any 0 screens out
severity  = weighted mean of the severity factors           weights in weights.json
urgency   = weighted mean of the urgency factors
confidence = share of factor weight that rested on real inputs (not neutral defaults)
priority  = A (>= 70, investigate now) | B (>= 45, review) | C (>= 20, monitor) | D (no action)
```

Why multiplicative relevance: an expert does not average "not visible from Finland" with "very high power". Multiplying lets a weak link pull the score down proportionally and a zero remove the item. Why a weighted mean for severity and urgency: within the cases that do reach Finland, considerations trade off, and a mean with visible weights is the simplest model an expert can argue with.

A finding is one (notice item, Finnish target) pair. A notice item (a satellite frequency group, a terrestrial notice) gets the score of its best finding; its breadth (how many distinct Finnish services it touches) breaks ties. Scores are not summed over findings: a network with thirty groups is not thirty times worse than one with one.

The window arithmetic uses an explicit `as_of` date (default: the IFIC publication date), so the evaluation of IFIC 3074 gives the same numbers in November as it did in June.

## 3. Space side: factors

Inputs mirror the SRS database (notice, grp, freq, s_beam, emiss, geo, orbit, non_geo, srv_area, srv_cls, provn, pub_ssn). The Finnish side is the M4 table of frequency allocations from the Traficom API, merged into allocation units (sub-band, service, usage, direction, class of station). Capitals in the service name mean primary, as in RR Article 5.

### Relevance (multiplied)

| Factor | Question | Inputs | Value |
|---|---|---|---|
| freq_overlap | Does the group's band fall inside a Finnish sub-band? | freq.freq_min/freq_max; M4 sub-band limits | Co-frequency: 0.6 + 0.4 x (share of the filed bandwidth inside the Finnish sub-band). Adjacent within a guard band (10 % of the filed bandwidth, at least 0.5 MHz): 0.3, or 0.5 for passive services. Otherwise 0. |
| geography | Can the emission reach Finnish territory? | geo.long_nom; orbit.inclin_ang, apog/perig; srv_area.ctry | GSO: elevation from nine reference points across Finland, ramp 0 at the horizon to 1 at 10 degrees, times a service-area multiplier (FIN listed 1.0, region code covering Finland 0.85, neighbour 0.6, not stated 0.5, elsewhere 0.35). NGSO: fraction of Finland's latitude span (59.8-70.1 N) below the highest latitude the orbit can see at 0 degrees elevation, times the same multiplier. Earth-station notices: distance to Finnish territory. |
| direction | Which Finnish stations are exposed? | grp.emi_rcp; M4 service name and direction | Downlink (E) into Finnish terrestrial receivers or space-to-Earth allocations: 1.0; into transmit-only sub-bands: 0.5; into Finnish Earth-to-space allocations: 0.2. Uplink (R): 0.15 base; 0.8 if a Finnish satellite network receives in the band; 1.0/0.7 if the associated earth stations are in Finland/a neighbour and Finnish stations receive in the band; 0.4 against Finnish Earth-to-space allocations. |

### Severity (weighted mean)

| Factor | Weight | Question | Method |
|---|---|---|---|
| pfd_margin | 0.40 | Does the downlink exceed the Article 21 limit on Finnish ground? | pfd = pwr_ds_max + 10 log10(min(reference bandwidth, emission bandwidth)) + max gain - 10 log10(4 pi d^2), evaluated at the Finnish reference point with the smallest margin (GSO) or over elevation samples 5-90 degrees (NGSO). Margin = limit - pfd. Bins: exceeds 1.0; within 6 dB 0.8; within 15 dB 0.5; within 30 dB 0.2; else 0.05. No limit in the band: an informative reference level is used and the value is scaled by 0.8. A pfd commitment (A.17) scales by 0.85. Always labelled indicative; maximum gain towards Finland is assumed because gain contours (GIMS) are not read. |
| finnish_sensitivity | 0.30 | How much would the Finnish use suffer? | Keyword rules over the M4 service and usage strings: passive and safety-of-life 1.0; public safety/government/defence 1.0; meteorological 0.9; public mobile networks 0.85; satellite earth stations and space operations 0.8; fixed links, PMR, maritime, broadcasting, radars 0.6; amateur 0.3; licence-exempt SRD 0.25. |
| finnish_status | 0.15 | Can Finland claim protection? | Primary 1.0; secondary 0.5; usage without allocation 0.3; not allocated 0.1. |
| bandwidth | 0.15 | How much of the Finnish sub-band is hit? | sqrt(overlap / Finnish sub-band width); adjacent 0.1. |

### Urgency (weighted mean)

| Factor | Weight | Question | Method |
|---|---|---|---|
| stage | 0.35 | Which procedure, and what does silence cost? | CR/C 1.0; AP30/30A/30B Part A 0.9; API/A 0.6; Part B sections 0.5; Part I-S 0.45; Part II-S 0.25; Part III-S 0.15; RES49 0.1. |
| deadline | 0.25 | How much of the four-month window is left? | IFIC date + 122 days; as of the `as_of` date: expired 0.1, under 30 days 1.0, under 90 days 0.8, otherwise 0.6; sections without a window 0.3. |
| finland_listed | 0.25 | Is Finland named as affected? | Named 1.0 (a reply is required); not named although Finnish use overlaps 0.6 (No. 9.41 request possible); section without a list 0.5. |
| novelty | 0.15 | New, modified, resubmitted, suppressed? | A 1.0; M 0.7; R 0.4; S 0 (the item is reported as withdrawn, not scored). |

## 4. Terrestrial side quest: factors

Inputs mirror the T11/T12 notice item keys (TerRaBase columns map onto them). Targets are the Finnish allocation units and, when loaded, the stations of special interest from the synthetic XLS.

| Group | Factor | Weight | Method |
|---|---|---|---|
| relevance | freq_overlap | x | Share of the notified emission (assigned frequency +/- half the necessary bandwidth) inside the Finnish sub-band or station channel; adjacent within 25 kHz: 0.3. |
| relevance | geography | x | Distance from the site to the nearest Finnish territory (polygon), with sea paths counted at half distance; bins 25 km 1.0 down to 400+ km 0.03; times antenna pointing (towards Finland 1.0, sideways 0.7, away 0.4). |
| relevance | action | x | ADD/MODIFY 1.0; SUPPRESS/WITHDRAW reported as withdrawn. |
| severity | field_strength_margin | 0.40 | Field strength at the nearest Finnish point versus the T/R 25-08 Annex 1 trigger (0/6/12/18/20 dB(uV/m) per 25 kHz for 29.7-47/47-108/108-380/380-400/400-470 MHz, plus 10 log10(channel/25 kHz) for wider channels). With a P.1546 model: margin bins. With only the free-space upper bound: if even free space stays below the trigger the case is closed (0.05); otherwise the factor is "not evaluated" (0.5, confidence lowered, flagged "needs P.1546"). |
| severity | interference_potential | 0.20 | e.r.p. (dBW) + 10 log10(antenna height / 30 m): a plain proxy that works when nothing else is known. |
| severity | finnish_sensitivity | 0.25 | Same keyword rules as the space side; stations of special interest are at least 0.8. |
| severity | protected_station | 0.15 | Distance to the nearest co-frequency station of special interest (30 km 1.0, 100 km 0.6, 200 km 0.3) with a bonus when that station's antenna looks at the notified site. |
| urgency | novelty | 0.40 | From the IFIC-to-IFIC diff: new 1.0; technical parameters changed 0.9; other change 0.7; unchanged 0.1. |
| urgency | provision | 0.35 | Agreement sought under No. 9.21 (four-month window) 1.0; notification under No. 11.2 0.6. |
| urgency | framework | 0.25 | A quantitative trigger exists for the band (T/R 25-08) 1.0; only the general RR framework 0.5. |

The diff keys notices by the administration's own reference when present, otherwise by the identifying elements of a T12 notice. Trends count notices per (administration, band, station class) against earlier IFICs with a z-score, and flag clusters within 50 km of Finnish territory and wideband notices.

## 5. What is deliberately not in the score

* **Who the administration is.** No weight for "Russia" or "Norway" as such. Proximity enters through geometry and earth-station location, not reputation.
* **Constellation size or fleet.** More satellites increase aggregate interference, but Article 21 limits are single-entry and aggregate (epfd) analysis is out of scope; the number of satellites is kept as evidence only.
* **Cost-recovery status, operator names, launch data.** Irrelevant to interference.
* **Any language-model judgement.** The explanation is a template over the factors. An LLM may later draft correspondence from this output, but it never changes a number.
* **Summing findings.** A notice is as serious as its worst finding.

## 6. Things to verify with Traficom before trusting the numbers

1. `reference/rr_article21_table21-4.json`: rows marked `verified: false` were written from memory of the 2020/2024 editions. Check against RR 2024 Article 21 (the rows at 1.5, 2, 2.5, 3.4-7.75, 6.7, 10.7-11.7 non-GSO, 19.3, 22-27.5, 31.8-33, 37.5-42.5 GHz).
2. Geographical-area symbols in `srv_area` (Preface Table 1B): which codes cover Finland (`region_codes_covering_finland` in `reference/itu_admin_codes.json`).
3. Where the list of affected administrations lives in the IFIC database for CR/C and AP30 sections (`provn`, `tr_aff_ntw`, or the Special Section PDF).
4. The meaning of CR/D, CR/E, CR/F, API/B, API/C and the Part B sections for the stage weights.
5. The list of Finnish satellite networks (adm FIN in the SRS) for the uplink direction factor.
6. The column names of the special-interest XLS (`adapters.protected_stations_from_rows` guesses them).
7. A P.1546 implementation. Until one is registered the terrestrial field-strength factor is screening only.
8. Bilateral agreements (FIN-RUS, FIN-SWE, FIN-NOR, FIN-EST) that replace the T/R 25-08 generic triggers in some bands.

## 7. Calibration plan

1. Ask the experts for verdicts (A-D or relevant/not) on the items of IFIC 3074 and 3076. Store them as `{subject_id: label}` next to the scored output.
2. Run `python -m scoring evaluate scored.json labels.json`: threshold sweep, precision/recall/F1, precision at k, priority agreement, and the lists of false positives and false negatives with their scores.
3. Read the false negatives first. A relevant item with score 0 is a gate problem (a wrong geographical-area code, a missing orbit); fix the data path, not the weights.
4. Only then adjust weights, one at a time, with `ablation()` showing what each factor buys. Keep every weight interpretable and bump `version` in `weights.json` with a line on why.
5. Never tune on the same items used to report accuracy. Split 3074 into a tuning half and a reporting half, or tune on 3074 and report on an earlier IFIC.

## 8. Extending the architecture

The terrestrial scorer is the proof: it reuses the models, the Finnish table, the geometry, the evidence and explanation code, and swaps the physics (pfd versus field strength) and the procedure (special sections versus T12 fragments). Adding AP30B allotment analysis, HAPS, or a new national table is the same pattern: new factor functions, same `Factor`/`Finding`/`ScoredSubject` output, same evaluation harness.

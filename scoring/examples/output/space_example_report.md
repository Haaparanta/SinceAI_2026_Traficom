# Space IFIC findings for Finland

Scoring model 2026-11-06 (scoring package 0.1.0). Score = 100 x relevance x (0.65 x severity + 0.35 x urgency).

| Rank | Score | Priority | Subject | Top Finnish target | Confidence | Deadline |
|---|---|---|---|---|---|---|
| 1 | 86 | A | POLAR-MSS (NOR) CR/C/4323 grp 126001007-1 E 1427-1432 MHz | 1427-1452 MHz | FIXED AND MOBILE | Military use | 100% | 2026-10-23 |
| 2 | 79 | A | KUPOLI-1 (RUS) CR/C/4321 grp 126001001-1 E 10950-11200 MHz | 10700-11700 MHz | FIXED SATELLITE (SPACE-TO-EARTH) | Fixed satellite | 100% | 2026-10-23 |
| 3 | 68 | B | NORDSAT-NG (NOR) API/A/13579 grp 126001002-1 E 17800-18600 MHz | 17800-18600 MHz | FIXED SATELLITE (EARTH-TO-SPACE, SPACE-TO-EARTH) | Fixed satellite | 100% | 2026-10-23 |
| 4 | 48 | B | KUPOLI-1 (RUS) CR/C/4321 grp 126001001-2 R 14250-14500 MHz | 14000-14500 MHz | Mobile-Satellite | Mobile satellite | 92% | 2026-10-23 |
| 5 | 29 | C | SIBIR-OBS (RUS) API/A/13582 grp 126001009-1 R 2025-2110 MHz | 2025-2070 MHz | FIXED | Military use | 92% | 2026-10-23 |
| 6 | 26 | C | BALTIC-UP (EST) API/A/13581 grp 126001006-1 R 14000-14250 MHz | 14000-14500 MHz | Mobile-Satellite | Mobile satellite | 92% | 2026-10-23 |
| 7 | 21 | C | EQUATOR-COM (IND) CR/C/4322 grp 126001003-1 E 3700-4200 MHz | 3800-4200 MHz | FIXED SATELLITE (SPACE-TO-EARTH) | Fixed satellite | 100% | 2026-10-23 |

10 subjects scored: 7 active, 2 screened out, 1 withdrawn/suppressed.

## 1. POLAR-MSS (NOR) CR/C/4323 grp 126001007-1 E 1427-1432 MHz

POLAR-MSS (NOR) CR/C/4323 grp 126001007-1 E 1427-1432 MHz: score 86 (A, Investigate now); 3 Finnish target(s); top finding against 1427-1452 MHz | FIXED AND MOBILE | Military use; confidence 100%; deadline 2026-10-23.

```
POLAR-MSS (NOR) CR/C/4323 grp 126001007-1 E 1427-1432 MHz vs 1427-1452 MHz | FIXED AND MOBILE | Military use.
Score 86/100, priority A (Investigate now): relevance 1.00 x (0.65 x severity 0.84 + 0.35 x urgency 0.90); confidence 100%.
Relevance (multiplied):
- freq_overlap = 1.00: co-frequency: 5 MHz (100% of the filed 5 MHz) falls inside the Finnish sub-band 1427-1452 MHz
- geography = 1.00: NGSO i=98 deg, h=550 km covers 100% of Finland's latitude span; Finland (FIN) is in the service area (x1.00)
- direction = 1.00: space-to-Earth emission into a band where Finnish terrestrial stations receive
Severity (weighted):
- pfd_margin = 0.80 (w=0.40) [indicative]: no Table 21-4 hard limit in this band; pfd -147.8 dB(W/m2) (4 kHz) compared with an informative reference of -150.0: margin -2.2 dB
- finnish_sensitivity = 1.00 (w=0.30): Finnish use 'FIXED AND MOBILE' / 'Military use' rated 1.00: Public safety, government and defence networks
- finnish_status = 1.00 (w=0.15): Finnish allocation status: primary (capitals = primary in the M4 table)
- bandwidth = 0.45 (w=0.15): 5 MHz overlapped = 20% of the Finnish sub-band
Urgency (weighted):
- stage = 1.00 (w=0.35): special section CR/C: coordination request: silence within 4 months counts as agreement (No. 9.52C)
- deadline = 0.60 (w=0.25): 4-month window from IFIC 3074 (2026-06-23) ends 2026-10-23: 122 days left as of 2026-06-23
- finland_listed = 1.00 (w=0.25): Finland is identified as an affected administration in the filing: a response is required
- novelty = 1.00 (w=0.15): new entry
Deadline for comments/agreement: 2026-10-23.
Calculated values are indicative; assumptions are listed with the evidence.
```

Evidence:

- [filing] ific3074.mdb notice.ntc_id=126001007 grp.grp_id=126001007-1: 1427-1432 MHz, E
- [finnish_table] M4 Taajuusjakotaulukko ID 3487,3488,3489: 1427-1452 MHz | FIXED AND MOBILE | Military use
- [geometry] ngso_coverage: inclination 98 deg, altitude 550 km -> satellites visible up to latitude 90.0 deg; Finland (59.8-70.1 N) covered 100%
- [filing] srv_area.ctry: NOR, S, FIN, DNK, ISL
- [filing] grp.emi_rcp: E
- [finnish_table] M4 Taajuusjakotaulukko ID 3487,3488,3489: FIXED AND MOBILE direction=n/a
- [calculation] pfd.py pfd_at_ground: pfd = -70.0 dBW/Hz + 10log10(4000 Hz) + 12.0 dBi - 10log10(4*pi*(550 km)^2) = -147.8 dB(W/m2) in 4 kHz at elevation 90 deg (elevation 90.0 deg); power density from emiss.pwr_ds_max
- [calculation] assumption: single satellite, maximum beam gain assumed towards the ground point
- [calculation] assumption: circular orbit at mean altitude
- [calculation] assumption: no atmospheric loss
- [calculation] assumption: no Table 21-4 hard limit for this band; pfd reported for information only
- [calculation] reference level: -150.0 dB(W/m2/4 kHz) configured in weights.json
- [finnish_table] M4 Taajuusjakotaulukko ID 3487,3488,3489: FIXED AND MOBILE
- [calculation] bandwidth: overlap 5 MHz / sub-band 25 MHz
- [filing] special section: CR/C/4323
- [regulation] RR Nos. 9.3 / 9.52 / AP30 4.1.5: 122 days from publication
- [filing] provn / tr_aff_ntw: FIN, S, RUS
- [filing] act_code / ntf_occurs: A / 

## 2. KUPOLI-1 (RUS) CR/C/4321 grp 126001001-1 E 10950-11200 MHz

KUPOLI-1 (RUS) CR/C/4321 grp 126001001-1 E 10950-11200 MHz: score 79 (A, Investigate now); 1 Finnish target(s); top finding against 10700-11700 MHz | FIXED SATELLITE (SPACE-TO-EARTH) | Fixed satellite; confidence 100%; deadline 2026-10-23.

```
KUPOLI-1 (RUS) CR/C/4321 grp 126001001-1 E 10950-11200 MHz vs 10700-11700 MHz | FIXED SATELLITE (SPACE-TO-EARTH) | Fixed satellite.
Score 79/100, priority A (Investigate now): relevance 1.00 x (0.65 x severity 0.79 + 0.35 x urgency 0.80); confidence 100%.
Relevance (multiplied):
- freq_overlap = 1.00: co-frequency: 250 MHz (100% of the filed 250 MHz) falls inside the Finnish sub-band 10700-11700 MHz
- geography = 1.00: GSO at +36.0 deg E seen at 21.1 deg elevation from Helsinki (visibility 1.00); Finland (FIN) is in the service area (x1.00)
- direction = 1.00: space-to-Earth emission into a Finnish space-to-Earth allocation (Finnish earth stations receive here)
Severity (weighted):
- pfd_margin = 0.80 (w=0.40) [indicative]: pfd -151.1 dB(W/m2) vs limit -146.8 (4 kHz) at Utsjoki: margin +4.3 dB, below the limit
- finnish_sensitivity = 0.80 (w=0.30): Finnish use 'FIXED SATELLITE (SPACE-TO-EARTH)' / 'Fixed satellite' rated 0.80: Satellite earth stations and space operations in Finland
- finnish_status = 1.00 (w=0.15): Finnish allocation status: primary (capitals = primary in the M4 table)
- bandwidth = 0.50 (w=0.15): 250 MHz overlapped = 25% of the Finnish sub-band
Urgency (weighted):
- stage = 1.00 (w=0.35): special section CR/C: coordination request: silence within 4 months counts as agreement (No. 9.52C)
- deadline = 0.60 (w=0.25): 4-month window from IFIC 3074 (2026-06-23) ends 2026-10-23: 122 days left as of 2026-06-23
- finland_listed = 0.60 (w=0.25): Finland is not in the affected list although Finnish use overlaps: inclusion can be requested under No. 9.41 within the 4-month window
- novelty = 1.00 (w=0.15): new entry
Deadline for comments/agreement: 2026-10-23.
Calculated values are indicative; assumptions are listed with the evidence.
```

Evidence:

- [filing] ific3074.mdb notice.ntc_id=126001001 grp.grp_id=126001001-1: 10950-11200 MHz, E
- [finnish_table] M4 Taajuusjakotaulukko ID 4438,4440,4442,4444,4446,4448 (+10 more): 10700-11700 MHz | FIXED SATELLITE (SPACE-TO-EARTH) | Fixed satellite
- [geometry] gso_geometry: GSO at +36.00 deg E: elevation 21.1 deg from Helsinki, slant range 39441 km; 9/9 reference points see it
- [filing] srv_area.ctry: RUS, FIN, S, EST, LVA
- [filing] grp.emi_rcp: E
- [finnish_table] M4 Taajuusjakotaulukko ID 4438,4440,4442,4444,4446,4448 (+10 more): FIXED SATELLITE (SPACE-TO-EARTH) direction=TX
- [calculation] pfd.py pfd_at_ground: pfd = -62.0 dBW/Hz + 10log10(4000 Hz) + 38.0 dBi - 10log10(4*pi*(40442 km)^2) = -151.1 dB(W/m2) in 4 kHz at Utsjoki (elevation 11.3 deg); power density from emiss.pwr_ds_max
- [calculation] assumption: maximum beam gain assumed towards Finland
- [calculation] assumption: no atmospheric or polarisation loss
- [regulation] RR Article 21 Table 21-4 row 10700-11700_gso: limit -146.8 dB(W/m2) in 4 kHz at 11.3 deg
- [finnish_table] M4 Taajuusjakotaulukko ID 4438,4440,4442,4444,4446,4448 (+10 more): FIXED SATELLITE (SPACE-TO-EARTH)
- [calculation] bandwidth: overlap 250 MHz / sub-band 1000 MHz
- [filing] special section: CR/C/4321
- [regulation] RR Nos. 9.3 / 9.52 / AP30 4.1.5: 122 days from publication
- [filing] provn / tr_aff_ntw: S, NOR, EST, D
- [filing] act_code / ntf_occurs: A / 

## 3. NORDSAT-NG (NOR) API/A/13579 grp 126001002-1 E 17800-18600 MHz

NORDSAT-NG (NOR) API/A/13579 grp 126001002-1 E 17800-18600 MHz: score 68 (B, Review); 3 Finnish target(s); top finding against 17800-18600 MHz | FIXED SATELLITE (EARTH-TO-SPACE, SPACE-TO-EARTH) | Fixed satellite; confidence 100%; deadline 2026-10-23.

```
NORDSAT-NG (NOR) API/A/13579 grp 126001002-1 E 17800-18600 MHz vs 17800-18600 MHz | FIXED SATELLITE (EARTH-TO-SPACE, SPACE-TO-EARTH) | Fixed satellite.
Score 68/100, priority B (Review): relevance 0.85 x (0.65 x severity 0.88 + 0.35 x urgency 0.64); confidence 100%.
Relevance (multiplied):
- freq_overlap = 1.00: co-frequency: 800 MHz (100% of the filed 800 MHz) falls inside the Finnish sub-band 17800-18600 MHz
- geography = 0.85: NGSO i=87.9 deg, h=600 km covers 100% of Finland's latitude span; a regional/global area code covering Finland is in the service area (x0.85)
- direction = 1.00: space-to-Earth emission into a Finnish space-to-Earth allocation (Finnish earth stations receive here)
Severity (weighted):
- pfd_margin = 0.85 (w=0.40) [indicative]: pfd -100.6 dB(W/m2) vs limit -105.0 (1000 kHz) at elevation 90 deg: margin -4.4 dB, EXCEEDS the limit; the filing commits to the pfd limit (A.17)
- finnish_sensitivity = 0.80 (w=0.30): Finnish use 'FIXED SATELLITE (EARTH-TO-SPACE, SPACE-TO-EARTH)' / 'Fixed satellite' rated 0.80: Satellite earth stations and space operations in Finland
- finnish_status = 1.00 (w=0.15): Finnish allocation status: primary (capitals = primary in the M4 table)
- bandwidth = 1.00 (w=0.15): 800 MHz overlapped = 100% of the Finnish sub-band
Urgency (weighted):
- stage = 0.60 (w=0.35): special section API/A: advance publication: comments under No. 9.3 within 4 months (only for networks not subject to coordination)
- deadline = 0.60 (w=0.25): 4-month window from IFIC 3074 (2026-06-23) ends 2026-10-23: 122 days left as of 2026-06-23
- finland_listed = 0.50 (w=0.25): API/A carries no affected-administration list
- novelty = 1.00 (w=0.15): new entry
Deadline for comments/agreement: 2026-10-23.
Calculated values are indicative; assumptions are listed with the evidence.
```

Evidence:

- [filing] ific3074.mdb notice.ntc_id=126001002 grp.grp_id=126001002-1: 17800-18600 MHz, E
- [finnish_table] M4 Taajuusjakotaulukko ID 4694,4696: 17800-18600 MHz | FIXED SATELLITE (EARTH-TO-SPACE, SPACE-TO-EARTH) | Fixed satellite
- [geometry] ngso_coverage: inclination 87.9 deg, altitude 600 km -> satellites visible up to latitude 90.0 deg; Finland (59.8-70.1 N) covered 100%
- [filing] srv_area.ctry: GLOBAL
- [filing] grp.emi_rcp: E
- [finnish_table] M4 Taajuusjakotaulukko ID 4694,4696: FIXED SATELLITE (EARTH-TO-SPACE, SPACE-TO-EARTH) direction=TX
- [calculation] pfd.py pfd_at_ground: pfd = -66.0 dBW/Hz + 10log10(1e+06 Hz) + 32.0 dBi - 10log10(4*pi*(600 km)^2) = -100.6 dB(W/m2) in 1000 kHz at elevation 90 deg (elevation 90.0 deg); power density from emiss.pwr_ds_max
- [calculation] assumption: single satellite, maximum beam gain assumed towards the ground point
- [calculation] assumption: circular orbit at mean altitude
- [calculation] assumption: no atmospheric loss
- [regulation] RR Article 21 Table 21-4 row 17700-19300: limit -105.0 dB(W/m2) in 1000 kHz at 90.0 deg
- [filing] f_pfd_limit: Y
- [finnish_table] M4 Taajuusjakotaulukko ID 4694,4696: FIXED SATELLITE (EARTH-TO-SPACE, SPACE-TO-EARTH)
- [calculation] bandwidth: overlap 800 MHz / sub-band 800 MHz
- [filing] special section: API/A/13579
- [regulation] RR Nos. 9.3 / 9.52 / AP30 4.1.5: 122 days from publication
- [filing] provn / tr_aff_ntw: no administrations listed
- [filing] act_code / ntf_occurs: A / 

## 4. KUPOLI-1 (RUS) CR/C/4321 grp 126001001-2 R 14250-14500 MHz

KUPOLI-1 (RUS) CR/C/4321 grp 126001001-2 R 14250-14500 MHz: score 48 (B, Review); 2 Finnish target(s); top finding against 14000-14500 MHz | Mobile-Satellite | Mobile satellite; confidence 92%; deadline 2026-10-23.

```
KUPOLI-1 (RUS) CR/C/4321 grp 126001001-2 R 14250-14500 MHz vs 14000-14500 MHz | Mobile-Satellite | Mobile satellite.
Score 48/100, priority B (Review): relevance 0.70 x (0.65 x severity 0.62 + 0.35 x urgency 0.80); confidence 92%.
Relevance (multiplied):
- freq_overlap = 1.00: co-frequency: 250 MHz (100% of the filed 250 MHz) falls inside the Finnish sub-band 14000-14500 MHz
- geography = 1.00: GSO at +36.0 deg E seen at 21.1 deg elevation from Helsinki (visibility 1.00); Finland (FIN) is in the service area (x1.00)
- direction = 0.70: associated earth stations in a neighbouring country (RUS,EST) transmit in a band where Finnish stations receive
Severity (weighted):
- pfd_margin = 0.50 (w=0.40) [input missing, neutral value used]: uplink group: pfd at the Earth's surface is not produced by the space station
- finnish_sensitivity = 0.80 (w=0.30): Finnish use 'Mobile-Satellite' / 'Mobile satellite' rated 0.80: Satellite earth stations and space operations in Finland
- finnish_status = 0.50 (w=0.15): Finnish allocation status: secondary (capitals = primary in the M4 table)
- bandwidth = 0.71 (w=0.15): 250 MHz overlapped = 50% of the Finnish sub-band
Urgency (weighted):
- stage = 1.00 (w=0.35): special section CR/C: coordination request: silence within 4 months counts as agreement (No. 9.52C)
- deadline = 0.60 (w=0.25): 4-month window from IFIC 3074 (2026-06-23) ends 2026-10-23: 122 days left as of 2026-06-23
- finland_listed = 0.60 (w=0.25): Finland is not in the affected list although Finnish use overlaps: inclusion can be requested under No. 9.41 within the 4-month window
- novelty = 1.00 (w=0.15): new entry
Deadline for comments/agreement: 2026-10-23.
Missing inputs: pfd_margin.
```

Evidence:

- [filing] ific3074.mdb notice.ntc_id=126001001 grp.grp_id=126001001-2: 14250-14500 MHz, R
- [finnish_table] M4 Taajuusjakotaulukko ID 4618,4622,4626,4630: 14000-14500 MHz | Mobile-Satellite | Mobile satellite
- [geometry] gso_geometry: GSO at +36.00 deg E: elevation 21.1 deg from Helsinki, slant range 39441 km; 9/9 reference points see it
- [filing] srv_area.ctry: RUS, FIN, S, EST, LVA
- [filing] grp.emi_rcp: R
- [finnish_table] M4 Taajuusjakotaulukko ID 4618,4622,4626,4630: Mobile-Satellite direction=TX
- [finnish_table] M4 Taajuusjakotaulukko ID 4618,4622,4626,4630: Mobile-Satellite
- [calculation] bandwidth: overlap 250 MHz / sub-band 500 MHz
- [filing] special section: CR/C/4321
- [regulation] RR Nos. 9.3 / 9.52 / AP30 4.1.5: 122 days from publication
- [filing] provn / tr_aff_ntw: S, NOR, EST, D
- [filing] act_code / ntf_occurs: A / 

## 5. SIBIR-OBS (RUS) API/A/13582 grp 126001009-1 R 2025-2110 MHz

SIBIR-OBS (RUS) API/A/13582 grp 126001009-1 R 2025-2110 MHz: score 29 (C, Monitor); 3 Finnish target(s); top finding against 2025-2070 MHz | FIXED | Military use; confidence 92%; deadline 2026-10-23.

```
SIBIR-OBS (RUS) API/A/13582 grp 126001009-1 R 2025-2110 MHz vs 2025-2070 MHz | FIXED | Military use.
Score 29/100, priority C (Monitor): relevance 0.39 x (0.65 x severity 0.80 + 0.35 x urgency 0.64); confidence 92%.
Relevance (multiplied):
- freq_overlap = 0.81: co-frequency: 45 MHz (53% of the filed 85 MHz) falls inside the Finnish sub-band 2025-2070 MHz
- geography = 0.60: NGSO i=97.5 deg, h=695 km covers 100% of Finland's latitude span; a neighbouring administration is in the service area (spill-over) (x0.60)
- direction = 0.80: Finnish satellite network FIN-LEO-OBS receives in this band (foreign uplink emissions can reach it)
Severity (weighted):
- pfd_margin = 0.50 (w=0.40) [input missing, neutral value used]: uplink group: pfd at the Earth's surface is not produced by the space station
- finnish_sensitivity = 1.00 (w=0.30): Finnish use 'FIXED' / 'Military use' rated 1.00: Public safety, government and defence networks
- finnish_status = 1.00 (w=0.15): Finnish allocation status: primary (capitals = primary in the M4 table)
- bandwidth = 1.00 (w=0.15): 45 MHz overlapped = 100% of the Finnish sub-band
Urgency (weighted):
- stage = 0.60 (w=0.35): special section API/A: advance publication: comments under No. 9.3 within 4 months (only for networks not subject to coordination)
- deadline = 0.60 (w=0.25): 4-month window from IFIC 3074 (2026-06-23) ends 2026-10-23: 122 days left as of 2026-06-23
- finland_listed = 0.50 (w=0.25): API/A carries no affected-administration list
- novelty = 1.00 (w=0.15): new entry
Deadline for comments/agreement: 2026-10-23.
Missing inputs: pfd_margin.
```

Evidence:

- [filing] ific3074.mdb notice.ntc_id=126001009 grp.grp_id=126001009-1: 2025-2110 MHz, R
- [finnish_table] M4 Taajuusjakotaulukko ID 3845,3846: 2025-2070 MHz | FIXED | Military use
- [geometry] ngso_coverage: inclination 97.5 deg, altitude 695 km -> satellites visible up to latitude 90.0 deg; Finland (59.8-70.1 N) covered 100%
- [filing] srv_area.ctry: RUS
- [filing] grp.emi_rcp: R
- [finnish_table] M4 Taajuusjakotaulukko ID 3845,3846: FIXED direction=n/a
- [asset] example: FIN-LEO-OBS 2025-2110 MHz R
- [finnish_table] M4 Taajuusjakotaulukko ID 3845,3846: FIXED
- [calculation] bandwidth: overlap 45 MHz / sub-band 45 MHz
- [filing] special section: API/A/13582
- [regulation] RR Nos. 9.3 / 9.52 / AP30 4.1.5: 122 days from publication
- [filing] provn / tr_aff_ntw: no administrations listed
- [filing] act_code / ntf_occurs: A / 

## 6. BALTIC-UP (EST) API/A/13581 grp 126001006-1 R 14000-14250 MHz

BALTIC-UP (EST) API/A/13581 grp 126001006-1 R 14000-14250 MHz: score 26 (C, Monitor); 1 Finnish target(s); top finding against 14000-14500 MHz | Mobile-Satellite | Mobile satellite; confidence 92%; deadline 2026-10-23.

```
BALTIC-UP (EST) API/A/13581 grp 126001006-1 R 14000-14250 MHz vs 14000-14500 MHz | Mobile-Satellite | Mobile satellite.
Score 26/100, priority C (Monitor): relevance 0.42 x (0.65 x severity 0.62 + 0.35 x urgency 0.64); confidence 92%.
Relevance (multiplied):
- freq_overlap = 1.00: co-frequency: 250 MHz (100% of the filed 250 MHz) falls inside the Finnish sub-band 14000-14500 MHz
- geography = 0.60: GSO at +8.0 deg E seen at 21.1 deg elevation from Mariehamn (visibility 1.00); a neighbouring administration is in the service area (spill-over) (x0.60)
- direction = 0.70: associated earth stations in a neighbouring country (EST) transmit in a band where Finnish stations receive
Severity (weighted):
- pfd_margin = 0.50 (w=0.40) [input missing, neutral value used]: uplink group: pfd at the Earth's surface is not produced by the space station
- finnish_sensitivity = 0.80 (w=0.30): Finnish use 'Mobile-Satellite' / 'Mobile satellite' rated 0.80: Satellite earth stations and space operations in Finland
- finnish_status = 0.50 (w=0.15): Finnish allocation status: secondary (capitals = primary in the M4 table)
- bandwidth = 0.71 (w=0.15): 250 MHz overlapped = 50% of the Finnish sub-band
Urgency (weighted):
- stage = 0.60 (w=0.35): special section API/A: advance publication: comments under No. 9.3 within 4 months (only for networks not subject to coordination)
- deadline = 0.60 (w=0.25): 4-month window from IFIC 3074 (2026-06-23) ends 2026-10-23: 122 days left as of 2026-06-23
- finland_listed = 0.50 (w=0.25): API/A carries no affected-administration list
- novelty = 1.00 (w=0.15): new entry
Deadline for comments/agreement: 2026-10-23.
Missing inputs: pfd_margin.
```

Evidence:

- [filing] ific3074.mdb notice.ntc_id=126001006 grp.grp_id=126001006-1: 14000-14250 MHz, R
- [finnish_table] M4 Taajuusjakotaulukko ID 4618,4622,4626,4630: 14000-14500 MHz | Mobile-Satellite | Mobile satellite
- [geometry] gso_geometry: GSO at +8.00 deg E: elevation 21.1 deg from Mariehamn, slant range 39444 km; 9/9 reference points see it
- [filing] srv_area.ctry: EST, LVA, LTU
- [filing] grp.emi_rcp: R
- [finnish_table] M4 Taajuusjakotaulukko ID 4618,4622,4626,4630: Mobile-Satellite direction=TX
- [finnish_table] M4 Taajuusjakotaulukko ID 4618,4622,4626,4630: Mobile-Satellite
- [calculation] bandwidth: overlap 250 MHz / sub-band 500 MHz
- [filing] special section: API/A/13581
- [regulation] RR Nos. 9.3 / 9.52 / AP30 4.1.5: 122 days from publication
- [filing] provn / tr_aff_ntw: no administrations listed
- [filing] act_code / ntf_occurs: A / 

## 7. EQUATOR-COM (IND) CR/C/4322 grp 126001003-1 E 3700-4200 MHz

EQUATOR-COM (IND) CR/C/4322 grp 126001003-1 E 3700-4200 MHz: score 21 (C, Monitor); 2 Finnish target(s); top finding against 3800-4200 MHz | FIXED SATELLITE (SPACE-TO-EARTH) | Fixed satellite; confidence 100%; deadline 2026-10-23.

```
EQUATOR-COM (IND) CR/C/4322 grp 126001003-1 E 3700-4200 MHz vs 3800-4200 MHz | FIXED SATELLITE (SPACE-TO-EARTH) | Fixed satellite.
Score 21/100, priority C (Monitor): relevance 0.24 x (0.65 x severity 0.94 + 0.35 x urgency 0.80); confidence 100%.
Relevance (multiplied):
- freq_overlap = 0.92: co-frequency: 400 MHz (80% of the filed 500 MHz) falls inside the Finnish sub-band 3800-4200 MHz
- geography = 0.26: GSO at +83.0 deg E seen at 7.4 deg elevation from Joensuu (visibility 0.74); service area lists IND, BGD, SRL only; Finland reached by side lobes at most (x0.35)
- direction = 1.00: space-to-Earth emission into a Finnish space-to-Earth allocation (Finnish earth stations receive here)
Severity (weighted):
- pfd_margin = 1.00 (w=0.40) [indicative]: pfd -151.3 dB(W/m2) vs limit -152.0 (4 kHz) at Oulu: margin -0.7 dB, EXCEEDS the limit
- finnish_sensitivity = 0.80 (w=0.30): Finnish use 'FIXED SATELLITE (SPACE-TO-EARTH)' / 'Fixed satellite' rated 0.80: Satellite earth stations and space operations in Finland
- finnish_status = 1.00 (w=0.15): Finnish allocation status: primary (capitals = primary in the M4 table)
- bandwidth = 1.00 (w=0.15): 400 MHz overlapped = 100% of the Finnish sub-band
Urgency (weighted):
- stage = 1.00 (w=0.35): special section CR/C: coordination request: silence within 4 months counts as agreement (No. 9.52C)
- deadline = 0.60 (w=0.25): 4-month window from IFIC 3074 (2026-06-23) ends 2026-10-23: 122 days left as of 2026-06-23
- finland_listed = 0.60 (w=0.25): Finland is not in the affected list although Finnish use overlaps: inclusion can be requested under No. 9.41 within the 4-month window
- novelty = 1.00 (w=0.15): new entry
Deadline for comments/agreement: 2026-10-23.
Calculated values are indicative; assumptions are listed with the evidence.
```

Evidence:

- [filing] ific3074.mdb notice.ntc_id=126001003 grp.grp_id=126001003-1: 3700-4200 MHz, E
- [finnish_table] M4 Taajuusjakotaulukko ID 4092,4094: 3800-4200 MHz | FIXED SATELLITE (SPACE-TO-EARTH) | Fixed satellite
- [geometry] gso_geometry: GSO at +83.00 deg E: elevation 7.4 deg from Joensuu, slant range 40864 km; 9/9 reference points see it
- [filing] srv_area.ctry: IND, BGD, SRL
- [filing] grp.emi_rcp: E
- [finnish_table] M4 Taajuusjakotaulukko ID 4092,4094: FIXED SATELLITE (SPACE-TO-EARTH) direction=TX
- [calculation] pfd.py pfd_at_ground: pfd = -60.0 dBW/Hz + 10log10(4000 Hz) + 36.0 dBi - 10log10(4*pi*(41182 km)^2) = -151.3 dB(W/m2) in 4 kHz at Oulu (elevation 4.4 deg); power density from emiss.pwr_ds_max
- [calculation] assumption: maximum beam gain assumed towards Finland
- [calculation] assumption: no atmospheric or polarisation loss
- [calculation] assumption: limit row 3400-4200_4500-4800_5670-5725_7250-7750 not yet verified against RR 2024 Table 21-4
- [regulation] RR Article 21 Table 21-4 row 3400-4200_4500-4800_5670-5725_7250-7750 (unverified transcription): limit -152.0 dB(W/m2) in 4 kHz at 4.4 deg
- [finnish_table] M4 Taajuusjakotaulukko ID 4092,4094: FIXED SATELLITE (SPACE-TO-EARTH)
- [calculation] bandwidth: overlap 400 MHz / sub-band 400 MHz
- [filing] special section: CR/C/4322
- [regulation] RR Nos. 9.3 / 9.52 / AP30 4.1.5: 122 days from publication
- [filing] provn / tr_aff_ntw: CHN, PAK, RUS, KAZ
- [filing] act_code / ntf_occurs: A / 

# Terrestrial IFIC land-mobile findings for Finland

Scoring model 2026-11-06 (scoring package 0.1.0). Score = 100 x relevance x (0.65 x severity + 0.35 x urgency).

| Rank | Score | Priority | Subject | Top Finnish target | Confidence | Deadline |
|---|---|---|---|---|---|---|
| 1 | 77 | A | S FB 410.5 MHz HAPARANDA (MODIFY) | Tornio wideband link | Digital wideband PMR networks for business activities | 410.5 MHz | 92% |  |
| 2 | 72 | A | RUS FB 160.2 MHz VYBORG (ADD) | 158.825-160.425 MHz | MOBILE | Government | 92% | 2026-11-13 |
| 3 | 63 | B | EST FB 453.5 MHz TALLINN (ADD) | 452.425-456.925 MHz | MOBILE | Digital broadband 450 mobile network | 92% |  |
| 4 | 52 | B | NOR FB 79.5 MHz KIRKENES (ADD) | 78.1-80 MHz | LAND MOBILE | Radiotelephony for energy suppliers | 92% |  |
| 5 | 40 | C | RUS FB 390.5 MHz SANKT-PETERBURG (ADD) | 390.012-394.988 MHz | MOBILE | Emergency services network (VIRVE) | 92% |  |
| 6 | 36 | C | RUS FB 2602.5 MHz SESTRORETSK (ADD) | 2570-2620 MHz | MOBILE | Terrestrial systems capable of providing electronic communications services | 92% |  |
| 7 | 23 | C | LVA FB 415 MHz RIGA (ADD) | 414.012-416.337 MHz | MOBILE | TETRA | 92% |  |
| 8 | 17 | D | RUS FB 169.5 MHz PETROZAVODSK (ADD) | 169.488-169.588 MHz | MOBILE | (SRD) Short range devices | 92% |  |

9 subjects scored: 8 active, 0 screened out, 1 withdrawn/suppressed.

## 1. S FB 410.5 MHz HAPARANDA (MODIFY)

S FB 410.5 MHz HAPARANDA (MODIFY): score 77 (A, Investigate now); 2 Finnish target(s); top finding against Tornio wideband link | Digital wideband PMR networks for business activities | 410.5 MHz; confidence 92%.

```
S FB 410.5 MHz HAPARANDA (MODIFY) vs Tornio wideband link | Digital wideband PMR networks for business activities | 410.5 MHz.
Score 77/100, priority A (Investigate now): relevance 1.00 x (0.65 x severity 0.75 + 0.35 x urgency 0.82); confidence 92%.
Relevance (multiplied):
- freq_overlap = 1.00: co-frequency: 100% of the notified emission falls in 410.4-410.6 MHz
- geography = 1.00: 2 km from Finnish territory over a land path (effective 2 km -> 1.00); non-directional antenna or azimuth not given (x1.00)
- action = 1.00: notice action MODIFY
Severity (weighted):
- field_strength_margin = 0.50 (w=0.40) [indicative] [input missing, neutral value used]: free-space upper bound 94.7 dB(uV/m) exceeds the trigger 29.0 dB(uV/m) (margin +65.6 dB); a P.1546 calculation is needed to decide
- interference_potential = 1.00 (w=0.20): e.r.p. 23.0 dBW with antenna 50 m above ground: potential index 25.2 dBW (height term 10log10(h/30 m))
- finnish_sensitivity = 0.80 (w=0.25): station of special interest 'Tornio wideband link' (Digital wideband PMR networks for business activities) rated 0.80
- protected_station = 1.00 (w=0.15): nearest co-frequency Finnish station of special interest: Tornio wideband link (FI-0004) at 3 km; its antenna (azimuth 250 deg) looks towards the notified site (off-axis 24 deg)
Urgency (weighted):
- novelty = 0.90 (w=0.40): technical parameters changed since the previous IFIC: erp_dbw, action
- provision = 0.60 (w=0.35): notification for recording in the MIFR under No. 11.2; objections possible through the Article 11 examination
- framework = 1.00 (w=0.25): ECC/ERC Rec. T/R 25-08 gives a quantitative coordination trigger for 400-470 MHz
Missing inputs: field_strength_margin.
Calculated values are indicative; assumptions are listed with the evidence.
```

Evidence:

- [filing] t_freq_assgn / t_bdwdth_cde: 410.5 MHz, 200.0 kHz
- [finnish_table] special-interest.xlsx row 5: Tornio wideband link 410.5 MHz
- [geometry] distance_to_finland_km: site (65.8300, 24.1000) -> nearest Finnish territory (65.8338, 24.1391): 1.8 km, path land (sea 0%)
- [filing] t_ant_dir / t_azm_max_e / t_bmwdth: ND / unknown / unknown
- [filing] t_action: MODIFY
- [calculation] free-space (upper bound): E = 94.7 dB(uV/m) at the nearest Finnish point (1.8 km, land path), e.r.p. 23.0 dBW
- [regulation] ECC/ERC Recommendation T/R 25-08, edition 6 June 2025 (https://docdb.cept.org/download/4789), Annex 1 section A1.2.3; values unchanged since the 28 September 2018 edition: trigger 29.0 dB(uV/m) in 400-470 MHz (base 20 + bandwidth correction 9.0 dB); Land mobile systems 29.7-470 MHz. Indicative coordination thresholds: co-channel, 50 % of locations, 10 % of time, 10 m receiving antenna height, reference bandwidth 25 kHz, at the border line.
- [calculation] assumption: free-space propagation: an upper bound, not a prediction
- [calculation] assumption: path type land ignored
- [filing] t_pwr_dbw / t_hgt_agl: 23.0 dBW e.r.p. / 50 m
- [asset] special-interest.xlsx row 5: Tornio wideband link
- [asset] special-interest.xlsx row 5: Tornio wideband link 410.5 MHz +/- 100 kHz at (65.8500, 24.1500)
- [history] ific diff: modified_technical
- [filing] t_fragment / t_prov: NTFD_RR / RR11.2
- [regulation] ECC/ERC Recommendation T/R 25-08, edition 6 June 2025 (https://docdb.cept.org/download/4789), Annex 1 section A1.2.3; values unchanged since the 28 September 2018 edition: 400-470 MHz

## 2. RUS FB 160.2 MHz VYBORG (ADD)

RUS FB 160.2 MHz VYBORG (ADD): score 72 (A, Investigate now); 2 Finnish target(s); top finding against 158.825-160.425 MHz | MOBILE | Government; confidence 92%; deadline 2026-11-13.

```
RUS FB 160.2 MHz VYBORG (ADD) vs 158.825-160.425 MHz | MOBILE | Government.
Score 72/100, priority A (Investigate now): relevance 0.90 x (0.65 x severity 0.70 + 0.35 x urgency 1.00); confidence 92%.
Relevance (multiplied):
- freq_overlap = 1.00: co-frequency: 100% of the notified emission falls in 158.825-160.425 MHz
- geography = 0.90: 28 km from Finnish territory over a land path (effective 28 km -> 0.90); non-directional antenna or azimuth not given (x1.00)
- action = 1.00: notice action ADD
Severity (weighted):
- field_strength_margin = 0.50 (w=0.40) [indicative] [input missing, neutral value used]: free-space upper bound 65.1 dB(uV/m) exceeds the trigger 12.0 dB(uV/m) (margin +53.1 dB); a P.1546 calculation is needed to decide
- interference_potential = 1.00 (w=0.20): e.r.p. 17.0 dBW with antenna 60 m above ground: potential index 20.0 dBW (height term 10log10(h/30 m))
- finnish_sensitivity = 1.00 (w=0.25): Finnish use 'MOBILE' / 'Government' rated 1.00: Public safety, government and defence networks
- protected_station = 0.30 (w=0.15): nearest co-frequency Finnish station of special interest: Kotka VHF base (FI-0001) at 102 km; its antenna looks away (off-axis 46 deg)
Urgency (weighted):
- novelty = 1.00 (w=0.40): not present in the previous IFIC
- provision = 1.00 (w=0.35): agreement sought under No. 9.21: Finland must comment within the 4-month window or is deemed to agree (ends 2026-11-13)
- framework = 1.00 (w=0.25): ECC/ERC Rec. T/R 25-08 gives a quantitative coordination trigger for 108-380 MHz
Deadline for comments/agreement: 2026-11-13.
Missing inputs: field_strength_margin.
Calculated values are indicative; assumptions are listed with the evidence.
```

Evidence:

- [filing] t_freq_assgn / t_bdwdth_cde: 160.2 MHz, 12.5 kHz
- [finnish_table] M4 Taajuusjakotaulukko ID 2350: 158.825-160.425 MHz | MOBILE | Government
- [geometry] distance_to_finland_km: site (60.7100, 28.7500) -> nearest Finnish territory (60.8682, 28.3589): 27.6 km, path land (sea 0%)
- [filing] t_ant_dir / t_azm_max_e / t_bmwdth: ND / unknown / unknown
- [filing] t_action: ADD
- [calculation] free-space (upper bound): E = 65.1 dB(uV/m) at the nearest Finnish point (27.6 km, land path), e.r.p. 17.0 dBW
- [regulation] ECC/ERC Recommendation T/R 25-08, edition 6 June 2025 (https://docdb.cept.org/download/4789), Annex 1 section A1.2.3; values unchanged since the 28 September 2018 edition: trigger 12.0 dB(uV/m) in 108-380 MHz (base 12 + bandwidth correction 0.0 dB); Land mobile systems 29.7-470 MHz. Indicative coordination thresholds: co-channel, 50 % of locations, 10 % of time, 10 m receiving antenna height, reference bandwidth 25 kHz, at the border line.
- [calculation] assumption: free-space propagation: an upper bound, not a prediction
- [calculation] assumption: path type land ignored
- [filing] t_pwr_dbw / t_hgt_agl: 17.0 dBW e.r.p. / 60 m
- [asset] special-interest.xlsx row 2: Kotka VHF base 160.2 MHz +/- 6.25 kHz at (60.4700, 26.9500)
- [history] ific diff: new
- [filing] t_fragment / t_prov: Req_agrt / RR9.21
- [regulation] ECC/ERC Recommendation T/R 25-08, edition 6 June 2025 (https://docdb.cept.org/download/4789), Annex 1 section A1.2.3; values unchanged since the 28 September 2018 edition: 108-380 MHz

## 3. EST FB 453.5 MHz TALLINN (ADD)

EST FB 453.5 MHz TALLINN (ADD): score 63 (B, Review); 2 Finnish target(s); top finding against 452.425-456.925 MHz | MOBILE | Digital broadband 450 mobile network; confidence 92%.

```
EST FB 453.5 MHz TALLINN (ADD) vs 452.425-456.925 MHz | MOBILE | Digital broadband 450 mobile network.
Score 63/100, priority B (Review): relevance 0.90 x (0.65 x severity 0.61 + 0.35 x urgency 0.86); confidence 92%.
Relevance (multiplied):
- freq_overlap = 1.00: co-frequency: 100% of the notified emission falls in 452.425-456.925 MHz
- geography = 0.90: 67 km from Finnish territory over a sea path (effective 37 km -> 0.90); antenna azimuth 10 deg points towards Finland (bearing 345 deg, off-axis 25 deg) (x1.00)
- action = 1.00: notice action ADD
Severity (weighted):
- field_strength_margin = 0.50 (w=0.40) [indicative] [input missing, neutral value used]: free-space upper bound 60.4 dB(uV/m) exceeds the trigger 20.0 dB(uV/m) (margin +40.4 dB); a P.1546 calculation is needed to decide
- interference_potential = 1.00 (w=0.20): e.r.p. 20.0 dBW with antenna 90 m above ground: potential index 24.8 dBW (height term 10log10(h/30 m))
- finnish_sensitivity = 0.85 (w=0.25): Finnish use 'MOBILE' / 'Digital broadband 450 mobile network' rated 0.85: Public mobile networks (IMT)
- protected_station = 0.00 (w=0.15): nearest co-frequency Finnish station of special interest: Lappeenranta PMR (FI-0002) at 262 km
Urgency (weighted):
- novelty = 1.00 (w=0.40): not present in the previous IFIC
- provision = 0.60 (w=0.35): notification for recording in the MIFR under No. 11.2; objections possible through the Article 11 examination
- framework = 1.00 (w=0.25): ECC/ERC Rec. T/R 25-08 gives a quantitative coordination trigger for 400-470 MHz
Missing inputs: field_strength_margin.
Calculated values are indicative; assumptions are listed with the evidence.
```

Evidence:

- [filing] t_freq_assgn / t_bdwdth_cde: 453.5 MHz, 25.0 kHz
- [finnish_table] M4 Taajuusjakotaulukko ID 2990,2992,2994,2996,2998: 452.425-456.925 MHz | MOBILE | Digital broadband 450 mobile network
- [geometry] distance_to_finland_km: site (59.4400, 24.7500) -> nearest Finnish territory (60.0213, 24.4456): 66.9 km, path sea (sea 90%)
- [filing] t_ant_dir / t_azm_max_e / t_bmwdth: D / 10 / 60
- [filing] t_action: ADD
- [calculation] free-space (upper bound): E = 60.4 dB(uV/m) at the nearest Finnish point (66.9 km, sea path), e.r.p. 20.0 dBW
- [regulation] ECC/ERC Recommendation T/R 25-08, edition 6 June 2025 (https://docdb.cept.org/download/4789), Annex 1 section A1.2.3; values unchanged since the 28 September 2018 edition: trigger 20.0 dB(uV/m) in 400-470 MHz (base 20 + bandwidth correction 0.0 dB); Land mobile systems 29.7-470 MHz. Indicative coordination thresholds: co-channel, 50 % of locations, 10 % of time, 10 m receiving antenna height, reference bandwidth 25 kHz, at the border line.
- [calculation] assumption: free-space propagation: an upper bound, not a prediction
- [calculation] assumption: path type sea ignored
- [filing] t_pwr_dbw / t_hgt_agl: 20.0 dBW e.r.p. / 90 m
- [asset] special-interest.xlsx row 3: Lappeenranta PMR 453.5 MHz +/- 12.5 kHz at (61.0600, 28.1900)
- [history] ific diff: new
- [filing] t_fragment / t_prov: NTFD_RR / RR11.2
- [regulation] ECC/ERC Recommendation T/R 25-08, edition 6 June 2025 (https://docdb.cept.org/download/4789), Annex 1 section A1.2.3; values unchanged since the 28 September 2018 edition: 400-470 MHz

## 4. NOR FB 79.5 MHz KIRKENES (ADD)

NOR FB 79.5 MHz KIRKENES (ADD): score 52 (B, Review); 1 Finnish target(s); top finding against 78.1-80 MHz | LAND MOBILE | Radiotelephony for energy suppliers; confidence 92%.

```
NOR FB 79.5 MHz KIRKENES (ADD) vs 78.1-80 MHz | LAND MOBILE | Radiotelephony for energy suppliers.
Score 52/100, priority B (Review): relevance 0.90 x (0.65 x severity 0.43 + 0.35 x urgency 0.86); confidence 92%.
Relevance (multiplied):
- freq_overlap = 1.00: co-frequency: 100% of the notified emission falls in 78.1-80 MHz
- geography = 0.90: 35 km from Finnish territory over a land path (effective 35 km -> 0.90); non-directional antenna or azimuth not given (x1.00)
- action = 1.00: notice action ADD
Severity (weighted):
- field_strength_margin = 0.50 (w=0.40) [indicative] [input missing, neutral value used]: free-space upper bound 56.0 dB(uV/m) exceeds the trigger 6.0 dB(uV/m) (margin +50.0 dB); a P.1546 calculation is needed to decide
- interference_potential = 0.40 (w=0.20): e.r.p. 10.0 dBW with antenna 30 m above ground: potential index 10.0 dBW (height term 10log10(h/30 m))
- finnish_sensitivity = 0.60 (w=0.25): Finnish use 'LAND MOBILE' / 'Radiotelephony for energy suppliers' rated 0.60: Fixed links, PMR, maritime, broadcasting, radars
- protected_station = 0.00 (w=0.15): no Finnish station of special interest shares the frequency
Urgency (weighted):
- novelty = 1.00 (w=0.40): not present in the previous IFIC
- provision = 0.60 (w=0.35): notification for recording in the MIFR under No. 11.2; objections possible through the Article 11 examination
- framework = 1.00 (w=0.25): ECC/ERC Rec. T/R 25-08 gives a quantitative coordination trigger for 47-108 MHz
Missing inputs: field_strength_margin.
Calculated values are indicative; assumptions are listed with the evidence.
```

Evidence:

- [filing] t_freq_assgn / t_bdwdth_cde: 79.5 MHz, 20.0 kHz
- [finnish_table] M4 Taajuusjakotaulukko ID 1916: 78.1-80 MHz | LAND MOBILE | Radiotelephony for energy suppliers
- [geometry] distance_to_finland_km: site (69.7300, 30.0500) -> nearest Finnish territory (69.6293, 29.1823): 35.3 km, path land (sea 2%)
- [filing] t_ant_dir / t_azm_max_e / t_bmwdth: ND / unknown / unknown
- [filing] t_action: ADD
- [calculation] free-space (upper bound): E = 56.0 dB(uV/m) at the nearest Finnish point (35.3 km, land path), e.r.p. 10.0 dBW
- [regulation] ECC/ERC Recommendation T/R 25-08, edition 6 June 2025 (https://docdb.cept.org/download/4789), Annex 1 section A1.2.3; values unchanged since the 28 September 2018 edition: trigger 6.0 dB(uV/m) in 47-108 MHz (base 6 + bandwidth correction 0.0 dB); Land mobile systems 29.7-470 MHz. Indicative coordination thresholds: co-channel, 50 % of locations, 10 % of time, 10 m receiving antenna height, reference bandwidth 25 kHz, at the border line.
- [calculation] assumption: free-space propagation: an upper bound, not a prediction
- [calculation] assumption: path type land ignored
- [filing] t_pwr_dbw / t_hgt_agl: 10.0 dBW e.r.p. / 30 m
- [history] ific diff: new
- [filing] t_fragment / t_prov: NTFD_RR / RR11.2
- [regulation] ECC/ERC Recommendation T/R 25-08, edition 6 June 2025 (https://docdb.cept.org/download/4789), Annex 1 section A1.2.3; values unchanged since the 28 September 2018 edition: 47-108 MHz

## 5. RUS FB 390.5 MHz SANKT-PETERBURG (ADD)

RUS FB 390.5 MHz SANKT-PETERBURG (ADD): score 40 (C, Monitor); 2 Finnish target(s); top finding against 390.012-394.988 MHz | MOBILE | Emergency services network (VIRVE); confidence 92%.

```
RUS FB 390.5 MHz SANKT-PETERBURG (ADD) vs 390.012-394.988 MHz | MOBILE | Emergency services network (VIRVE).
Score 40/100, priority C (Monitor): relevance 0.55 x (0.65 x severity 0.65 + 0.35 x urgency 0.86); confidence 92%.
Relevance (multiplied):
- freq_overlap = 1.00: co-frequency: 100% of the notified emission falls in 390.012-394.988 MHz
- geography = 0.55: 151 km from Finnish territory over a land path (effective 151 km -> 0.55); antenna azimuth 300 deg points towards Finland (bearing 321 deg, off-axis 21 deg) (x1.00)
- action = 1.00: notice action ADD
Severity (weighted):
- field_strength_margin = 0.50 (w=0.40) [indicative] [input missing, neutral value used]: free-space upper bound 53.3 dB(uV/m) exceeds the trigger 18.0 dB(uV/m) (margin +35.3 dB); a P.1546 calculation is needed to decide
- interference_potential = 1.00 (w=0.20): e.r.p. 20.0 dBW with antenna 100 m above ground: potential index 25.2 dBW (height term 10log10(h/30 m))
- finnish_sensitivity = 1.00 (w=0.25): Finnish use 'MOBILE' / 'Emergency services network (VIRVE)' rated 1.00: Public safety, government and defence networks
- protected_station = 0.00 (w=0.15): nearest co-frequency Finnish station of special interest: Helsinki TETRA site (FI-0003) at 297 km
Urgency (weighted):
- novelty = 1.00 (w=0.40): not present in the previous IFIC
- provision = 0.60 (w=0.35): notification for recording in the MIFR under No. 11.2; objections possible through the Article 11 examination
- framework = 1.00 (w=0.25): ECC/ERC Rec. T/R 25-08 gives a quantitative coordination trigger for 380-400 MHz
Missing inputs: field_strength_margin.
Calculated values are indicative; assumptions are listed with the evidence.
```

Evidence:

- [filing] t_freq_assgn / t_bdwdth_cde: 390.5 MHz, 25.0 kHz
- [finnish_table] M4 Taajuusjakotaulukko ID 2619,2621,2623,2625,2627,2629 (+1 more): 390.012-394.988 MHz | MOBILE | Emergency services network (VIRVE)
- [geometry] distance_to_finland_km: site (59.9300, 30.3300) -> nearest Finnish territory (60.9602, 28.5682): 150.9 km, path land (sea 0%)
- [filing] t_ant_dir / t_azm_max_e / t_bmwdth: D / 300 / 70
- [filing] t_action: ADD
- [calculation] free-space (upper bound): E = 53.3 dB(uV/m) at the nearest Finnish point (150.9 km, land path), e.r.p. 20.0 dBW
- [regulation] ECC/ERC Recommendation T/R 25-08, edition 6 June 2025 (https://docdb.cept.org/download/4789), Annex 1 section A1.2.3; values unchanged since the 28 September 2018 edition: trigger 18.0 dB(uV/m) in 380-400 MHz (base 18 + bandwidth correction 0.0 dB); Land mobile systems 29.7-470 MHz. Indicative coordination thresholds: co-channel, 50 % of locations, 10 % of time, 10 m receiving antenna height, reference bandwidth 25 kHz, at the border line.
- [calculation] assumption: free-space propagation: an upper bound, not a prediction
- [calculation] assumption: path type land ignored
- [filing] t_pwr_dbw / t_hgt_agl: 20.0 dBW e.r.p. / 100 m
- [asset] special-interest.xlsx row 4: Helsinki TETRA site 390.5 MHz +/- 12.5 kHz at (60.2000, 25.0000)
- [history] ific diff: new
- [filing] t_fragment / t_prov: NTFD_RR / RR11.2
- [regulation] ECC/ERC Recommendation T/R 25-08, edition 6 June 2025 (https://docdb.cept.org/download/4789), Annex 1 section A1.2.3; values unchanged since the 28 September 2018 edition: 380-400 MHz

## 6. RUS FB 2602.5 MHz SESTRORETSK (ADD)

RUS FB 2602.5 MHz SESTRORETSK (ADD): score 36 (C, Monitor); 1 Finnish target(s); top finding against 2570-2620 MHz | MOBILE | Terrestrial systems capable of providing electronic communications services; confidence 92%.

```
RUS FB 2602.5 MHz SESTRORETSK (ADD) vs 2570-2620 MHz | MOBILE | Terrestrial systems capable of providing electronic communications services.
Score 36/100, priority C (Monitor): relevance 0.55 x (0.65 x severity 0.61 + 0.35 x urgency 0.73); confidence 92%.
Relevance (multiplied):
- freq_overlap = 1.00: co-frequency: 100% of the notified emission falls in 2570-2620 MHz
- geography = 0.55: 140 km from Finnish territory over a land path (effective 140 km -> 0.55); antenna azimuth 280 deg points towards Finland (bearing 319 deg, off-axis 39 deg) (x1.00)
- action = 1.00: notice action ADD
Severity (weighted):
- field_strength_margin = 0.50 (w=0.40) [input missing, neutral value used]: 2602.5 MHz is outside the T/R 25-08 range (29.7-470 MHz); no coordination trigger loaded for this band
- interference_potential = 1.00 (w=0.20): e.r.p. 30.0 dBW with antenna 45 m above ground: potential index 31.8 dBW (height term 10log10(h/30 m))
- finnish_sensitivity = 0.85 (w=0.25): Finnish use 'MOBILE' / 'Terrestrial systems capable of providing electronic communications services' rated 0.85: Public mobile networks (IMT)
- protected_station = 0.00 (w=0.15): no Finnish station of special interest shares the frequency
Urgency (weighted):
- novelty = 1.00 (w=0.40): not present in the previous IFIC
- provision = 0.60 (w=0.35): notification for recording in the MIFR under No. 11.2; objections possible through the Article 11 examination
- framework = 0.50 (w=0.25): no quantitative trigger loaded for this band; only the general RR Article 9/11 framework applies
Missing inputs: field_strength_margin.
```

Evidence:

- [filing] t_freq_assgn / t_bdwdth_cde: 2602.5 MHz, 20000.0 kHz
- [finnish_table] M4 Taajuusjakotaulukko ID 4015,4017,4019,4021,4023,4025 (+3 more): 2570-2620 MHz | MOBILE | Terrestrial systems capable of providing electronic communications services
- [geometry] distance_to_finland_km: site (60.0500, 30.3000) -> nearest Finnish territory (60.9823, 28.6173): 139.5 km, path land (sea 0%)
- [filing] t_ant_dir / t_azm_max_e / t_bmwdth: D / 280 / 65
- [filing] t_action: ADD
- [filing] t_pwr_dbw / t_hgt_agl: 30.0 dBW e.r.p. / 45 m
- [history] ific diff: new
- [filing] t_fragment / t_prov: NTFD_RR / RR11.2

## 7. LVA FB 415 MHz RIGA (ADD)

LVA FB 415 MHz RIGA (ADD): score 23 (C, Monitor); 1 Finnish target(s); top finding against 414.012-416.337 MHz | MOBILE | TETRA; confidence 92%.

```
LVA FB 415 MHz RIGA (ADD) vs 414.012-416.337 MHz | MOBILE | TETRA.
Score 23/100, priority C (Monitor): relevance 0.35 x (0.65 x severity 0.55 + 0.35 x urgency 0.86); confidence 92%.
Relevance (multiplied):
- freq_overlap = 1.00: co-frequency: 100% of the notified emission falls in 414.012-416.337 MHz
- geography = 0.35: 325 km from Finnish territory over a sea path (effective 171 km -> 0.35); non-directional antenna or azimuth not given (x1.00)
- action = 1.00: notice action ADD
Severity (weighted):
- field_strength_margin = 0.50 (w=0.40) [indicative] [input missing, neutral value used]: free-space upper bound 46.7 dB(uV/m) exceeds the trigger 20.0 dB(uV/m) (margin +26.7 dB); a P.1546 calculation is needed to decide
- interference_potential = 1.00 (w=0.20): e.r.p. 20.0 dBW with antenna 80 m above ground: potential index 24.3 dBW (height term 10log10(h/30 m))
- finnish_sensitivity = 0.60 (w=0.25): Finnish use 'MOBILE' / 'TETRA' rated 0.60: Fixed links, PMR, maritime, broadcasting, radars
- protected_station = 0.00 (w=0.15): no Finnish station of special interest shares the frequency
Urgency (weighted):
- novelty = 1.00 (w=0.40): not present in the previous IFIC
- provision = 0.60 (w=0.35): notification for recording in the MIFR under No. 11.2; objections possible through the Article 11 examination
- framework = 1.00 (w=0.25): ECC/ERC Rec. T/R 25-08 gives a quantitative coordination trigger for 400-470 MHz
Missing inputs: field_strength_margin.
Calculated values are indicative; assumptions are listed with the evidence.
```

Evidence:

- [filing] t_freq_assgn / t_bdwdth_cde: 415 MHz, 25.0 kHz
- [finnish_table] M4 Taajuusjakotaulukko ID 2726,2729,2732,2735: 414.012-416.337 MHz | MOBILE | TETRA
- [geometry] distance_to_finland_km: site (56.9500, 24.1000) -> nearest Finnish territory (59.8160, 23.0213): 325.3 km, path sea (sea 95%)
- [filing] t_ant_dir / t_azm_max_e / t_bmwdth: ND / unknown / unknown
- [filing] t_action: ADD
- [calculation] free-space (upper bound): E = 46.7 dB(uV/m) at the nearest Finnish point (325.3 km, sea path), e.r.p. 20.0 dBW
- [regulation] ECC/ERC Recommendation T/R 25-08, edition 6 June 2025 (https://docdb.cept.org/download/4789), Annex 1 section A1.2.3; values unchanged since the 28 September 2018 edition: trigger 20.0 dB(uV/m) in 400-470 MHz (base 20 + bandwidth correction 0.0 dB); Land mobile systems 29.7-470 MHz. Indicative coordination thresholds: co-channel, 50 % of locations, 10 % of time, 10 m receiving antenna height, reference bandwidth 25 kHz, at the border line.
- [calculation] assumption: free-space propagation: an upper bound, not a prediction
- [calculation] assumption: path type sea ignored
- [filing] t_pwr_dbw / t_hgt_agl: 20.0 dBW e.r.p. / 80 m
- [history] ific diff: new
- [filing] t_fragment / t_prov: NTFD_RR / RR11.2
- [regulation] ECC/ERC Recommendation T/R 25-08, edition 6 June 2025 (https://docdb.cept.org/download/4789), Annex 1 section A1.2.3; values unchanged since the 28 September 2018 edition: 400-470 MHz

## 8. RUS FB 169.5 MHz PETROZAVODSK (ADD)

RUS FB 169.5 MHz PETROZAVODSK (ADD): score 17 (D, No action); 0 Finnish target(s); top finding against 169.488-169.588 MHz | MOBILE | (SRD) Short range devices; confidence 92%.

```
RUS FB 169.5 MHz PETROZAVODSK (ADD) vs 169.488-169.588 MHz | MOBILE | (SRD) Short range devices.
Score 17/100, priority D (No action): relevance 0.35 x (0.65 x severity 0.49 + 0.35 x urgency 0.50); confidence 92%.
Relevance (multiplied):
- freq_overlap = 1.00: co-frequency: 100% of the notified emission falls in 169.488-169.588 MHz
- geography = 0.35: 183 km from Finnish territory over a land path (effective 183 km -> 0.35); non-directional antenna or azimuth not given (x1.00)
- action = 1.00: notice action ADD
Severity (weighted):
- field_strength_margin = 0.50 (w=0.40) [indicative] [input missing, neutral value used]: free-space upper bound 45.6 dB(uV/m) exceeds the trigger 12.0 dB(uV/m) (margin +33.6 dB); a P.1546 calculation is needed to decide
- interference_potential = 0.70 (w=0.20): e.r.p. 14.0 dBW with antenna 40 m above ground: potential index 15.2 dBW (height term 10log10(h/30 m))
- finnish_sensitivity = 0.60 (w=0.25): Finnish use 'MOBILE' / '(SRD) Short range devices' rated 0.60: Fixed links, PMR, maritime, broadcasting, radars
- protected_station = 0.00 (w=0.15): no Finnish station of special interest shares the frequency
Urgency (weighted):
- novelty = 0.10 (w=0.40): unchanged re-publication
- provision = 0.60 (w=0.35): notification for recording in the MIFR under No. 11.2; objections possible through the Article 11 examination
- framework = 1.00 (w=0.25): ECC/ERC Rec. T/R 25-08 gives a quantitative coordination trigger for 108-380 MHz
Missing inputs: field_strength_margin.
Calculated values are indicative; assumptions are listed with the evidence.
```

Evidence:

- [filing] t_freq_assgn / t_bdwdth_cde: 169.5 MHz, 12.5 kHz
- [finnish_table] M4 Taajuusjakotaulukko ID 2483,2484,2485,2486,2487,2488 (+3 more): 169.488-169.588 MHz | MOBILE | (SRD) Short range devices
- [geometry] distance_to_finland_km: site (61.7800, 34.3500) -> nearest Finnish territory (62.5651, 31.2825): 183.4 km, path land (sea 0%)
- [filing] t_ant_dir / t_azm_max_e / t_bmwdth: ND / unknown / unknown
- [filing] t_action: ADD
- [calculation] free-space (upper bound): E = 45.6 dB(uV/m) at the nearest Finnish point (183.4 km, land path), e.r.p. 14.0 dBW
- [regulation] ECC/ERC Recommendation T/R 25-08, edition 6 June 2025 (https://docdb.cept.org/download/4789), Annex 1 section A1.2.3; values unchanged since the 28 September 2018 edition: trigger 12.0 dB(uV/m) in 108-380 MHz (base 12 + bandwidth correction 0.0 dB); Land mobile systems 29.7-470 MHz. Indicative coordination thresholds: co-channel, 50 % of locations, 10 % of time, 10 m receiving antenna height, reference bandwidth 25 kHz, at the border line.
- [calculation] assumption: free-space propagation: an upper bound, not a prediction
- [calculation] assumption: path type land ignored
- [filing] t_pwr_dbw / t_hgt_agl: 14.0 dBW e.r.p. / 40 m
- [history] ific diff: unchanged
- [filing] t_fragment / t_prov: NTFD_RR / RR11.2
- [regulation] ECC/ERC Recommendation T/R 25-08, edition 6 June 2025 (https://docdb.cept.org/download/4789), Annex 1 section A1.2.3; values unchanged since the 28 September 2018 edition: 108-380 MHz

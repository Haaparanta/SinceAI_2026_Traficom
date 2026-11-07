# Submission text (Since AI 2026 platform)

Paste-ready text for the four fields of the Traficom challenge submission form. Deadline Sunday 8 November, 10:00 Helsinki time. Every number comes from `README.md` and `results/README.md` on Sat 7 Nov 2026; recheck them if the results are regenerated.

## PROJECT NAME

Filing Radar

## TAGLINE (max 140 characters)

Turns an ITU BR IFIC issue into a ranked, cited list of filings that may affect Finland, with every calculation shown and a letter drafted.

## ABOUT THE PROJECT (max 5000 characters)

**The problem.** Every two weeks the ITU publishes a BR IFIC: hundreds of satellite and terrestrial frequency filings from administrations around the world. A few of them can interfere with radio use in Finland. Today a Traficom specialist reads through the issue by hand, decides which notices matter, checks the technical parameters and writes to the notifying administration. The space issue 3074 alone holds 199 notices and 25 127 frequency groups; the terrestrial issue 3076 holds 4 057 notices. The brief asks for AI-assisted support that finds the relevant filings, explains why, and prepares the response, with the expert in control of every decision.

**Our solution.** Filing Radar takes an IFIC issue number and produces a ranked, cited, expert-reviewable list of the notices that may affect Finland. Each finding shows its evidence (the ITU row, the Finnish allocation table row, the regulation), its geometry (can the satellite or station reach Finland at all), and an indicative technical check with every input, the formula, the limit and the margin on screen. A reviewer approves, investigates or dismisses a finding with a note into a hash-chained audit log, can ask for a plain-language explanation, and can turn the finding into a letter draft to the notifying administration. Nothing is ever sent. The tool suggests; a person decides.

On Space IFIC 3074 it flags 135 of 199 notices: 18 where the Radiocommunication Bureau itself names Finland as affected, GSO downlinks whose worst-case power flux-density exceeds the RR Article 21 limit (CHINASAT-H-60.5E by 6.3 dB), non-GSO constellations whose single-satellite pfd over Finland exceeds the limit (USASAT-NGSO-8F by 22.9 dB), and foreign networks with earth stations in Tampere and Muonio. The same engine runs the terrestrial side quest on IFIC 3076: new Russian VHF base stations at Kostomuksha, Lyaskelya and Vyborg are 8 to 13 dB above the ECC T/R 25-08 coordination trigger at the Finnish border, computed with ITU-R P.1546-6. The results are two CSV and JSON files, one row per notice, every notice included with its reason, so nothing is dropped silently. The 870 special-interest stations from the challenge data are matched to every group that overlaps their protected channel and can reach them.

**How we built it.** The ITU Access databases are converted with mdbtools into DuckDB, typed from the ITU schema and row-count checked. A single schema map is the only place where ITU table and column names live, so any space or terrestrial issue, past or future, goes through the same one command. Screening, geometry, pfd and field strength are plain Python with 427 tests, including the ITU validation suite for P.1546 (52 reference cases reproduced to 0.0 dB). The limits are transcribed from RR 2024 Table 21-4 and T/R 25-08 into CSV files with a source and page per row. Two full runs produce byte-identical results files, and a checker re-opens all 6 001 citations of both issues and fails on any mismatch. Claude (claude-opus-5-5) writes the explanations and letter drafts; it sees only the finding and its evidence, must cite evidence IDs of that finding, and a validator rejects any text that introduces a number not present in the inputs. It never sets a concern level and never computes anything. The screen is React with plain SVG maps and spectrum strips, driven by Playwright end-to-end tests, and runs offline from a committed cache. The whole thing is one container on Cloud Run in Finland, redeployed on every merge.

**Challenges.** The ITU schema documentation does not match the files: the same direction flag means space-to-Earth for a satellite notice and Earth-to-space for an earth station notice, the terrestrial extract is a change set that points into the Master Register, and the IFIC carries no pfd masks or gain contours, so the pfd check is a stated upper bound rather than a verdict. One Indian filing declares a power density that its own peak power contradicts by 146 dB; we keep it as filed and flag it. We never got a partner slot, so every rule we could not confirm is labelled as a hypothesis in the code, the results and the screen, with the reason written down, and one constant changes when the answer arrives. The hardest part was discipline: no number on screen that is not a traced calculation, no finding without evidence, no model output that is not checked against the evidence it cites.

**What comes next.** Confirm the relevance rules, pfd method and T/R 25-08 parameters with Traficom's specialists and relabel the confirmed methods. Add epfd for non-GSO constellations from the pfd masks when the partner can supply them, the Finnish satellite filings as a second protection target, and the previous issue diff for space as for terrestrial. Then run it every two weeks on the new issue and measure how much reading time the specialist saves.

## BUILT WITH (comma-separated, first five on the vote card)

Python, DuckDB, FastAPI, React, Claude, mdbtools, Pydantic, TypeScript, Vite, Tailwind CSS, ITU-R P.1546 (Py1546), Playwright, pytest, Docker, Google Cloud Run, Remotion, ElevenLabs

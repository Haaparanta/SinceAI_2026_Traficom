# SinceAI_2026_Traficom

## Hackathon Challenge

Space is getting more crowded, and the invisible radio spectrum connecting satellites, infrastructure and everyday services is a finite shared resource. A new transmission planned far away can raise technical questions for systems operating in Finland. Protecting those services requires experts to interpret international filings, national rules and large amounts of complicated information.

Finland's Transport and Communications Agency Traficom invites you to explore an AI-assisted approach to this high-stakes analytical work. Could intelligent software help specialists discover relevant filings, understand their implications, connect evidence across sources and identify situations worth investigating?

This is a fascinating intersection of space technology, regulatory intelligence, information extraction, technical reasoning and explainable AI. Build for a world where critical infrastructure increasingly depends on clear, reliable coordination across borders and orbits.

The most valuable ideas will make complex analysis more transparent and efficient while keeping human experts firmly in control of consequential decisions.

## Datasets and APIs Provided

> [!NOTE]
> Datasets marked **(mandatory)** must be used to complete the challenge successfully. All other data may be used, whether listed here or from other sources.

### ITU Space IFIC (mandatory)

- Source: https://www.itu.int/en/ITU-R/space/brific/Pages/default.aspx
- Downloadable Space IFIC: https://www.itu.int/sns/wic/demowic.html
- All existing and forthcoming IFICs must be able to be evaluated.
- **Space IFIC no. 3074** must be analysed and possible concerns raised from it. It is used to evaluate accuracy, and its results must be submitted separately.

### ITU Terrestrial IFIC (mandatory)

- Source: https://www.itu.int/en/ITU-R/terrestrial/brific/Pages/default.aspx
- Downloadable Terrestrial IFIC extract: https://www.itu.int/en/ITU-R/terrestrial/brific/Pages/default.aspx
- All existing and forthcoming IFICs must be able to be evaluated.
- **Terrestrial IFIC no. 3076** must be analysed and possible concerns raised from it. It is used to evaluate accuracy, and its results must be submitted separately.

### Regulation 4, "M4" (mandatory)

Finnish Radio Frequency Regulation, including the table of frequencies in Finland.

- Regulation: https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2026/3
- Radio frequency table API (Swagger): https://opendata.traficom.fi/swagger/ui/index#/Taajuusjakotaulukko
- Radio frequency table API endpoint: https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko

## Team plan

The engineering plan, partner questions and agent context live in [`pm_pack/`](pm_pack/README.md). Start with `scripts/fetch_data.sh` (the graded issues, M4 and the Finnish frequency table; `scripts/download_data.sh` fetches every 2026 IFIC issue and the optional sources, see [`data/SOURCES.md`](data/SOURCES.md)), then `python3 scripts/inspect_mdb.py data/raw/ific3074/*.mdb`. `AGENTS.md`, `CLAUDE.md` and `.cursorrules` point at the master context for coding agents.

## Scoring

The `scoring/` folder holds a deterministic, stdlib-only scoring model that ranks IFIC notices by relevance to Finland: `score = 100 x relevance x (0.65 x severity + 0.35 x urgency)`, with every factor carrying its evidence. See [scoring/README.md](scoring/README.md) for usage and [scoring/DESIGN.md](scoring/DESIGN.md) for the reasoning, the factor tables and the calibration plan.

```bash
python -m unittest discover -s scoring/tests -t .
```

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

## Project Documents

Planning material lives in `pm_pack/`. Docs 01–06 were drafted from this README before the official brief arrived; doc 07 is based on the official brief and on verified ITU, CEPT and Traficom sources and takes precedence where they differ.

- [01 Partner briefing questions](pm_pack/01_Partner_Briefing_Questions.md)
- [02 Requirements and PRD](pm_pack/02_Requirements_Management_PRD.md)
- [03 Strategic SWOT and competitor matrix](pm_pack/03_Strategic_SWOT_and_Competitor_Matrix.md)
- [04 Risk register](pm_pack/04_Risk_Register_and_Mitigation.md)
- [05 Execution roadmap](pm_pack/05_Execution_Roadmap_and_Milestones.md)
- [06 Agents master context](pm_pack/06_AGENTS_Master_Context.md)
- [07 Solution catalogue: solutions, what each needs, what is fast enough, logic-based components](pm_pack/07_Solution_Catalogue.md)
- [Official challenge brief (PDF)](Since_AI_Traficom_Challenge_Brief_FINAL_04112026.pdf)

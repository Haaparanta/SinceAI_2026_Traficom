# Filing Radar: the one screen

React 19, Vite, TypeScript and Tailwind CSS v4 with the Girlypop v2 tokens from `../design/girlypop.css`
(rules in `../design/girlypop-theme.md`). Step D1 of `pm_pack/08_Build_Plan_Step_by_Step.md`.

```bash
make api          # FastAPI on http://127.0.0.1:8000 (reads data/cache/*.json)
make frontend     # this screen on http://127.0.0.1:5173, /api proxied to the API
make cache        # rebuild data/cache from a live pipeline run (needs data/derived)
make frontend-build
make e2e                      # Playwright: own API (8100) and dev server (5180), throwaway decision log
make screenshots STEP=d3      # PR screenshots into docs/screenshots/d3/
```

| Part | File |
|---|---|
| Issue selector, proof metrics, export, layout | `src/App.tsx` |
| Ranked findings with concern filter and search | `src/components/RankedList.tsx` |
| Spectrum tab: the lead group against the Finnish table rows | `src/components/SpectrumView.tsx` |
| Map tab: reference points and elevations, or the station and its path to the border | `src/components/MapView.tsx` |
| Calculation tab: inputs with evidence links, formula, result, limit, margin | `src/components/CalcTraceView.tsx` |
| Finding card: concern, reason, every evidence item, score factors | `src/components/FindingCard.tsx` |
| Decision: approve, investigate, dismiss with a required note; the finding's history | `src/components/DecisionPanel.tsx` |
| Audit log tab: every decision of the issue and the server's hash-chain check | `src/components/AuditLogView.tsx` |
| Contract types (mirror `backend/radar/models.py`) | `src/types.ts` |

Every number on screen comes from the API (findings, `CalcTrace` and counted metrics); nothing is typed into the UI.
Risk badges always carry a text label. The sigil background sits on the page root only.

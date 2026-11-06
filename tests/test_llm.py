"""Step D2 of pm_pack/08: grounded explanation and letter. No network: a stand-in client returns crafted responses."""
from __future__ import annotations

import json
from types import SimpleNamespace as NS

import pytest

from radar.config import settings
from radar.llm import client as C
from radar.llm import drafts as D
from radar.llm import grounding as G

CACHE = settings.data_dir / "cache" / "space_3074.json"
needs_cache = pytest.mark.skipif(not CACHE.exists(), reason="run scripts/build_cache.py")


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)          # LLM cache goes to a temp folder
    monkeypatch.delenv("LLM_DISABLED", raising=False)
    yield


@pytest.fixture(scope="module")
def first():
    b = json.loads(CACHE.read_text())
    f = b["result"]["findings"][0]
    return f, b["context"][f["id"]]


class FakeClient:
    """Mimics client.beta.messages.create and records the request."""
    def __init__(self, payload=None, stop_reason="end_turn", model="claude-opus-5-5"):
        self.payload, self.stop_reason, self.model, self.calls = payload, stop_reason, model, []
        self.beta = NS(messages=NS(create=self._create))

    def _create(self, **kw):
        self.calls.append(kw)
        content = [NS(type="text", text=json.dumps(self.payload))] if self.payload is not None else []
        return NS(stop_reason=self.stop_reason, model=self.model, content=content,
                  stop_details=NS(category="cyber") if self.stop_reason == "refusal" else None,
                  usage=NS(input_tokens=1200, output_tokens=180, iterations=[]))


# ---- grounding --------------------------------------------------------------------------------------------------

def test_numbers_are_normalised():
    assert G.numbers("pfd -107.20 dB, margin 6.30, 18 700 MHz, 3,5 GHz") >= {"107.2", "6.3", "18700", "3.5"}
    assert "3074" in G.numbers("F-3074-0001") and not G.numbers("E-dB")


@needs_cache
def test_validate_accepts_facts_and_rejects_inventions(first):
    f, ctx = first
    data = G.payload(f, ctx, "space", 3074)
    good = G.validate(["The margin is -6.28 dB at 18.7 GHz."], ["E-001"], data)
    assert good.ok
    bad = G.validate(["The margin is 7.5 dB."], ["E-999"], data)
    assert not bad.ok and bad.unknown_ids == ["E-999"] and "7.5" in bad.unsupported_numbers
    assert not G.validate(["No numbers here."], [], data).ok          # citing nothing is not grounded


# ---- the model path ---------------------------------------------------------------------------------------------

@needs_cache
def test_request_shape(first):
    f, ctx = first
    fake = FakeClient({"text": "CHN CHINASAT-H-60.5E exceeds the RR Article 21 limit by 6.3 dB (indicative).",
                       "cited_evidence_ids": ["E-001"]})
    d = D.explain(f, ctx, "space", 3074, client=fake)
    kw = fake.calls[0]
    assert kw["model"] == "claude-opus-5-5" and kw["fallbacks"] == "default" and kw["betas"] == ["server-side-fallback-2026-07-01"]
    assert kw["output_config"]["effort"] == "medium" and kw["output_config"]["format"]["type"] == "json_schema"
    assert kw["output_config"]["format"]["schema"]["additionalProperties"] is False
    assert "temperature" not in kw and "thinking" not in kw
    assert kw["system"][0]["text"] == G.prompt("explain")
    assert json.loads(kw["messages"][0]["content"])["notice_id"] == f["notice_id"]
    assert d.source == "claude-opus-5-5" and d.check.startswith("checked")


@needs_cache
def test_valid_output_is_cached_and_reused(first):
    f, ctx = first
    fake = FakeClient({"text": "Exceeds by 6.3 dB.", "cited_evidence_ids": ["E-001"]})
    D.explain(f, ctx, "space", 3074, client=fake)
    again = D.explain(f, ctx, "space", 3074, client=FakeClient({"text": "different", "cited_evidence_ids": ["E-001"]}))
    assert again.source == "cache: claude-opus-5-5" and again.output.text == "Exceeds by 6.3 dB."


@needs_cache
@pytest.mark.parametrize("payload, reason", [
    ({"text": "Exceeds the limit by 9.9 dB.", "cited_evidence_ids": ["E-001"]}, "numbers not in the evidence: 9.9"),
    ({"text": "Exceeds the limit.", "cited_evidence_ids": ["E-404"]}, "cites ids not in the finding: E-404"),
])
def test_ungrounded_model_text_is_never_shown(first, payload, reason):
    f, ctx = first
    d = D.explain(f, ctx, "space", 3074, client=FakeClient(payload))
    assert d.source == "template" and reason in d.notes[0]
    assert payload["text"] not in d.output.text


@needs_cache
@pytest.mark.parametrize("stop", ["refusal", "max_tokens"])
def test_refusal_or_truncation_falls_back_to_the_template(first, stop):
    f, ctx = first
    d = D.explain(f, ctx, "space", 3074, client=FakeClient(None, stop_reason=stop))
    assert d.source == "template" and "not used" in d.notes[0]


@needs_cache
def test_letter_is_marked_draft_and_addressed_to_the_notifying_administration(first):
    f, ctx = first
    fake = FakeClient({"subject": "BR IFIC 3074, CR/C 6324", "body_markdown": "Finland requests coordination.",
                       "cited_evidence_ids": ["E-001", "E-002"]})
    d = D.letter(f, ctx, "space", 3074, client=fake)
    assert fake.calls[0]["output_config"]["effort"] == "high"
    assert d.output.to_administration == ctx["notice"]["administration"]
    assert d.output.body_markdown.startswith(f"*{D.DRAFT_BANNER}*") and d.output.finding_id == f["id"]


@needs_cache
def test_without_credentials_no_call_is_made_and_the_template_is_grounded(first, monkeypatch):
    f, ctx = first
    monkeypatch.setattr(C, "credentials_present", lambda: False)
    for d in (D.explain(f, ctx, "space", 3074), D.letter(f, ctx, "space", 3074)):
        assert d.source == "template" and d.check.startswith("checked") and "credentials" in d.notes[0]


def test_disabled_switch(monkeypatch):
    monkeypatch.setenv("LLM_DISABLED", "1")
    assert C.status() == {"available": False, "model": settings.llm_model, "reason": "LLM_DISABLED=1"}


@pytest.mark.parametrize("kind, issue", [("space", 3074), ("terrestrial", 3076)])
def test_every_template_is_grounded(kind, issue, monkeypatch):
    path = CACHE.parent / f"{kind}_{issue}.json"
    if not path.exists():
        pytest.skip("run scripts/build_cache.py")
    monkeypatch.setattr(C, "credentials_present", lambda: False)
    b = json.loads(path.read_text())
    flagged = [f for f in b["result"]["findings"] if f["concern"] != "none"]
    assert flagged
    for f in flagged:
        for d in (D.explain(f, b["context"].get(f["id"]), kind, issue), D.letter(f, b["context"].get(f["id"]), kind, issue)):
            assert d.source == "template" and d.check.startswith("checked"), (f["id"], d.check)

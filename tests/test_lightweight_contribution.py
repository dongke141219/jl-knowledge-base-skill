"""The distributed clients keep light records without weakening shared access."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_three_skill_copies_defer_semantic_work_and_keep_exact_consent():
    skills = [ROOT / "skills/jl-knowledge-base-skill/SKILL.md"]
    skills += [ROOT / "plugins" / plugin / "skills/jl-knowledge-base-skill/SKILL.md"
               for plugin in ("codex-jl-knowledge-base-skill", "zcode-jl-knowledge-base-skill")]
    contents = [path.read_text(encoding="utf-8") for path in skills]
    assert len(set(contents)) == 1
    text = contents[0]
    assert 'client_version: "0.8.5"' in text
    assert "at most one sanitized candidate" in text
    assert "Do not perform corpus-wide novelty checks, semantic deduplication" in text
    assert "pending hardware verification, or absent customer feedback" in text
    assert "2026-08-31-v2" in text
    assert 'contribution_consent: "同意"' in text
    assert "Never persist or republish returned fragment text" in text
    assert "Do not decide that silence proves success" in text
    for path in skills:
        contract = (path.parent / "references/gateway-contract.md").read_text(encoding="utf-8")
        workflow = (path.parent / "references/contribution-workflow.md").read_text(encoding="utf-8")
        assert "The client does not prove global novelty" in contract
        assert "Central candidate review handles semantic deduplication" in workflow
        assert "one genuinely new reusable result" not in contract
        assert "exact phrase `同意`" in workflow


def test_gemini_uses_same_light_record_rule_and_restricted_access_boundary():
    text = (ROOT / "GEMINI.md").read_text(encoding="utf-8")
    assert "A small change needs one short record" in text
    assert "Central review handles semantic deduplication" in text
    assert "exact Chinese phrase `同意`" in text
    assert "Never browse, enumerate, export, persist, republish, or reconstruct the private corpus" in text

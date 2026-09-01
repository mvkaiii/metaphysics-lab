from pathlib import Path


def read(path):
    return Path(path).read_text(encoding="utf-8")


def test_ai_workflow_declares_python_coordination_authority():
    text = read("core/AI工作流程.md")
    assert "Python 算 coordination，AI 讀 coordination。" in text
    assert "coordination_relation" in text
    assert "parallel_signals" in text
    assert "legacy_cross_system_relation" in text
    assert "coordination_specificity_cap" in text


def test_core_prompt_prevents_ai_recomputation_and_conflict_rewrite():
    text = read("core/核心提示詞.md")
    assert "coordination metadata" in text
    assert "不得自行重算" in text
    assert "parallel_signals" in text
    assert "legacy relation" in text
    assert "specificity" in text


def test_architecture_keeps_single_prompt_authority_and_coordination_layer():
    text = read("docs/架構說明.md")
    assert "Claim Evidence -> Coordination v2 -> AI interpretation" in text
    assert "不重新計算 coordination" in text
    assert "不得建立第二套 prompt authority" in text

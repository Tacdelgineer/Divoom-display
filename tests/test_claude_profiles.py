import pytest
from models import ClaudeAccountProfile
from claude_usage import mask_account_identifier, get_claude_env_diagnostics


def test_mask_account_identifier():
    assert mask_account_identifier("developer@example.com") == "de***@example.com"
    assert mask_account_identifier("test.user@company.org") == "te***@company.org"
    assert mask_account_identifier("a@b.com") == "a***@b.com"
    assert mask_account_identifier(None) == "UNKNOWN"
    assert mask_account_identifier("") == "UNKNOWN"


def test_env_diagnostics_structure():
    diag = get_claude_env_diagnostics()
    assert "variables" in diag
    assert "active_auth_type" in diag
    assert "precedence" in diag
    # Ensure all audited env vars are checked
    vars_map = diag["variables"]
    for k in [
        "ANTHROPIC_API_KEY",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "ANTHROPIC_BASE_URL",
        "CLAUDE_CODE_USE_BEDROCK",
        "CLAUDE_CODE_USE_VERTEX",
        "CLAUDE_CODE_USE_FOUNDRY",
    ]:
        assert k in vars_map
        assert vars_map[k] in ("PRESENT", "ABSENT")


def test_claude_profile_remaining_semantics():
    prof = ClaudeAccountProfile(
        id="personal",
        user_label="Personal",
        account_identity_masked="no***@gmail.com",
        plan="Claude Pro",
        auth_type="Subscription (OAuth)",
        five_hour_used_pct=3.0,
        five_hour_remaining_pct=97.0,
        weekly_used_pct=38.0,
        weekly_remaining_pct=62.0,
        is_active=True,
    )
    # UI must prioritize remaining percentage
    assert prof.five_hour_remaining_pct == 97.0
    assert prof.weekly_remaining_pct == 62.0
    assert prof.five_hour_remaining_pct + prof.five_hour_used_pct == 100.0


def test_account_mixup_prevention():
    # Verify two isolated profiles have independent identities, directories, and quota values
    p1 = ClaudeAccountProfile(
        id="personal",
        user_label="Personal Account",
        account_identity_masked="pe***@gmail.com",
        plan="Claude Pro",
        auth_type="Subscription",
        five_hour_remaining_pct=72.0,
        config_dir="/home/user/.claude",
        is_active=True,
    )

    p2 = ClaudeAccountProfile(
        id="work",
        user_label="Work Account",
        account_identity_masked="wo***@enterprise.com",
        plan="Claude Enterprise",
        auth_type="Subscription",
        five_hour_remaining_pct=41.0,
        config_dir="/home/user/.claude-secondary",
        is_active=False,
    )

    assert p1.id != p2.id
    assert p1.account_identity_masked != p2.account_identity_masked
    assert p1.config_dir != p2.config_dir
    assert p1.five_hour_remaining_pct == 72.0
    assert p2.five_hour_remaining_pct == 41.0
    assert p1.is_active is True
    assert p2.is_active is False

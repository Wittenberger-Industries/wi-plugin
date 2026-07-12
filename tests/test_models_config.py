import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "ship" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import cross_review  # noqa: E402


FULL_CONFIG = """---
type: Model Routing Config
title: "Model assignments: demo"
description: Per-role model assignments for wi-dispatched agents.
preset: smart
timestamp: 2026-07-02
---

# Model assignments

## Roles
| Role | Model | Notes |
|------|-------|-------|
| orchestrator | fable | informational: session model |
| wi-code-checker | fable | same-family fallback tier |
| wi-researcher | opus | one tier below orchestrator |
| wi-task-runner | sonnet | default for wi-task-runner dispatches |

## Cross-provider config
| Key | Value |
|-----|-------|
| provider | openai |
| base_url | https://api.openai.com/v1 |
| model | gpt-5 |
| api_key_env | OPENAI_API_KEY |
| check_points | at-finish |

## Per-agent overrides
| Agent | Model |
|-------|-------|
| wi-researcher | haiku |
"""

SIMPLE_CONFIG = """---
type: Model Routing Config
title: "Model assignments: demo"
description: Per-role model assignments for wi-dispatched agents.
preset: simple
timestamp: 2026-07-02
---

# Model assignments

## Roles
| Role | Model | Notes |
|------|-------|-------|
| orchestrator | opus | informational |
| wi-code-checker | opus | matches orchestrator tier |
| wi-researcher | sonnet | one tier below orchestrator |
| wi-task-runner | sonnet | default |

## Cross-provider config
| Key | Value |
|-----|-------|
| provider | none |
"""

MOA_SECTION = """
## Mixture of Agents
| Key | Value |
|-----|-------|
| points | review |
| proposers | opus, sonnet, sonnet |
| layers | 1 |
| aggregator | opus |
"""

# Golden: byte-identical to the ## Platform model map table in references/models.md
GROK_PLATFORM_SECTION = """
## Platform model map
| Tier | grok |
|------|------|
| fable | grok-4.5 |
| opus | grok-4.5 |
| sonnet | grok-composer-2.5-fast |
| haiku | grok-composer-2.5-fast |
"""

XAI_CONFIG = """---
preset: custom
---
## Cross-provider config
| Key | Value |
|-----|-------|
| provider | xai |
| model | grok-4.5 |
| api_key_env | XAI_API_KEY |
"""


class ParseConfigTest(unittest.TestCase):
    def test_roles_parsed(self):
        cfg = cross_review.parse_models_config(FULL_CONFIG)
        self.assertEqual(cfg["preset"], "smart")
        self.assertEqual(cfg["roles"]["orchestrator"], "fable")
        self.assertEqual(cfg["roles"]["wi-code-checker"], "fable")
        self.assertEqual(cfg["roles"]["wi-researcher"], "opus")
        self.assertEqual(cfg["roles"]["wi-task-runner"], "sonnet")

    def test_cross_provider_parsed(self):
        cfg = cross_review.parse_models_config(FULL_CONFIG)
        cp = cfg["cross_provider"]
        self.assertEqual(cp["provider"], "openai")
        self.assertEqual(cp["base_url"], "https://api.openai.com/v1")
        self.assertEqual(cp["model"], "gpt-5")
        self.assertEqual(cp["api_key_env"], "OPENAI_API_KEY")
        self.assertEqual(cp["check_points"], "at-finish")

    def test_overrides_parsed(self):
        cfg = cross_review.parse_models_config(FULL_CONFIG)
        self.assertEqual(cfg["overrides"]["wi-researcher"], "haiku")

    def test_provider_none_means_disabled(self):
        cfg = cross_review.parse_models_config(SIMPLE_CONFIG)
        self.assertEqual(cfg["cross_provider"]["provider"], "none")
        self.assertFalse(cross_review.cross_provider_configured(cfg))

    def test_cross_provider_configured_with_provider(self):
        cfg = cross_review.parse_models_config(FULL_CONFIG)
        self.assertTrue(cross_review.cross_provider_configured(cfg))

    def test_missing_sections_default(self):
        cfg = cross_review.parse_models_config(SIMPLE_CONFIG)
        self.assertEqual(cfg["overrides"], {})
        # provider defaults exist even when api_key_env/model/base_url rows are absent
        self.assertEqual(cfg["cross_provider"]["api_key_env"], "OPENAI_API_KEY")

    def test_moa_section_is_ignored(self):
        # The `## Mixture of Agents` section is read by prose, not by this script:
        # an unknown section must not change what parse_models_config returns.
        self.assertEqual(
            cross_review.parse_models_config(FULL_CONFIG + MOA_SECTION),
            cross_review.parse_models_config(FULL_CONFIG),
        )


class ModelForTest(unittest.TestCase):
    def test_override_beats_role(self):
        cfg = cross_review.parse_models_config(FULL_CONFIG)
        self.assertEqual(cross_review.model_for("wi-researcher", cfg), "haiku")

    def test_task_runner_uses_its_own_role(self):
        cfg = cross_review.parse_models_config(FULL_CONFIG)
        self.assertEqual(cross_review.model_for("wi-task-runner", cfg), "sonnet")

    def test_checker_uses_its_own_role(self):
        cfg = cross_review.parse_models_config(FULL_CONFIG)
        self.assertEqual(cross_review.model_for("wi-code-checker", cfg), "fable")

    def test_unknown_agent_inherits(self):
        cfg = cross_review.parse_models_config(FULL_CONFIG)
        self.assertEqual(cross_review.model_for("some-other-agent", cfg), "inherit")

    def test_no_config_inherits(self):
        self.assertEqual(cross_review.model_for("wi-task-runner", None), "inherit")


class PlatformMapTest(unittest.TestCase):
    def test_platform_map_parsed(self):
        cfg = cross_review.parse_models_config(FULL_CONFIG + GROK_PLATFORM_SECTION)
        self.assertEqual(cfg["platform_map"]["grok"]["opus"], "grok-4.5")
        self.assertEqual(cfg["platform_map"]["grok"]["sonnet"], "grok-composer-2.5-fast")

    def test_absent_platform_map_is_empty(self):
        cfg = cross_review.parse_models_config(FULL_CONFIG)
        self.assertEqual(cfg["platform_map"], {})

    def test_claude_host_passes_tier_through(self):
        cfg = cross_review.parse_models_config(FULL_CONFIG + GROK_PLATFORM_SECTION)
        # wi-task-runner role is sonnet; on the Claude host the tier is unchanged
        self.assertEqual(cross_review.platform_model_for("wi-task-runner", cfg, "claude"), "sonnet")

    def test_grok_host_maps_tier_to_model(self):
        cfg = cross_review.parse_models_config(FULL_CONFIG + GROK_PLATFORM_SECTION)
        self.assertEqual(cross_review.platform_model_for("wi-task-runner", cfg, "grok"), "grok-composer-2.5-fast")
        # wi-researcher has an override to haiku -> cheap Grok model
        self.assertEqual(cross_review.platform_model_for("wi-researcher", cfg, "grok"), "grok-composer-2.5-fast")

    def test_grok_host_unmapped_tier_passes_through(self):
        cfg = cross_review.parse_models_config(SIMPLE_CONFIG + GROK_PLATFORM_SECTION)
        # 'inherit' is not a mapped tier -> returned verbatim
        self.assertEqual(cross_review.platform_model_for("some-agent", cfg, "grok"), "inherit")


class XaiProviderTest(unittest.TestCase):
    def test_xai_defaults_base_url_when_unset(self):
        # No base_url row -> parser pre-fills the OpenAI default -> normalization swaps in XAI_BASE.
        cfg = cross_review.parse_models_config(XAI_CONFIG)
        self.assertEqual(cfg["cross_provider"]["provider"], "xai")
        self.assertEqual(cfg["cross_provider"]["base_url"], cross_review.XAI_BASE)
        self.assertTrue(cross_review.cross_provider_configured(cfg))

    def test_xai_respects_explicit_base_url(self):
        cfg = cross_review.parse_models_config(
            XAI_CONFIG + "| base_url | https://custom.example/v1 |\n"
        )
        self.assertEqual(cfg["cross_provider"]["base_url"], "https://custom.example/v1")


if __name__ == "__main__":
    unittest.main()

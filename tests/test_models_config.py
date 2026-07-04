import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "ship" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import cross_review  # noqa: E402


FULL_CONFIG = """---
type: Model Routing Config
title: Model assignments — demo
description: Per-role model assignments for wi-dispatched agents.
preset: smart
timestamp: 2026-07-02
---

# Model assignments

## Roles
| Role | Model | Notes |
|------|-------|-------|
| orchestrator | fable | informational — session model |
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
title: Model assignments — demo
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


if __name__ == "__main__":
    unittest.main()

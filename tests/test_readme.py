from pathlib import Path

import lgpd_views as views

ROOT = Path(__file__).resolve().parent.parent


def test_readme_has_disclaimer_cta_and_sections():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert views.DISCLAIMER in text
    assert "utm_source=github" in text
    for heading in ("## Install", "## Usage", "## Labels", "## Metrics", "## Privacidade desta demonstração"):
        assert heading in text


def test_space_card_mirrors_privacy_section():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    card = (ROOT / "space" / "README.md").read_text(encoding="utf-8")
    section = readme.split("## Privacidade desta demonstração", 1)[1].split("\n## ", 1)[0]
    assert section.strip() in card

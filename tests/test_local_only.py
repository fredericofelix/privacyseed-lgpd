"""The library must never call gliner2's hosted API client."""

from pathlib import Path

import privacyseed_lgpd

FORBIDDEN = ("GLiNER2API", "gliner2.API", "import API", "api_client")


def test_no_hosted_api_usage():
    root = Path(privacyseed_lgpd.__file__).parent
    for path in root.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in source, f"{path.name} mentions {token}"

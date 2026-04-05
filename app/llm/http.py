from __future__ import annotations

import json
from urllib import error, request


def post_json(
    url: str,
    payload: dict[str, object],
    headers: dict[str, str],
    timeout_seconds: int,
    provider_name: str,
) -> dict[str, object]:
    http_request = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with request.urlopen(http_request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"{provider_name} request failed with status {exc.code}: {details}"
        ) from exc
    except error.URLError as exc:
        raise RuntimeError(f"{provider_name} request failed: {exc.reason}") from exc

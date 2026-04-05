from __future__ import annotations

import json
import os
import re
import time
from urllib import error, parse, request

from processing.vectorization.contracts import EmbeddingGenerator


class GeminiEmbeddingGenerator(EmbeddingGenerator):
    _MAX_BATCH_REQUESTS = 100
    _MAX_RETRY_ATTEMPTS = 5

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: int = 60,
        output_dimensionality: int | None = None,
        min_request_interval_seconds: float = 1.0,
    ) -> None:
        if not model.strip():
            raise ValueError("Gemini embedding model must not be empty.")
        if not api_key.strip():
            raise ValueError("GEMINI_API_KEY must not be empty.")
        if output_dimensionality is not None and output_dimensionality <= 0:
            raise ValueError("Gemini output dimensionality must be greater than zero.")
        if min_request_interval_seconds < 0:
            raise ValueError("Gemini request interval must not be negative.")

        self._model = self._normalize_model_name(model)
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._output_dimensionality = output_dimensionality
        self._min_request_interval_seconds = min_request_interval_seconds
        self._last_request_started_at: float | None = None

    @classmethod
    def from_env(
        cls,
        default_output_dimensionality: int | None = None,
    ) -> "GeminiEmbeddingGenerator":
        raw_dimension = os.getenv("GEMINI_OUTPUT_DIMENSION", "").strip()
        output_dimensionality = (
            int(raw_dimension) if raw_dimension else default_output_dimensionality
        )
        raw_interval = os.getenv("GEMINI_MIN_REQUEST_INTERVAL_SECONDS", "1.0").strip()
        return cls(
            model=os.getenv(
                "GEMINI_EMBEDDING_MODEL",
                os.getenv("EMBEDDING_MODEL", "gemini-embedding-001"),
            ),
            api_key=os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")),
            output_dimensionality=output_dimensionality,
            min_request_interval_seconds=float(raw_interval),
        )

    def embed_query(self, text: str) -> list[float]:
        return self.embed_queries([text])[0]

    def embed_queries(self, texts: list[str]) -> list[list[float]]:
        return self._batch_embed(texts=texts, task_type="RETRIEVAL_QUERY")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._batch_embed(texts=texts, task_type="RETRIEVAL_DOCUMENT")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self._batch_embed(texts=texts, task_type="SEMANTIC_SIMILARITY")

    def _batch_embed(
        self,
        texts: list[str],
        task_type: str,
    ) -> list[list[float]]:
        if not texts:
            return []

        values_list: list[list[float]] = []
        for text_batch in self._chunk_texts(texts):
            payload = {
                "requests": [
                    self._build_request(text, task_type) for text in text_batch
                ]
            }
            endpoint = (
                f"{self._base_url}/{self._model}:batchEmbedContents"
                f"?{parse.urlencode({'key': self._api_key})}"
            )
            response_payload = self._post_json(url=endpoint, payload=payload)

            embeddings = response_payload.get("embeddings")
            if not isinstance(embeddings, list):
                raise RuntimeError(
                    "Gemini embeddings response did not contain embeddings."
                )

            for item in embeddings:
                if not isinstance(item, dict):
                    raise RuntimeError(
                        "Gemini embeddings response contained an invalid embedding object."
                    )

                values = item.get("values")
                if not isinstance(values, list):
                    raise RuntimeError(
                        "Gemini embeddings response contained an invalid values list."
                    )
                values_list.append([float(value) for value in values])

        if len(values_list) != len(texts):
            raise RuntimeError(
                "Gemini embeddings response count did not match request count."
            )

        return values_list

    def _build_request(self, text: str, task_type: str) -> dict[str, object]:
        embed_request: dict[str, object] = {
            "model": self._model,
            "content": {
                "parts": [{"text": text}],
            },
            "taskType": task_type,
        }

        if self._output_dimensionality is not None:
            embed_request["outputDimensionality"] = self._output_dimensionality

        return embed_request

    def _post_json(self, url: str, payload: dict[str, object]) -> dict[str, object]:
        http_request = request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key,
            },
            method="POST",
        )

        for attempt in range(1, self._MAX_RETRY_ATTEMPTS + 1):
            try:
                self._wait_for_request_slot()
                with request.urlopen(
                    http_request,
                    timeout=self._timeout_seconds,
                ) as response:
                    self._last_request_started_at = time.monotonic()
                    return json.loads(response.read().decode("utf-8"))
            except error.HTTPError as exc:
                details = exc.read().decode("utf-8", errors="replace")
                if exc.code == 429 and attempt < self._MAX_RETRY_ATTEMPTS:
                    retry_delay = self._extract_retry_delay_seconds(details)
                    time.sleep(retry_delay)
                    continue
                raise RuntimeError(
                    f"Gemini embeddings request failed with status {exc.code}: {details}"
                ) from exc
            except error.URLError as exc:
                raise RuntimeError(
                    f"Gemini embeddings request failed: {exc.reason}"
                ) from exc

        raise RuntimeError("Gemini embeddings request failed after retries.")

    @classmethod
    def _chunk_texts(cls, texts: list[str]) -> list[list[str]]:
        return [
            texts[index : index + cls._MAX_BATCH_REQUESTS]
            for index in range(0, len(texts), cls._MAX_BATCH_REQUESTS)
        ]

    @staticmethod
    def _extract_retry_delay_seconds(error_details: str) -> float:
        retry_delay_match = re.search(r'"retryDelay":\s*"(\d+)s"', error_details)
        if retry_delay_match is not None:
            return float(retry_delay_match.group(1)) + 1.0

        retry_in_match = re.search(r"Please retry in ([0-9.]+)s", error_details)
        if retry_in_match is not None:
            return float(retry_in_match.group(1)) + 1.0

        return 10.0

    def _wait_for_request_slot(self) -> None:
        if self._last_request_started_at is None:
            return

        elapsed_seconds = time.monotonic() - self._last_request_started_at
        remaining_seconds = self._min_request_interval_seconds - elapsed_seconds
        if remaining_seconds > 0:
            time.sleep(remaining_seconds)

        self._last_request_started_at = time.monotonic()

    @staticmethod
    def _normalize_model_name(model: str) -> str:
        model_name = model.strip()
        if model_name.startswith("models/"):
            return model_name
        return f"models/{model_name}"

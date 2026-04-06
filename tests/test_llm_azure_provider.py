from __future__ import annotations

import unittest
from unittest.mock import patch

from app.llm.action_extraction import AppointmentExtractorFactory
from app.llm.action_factory import ActionReplyGeneratorFactory
from app.llm.factory import KbAnswerGeneratorFactory
from app.llm.providers.azure_openai import (
    AzureOpenAIActionReplyGenerator,
    AzureOpenAIAppointmentExtractor,
    AzureOpenAIKbAnswerGenerator,
)
from app.services.action_models import AppointmentActionReplyContext


class AzureOpenAIProviderTests(unittest.TestCase):
    def test_kb_factory_can_build_azure_openai_generator(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "KB_ANSWER_PROVIDER": "azure_openai",
                "AZURE_OPENAI_API_KEY": "test-key",
                "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com/",
                "AZURE_OPENAI_CHAT_DEPLOYMENT": "gpt-4o-mini",
                "AZURE_OPENAI_API_VERSION": "2024-02-01",
            },
            clear=False,
        ):
            generator = KbAnswerGeneratorFactory().build()

        self.assertIsInstance(generator, AzureOpenAIKbAnswerGenerator)

    def test_action_factory_can_build_azure_openai_generator(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "ACTION_AGENT_PROVIDER": "azure_openai",
                "AZURE_OPENAI_API_KEY": "test-key",
                "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com/",
                "AZURE_OPENAI_CHAT_DEPLOYMENT": "gpt-4o-mini",
                "AZURE_OPENAI_API_VERSION": "2024-02-01",
            },
            clear=False,
        ):
            generator = ActionReplyGeneratorFactory().build()

        self.assertIsInstance(generator, AzureOpenAIActionReplyGenerator)

    def test_extractor_factory_can_build_azure_openai_extractor(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "ACTION_EXTRACTION_PROVIDER": "azure_openai",
                "AZURE_OPENAI_API_KEY": "test-key",
                "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com/",
                "AZURE_OPENAI_CHAT_DEPLOYMENT": "gpt-4o-mini",
                "AZURE_OPENAI_API_VERSION": "2024-02-01",
            },
            clear=False,
        ):
            extractor = AppointmentExtractorFactory().build()

        self.assertIsInstance(extractor, AzureOpenAIAppointmentExtractor)

    def test_azure_kb_generator_uses_chat_completions_endpoint(self) -> None:
        generator = AzureOpenAIKbAnswerGenerator(
            api_key="test-key",
            endpoint="https://example.openai.azure.com/",
            deployment="my deployment",
            api_version="2024-02-01",
        )

        with patch("app.llm.providers.azure_openai.post_json") as post_json_mock:
            post_json_mock.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "Grounded answer.",
                        }
                    }
                ]
            }

            answer = generator.generate_answer(
                user_query="What does credentialing include?",
                retrieved_context=["FAQ context"],
                conversation_history=["user: hi"],
            )

        self.assertEqual(answer, "Grounded answer.")
        self.assertEqual(
            post_json_mock.call_args.kwargs["url"],
            (
                "https://example.openai.azure.com/openai/deployments/"
                "my%20deployment/chat/completions?api-version=2024-02-01"
            ),
        )
        self.assertEqual(
            post_json_mock.call_args.kwargs["headers"]["api-key"],
            "test-key",
        )
        self.assertNotIn("Authorization", post_json_mock.call_args.kwargs["headers"])

    def test_azure_action_reply_generator_reads_text_choice(self) -> None:
        generator = AzureOpenAIActionReplyGenerator(
            api_key="test-key",
            endpoint="https://example.openai.azure.com",
            deployment="gpt-4o-mini",
            api_version="2024-02-01",
        )
        context = AppointmentActionReplyContext(
            phase="collecting",
            user_query="I need to schedule a meeting",
            conversation_history=[],
            current_slots={},
            missing_fields=["service", "date", "time", "name", "email"],
            next_required_field="service",
            service_options=[],
            available_dates=[],
            available_slots=[],
            awaiting_confirmation=False,
            date_confirmed=False,
            time_confirmed=False,
        )

        with patch("app.llm.providers.azure_openai.post_json") as post_json_mock:
            post_json_mock.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "Which service would you like to book?",
                        }
                    }
                ]
            }

            reply = generator.generate_reply(context)

        self.assertEqual(reply, "Which service would you like to book?")

    def test_azure_extractor_parses_json_content(self) -> None:
        extractor = AzureOpenAIAppointmentExtractor(
            api_key="test-key",
            endpoint="https://example.openai.azure.com",
            deployment="gpt-4o-mini",
            api_version="2024-02-01",
        )

        with patch("app.llm.providers.azure_openai.post_json") as post_json_mock:
            post_json_mock.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"service": null, "date": "today", "time": null, '
                                '"time_preference": null, "selected_date": null, '
                                '"selected_time": null, "selected_service": '
                                '"Medical Billing and Denial Management", '
                                '"confirmation_intent": null, "name": null, "email": null}'
                            )
                        }
                    }
                ]
            }

            extraction = extractor.extract(
                user_query="medical billing today",
                conversation_history=[],
                current_slots={},
                offered_services=["Medical Billing and Denial Management"],
            )

        self.assertEqual(
            extraction.selected_service,
            "Medical Billing and Denial Management",
        )
        self.assertEqual(extraction.date, "today")


if __name__ == "__main__":
    unittest.main()

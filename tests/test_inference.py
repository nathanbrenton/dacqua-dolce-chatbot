"""Unit tests for inference-provider contracts."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dacqua_chatbot.inference import (
    ChatMessage,
    GenerationResult,
    TransformersProvider,
)


class ChatMessageTests(unittest.TestCase):
    def test_message_preserves_role_and_content(self) -> None:
        message = ChatMessage(
            role="user",
            content="Hello",
        )

        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Hello")


class GenerationResultTests(unittest.TestCase):
    def test_result_preserves_normalized_metadata(self) -> None:
        result = GenerationResult(
            text="Hello",
            model="example-model",
            device="cpu",
            input_tokens=10,
            output_tokens=2,
            generation_seconds=0.5,
        )

        self.assertEqual(result.model, "example-model")
        self.assertEqual(result.output_tokens, 2)


class TransformersProviderTests(unittest.TestCase):
    def test_missing_model_directory_is_rejected(self) -> None:
        with self.assertRaises(FileNotFoundError):
            TransformersProvider(
                "/definitely/not/a/model",
                device="cpu",
            )

    def test_environment_factory_uses_model_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {"DACQUA_MODEL_PATH": directory},
                clear=False,
            ):
                provider = TransformersProvider.from_environment()

            self.assertEqual(
                provider.model_path,
                Path(directory).resolve(),
            )
            self.assertFalse(provider.is_loaded)

    def test_environment_factory_requires_model_path(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                TransformersProvider.from_environment()

    def test_empty_message_sequence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = TransformersProvider(
                directory,
                device="cpu",
            )

            with self.assertRaises(ValueError):
                provider.generate([])


if __name__ == "__main__":
    unittest.main()

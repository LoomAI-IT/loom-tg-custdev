import io
import re
import json
from typing import Literal

import httpx
import pypdf
import base64
import openai
from openai.types import ImagesResponse

from openai.types.audio import Transcription, TranscriptionVerbose
from pdf2image import convert_from_bytes
from openai.types.chat.chat_completion import ChatCompletion

from opentelemetry.trace import Status, StatusCode, SpanKind

from internal import interface
from pkg.trace_wrapper import traced_method

from .price import *


class OpenAIClient(interface.IOpenAIClient):
    def __init__(
            self,
            tel: interface.ITelemetry,
            api_key: str,
            neuroapi_api_key: str,
            proxy: str = None,
    ):
        self.tracer = tel.tracer()
        self.logger = tel.logger()
        self._encoders = {}

        if proxy:
            self.client = openai.AsyncOpenAI(
                api_key=api_key,
                http_client=httpx.AsyncClient(proxy=proxy)
            )
        else:
            self.client = openai.AsyncOpenAI(
                api_key=api_key
            )

        self.neuroapi_client = openai.AsyncOpenAI(
                api_key=neuroapi_api_key,
                base_url="https://neuroapi.host/v1",
            )

    @traced_method()
    async def transcribe_audio(
            self,
            audio_file: bytes,
            filename: str,
            audio_model: str,
            language: str = None,
            prompt: str = None,
            response_format: Literal["json", "text", "srt", "verbose_json", "vtt"] = "verbose_json",
            temperature: float = None,
            timestamp_granularities: list[Literal["word", "segment"]] = None
    ) -> tuple[str, dict]:
        """
        Транскрибирует аудиофайл и рассчитывает стоимость операции.

        Args:
            audio_file: Байты аудиофайла
            filename: Имя файла
            audio_model: Модель для транскрипции ("whisper-1", "gpt-4o-transcribe", "gpt-4o-mini-transcribe")
            language: Язык аудио (ISO-639-1 код, например "ru", "en")
            prompt: Подсказка для улучшения точности транскрипции
            response_format: Формат ответа
            temperature: Температура семплирования (0-1)
            timestamp_granularities: Детализация временных меток ["word", "segment"]

        Returns:
            Tuple[результат_транскрипции, детали_стоимости_или_None]
        """
        audio_buffer = io.BytesIO(audio_file)
        audio_buffer.name = filename

        api_params: dict = {
            "model": audio_model,
            "file": audio_buffer,
            "response_format": response_format
        }

        if language:
            api_params["language"] = language
        if prompt:
            api_params["prompt"] = prompt
        if temperature is not None:
            api_params["temperature"] = temperature
        if timestamp_granularities:
            api_params["timestamp_granularities"] = timestamp_granularities

        transcript: TranscriptionVerbose = await self.client.audio.transcriptions.create(**api_params)

        cost_details = self._calculate_transcription_cost(audio_model, transcript)
        return transcript.text, cost_details

    def _calculate_transcription_cost(
            self,
            audio_model: str,
            transcription_result: Transcription | TranscriptionVerbose
    ) -> dict:
        """
        Рассчитывает стоимость транскрипции на основе результата API.
        """
        if audio_model not in TRANSCRIPTION_PRICING:
            return {
                'error': f'Неизвестная модель: {audio_model}',
                'available_models': list(TRANSCRIPTION_PRICING.keys())
            }

        pricing = TRANSCRIPTION_PRICING[audio_model]

        # Для whisper-1 - только по минутам
        if audio_model == 'whisper-1':
            if isinstance(transcription_result, TranscriptionVerbose) and hasattr(transcription_result, 'duration'):
                duration_minutes = transcription_result.duration / 60
                cost = duration_minutes * pricing

                return {
                    'total_cost': round(cost, 6),
                    'model': audio_model,
                    'billing_method': 'per_minute',
                    'details': {
                        'duration_minutes': round(duration_minutes, 4),
                        'duration_seconds': round(transcription_result.duration, 2),
                        'price_per_minute': pricing
                    }
                }
            else:
                return {
                    'error': 'Для whisper-1 нужен response_format="verbose_json" для получения duration'
                }

        # Для gpt-4o моделей - сначала пробуем по токенам
        if hasattr(transcription_result, 'usage') and transcription_result.usage:
            usage = transcription_result.usage
            input_tokens = getattr(usage, 'prompt_tokens', 0)
            output_tokens = getattr(usage, 'completion_tokens', 0)

            input_cost = (input_tokens / 1_000_000) * pricing['input_tokens']
            output_cost = (output_tokens / 1_000_000) * pricing['output_tokens']
            total_cost = input_cost + output_cost

            return {
                'total_cost': round(total_cost, 6),
                'input_cost': round(input_cost, 6),
                'output_cost': round(output_cost, 6),
                'model': audio_model,
                'billing_method': 'per_token',
                'details': {
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'total_tokens': input_tokens + output_tokens,
                    'input_price_per_1m': pricing['input_tokens'],
                    'output_price_per_1m': pricing['output_tokens']
                }
            }

        # Fallback: расчет по минутам для gpt-4o моделей
        if isinstance(transcription_result, TranscriptionVerbose) and hasattr(transcription_result, 'duration'):
            duration_minutes = transcription_result.duration / 60
            cost = duration_minutes * pricing['per_minute']

            return {
                'total_cost': round(cost, 6),
                'model': audio_model,
                'billing_method': 'per_minute_fallback',
                'details': {
                    'duration_minutes': round(duration_minutes, 4),
                    'duration_seconds': round(transcription_result.duration, 2),
                    'price_per_minute': pricing['per_minute']
                }
            }

        return {
            'error': f'Не удалось рассчитать стоимость для модели {audio_model}',
            'help': 'Используйте response_format="verbose_json" или модель с поддержкой usage'
        }

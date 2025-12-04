from aiogram import Bot
from aiogram.enums import ContentType
from aiogram.types import Message
from aiogram_dialog import DialogManager

from internal import interface


class MessageExtractor:
    def __init__(
            self,
            logger,
            bot: Bot,
            openai_client: interface.IOpenAIClient
    ):
        self.logger = logger
        self.bot = bot
        self.openai_client = openai_client

    async def process_voice_or_text_input(
            self,
            message: Message,
            return_html: bool = False,
    ) -> str:
        if message.content_type == ContentType.TEXT:
            return message.text if not return_html else message.html_text.replace('\n', '<br/>')
        else:
            return await self.speech_to_text(
                message=message,
            )

    async def speech_to_text(
            self,
            message: Message,
    ) -> str:
        if message.voice:
            file_id = message.voice.file_id
        else:
            file_id = message.audio.file_id

        file = await self.bot.get_file(file_id)
        file_data = await self.bot.download_file(file.file_path)

        text, _ = await self.openai_client.transcribe_audio(
            audio_file=file_data.read(),
            filename="audio.mp3",
            audio_model="whisper-1",
            language="ru",
        )

        return text

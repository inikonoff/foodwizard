import os
import asyncio
import logging
import tempfile
import speech_recognition as sr
from pydub import AudioSegment
from config import TEMP_DIR

logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Настройка языков распознавания
        self.language_map = {
            "ru": "ru-RU",
            "en": "en-US",
            "de": "de-DE",
            "fr": "fr-FR",
            "it": "it-IT",
            "es": "es-ES"
        }
    
    async def convert_ogg_to_wav(self, ogg_path: str) -> str:
        """Конвертирует OGG в WAV"""
        wav_path = ogg_path.replace('.ogg', '.wav')
        
        # Используем asyncio для блокирующей операции
        await asyncio.to_thread(self._convert_audio, ogg_path, wav_path)
        
        return wav_path
    
    def _convert_audio(self, input_path: str, output_path: str):
        """Синхронная конвертация аудио"""
        try:
            audio = AudioSegment.from_ogg(input_path)
            audio.export(output_path, format="wav")
        except Exception as e:
            logger.error(f"Ошибка конвертации аудио: {e}")
            raise
    
    async def recognize_speech(self, wav_path: str, language: str = "ru") -> str:
        """Распознает речь из WAV файла"""
        # Получаем код языка для распознавания
        recognizer_lang = self.language_map.get(language, "ru-RU")
        
        try:
            # Используем asyncio для блокирующего вызова
            text = await asyncio.to_thread(
                self._recognize_speech_sync, wav_path, recognizer_lang
            )
            return text
        except Exception as e:
            logger.error(f"Ошибка распознавания речи: {e}")
            return ""
    
    def _recognize_speech_sync(self, wav_path: str, language: str) -> str:
        """Синхронное распознавание речи"""
        try:
            with sr.AudioFile(wav_path) as source:
                audio = self.recognizer.record(source)
                return self.recognizer.recognize_google(audio, language=language)
        except sr.UnknownValueError:
            logger.warning("Речь не распознана")
            return ""
        except sr.RequestError as e:
            logger.error(f"Ошибка сервиса распознавания: {e}")
            return ""
        except Exception as e:
            logger.error(f"Неизвестная ошибка распознавания: {e}")
            return ""
    
    async def process_voice(self, voice_file_path: str, language: str = "ru") -> str:
        """Основной метод обработки голосового сообщения"""
        temp_files = []
        
        try:
            # Создаем временный WAV файл
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_wav:
                wav_path = tmp_wav.name
                temp_files.append(wav_path)
            
            # Конвертируем OGG в WAV
            await self.convert_ogg_to_wav(voice_file_path)
            
            # Распознаем речь
            text = await self.recognize_speech(wav_path, language)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Ошибка обработки голоса: {e}")
            return ""
        
        finally:
            # Удаляем временные файлы
            for file_path in temp_files:
                try:
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    logger.warning(f"Не удалось удалить временный файл {file_path}: {e}")
    
    async def get_supported_languages(self) -> list:
        """Возвращает список поддерживаемых языков"""
        return list(self.language_map.keys())
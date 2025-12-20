import logging
import os
import asyncio # !!! НУЖЕН НОВЫЙ ИМПОРТ !!!
from typing import Optional

from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
import speech_recognition as sr

# Твои модули
from locales.prompts import get_prompt 
from locales.texts import get_text # !!! НУЖЕН НОВЫЙ ИМПОРТ !!!

logger = logging.getLogger(__name__)

# Инициализируем только recognizer (он синхронный)
recognizer = sr.Recognizer()

class VoiceService:
    @staticmethod
    def _sync_process_audio(ogg_path: str, lang: str) -> Optional[str]:
        """
        СИНХРОННАЯ функция, которая выполняет тяжелые, блокирующие операции
        (pydub, speech_recognition).
        """
        temp_flac_path = None
        try:
            # 1. Конвертация (требует FFMPEG)
            audio_ogg = AudioSegment.from_ogg(ogg_path)
            temp_flac_path = ogg_path.replace(".ogg", ".flac")
            
            # Сохраняем во временный FLAC-файл, чтобы SpeechRecognition мог его прочитать
            # NOTE: pydub не всегда может прочитать из буфера, лучше использовать файл
            audio_ogg.export(temp_flac_path, format="flac") 

            # 2. Распознавание
            with sr.AudioFile(temp_flac_path) as source:
                audio = recognizer.record(source)
            
            # Определяем код языка для Google API
            lang_code_google = "ru-RU" if lang == "ru" else "en-US" # и т.д.
            
            text = recognizer.recognize_google(audio, language=lang_code_google)
            return text
            
        except CouldntDecodeError:
            logger.error(f"Ошибка декодирования аудио (CouldntDecodeError). Нет FFMPEG?")
            # NOTE: Это самая частая ошибка, если нет FFMPEG
            return None
        except sr.UnknownValueError:
            # Голос распознан, но не понятен
            return "" 
        except Exception as e:
            logger.error(f"Неизвестная ошибка распознавания: {e}")
            return None
            
        finally:
            # Обязательно удаляем временный FLAC-файл
            if temp_flac_path and os.path.exists(temp_flac_path):
                try:
                    os.unlink(temp_flac_path)
                except Exception as e:
                    logger.warning(f"Не удалось удалить временный FLAC файл {temp_flac_path}: {e}")

    async def process_voice(self, ogg_path: str, lang: str) -> Optional[str]:
        """
        АСИНХРОННАЯ функция-обертка, запускающая синхронную работу в отдельном потоке.
        """
        # !!! КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Запускаем блокирующую функцию в отдельном потоке !!!
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(
             None, # Используем стандартный ThreadPoolExecutor
             self._sync_process_audio,
             ogg_path,
             lang
        )
        # Если None - это ошибка сервера/файла, если "" - не распознано
        return text 

voice_service = VoiceService()
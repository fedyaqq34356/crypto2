import os
import logging
from aiogram.types import Message, FSInputFile
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

class ImageHandler:
    def __init__(self):

        self.image_paths = [
            "images/",
            "assets/",
            "static/",
            "media/",
            "bot/images/",
            "bot/assets/",
            "resources/",
            ""  
        ]
    
    def find_image(self, filename: str) -> str:
        """Поиск изображения в возможных путях"""
        for path in self.image_paths:
            full_path = os.path.join(path, filename)
            if os.path.exists(full_path):
                logger.info(f"Найдено изображение: {full_path}")
                return full_path
        
        logger.warning(f"Изображение {filename} не найдено")
        return None
    
    def create_welcome_image(self, text: str) -> BytesIO:
        """Создание изображения приветствия с текстом"""
        try:

            width, height = 800, 600
            img = Image.new('RGB', (width, height), color='#1a1a1a')
            draw = ImageDraw.Draw(img)
            
   
            try:
                font_large = ImageFont.truetype("arial.ttf", 32)
                font_small = ImageFont.truetype("arial.ttf", 16)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            

            title = "CryptoBusinessTeam"
            title_bbox = draw.textbbox((0, 0), title, font=font_large)
            title_width = title_bbox[2] - title_bbox[0]
            draw.text(((width - title_width) // 2, 50), title, fill='#ffffff', font=font_large)
            

            lines = text.split('\n')
            y_offset = 150
            for line in lines[:15]:  
                if line.strip():
                    line_bbox = draw.textbbox((0, 0), line, font=font_small)
                    line_width = line_bbox[2] - line_bbox[0]
                    draw.text(((width - line_width) // 2, y_offset), line, fill='#cccccc', font=font_small)
                y_offset += 25
            

            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            logger.info("Создано изображение приветствия")
            return img_bytes
            
        except Exception as e:
            logger.error(f"Ошибка при создании изображения: {e}")
            return None
    
    async def send_message_with_image(self, message: Message, text: str, image_name: str = "welcome.jpg", reply_markup=None):
        """Отправка сообщения с изображением"""
        try:

            image_path = self.find_image(image_name)
            
            if image_path:
                try:
                    photo = FSInputFile(image_path)
                    await message.answer_photo(
                        photo=photo,
                        caption=text,
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                    logger.info(f"Отправлено изображение: {image_path}")
                    return True
                except Exception as e:
                    logger.error(f"Ошибка при отправке файла {image_path}: {e}")
            

            logger.info("Создаем изображение программно")
            img_bytes = self.create_welcome_image(text)
            
            if img_bytes:
                try:
                    await message.answer_photo(
                        photo=("welcome.png", img_bytes, "image/png"),
                        caption=text,
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                    logger.info("Отправлено созданное изображение")
                    return True
                except Exception as e:
                    logger.error(f"Ошибка при отправке созданного изображения: {e}")
            

            logger.warning("Отправляем только текст без изображения")
            await message.answer(
                text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return False
            
        except Exception as e:
            logger.error(f"Критическая ошибка в send_message_with_image: {e}")

            await message.answer(text, reply_markup=reply_markup)
            return False


image_handler = ImageHandler()
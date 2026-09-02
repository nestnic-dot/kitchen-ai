import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from PIL import Image

from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# Загружаем переменные окружения (.env)
load_dotenv()

# ==========================================
# 1. Pydantic-схемы для розеток и коммуникаций
# ==========================================

class Point2D(BaseModel):
    x_mm: float = Field(description="Расстояние по горизонтали от левого угла стены (в мм)")
    z_mm: float = Field(description="Расстояние по вертикали от чистового пола (в мм)")

class CommunicationItem(BaseModel):
    type: str = Field(
        description="Тип элемента: socket_220v, water_cold, water_hot, drain, vent, gas, other"
    )
    description: str = Field(description="Описание (например, 'Двойная розетка для фартука', 'Вывод холодной воды')")
    wall_name: Optional[str] = Field(default=None, description="Название стены, если указано на фото (например 'Стена 1')")
    position: Point2D = Field(description="Координаты X и Z точки подключения в мм")
    notes: Optional[str] = Field(default=None, description="Дополнительные пометки или измерения")

class VisionAnalysisResult(BaseModel):
    items: List[CommunicationItem] = Field(default_factory=list, description="Список распознанных коммуникаций")
    summary: str = Field(description="Краткий текстовый вывод по результатам анализа снимка")


# ==========================================
# 2. Парсер изображений на базе Gemini Flash Vision
# ==========================================

class VisionParser:
    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY не найден в переменных окружения или файле .env")
        
        self.client = genai.Client(api_key=key)
        # Используем современную и быструю модель Gemini 3.6 Flash
        self.model_name = "gemini-3.6-flash"

    def parse_image(self, image_path: str, wall_context: Optional[str] = None) -> VisionAnalysisResult:
        """
        Отправляет фото замера в Gemini Vision и возвращает строго структурированные координаты коммуникаций.
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл изображения {image_path} не найден.")

        image = Image.open(path)

        # Системный промпт с инструкциями для ИИ-эксперта по замеру кухонь
        prompt = f"""
Ты — профессиональный замерщик кухонной мебели и инженер-проектировщик.
Проанализируй предоставленную фотографию замера помещения.

На фото нанесены размеры, стрелки или разметка от чистового пола (высота Z) и от базового/левого угла (расстояние X) до выходов коммуникаций.

Твоя задача:
1. Найти все инженерные выводы (розетки 220V, выводы воды, канализацию, вентиляционные отверстия, газ).
2. Определить их координаты:
   - X: расстояние от угла/левого края (в мм).
   - Z: расстояние от чистового пола (в мм).
   Если размеры на фото указаны в метрах (например 1.25 m) или сантиметрах (125 cm), АВТОМАТИЧЕСКИ ПЕРЕВЕДИ ИХ В МИЛЛИМЕТРЫ (1250 мм).
3. Заполнить строго структурированный JSON по предоставленной Pydantic-схеме.

Контекст стены: {wall_context or 'Не указан (определи по изображению, если есть надписи)'}
"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[image, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=VisionAnalysisResult,
                temperature=0.1,  # Низкая температура для максимально точных и численных ответов
            ),
        )

        # Валидируем и возвращаем спарсенный Pydantic объект
        return VisionAnalysisResult.model_validate_json(response.text)


# ==========================================
# 3. Блок локального тестирования
# ==========================================
if __name__ == "__main__":
    print("=== Модуль 1: Vision Parser (Gemini Flash) ===")
    
    test_image = "sample_photo.jpg"
    
    if Path(test_image).exists():
        try:
            parser = VisionParser()
            print(f"Анализируем фото '{test_image}' через Gemini API...")
            result = parser.parse_image(test_image, wall_context="Стена A (Рабочая зона)")
            print("\nУспешно распознано:")
            print(result.model_dump_json(indent=2))
        except Exception as e:
            print(f"\n[!] Ошибка при вызове Gemini API: {e}")
    else:
        print(f"\n[!] Тестовое изображение '{test_image}' не найдено.")
        print("Создайте тестовую картинку или положите реальное фото замера в корень проекта.")
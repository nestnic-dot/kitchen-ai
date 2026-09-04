import os
import time
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from PIL import Image

from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.genai import errors as google_errors

load_dotenv()

# ==========================================
# 1. Pydantic-модели
# ==========================================

class Point2D(BaseModel):
    x_mm: float = Field(description="Расстояние по горизонтали от левого угла стены (в мм)")
    z_mm: float = Field(description="Расстояние по вертикали от чистового пола (в мм)")

class CommunicationItem(BaseModel):
    type: str = Field(description="Тип элемента: socket_220v, water_cold, water_hot, drain, vent, gas, other")
    description: str = Field(description="Описание (например, 'Двойная розетка для фартука')")
    wall_name: Optional[str] = Field(default=None, description="Название стены (например 'Стена A')")
    position: Point2D = Field(description="Координаты X и Z точки подключения в мм")
    notes: Optional[str] = Field(default=None, description="Дополнительные пометки")

class VisionAnalysisResult(BaseModel):
    items: List[CommunicationItem] = Field(default_factory=list)
    summary: str = Field(description="Краткий текстовый вывод")


# ==========================================
# 2. Vision Parser (Gemini Flash)
# ==========================================

class VisionParser:
    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY не найден в файле .env")
        
        self.client = genai.Client(api_key=key)
        self.model_name = "gemini-3.6-flash"

    def parse_image(self, image_path: str, wall_context: Optional[str] = None, max_retries: int = 3) -> VisionAnalysisResult:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл {image_path} не найден.")

        image = Image.open(path)

        prompt = f"""
Ты — профессиональный замерщик кухонной мебели.
Проанализируй фотографию замера и найди все инженерные выводы (розетки, воду, канализацию, вентиляцию, газ).
Определи их координаты в миллиметрах (X — от левого угла, Z — от пола).
Если значения указаны в см или м — переведи в миллиметры.
Контекст стены: {wall_context or 'Не указан'}
"""

        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[image, prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=VisionAnalysisResult,
                        temperature=0.1,
                    ),
                )
                return VisionAnalysisResult.model_validate_json(response.text)

            except google_errors.ServerError as e:
                if attempt == max_retries:
                    print(f"[!] Сервер Gemini недоступен после {max_retries} попыток.")
                    raise e
                wait_time = attempt * 3
                print(f"[!] Временная задержка на сервере Gemini (503). Повтор {attempt}/{max_retries} через {wait_time} сек...")
                time.sleep(wait_time)


# ==========================================
# Локальное тестирование
# ==========================================
if __name__ == "__main__":
    print("=== Тестирование Vision Parser (Gemini Flash) ===")
    test_image = "sample_photo.jpg"
    
    if Path(test_image).exists():
        parser = VisionParser()
        result = parser.parse_image(test_image, wall_context="Стена A")
        print("\nРезультат распознавания:")
        print(result.model_dump_json(indent=2))
    else:
        print(f"[!] Тестовый файл {test_image} не найден.")
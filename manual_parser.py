import json
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

from bosch_parser import RoomGeometry, WallData
from vision_parser import VisionParser
from pipeline import MasterProjectData

# ==========================================
# 1. Pydantic-схема данных из формы Telegram Mini App
# ==========================================

class ManualWallEntry(BaseModel):
    name: str = Field(description="Название стены, например 'Стена 1'")
    length_mm: float = Field(description="Длина в мм")

class ManualInputPayload(BaseModel):
    walls: List[ManualWallEntry]
    ceiling_height_mm: Optional[float] = Field(default=2600.0, description="Высота потолка в мм")
    photo_paths: List[str] = Field(default_factory=list, description="Список загруженных фото замера (JPG/PNG)")

# ==========================================
# 2. Обработчик ручного ввода
# ==========================================

class ManualInputParser:
    @staticmethod
    def process_manual_entry(payload: ManualInputPayload, output_json: str = "project_measurement.json") -> MasterProjectData:
        print("=== Обработка ручного ввода замера (Manual Fallback) ===")
        
        # 1. Формируем геометрию стен
        walls_data = [
            WallData(name=w.name, length_mm=w.length_mm) 
            for w in payload.walls
        ]
        
        geometry = RoomGeometry(
            walls=walls_data,
            ceiling_height_mm=payload.ceiling_height_mm,
            extracted_image_paths=payload.photo_paths
        )
        print(f"[x] Геометрия собрана вручную: {len(walls_data)} стен.")

        # 2. Если мастер прикрепил фото замеров — распознаем коммуникации через Gemini Vision
        all_comms = []
        if payload.photo_paths:
            vision_parser = VisionParser()
            for img_path in payload.photo_paths:
                if Path(img_path).exists():
                    print(f"[...] Обработка фото {img_path} через Gemini Flash...")
                    res = vision_parser.parse_image(img_path)
                    all_comms.extend(res.items)
        else:
            print("[!] Фото замера не загружены. Коммуникации можно добавить вручную или пропустить.")

        # 3. Сводим в единый мастер-формат
        master_data = MasterProjectData(
            geometry=geometry,
            all_communications=all_comms
        )

        # 4. Сохраняем в тот же самый JSON-файл
        with open(output_json, "w", encoding="utf-8") as f:
            f.write(master_data.model_dump_json(indent=2))

        print(f"[УСПЕХ] Ручные данные обработаны и сохранены в {output_json}")
        return master_data


# ==========================================
# 3. Тестовый запуск фолбека
# ==========================================
if __name__ == "__main__":
    fake_tma_data = ManualInputPayload(
        walls=[
            ManualWallEntry(name="Стена A", length_mm=3200.0),
            ManualWallEntry(name="Стена B", length_mm=2400.0)
        ],
        ceiling_height_mm=2700.0,
        photo_paths=["sample_photo.jpg"]
    )
    
    ManualInputParser.process_manual_entry(fake_tma_data)
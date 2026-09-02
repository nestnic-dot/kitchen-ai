import json
from pydantic import BaseModel
from bosch_parser import BoschPDFParser, RoomGeometry
from vision_parser import VisionParser, VisionAnalysisResult, CommunicationItem

class MasterProjectData(BaseModel):
    geometry: RoomGeometry
    all_communications: List[CommunicationItem] = []

def run_one_click_pipeline(pdf_path: str, output_json: str = "project_measurement.json"):
    print(f"=== Запуск Гибридного Pipeline (1-Click PDF) ===")
    
    # 1. Парсинг PDF (Стены + Выемка фото)
    pdf_parser = BoschPDFParser(pdf_path)
    geometry = pdf_parser.parse()
    
    print(f"[x] Найдено стен: {len(geometry.walls)}")
    print(f"[x] Извлечено фото замеров: {len(geometry.extracted_image_paths)}")
    
    # 2. Передача всех извлеченных фото в Gemini Vision
    vision_parser = VisionParser()
    all_comms: List[CommunicationItem] = []
    
    for img_path in geometry.extracted_image_paths:
        print(f"[...] Обработка фото {img_path} через Gemini Flash...")
        res = vision_parser.parse_image(img_path)
        all_comms.extend(res.items)
        
    master_data = MasterProjectData(
        geometry=geometry,
        all_communications=all_comms
    )
    
    with open(output_json, "w", encoding="utf-8") as f:
        f.write(master_data.model_dump_json(indent=2))
        
    print(f"\n[УСПЕХ] Все данные замера сведены в {output_json}")

if __name__ == "__main__":
    run_one_click_pipeline("sample_measure.pdf")
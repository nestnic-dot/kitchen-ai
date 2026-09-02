import re
from pathlib import Path
from typing import List, Optional
import pdfplumber
import fitz  # PyMuPDF
from pydantic import BaseModel, Field

class WallData(BaseModel):
    name: str = Field(description="Название стены (например: 'Стена A')")
    length_mm: float = Field(description="Длина стены в мм")
    height_mm: Optional[float] = Field(default=None, description="Высота стены в мм")

class RoomGeometry(BaseModel):
    walls: List[WallData] = Field(default_factory=list)
    ceiling_height_mm: Optional[float] = Field(default=None)
    extracted_image_paths: List[str] = Field(default_factory=list, description="Пути к вытащенным из PDF фото")

class BoschPDFParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)

    def extract_raw_text(self) -> str:
        """Извлекает весь текст из PDF."""
        full_text = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text)
        return "\n".join(full_text)

    def extract_images(self, output_dir: str = "extracted_photos") -> List[str]:
        """Автоматически извлекает все встроенные фото замеров из PDF файла."""
        out_path = Path(output_dir)
        out_path.mkdir(exist_ok=True)
        
        extracted_files = []
        doc = fitz.open(self.pdf_path)
        
        img_counter = 1
        for page_index in range(len(doc)):
            page = doc[page_index]
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Игнорируем иконки и мелкие логотипы (меньше 10 КБ)
                if len(image_bytes) < 10240:
                    continue

                filename = out_path / f"photo_page{page_index+1}_{img_counter}.{image_ext}"
                with open(filename, "wb") as f:
                    f.write(image_bytes)
                
                extracted_files.append(str(filename))
                img_counter += 1
                
        return extracted_files

    def parse(self) -> RoomGeometry:
        """Сбор геометрии и фото в единую модель."""
        raw_text = self.extract_raw_text()
        walls: List[WallData] = []
        ceiling_height: Optional[float] = None

        # Поиск высоты потолка
        ceiling_match = re.search(r"(?:Высота|Потолок|Ceiling)[:\s]+([\d[.,]+)\s*(м|m|см|cm|мм|mm)?", raw_text, re.IGNORECASE)
        if ceiling_match:
            ceiling_height = self._to_mm(float(ceiling_match.group(1).replace(",", ".")), ceiling_match.group(2))

        # Поиск стен
        matches = re.findall(r"(Стена\s*[\w\d]+|Wall\s*[\w\d]+)[:\s=]+([\d[.,]+)\s*(м|m|см|cm|мм|mm)?", raw_text, re.IGNORECASE)
        for name, val_str, unit in matches:
            length_mm = self._to_mm(float(val_str.replace(",", ".")), unit)
            if not any(w.name.lower() == name.lower() for w in walls):
                walls.append(WallData(name=name.strip(), length_mm=length_mm))

        # Извлекаем вложенные фотографии замеров
        images = self.extract_images()

        return RoomGeometry(
            walls=walls,
            ceiling_height_mm=ceiling_height,
            extracted_image_paths=images
        )

    @staticmethod
    def _to_mm(val: float, unit: Optional[str]) -> float:
        if not unit:
            return val * 1000.0 if val < 100 else val
        unit = unit.lower()
        if unit in ["м", "m"]:
            return val * 1000.0
        elif unit in ["см", "cm"]:
            return val * 10.0
        return val
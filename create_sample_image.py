from PIL import Image, ImageDraw, ImageFont

def create_test_measure_image(filename="sample_photo.jpg"):
    # Создаем серый холст (имитация стены)
    img = Image.new("RGB", (800, 600), color=(220, 220, 220))
    draw = ImageDraw.Draw(img)

    # Рисуем подпись
    draw.text((30, 20), "BOSCH MeasureOn - Photo Measure", fill=(0, 0, 0))
    draw.text((30, 50), "Wall A - Socket & Water Layout", fill=(50, 50, 50))

    # Рисуем линию пола
    draw.line([(0, 550), (800, 550)], fill=(0, 0, 255), width=4)
    draw.text((10, 525), "Floor (Z=0)", fill=(0, 0, 255))

    # Рисуем левый угол
    draw.line([(50, 0), (50, 600)], fill=(255, 0, 0), width=4)
    draw.text((60, 570), "Corner (X=0)", fill=(255, 0, 0))

    # Рисуем блок розеток
    draw.rectangle([(300, 300), (360, 340)], fill=(50, 50, 50), outline=(0, 0, 0))
    draw.text((280, 275), "Socket 220V", fill=(0, 0, 0))
    draw.text((280, 350), "X = 1450 mm", fill=(255, 0, 0))
    draw.text((370, 310), "Z = 950 mm", fill=(0, 0, 255))

    # Рисуем вывод воды
    draw.ellipse([(500, 400), (540, 440)], fill=(0, 150, 255), outline=(0, 0, 0))
    draw.text((490, 375), "Water Cold", fill=(0, 0, 0))
    draw.text((480, 450), "X = 2100 mm", fill=(255, 0, 0))
    draw.text((550, 410), "Z = 550 mm", fill=(0, 0, 255))

    img.save(filename)
    print(f"[x] Тестовая картинка создана: {filename}")

if __name__ == "__main__":
    create_test_measure_image()
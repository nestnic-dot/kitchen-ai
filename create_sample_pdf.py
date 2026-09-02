from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_sample_measure_pdf(filename="sample_measure.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    
    # Заголовок отчета Bosch MeasureOn
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Bosch MeasureOn - Test Project Report")
    
    # Служебные данные
    c.setFont("Helvetica", 10)
    c.drawString(100, 730, "Date: 2026-08-25 | Operator: Test User")
    c.line(100, 720, 500, 720)
    
    # Текст замеров (используем стандарты Bosch)
    c.setFont("Helvetica", 12)
    lines = [
        "Room Geometry Data:",
        "Ceiling Height: 2.65 m",
        "Wall 1: 3.450 m",
        "Wall 2: 2.800 m",
        "Wall 3: 3.450 m",
        "Wall 4: 2.800 m"
    ]
    
    y = 690
    for line in lines:
        c.drawString(100, y, line)
        y -= 25
        
    c.save()
    print(f"[x] Тестовый PDF создан: {filename}")

if __name__ == "__main__":
    generate_sample_measure_pdf()

from django.shortcuts import render, redirect
from .models import PDF
import PyPDF2
import re

def import_success(request):
    return render(request, 'import_success.html')


def importar_pdf(request):
    if request.method == 'POST' and request.FILES.getlist('pdf_files'):
        pdf_files = request.FILES.getlist('pdf_files')

        for pdf_file in pdf_files:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            page = pdf_reader.pages[0]
            text = page.extract_text()

            nombre_archivo = pdf_file.name
            materia = None
            codigo = None
            carrera = None
            objetivos_text = None

            # Extraer datos del PDF
            materia_match = re.search(r'Nombre\s*de\s*la\s*Materia\s*:\s*(.*)', text)
            materia = materia_match.group(1).strip() if materia_match else None
            materia = re.sub(r'\.\s*$', '', materia) if materia else None

            codigo_match = re.search(r'Código\s*:\s*(.*)', text)
            codigo = codigo_match.group(1).strip().replace(" ", "") if codigo_match else None
            codigo = re.sub(r'\.\s*$', '', codigo) if codigo else None

            carrera_match = re.search(r'Carrera\s*:\s*(.*)', text)
            carrera = carrera_match.group(1).strip() if carrera_match else None
            carrera = re.sub(r'\.\s*$', '', carrera) if carrera else None

            objetivos_match = re.search(r'OBJETIVOS\s*(?:\. )?(.*?)(?=IV.|$)', text, re.DOTALL)
            objetivos_text = objetivos_match.group(1).strip() if objetivos_match else None

            # Guardar en la base de datos
            pdf = PDF(nombre=nombre_archivo, materia=materia, carrera=carrera, codigo=codigo, objetivos=objetivos_text)
            pdf.save()

        return redirect('import_success')
    return render(request, 'import_pdf.html')


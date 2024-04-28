import pdfplumber
from django.shortcuts import render, redirect
from .models import PDF, Carrera
from io import BytesIO
from unidecode import unidecode
from django.http import HttpResponse
from django.template.loader import render_to_string


def import_success(request):
    return render(request, 'import_success.html')


def carrera_pdf_list(request):
    carreras = Carrera.objects.all()
    pdfs = PDF.objects.none()
    selected_carrera_id = request.GET.get('id_carrera')

    if selected_carrera_id:
        selected_carrera = Carrera.objects.get(pk=selected_carrera_id)
        pdfs = PDF.objects.filter(id_carrera=selected_carrera)

    return render(request, 'carrera_pdf_list.html',
                  {'carreras': carreras, 'pdfs': pdfs, 'selected_carrera_id': selected_carrera_id})


def procesar_lista(contenido):
    # Dividir el contenido en párrafos
    parrafos = contenido.split('\n\n')

    # Iniciar el contenido HTML
    html_contenido = ''

    # Recorrer los párrafos y agregarlos al contenido HTML
    for parrafo in parrafos:
        # Dividir el párrafo en elementos de la lista
        items = parrafo.split('-')

        # Si el delimitador "-" no funcionó, intentar con ""
        if len(items) == 1:
            items = parrafo.split("")
        # Iniciar la lista HTML para el párrafo
        lista_html = '<ul>'

        # Recorrer los elementos y agregarlos a la lista HTML
        for item in items:
            # Eliminar espacios en blanco al inicio y final de cada elemento
            item = item.strip()
            # Si el elemento no está vacío, agregarlo a la lista HTML
            if item:
                lista_html += f'<li>{item}</li>'

        # Cerrar la lista HTML para el párrafo
        lista_html += '</ul>'

        # Agregar la lista HTML al contenido HTML
        html_contenido += lista_html

    return html_contenido


def pdf_to_html(request):
    pdf_id = request.GET.get('pdf_id')
    if pdf_id:
        # Obtener el objeto PDF correspondiente a la ID proporcionada
        pdf_instance = PDF.objects.get(id=pdf_id)
        identificacion = {
            'nombre': pdf_instance.nombre,
            'materia': pdf_instance.materia,
            'codigo': pdf_instance.codigo,
            'condicion': pdf_instance.condicion,
            'carrera': pdf_instance.carrera,
            'curso': pdf_instance.curso,
            'semestre': pdf_instance.semestre,
            'requisitos': pdf_instance.requisitos,
            'cargaSemanal': pdf_instance.cargaSemanal,
            'cargaSemestral': pdf_instance.cargaSemestral,
        }
        secciones = {
            'fundamentacion': pdf_instance.fundamentacion,
            'objetivos': procesar_lista(pdf_instance.objetivos),
            'contenido': pdf_instance.contenido.replace('\n', '<br>'),
            'metodologia': procesar_lista(pdf_instance.metodologia),
            'evaluacion': pdf_instance.evaluacion.replace('\n', '<br>'),
            'bibliografia': procesar_lista(pdf_instance.bibliografia),
        }

        html_content = render_to_string('pdf_to_html_template.html',
                                        {'nombre_archivo': pdf_instance.nombre, 'identificacion': identificacion,
                                         'secciones': secciones})
        return HttpResponse(html_content)
    else:
        return HttpResponse("No se proporcionó ninguna ID de PDF.")


def eliminar_encabezados_pies_pagina(page):
    # Obtener el tamaño de la página
    width, height = page.width, page.height

    # Recortar la página para eliminar los encabezados
    page = page.within_bbox((0, 0, width, height))

    # Extraer el texto de la página
    page_text = page.extract_text()

    # Eliminar cualquier texto que contenga "Página [número]"
    page_text_lines = page_text.split('\n')
    page_text_filtered = []

    for line in page_text_lines:
        if not line.startswith("Página "):
            # Si la línea no comienza con "Página ", la agregamos sin modificaciones
            page_text_filtered.append(line)
        else:
            # Si la línea comienza con "Página ", la ignoramos
            continue

    # Eliminar la frase "Carrera de Ingeniería en Informática Facultad de Ciencias Tecnológicas – UNC@" si aparece como una frase completa
    page_text_filtered = [
        line.replace("Carrera de Ingeniería en Informática Facultad de Ciencias Tecnológicas – UNC@", "") for line in
        page_text_filtered]

    # Unir las líneas con saltos de línea
    page_text_filtered = '\n'.join(page_text_filtered)

    return page_text_filtered


def importar_pdf(request):
    if request.method == 'POST' and request.FILES.getlist('pdf_files'):
        pdf_files = request.FILES.getlist('pdf_files')

        for pdf_file in pdf_files:
            file_data = BytesIO(pdf_file.read())
            pdf_document = pdfplumber.open(file_data)

            text = ""
            for page_number in range(len(pdf_document.pages)):
                page = pdf_document.pages[page_number]

                # Eliminar encabezados y pies de página
                page_text = eliminar_encabezados_pies_pagina(page)

                text += page_text
            if not text:
                continue  # Si el texto está vacío, se pasa al siguiente archivo

            # Utilizar pdfplumber para obtener los títulos del PDF
            titles = []
            for page in pdf_document.pages:
                title_parts = []
                title = ""
                upper_count = 0
                for obj in page.chars:
                    if "Bold" in obj["fontname"]:
                        title += obj["text"]
                        if obj["text"].isupper():
                            upper_count += 1
                    elif title:
                        title_parts.extend(title.split('.')) if '.' in title else title_parts.append(title.strip())
                        title = ""
                for part in title_parts:
                    if part and len(part.strip()) > 8 and sum(1 for c in part if c.isupper()) >= 5:
                        titles.append(part.strip())

            nombre_archivo = pdf_file.name
            del titles[:2]

            # print(titles)
            # Identificar las secciones basadas en los títulos y sus ubicaciones en el texto
            secciones = {}
            patrones_secciones = titles

            for i in range(len(patrones_secciones)):
                start_idx = text.find(patrones_secciones[i])
                end_idx = text.find(patrones_secciones[i + 1]) if i + 1 < len(patrones_secciones) else len(text)
                secciones[patrones_secciones[i]] = text[start_idx:end_idx].strip()

            # Crear una nueva instancia
            pdf_instance = PDF(nombre=nombre_archivo)

            for titulo, texto in secciones.items():
                titulo_normalized = unidecode(titulo)  # Normalizar los caracteres
                if 'IDENTIFICACION' in titulo_normalized:
                    extraer_datos_identificacion(pdf_instance, texto)
                elif 'FUNDAMENTACION' in titulo_normalized:
                    partes_texto = texto.split('.')
                    if len(partes_texto) > 1:
                        texto_fundamentacion = '.'.join(partes_texto[1:-2]).strip()
                    else:
                        texto_fundamentacion = ''
                    pdf_instance.fundamentacion = texto_fundamentacion
                elif 'OBJETIVOS' in titulo_normalized:
                    partes_texto = texto.split('.')
                    if len(partes_texto) > 1:
                        texto_objetivos = '.'.join(partes_texto[1:-2]).strip()
                        if not texto_objetivos:
                            partes_texto = texto.split('\n')
                            print(partes_texto)
                            texto_objetivos = '\n'.join(partes_texto[1:-2]).strip()
                    else:
                        texto_objetivos = ''
                    pdf_instance.objetivos = texto_objetivos
                elif 'CONTENIDO' in titulo_normalized:
                    partes_texto = texto.split('.')
                    if len(partes_texto) > 1:
                        texto_contenido = '.'.join(partes_texto[1:-2]).strip()
                    else:
                        texto_contenido = ''
                    pdf_instance.contenido = texto_contenido
                elif 'METODOLOGIA' in titulo_normalized:
                    partes_texto = texto.split('.')
                    if len(partes_texto) > 1:
                        texto_metodologia = '.'.join(partes_texto[1:-2]).strip()
                    else:
                        texto_metodologia = ''
                    pdf_instance.metodologia = texto_metodologia
                elif 'EVALUACION' in titulo_normalized:
                    partes_texto = texto.split('.')
                    if len(partes_texto) > 1:
                        texto_evaluacion = '.'.join(partes_texto[1:-2]).strip()
                    else:
                        texto_evaluacion = ''
                    pdf_instance.evaluacion = texto_evaluacion
                elif 'BIBLIOGRAFIA' in titulo_normalized:
                    partes_texto = texto.split('\n')
                    print(partes_texto)
                    if len(partes_texto) > 1:
                        texto_bibliografia = '\n'.join(partes_texto[1:]).strip()
                    else:
                        texto_bibliografia = ''
                    pdf_instance.bibliografia = texto_bibliografia
            # Guardar la instancia en la base de datos
            pdf_instance.save()

        return redirect('import_success')
    return render(request, 'import_pdf.html')


def extraer_datos_identificacion(pdf_instance, texto):
    lines = texto.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if 'nombre de la materia' in line.lower():
            pdf_instance.materia = extraer_valor(line, lines[i + 1])
        elif 'código' in line.lower():
            pdf_instance.codigo = extraer_valor(line, lines[i + 1])
        elif 'condición' in line.lower():
            pdf_instance.condicion = extraer_valor(line, lines[i + 1])
        elif 'carrera' in line.lower():
            pdf_instance.carrera = extraer_valor(line, lines[i + 1])
        elif 'curso' in line.lower():
            pdf_instance.curso = extraer_valor(line, lines[i + 1])
        elif 'semestre' in line.lower():
            pdf_instance.semestre = extraer_valor(line, lines[i + 1])
        elif 'requisitos' in line.lower():
            pdf_instance.requisitos = extraer_valor(line, lines[i + 1])
        elif 'semanal' in line.lower():
            pdf_instance.cargaSemanal = extraer_valor(line, lines[i + 1])
        elif 'semestral' in line.lower():
            pdf_instance.cargaSemestral = extraer_valor(line, lines[i + 1])


def extraer_valor(linea_actual, linea_siguiente):
    # Si la línea actual contiene un ':', lo dividimos y tomamos el segundo elemento
    if ':' in linea_actual:
        valor = linea_actual.split(':', 1)[1].strip()
        valor = valor.replace(':', '').strip()
        # Si el valor de la línea actual no está vacío después de eliminar los dos puntos, lo retornamos
        if valor:
            return valor

    # Si la línea siguiente no está vacía, la retornamos como valor
    if linea_siguiente.strip():
        valor_siguiente = linea_siguiente.replace(':', '').strip()
        if valor_siguiente:
            return valor_siguiente

    return None

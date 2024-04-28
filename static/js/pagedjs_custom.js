class MyHandler extends Paged.Handler {
    constructor(chunker, polisher, caller) {
        super(chunker, polisher, caller);
    }

    beforeParsed(content) {
        // Crear el contenido del primer encabezado
        let header = document.createElement('p');
        header.innerHTML = 'UNIVERSIDAD NACIONAL DE CAAGUAZU<br>Con sede en Coronel Oviedo<br><b>FACULTAD DE CIENCIAS Y TECNOLOGÍAS</b><br>CARRERA DE INGENIERIA EN INFORMÁTICA<br>PLAN CURRICULAR 2010<br><b>PROGRAMA DE ESTUDIOS</b>';
        header.className = 'header';
        content.prepend(header);

        // Crear el contenido del segundo encabezado como un párrafo con dos spans
        let header2 = document.createElement('p');
        let span1 = document.createElement('span');
        span1.innerHTML = 'Carrera de Ingeniería en Informática';
        span1.className = 'left-span';
        let span2 = document.createElement('span');
        span2.innerHTML = 'Facultad de Ciencias Tecnológicas – UNC@';
        span2.className = 'right-span';
        header2.appendChild(span1);
        header2.appendChild(span2);
        header2.className = 'header2';
        content.prepend(header2);
    }
}

Paged.registerHandlers(MyHandler);

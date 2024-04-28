class MyHandler extends Paged.Handler {
    constructor(chunker, polisher, caller) {
        super(chunker, polisher, caller);
    }

    beforeParsed(content) {
        // Crear el contenido
        let header2 = document.createElement('p');
        header2.innerHTML = 'UNIVERSIDAD NACIONAL DE CAAGUAZU<br>Con sede en Coronel Oviedo<br>';
        header2.className = 'header2';
        content.prepend(header2);
    }
}

Paged.registerHandlers(MyHandler);

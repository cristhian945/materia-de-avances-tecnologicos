class AplicacionMascotas {
    constructor() {
        this.imagenSeleccionada = null;
        this.inicializarEventos();
        this.verificarServidor();
    }

    inicializarEventos() {
        // Chat
        document.getElementById('btn-enviar').addEventListener('click', () => this.enviarMensaje());
        document.getElementById('entrada-usuario').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.enviarMensaje();
        });

        // Clasificador de imágenes
        const areaSubida = document.getElementById('area-subida');
        const entradaImagen = document.getElementById('entrada-imagen');

        areaSubida.addEventListener('click', () => entradaImagen.click());
        areaSubida.addEventListener('dragover', (e) => this.manejarArrastreSobre(e));
        areaSubida.addEventListener('dragleave', (e) => this.manejarArrastreSale(e));
        areaSubida.addEventListener('drop', (e) => this.manejarSoltar(e));

        entradaImagen.addEventListener('change', (e) => this.manejarSeleccionImagen(e));
        
        document.getElementById('btn-clasificar').addEventListener('click', () => this.clasificarImagen());
    }

    async verificarServidor() {
        try {
            const respuesta = await fetch('/api/salud');
            const datos = await respuesta.json();
            console.log('✅ Servidor:', datos);
        } catch (error) {
            console.error('❌ Servidor no disponible:', error);
            this.mostrarResultado('❌ Error: Servidor no disponible', 'error');
        }
    }

    // Funciones del Chat
    async enviarMensaje() {
        const entrada = document.getElementById('entrada-usuario');
        const mensaje = entrada.value.trim();
        const boton = document.getElementById('btn-enviar');

        if (!mensaje) return;

        // Deshabilitar temporalmente
        entrada.disabled = true;
        boton.disabled = true;

        this.agregarMensaje(mensaje, 'usuario');
        entrada.value = '';

        try {
            const respuesta = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ mensaje: mensaje })
            });

            const datos = await respuesta.json();
            
            if (datos.respuesta) {
                this.agregarMensaje(datos.respuesta, 'bot');
            } else {
                this.agregarMensaje('❌ Error: No se pudo obtener respuesta', 'bot');
            }
        } catch (error) {
            this.agregarMensaje('❌ Error de conexión con el servidor', 'bot');
        } finally {
            // Rehabilitar
            entrada.disabled = false;
            boton.disabled = false;
            entrada.focus();
        }
    }

    agregarMensaje(texto, remitente) {
        const contenedorMensajes = document.getElementById('mensajes-chat');
        const divMensaje = document.createElement('div');
        divMensaje.className = `mensaje mensaje-${remitente}`;
        divMensaje.textContent = texto;
        
        contenedorMensajes.appendChild(divMensaje);
        contenedorMensajes.scrollTop = contenedorMensajes.scrollHeight;
    }

    // Funciones del Clasificador de Imágenes
    manejarArrastreSobre(e) {
        e.preventDefault();
        e.currentTarget.classList.add('drag-over');
    }

    manejarArrastreSale(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');
    }

    manejarSoltar(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');
        
        const archivos = e.dataTransfer.files;
        this.procesarArchivos(archivos);
    }

    manejarSeleccionImagen(e) {
        const archivos = e.target.files;
        this.procesarArchivos(archivos);
    }

    procesarArchivos(archivos) {
        if (archivos.length === 0) return;
        
        const archivo = archivos[0];
        if (!archivo.type.startsWith('image/')) {
            this.mostrarResultado('❌ Por favor, selecciona un archivo de imagen válido', 'error');
            return;
        }

        this.imagenSeleccionada = archivo;
        this.mostrarVistaPrevia(archivo);
        document.getElementById('btn-clasificar').disabled = false;
    }

    mostrarVistaPrevia(archivo) {
        const lector = new FileReader();
        const vistaPrevia = document.getElementById('vista-previa');
        
        lector.onload = (e) => {
            vistaPrevia.innerHTML = `
                <img src="${e.target.result}" alt="Vista previa" class="imagen-previa">
                <p><small>${archivo.name}</small></p>
            `;
        };

        lector.readAsDataURL(archivo);
    }

    async clasificarImagen() {
        if (!this.imagenSeleccionada) return;

        const boton = document.getElementById('btn-clasificar');
        const resultados = document.getElementById('resultados');

        boton.disabled = true;
        boton.textContent = '🔄 Clasificando...';
        boton.classList.add('procesando');
        resultados.innerHTML = '<div class="estado-carga">Procesando imagen...</div>';

        try {
            const formData = new FormData();
            formData.append('imagen', this.imagenSeleccionada);

            const respuesta = await fetch('/api/clasificar', {
                method: 'POST',
                body: formData
            });

            const resultado = await respuesta.json();

            if (resultado.exito) {
                this.mostrarResultado(
                    `🎯 Resultado: ${resultado.resultado} (Confianza: ${resultado.confianza})`,
                    'exito'
                );
            } else {
                this.mostrarResultado(`❌ Error: ${resultado.error}`, 'error');
            }
        } catch (error) {
            this.mostrarResultado('❌ Error de conexión con el servidor', 'error');
        } finally {
            boton.disabled = false;
            boton.textContent = 'Clasificar Imagen';
            boton.classList.remove('procesando');
        }
    }

    mostrarResultado(mensaje, tipo) {
        const resultados = document.getElementById('resultados');
        const divResultado = document.createElement('div');
        divResultado.className = `resultado ${tipo}`;
        divResultado.textContent = mensaje;
        resultados.innerHTML = '';
        resultados.appendChild(divResultado);
    }
}

// Inicializar la aplicación cuando se cargue la página
document.addEventListener('DOMContentLoaded', () => {
    new AplicacionMascotas();
});
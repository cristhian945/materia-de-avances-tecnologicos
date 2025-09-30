from flask import Flask, render_template, request, jsonify
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
import numpy as np
from PIL import Image
import io
import requests
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Cargar variables del entorno
load_dotenv()

app = Flask(__name__)

# Configuración
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '').strip()
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
PORT = int(os.getenv('PORT', 5000))

print("=" * 60)
print("🐾 CLASIFICADOR DE MASCOTAS CON GEMINI 1.5")
print("=" * 60)
print(f"🔑 Gemini API Key: {'✅ CONFIGURADA' if GEMINI_API_KEY else '❌ NO CONFIGURADA'}")
if GEMINI_API_KEY:
    print(f"   Key: {GEMINI_API_KEY[:12]}...{GEMINI_API_KEY[-6:]}")
print(f"🌐 Puerto: {PORT}")
print("=" * 60)

# Configurar Gemini si hay API key
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("✅ Gemini 1.5 Flash - Configurado correctamente")
        GEMINI_ACTIVO = True
    except Exception as e:
        print(f"❌ Gemini - Error en configuración: {e}")
        GEMINI_ACTIVO = False
else:
    print("ℹ️  Gemini - Usando modo local (sin API)")
    GEMINI_ACTIVO = False

# Cargar modelo de TensorFlow
try:
    model = MobileNetV2(weights='imagenet')
    print("✅ TensorFlow - Modelo cargado correctamente")
except Exception as e:
    print(f"❌ TensorFlow - Error: {e}")
    model = None

class ClasificadorImagenes:
    def __init__(self):
        self.model = model
        self.tamaño_imagen = 224
    
    def clasificar(self, img):
        """Clasificar imagen como perro o gato"""
        if self.model is None:
            return "❌ Modelo no disponible", 0.0
        
        try:
            # Preprocesar imagen
            img = img.resize((self.tamaño_imagen, self.tamaño_imagen))
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)
            
            # Predecir
            predicciones = self.model.predict(img_array, verbose=0)
            resultados = decode_predictions(predicciones, top=5)[0]
            
            # Buscar perros y gatos
            for _, nombre, confianza in resultados:
                confianza_float = float(confianza)
                if 'dog' in nombre.lower():
                    return '🐕 PERRO', confianza_float
                elif 'cat' in nombre.lower():
                    return '🐈 GATO', confianza_float
            
            # Si no encuentra, devolver el primer resultado
            primer_resultado = resultados[0]
            return f'❓ {primer_resultado[1]}', primer_resultado[2]
            
        except Exception as e:
            return f'❌ Error: {str(e)}', 0.0

class ChatBot:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.gemini_activo = GEMINI_ACTIVO
        
        if self.gemini_activo:
            print("🤖 ChatBot: Modo Gemini 1.5 Activado - Respuestas naturales")
        else:
            print("🤖 ChatBot: Modo Local - Respuestas predefinidas")
    
    def enviar_mensaje(self, mensaje):
        """Enviar mensaje - Gemini 1.5 para respuestas naturales"""
        mensaje = mensaje.strip()
        
        if not mensaje:
            return "Por favor, escribe un mensaje."
        
        # SI GEMINI ESTÁ ACTIVO, USARLO SIEMPRE
        if self.gemini_activo:
            print(f"🔗 Enviando a Gemini: '{mensaje}'")
            return self._usar_gemini_natural(mensaje)
        else:
            # Modo local sin API key
            return self._respuesta_local_natural(mensaje.lower())
    
    def _usar_gemini_natural(self, mensaje):
        """Usar Gemini 1.5 para respuestas conversacionales y naturales"""
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Eres un veterinario virtual amable y experto en mascotas, especialmente perros y gatos.
            
            INSTRUCCIONES IMPORTANTES:
            - Responde en español de manera NATURAL y CONVERSACIONAL
            - NO uses listas con puntos • ni formato markdown
            - NO uses asteriscos * ni guiones -
            - Habla como si estuvieras conversando con un amigo
            - Sé útil, práctico y específico
            - Mantén las respuestas entre 50-200 palabras
            - Si no sabes algo, admítelo amablemente
            - Enfócate en información práctica sobre mascotas
            
            Pregunta del usuario: "{mensaje}"
            
            Respuesta natural y conversacional:
            """
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.8,
                    top_p=0.9,
                    top_k=40
                )
            )
            
            respuesta = response.text.strip()
            
            # Limpiar la respuesta de formatos no deseados
            respuesta = self._limpiar_respuesta(respuesta)
            
            print(f"✅ Gemini respondió: {respuesta[:80]}...")
            return respuesta
            
        except Exception as e:
            error_msg = f"Error al conectar con Gemini: {str(e)}. Estoy usando respuestas locales por ahora."
            print(f"❌ {error_msg}")
            return self._respuesta_local_natural(mensaje.lower())
    
    def _limpiar_respuesta(self, texto):
        """Limpiar formato de la respuesta para hacerla más natural"""
        # Remover puntos de lista y otros formatos
        lineas_limpias = []
        for linea in texto.split('\n'):
            linea = linea.strip()
            if linea.startswith('•') or linea.startswith('-') or linea.startswith('*'):
                # Convertir puntos de lista a texto normal
                linea = linea[1:].strip()
                if linea and not linea[0].isupper():
                    linea = linea[0].upper() + linea[1:]
            elif linea.startswith('**') and linea.endswith('**'):
                # Remover markdown de negrita
                linea = linea[2:-2]
            
            if linea and not linea.startswith('#'):
                lineas_limpias.append(linea)
        
        # Unir en párrafos naturales
        respuesta_final = ' '.join(lineas_limpias)
        
        # Asegurar que empiece con mayúscula y termine con punto
        if respuesta_final and not respuesta_final[0].isupper():
            respuesta_final = respuesta_final[0].upper() + respuesta_final[1:]
        if respuesta_final and not respuesta_final.endswith(('.', '!', '?')):
            respuesta_final += '.'
            
        return respuesta_final
    
    def _respuesta_local_natural(self, mensaje):
        """Respuestas locales en formato conversacional (sin puntos)"""
        if any(palabra in mensaje for palabra in ['hola', 'buenos', 'buenas']):
            return "¡Hola! Soy tu asistente veterinario virtual. Me encanta ayudar con todo lo relacionado a perros y gatos. ¿En qué puedo ayudarte hoy?"
        
        elif 'perro' in mensaje and 'aliment' in mensaje:
            return "La alimentación de los perros es muy importante y depende de varios factores como su edad, raza y nivel de actividad. Los cachorros necesitan comida rica en proteínas para su crecimiento, mientras los perros adultos requieren una dieta balanceada. Es fundamental elegir un alimento de calidad y controlar las porciones para mantener un peso saludable."
        
        elif 'gato' in mensaje and 'aliment' in mensaje:
            return "Los gatos son carnívoros estrictos, lo que significa que necesitan una dieta basada principalmente en proteínas animales. Es importante ofrecerles alimento húmedo y seco de alta calidad, controlar las porciones para evitar sobrepeso, y asegurarse de que siempre tengan agua fresca disponible. Los gatos tienden a beber poca agua, por lo que el alimento húmedo ayuda a mantenerlos hidratados."
        
        elif 'perro' in mensaje and 'ejercicio' in mensaje:
            return "El ejercicio es esencial para la salud física y mental de los perros. La cantidad varía según la raza y edad: los perros activos como los border collies necesitan mucho ejercicio diario, mientras que razas más tranquilas o braquicéfalas requieren menos. Los paseos diarios, el juego y la socialización son actividades importantes para su bienestar."
        
        elif 'gato' in mensaje and 'juego' in mensaje:
            return "Los gatos necesitan juego y estimulación mental diaria para mantenerse felices y saludables. Juguetes interactivos como varitas con plumas, pelotas y rascadores son excelentes opciones. El juego no solo los mantiene activos sino que también fortalece el vínculo contigo. Es importante rotar los juguetes para mantener su interés."
        
        elif 'vacuna' in mensaje:
            return "Las vacunas son fundamentales para proteger la salud de perros y gatos. Los cachorros y gatitos necesitan un calendario inicial de vacunación, mientras los adultos requieren refuerzos anuales o según lo indique el veterinario. Las vacunas principales protegen contra enfermedades graves como el moquillo en perros y la panleucopenia en gatos."
        
        elif 'perro' in mensaje:
            return "Los perros son animales maravillosos y leales que forman fuertes vínculos con sus familias. Cada raza tiene características únicas en cuanto a energía, cuidado y personalidad. Lo más importante es proporcionarles amor, ejercicio adecuado, alimentación balanceada y atención veterinaria regular. ¿Hay algo específico sobre perros que te gustaría saber?"
        
        elif 'gato' in mensaje:
            return "Los gatos son animales fascinantes, independientes pero muy cariñosos con sus personas favoritas. Les encanta tener sus rutinas, espacios elevados para observar, y momentos de juego. Son expertos en comunicarse mediante el lenguaje corporal y los sonidos. ¿Te gustaría conocer más sobre algún aspecto específico de los gatos?"
        
        else:
            return "Como tu asistente veterinario virtual, puedo ayudarte con información sobre cuidados, alimentación, salud, comportamiento y entrenamiento de perros y gatos. Puedes preguntarme sobre temas específicos como alimentación adecuada, ejercicio, vacunas, comportamiento, o cualquier duda que tengas sobre tus mascotas. ¿En qué puedo ayudarte?"

# Crear instancias
clasificador = ClasificadorImagenes()
chatbot = ChatBot()

@app.route('/')
def inicio():
    info_app = {
        'gemini_activo': GEMINI_ACTIVO,
        'modelo_activo': model is not None
    }
    return render_template('index.html', info_app=info_app)

@app.route('/api/salud')
def salud():
    return jsonify({
        "estado": "ok",
        "mensaje": "Servidor funcionando correctamente",
        "modelo_tensorflow": "activado" if model is not None else "desactivado",
        "gemini_1.5": "activado" if GEMINI_ACTIVO else "desactivado",
        "modo_chat": "Gemini 1.5 Flash" if GEMINI_ACTIVO else "Modo Local"
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        datos = request.get_json()
        if not datos:
            return jsonify({"error": "No se recibieron datos"}), 400
            
        mensaje = datos.get('mensaje', '').strip()
        
        if not mensaje:
            return jsonify({"error": "El mensaje no puede estar vacío"}), 400
        
        respuesta = chatbot.enviar_mensaje(mensaje)
        return jsonify({
            "respuesta": respuesta,
            "gemini_utilizado": GEMINI_ACTIVO
        })
        
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

@app.route('/api/clasificar', methods=['POST'])
def clasificar_imagen():
    try:
        if 'imagen' not in request.files:
            return jsonify({"error": "No se envió ninguna imagen"}), 400
        
        archivo = request.files['imagen']
        if archivo.filename == '':
            return jsonify({"error": "No se seleccionó ningún archivo"}), 400
        
        # Verificar que sea una imagen
        if not archivo.content_type.startswith('image/'):
            return jsonify({"error": "El archivo debe ser una imagen"}), 400
        
        # Procesar imagen
        imagen = Image.open(archivo.stream)
        if imagen.mode != 'RGB':
            imagen = imagen.convert('RGB')
        
        resultado, confianza = clasificador.clasificar(imagen)
        
        return jsonify({
            "resultado": resultado,
            "confianza": f"{confianza * 100:.1f}%",
            "exito": True,
            "archivo": archivo.filename
        })
        
    except Exception as e:
        return jsonify({"error": f"Error procesando imagen: {str(e)}"}), 500

@app.route('/api/info')
def info():
    """Endpoint de información del sistema"""
    return jsonify({
        "aplicacion": "Clasificador de Mascotas con Gemini 1.5",
        "version": "2.0",
        "caracteristicas": {
            "clasificador_imagenes": True,
            "chatbot_gemini": GEMINI_ACTIVO,
            "modelo_tensorflow": model is not None
        },
        "estado": {
            "gemini": "conectado" if GEMINI_ACTIVO else "modo_local",
            "tensorflow": "activo" if model is not None else "inactivo"
        }
    })

if __name__ == '__main__':
    print("\n🎯 ESTADO DEL SISTEMA:")
    print(f"   📸 Clasificador de imágenes: {'✅ LISTO' if model else '❌ INACTIVO'}")
    print(f"   💬 Chatbot: {'✅ GEMINI 1.5' if GEMINI_ACTIVO else '🔶 MODO LOCAL'}")
    print(f"   🌐 Servidor: http://localhost:{PORT}")
    print("\n🚀 Iniciando servidor...")
    app.run(debug=DEBUG, host='0.0.0.0', port=PORT)
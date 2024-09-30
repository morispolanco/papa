import streamlit as st
import requests
import json

# Obtener las claves API desde los secretos de Streamlit
serper_api_key = st.secrets["SERPER_API_KEY"]
together_api_key = st.secrets["TOGETHER_API_KEY"]

# Configurar los encabezados para las APIs
serper_headers = {
    "X-API-KEY": serper_api_key,
    "Content-Type": "application/json"
}

together_headers = {
    "Authorization": f"Bearer {together_api_key}",
    "Content-Type": "application/json"
}

st.title("Análisis de Declaraciones del Papa Francisco por Año")

# Entrada del usuario para el año
anio = st.number_input("Ingrese un año para analizar las declaraciones del Papa Francisco:", min_value=2013, max_value=2024, step=1)

if st.button("Analizar"):
    if anio:
        # Paso 1: Utilizar la API de Serper para buscar declaraciones del año especificado
        consulta = f"Declaraciones del Papa Francisco en {anio}"
        serper_url = 'https://google.serper.dev/search'
        serper_payload = {
            "q": consulta
        }

        respuesta_serper = requests.post(serper_url, headers=serper_headers, data=json.dumps(serper_payload))
        if respuesta_serper.status_code == 200:
            resultados_busqueda = respuesta_serper.json()

            declaraciones = []
            # Intentar obtener contenido más largo de la sección 'peopleAlsoAsk'
            if 'peopleAlsoAsk' in resultados_busqueda:
                for item in resultados_busqueda['peopleAlsoAsk']:
                    respuesta = item.get('answer', '')
                    if respuesta:
                        declaraciones.append({
                            'declaracion': respuesta,
                            'fuente': item.get('link', '')
                        })

            # Si no hay contenido en 'peopleAlsoAsk', usar 'organic' results
            if not declaraciones:
                for resultado in resultados_busqueda.get('organic', []):
                    # Usar 'description' si está disponible, que suele ser más larga
                    descripcion = resultado.get('description', '')
                    link = resultado.get('link', '')
                    if descripcion and link:
                        declaraciones.append({
                            'declaracion': descripcion,
                            'fuente': link
                        })
                    elif resultado.get('snippet', '') and link:
                        declaraciones.append({
                            'declaracion': resultado.get('snippet', ''),
                            'fuente': link
                        })

            if not declaraciones:
                st.warning("No se encontraron declaraciones en los resultados de búsqueda.")
            else:
                # Mostrar las declaraciones y sus fuentes en la aplicación
                texto_combinado = ""
                for idx, item in enumerate(declaraciones, 1):
                    texto_combinado += f"Declaración {idx}:\n{item['declaracion']}\nFuente: {item['fuente']}\n\n"

                # Paso 2: Utilizar la API de Together para analizar las declaraciones
                together_url = "https://api.together.xyz/v1/chat/completions"
                mensajes = [
                    {"role": "system", "content": "Eres un experto en teología católica. Analiza cuidadosamente las declaraciones proporcionadas, asegurándote de ser preciso y objetivo."},
                    {"role": "user", "content": f"A continuación se presentan declaraciones del Papa Francisco del año {anio}. Identifica únicamente las que no están en concordancia con la fe y la tradición católica. Por cada declaración contraria, explica por qué lo es y cita las fuentes proporcionadas:\n{texto_combinado}"}
                ]

                together_payload = {
                    "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                    "messages": mensajes,
                    "max_tokens": 2512,
                    "temperature": 0.7,
                    "top_p": 0.7,
                    "top_k": 50,
                    "repetition_penalty": 1,
                    "stop": ["<|eot_id|>"],
                    "stream": False
                }

                respuesta_together = requests.post(together_url, headers=together_headers, data=json.dumps(together_payload))
                if respuesta_together.status_code == 200:
                    analisis = respuesta_together.json()
                    # Extraer la respuesta del asistente
                    respuesta_asistente = analisis.get('choices', [{}])[0].get('message', {}).get('content', '')
                    st.subheader("Declaraciones No Concordantes con la Fe Católica:")
                    if respuesta_asistente.strip():
                        st.write(respuesta_asistente)
                    else:
                        st.write("No se encontraron declaraciones que no estén en concordancia con la fe y tradición católica.")
                else:
                    st.error("Error al analizar las declaraciones con la API de Together.")
        else:
            st.error("Error al obtener resultados de búsqueda con la API de Serper.")
    else:
        st.warning("Por favor, ingrese un año para analizar.")

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

st.title("Análisis de Declaraciones del Papa Francisco con Fuentes")

# Entrada del usuario para el tema
tema = st.text_input("Ingrese un tema para analizar las declaraciones del Papa Francisco:")

if st.button("Analizar"):
    if tema:
        # Paso 1: Utilizar la API de Serper para buscar declaraciones
        consulta = f"Declaraciones del Papa Francisco sobre {tema}"
        serper_url = 'https://google.serper.dev/search'
        serper_payload = {
            "q": consulta
        }

        respuesta_serper = requests.post(serper_url, headers=serper_headers, data=json.dumps(serper_payload))
        if respuesta_serper.status_code == 200:
            resultados_busqueda = respuesta_serper.json()
            # Extraer fragmentos y fuentes de los resultados de búsqueda
            fragmentos_fuentes = []
            for resultado in resultados_busqueda.get('organic', []):
                snippet = resultado.get('snippet', '')
                link = resultado.get('link', '')
                if snippet and link:
                    fragmentos_fuentes.append((snippet, link))

            if not fragmentos_fuentes:
                st.warning("No se encontraron declaraciones en los resultados de búsqueda.")
            else:
                # Mostrar las declaraciones y sus fuentes en la aplicación
                texto_combinado = ""
                for idx, (fragmento, fuente) in enumerate(fragmentos_fuentes, 1):
                    texto_combinado += f"Declaración {idx}:\n{fragmento}\nFuente: {fuente}\n\n"

                # Paso 2: Utilizar la API de Together para analizar las declaraciones
                together_url = "https://api.together.xyz/v1/chat/completions"
                mensajes = [
                    {"role": "system", "content": "Eres un teólogo católico que analiza declaraciones para verificar si son contrarias al dogma y a la fe católica."},
                    {"role": "user", "content": f"A continuación tienes varias declaraciones del Papa Francisco sobre el tema '{tema}'. Evalúa cada una y solo devuelve las que son contrarias al dogma y a la fe católica, con una explicación de por qué son contrarias:\n{texto_combinado}"}
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

                    if respuesta_asistente.strip():
                        st.subheader("Declaraciones Contrarias al Dogma y Fe Católicas:")
                        st.write(respuesta_asistente)
                    else:
                        st.info("No se encontraron declaraciones contrarias al dogma y la fe católica.")
                else:
                    st.error("Error al analizar las declaraciones con la API de Together.")
        else:
            st.error("Error al obtener resultados de búsqueda con la API de Serper.")
    else:
        st.warning("Por favor, ingrese un tema para analizar.")

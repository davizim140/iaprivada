import streamlit as st 
import g4f 
import asyncio 
import urllib.parse 

st.set_page_config(page_title="Assistente Grok-like", page_icon="🤖", layout="centered") 

st.title("🤖 Assistente Estilo Grok") 
st.write("Mande sua dúvida na velocidade da luz, envie arquivos/fotos ou peça para gerar uma imagem.") 

# Opção de upload de arquivos e imagens na interface
uploaded_file = st.file_uploader(
    "Envie uma imagem ou arquivo para análise (opcional):", 
    type=["png", "jpg", "jpeg", "pdf", "txt", "csv"]
)

if "messages" not in st.session_state: 
    # Instrução de sistema configurada com a personalidade do Grok
    st.session_state.messages = [ 
        {
            "role": "system", 
            "content": (
                "Você é um assistente com a personalidade do Grok. "
                "Você é espirituoso, irônico, sarcástico, vai direto ao ponto sem enrolação corporativa, "
                "adora cultura pop e memes, e responde rápido. "
                "Responda sempre em português do Brasil. Nunca mostre seu raciocínio interno."
            )
        } 
    ] 

# Exibe mensagens pulando a instrução de sistema oculta 
for message in st.session_state.messages: 
    if message["role"] == "system": 
        continue 
    with st.chat_message(message["role"]): 
        st.markdown(message["content"]) 
        if "image_url" in message and message["image_url"]: 
            st.image(message["image_url"]) 

def gerar_resposta_ia(formatted_messages): 
    try: 
        try: 
            loop = asyncio.get_event_loop() 
        except RuntimeError: 
            loop = asyncio.new_event_loop() 
        asyncio.set_event_loop(loop) 
        
        resposta = g4f.ChatCompletion.create( 
            model=g4f.models.default, 
            messages=formatted_messages, 
        ) 
        return resposta 
    except Exception as e: 
        return f"Deu ruim na velocidade da luz: {e}" 

if prompt := st.chat_input("Mande sua braba..."): 
    st.session_state.messages.append({"role": "user", "content": prompt}) 
    with st.chat_message("user"): 
        st.markdown(prompt) 
        if uploaded_file is not None:
            if uploaded_file.type in ["image/png", "image/jpeg", "image/jpg"]:
                st.image(uploaded_file, width=250)
            else:
                st.info(f"Arquivo anexado: {uploaded_file.name}")

    is_image_request = any(palavra in prompt.lower() for palavra in ["gere uma imagem", "crie uma imagem", "desenhe", "gerar imagem"]) 
    
    with st.chat_message("assistant"): 
        message_placeholder = st.empty() 
        message_placeholder.markdown("Processando à milhão...") 
        image_url = None 
        
        if is_image_request: 
            prompt_encoded = urllib.parse.quote(prompt) 
            image_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}" 
            resposta = f"Toma aí a sua obra-prima gerada na base do caos: '{prompt}'" 
            message_placeholder.markdown(resposta) 
            st.image(image_url) 
        else: 
            formatted_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if "content" in m] 
            resposta = gerar_resposta_ia(formatted_messages) 
            
            # Exibe a resposta de uma vez, corrigindo o erro de renderização de espaçamento
            message_placeholder.markdown(resposta) 
            
        msg_dict = {"role": "assistant", "content": resposta} 
        if image_url: 
            msg_dict["image_url"] = image_url 
        st.session_state.messages.append(msg_dict) 
        
        st.rerun()

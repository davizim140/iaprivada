import streamlit as st 
import g4f 
import asyncio 
import urllib.parse 

st.set_page_config(page_title="Assistente Grok-like", page_icon="🤖", layout="centered") 

st.title("🤖 Assistente Estilo Grok") 
st.write("Mande sua dúvida, cole ou anexe arquivos/fotos direto na barra abaixo, ou peça para gerar uma imagem.") 

if "messages" not in st.session_state: 
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

for message in st.session_state.messages: 
    if message["role"] == "system": 
        continue 
    with st.chat_message(message["role"]): 
        st.markdown(message["content"]) 
        if "image_url" in message and message["image_url"]: 
            st.image(message["image_url"]) 
        if "file_info" in message and message["file_info"]:
            st.info(f"Arquivo anexado: {message['file_info']}")

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

# Barra de chat com suporte nativo a anexos (botão e Ctrl+V de arquivos/imagens)
chat_input_dict = st.chat_input("Mande sua braba ou anexe um arquivo...", accept_file="multiple")

if chat_input_dict:
    prompt = chat_input_dict.text if hasattr(chat_input_dict, "text") else chat_input_dict.get("text", "")
    files = chat_input_dict.files if hasattr(chat_input_dict, "files") else chat_input_dict.get("files", [])
    
    file_name_display = None
    if files:
        file_name_display = files[0].name

    # Adiciona a mensagem do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt, "file_info": file_name_display}) 
    
    with st.chat_message("user"): 
        if prompt:
            st.markdown(prompt)
        if files:
            for f in files:
                if f.type and f.type.startswith("image/"):
                    st.image(f, width=250)
                else:
                    st.info(f"Arquivo anexado: {f.name}")

    is_image_request = any(palavra in prompt.lower() for palavra in ["gere uma imagem", "crie uma imagem", "desenhe", "gerar imagem"]) if prompt else False
    
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
            message_placeholder.markdown(resposta) 
            
        msg_dict = {"role": "assistant", "content": resposta, "file_info": file_name_display} 
        if image_url: 
            msg_dict["image_url"] = image_url 
        st.session_state.messages.append(msg_dict) 
        
        st.rerun()

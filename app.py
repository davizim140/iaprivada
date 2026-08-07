import streamlit as st 
import g4f 
import asyncio 
import urllib.parse 
import uuid

st.set_page_config(page_title="Assistente Grok-like", page_icon="🤖", layout="centered") 

# Gerencia ou recupera um ID único de dispositivo via session_state (vinculado à aba/sessão do navegador)
if "device_id" not in st.session_state:
    st.session_state.device_id = str(uuid.uuid4())

# Estrutura de múltiplos históricos por dispositivo salvos na sessão
if "historico_chats" not in st.session_state:
    st.session_state.historico_chats = {
        "Chat Principal": [
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
    }

if "chat_ativo" not in st.session_state:
    st.session_state.chat_ativo = "Chat Principal"

# Barra lateral para gerenciar o histórico de conversas do dispositivo
with st.sidebar:
    st.title("📂 Histórico do Dispositivo")
    st.caption(id_cur := f"ID: {st.session_state.device_id[:8]}...")
    
    if st.button("➕ Novo Chat", use_container_width=True):
        novo_nome = f"Chat {len(st.session_state.historico_chats) + 1}"
        st.session_state.historico_chats[novo_nome] = [st.session_state.historico_chats["Chat Principal"][0]]
        st.session_state.chat_ativo = novo_nome
        st.rerun()

    st.markdown("---")
    st.write("### Suas Conversas:")
    
    for nome_chat in list(st.session_state.historico_chats.keys()):
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.button(nome_chat, key=f"btn_{nome_chat}", use_container_width=True):
                st.session_state.chat_ativo = nome_chat
                st.rerun()
        with col2:
            if len(st.session_state.historico_chats) > 1:
                if st.button("🗑️", key=f"del_{nome_chat}"):
                    del st.session_state.historico_chats[nome_chat]
                    if st.session_state.chat_ativo == nome_chat:
                        st.session_state.chat_ativo = list(st.session_state.historico_chats.keys())[0]
                    st.rerun()

st.title("🤖 Assistente Estilo Grok") 
st.write(f"Conversando no chat: **{st.session_state.chat_ativo}**") 

# Pega as mensagens do chat selecionado atualmente
mensagens_atuais = st.session_state.historico_chats[st.session_state.chat_ativo]

# Exibe o histórico de mensagens do chat ativo
for message in mensagens_atuais: 
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

    # Adiciona a mensagem do usuário no histórico do chat ativo
    st.session_state.historico_chats[st.session_state.chat_ativo].append(
        {"role": "user", "content": prompt, "file_info": file_name_display}
    ) 
    
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
            formatted_messages = [{"role": m["role"], "content": m["content"]} for m in mensagens_atuais if "content" in m] 
            resposta = gerar_resposta_ia(formatted_messages) 
            message_placeholder.markdown(resposta) 
            
        msg_dict = {"role": "assistant", "content": resposta, "file_info": file_name_display} 
        if image_url: 
            msg_dict["image_url"] = image_url 
            
        st.session_state.historico_chats[st.session_state.chat_ativo].append(msg_dict) 
        st.rerun()

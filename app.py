import streamlit as st 
from google import genai
import urllib.parse 
import uuid

st.set_page_config(page_title="Assistente Grok-like Rápido", page_icon="🤖", layout="centered") 

# Inicializa o cliente oficial do Google Gemini
@st.cache_resource
def carregar_cliente():
    return genai.Client()

try:
    client = carregar_cliente()
except Exception:
    client = None

if "device_id" not in st.session_state:
    st.session_state.device_id = str(uuid.uuid4())

if "historico_chats" not in st.session_state:
    st.session_state.historico_chats = {
        "Chat Principal": [
            {
                "role": "user", 
                "content": (
                    "Instrução de Sistema: Você é um assistente com a personalidade do Grok. "
                    "Seja irônico, sarcástico, direto ao ponto e sem enrolação corporativa. "
                    "Responda sempre em português do Brasil e de forma muito rápida."
                )
            }
        ]
    }

if "chat_ativo" not in st.session_state:
    st.session_state.chat_ativo = "Chat Principal"

with st.sidebar:
    st.title("📂 Histórico")
    
    if st.button("➕ Novo Chat", use_container_width=True):
        novo_nome = f"Chat {len(st.session_state.historico_chats) + 1}"
        st.session_state.historico_chats[novo_nome] = [st.session_state.historico_chats["Chat Principal"][0]]
        st.session_state.chat_ativo = novo_nome
        st.rerun()

    st.markdown("---")
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

mensagens_atuais = st.session_state.historico_chats[st.session_state.chat_ativo]

for message in mensagens_atuais: 
    # Pula a instrução inicial exibida
    if message == mensagens_atuais[0] and "Instrução de Sistema" in message["content"]:
        continue
    with st.chat_message(message["role"]): 
        st.markdown(message["content"]) 
        if "image_url" in message and message["image_url"]: 
            st.image(message["image_url"]) 
        if "file_info" in message and message["file_info"]:
            st.info(f"Arquivo anexado: {message['file_info']}")

def gerar_resposta_gemini(mensagens, arquivo_enviado=None):
    if not client:
        return "Erro: Chave de API do Gemini não configurada nas Secrets do Streamlit."
    try:
        conteudo = []
        
        # Adiciona o contexto de personalidade
        conteudo.append(mensagens[0]["content"])
        
        # Adiciona o histórico recente
        for m in mensagens[1:]:
            prefixo = "Usuário: " if m["role"] == "user" else "Assistente: "
            conteudo.append(prefixo + m["content"])
            
        # Se houver arquivo anexado na hora, injeta no payload
        if arquivo_enviado is not None:
            bytes_arq = arquivo_enviado.read()
            conteudo.append({
                "mime_type": arquivo_enviado.type,
                "data": bytes_arq
            })

        resposta = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=conteudo
        )
        return resposta.text
    except Exception as e:
        return f"Deu ruim: {e}"

chat_input_dict = st.chat_input("Mande sua braba ou anexe um arquivo...", accept_file="multiple")

if chat_input_dict:
    prompt = chat_input_dict.text if hasattr(chat_input_dict, "text") else chat_input_dict.get("text", "")
    files = chat_input_dict.files if hasattr(chat_input_dict, "files") else chat_input_dict.get("files", [])
    
    file_name_display = files[0].name if files else None
    arquivo_objeto = files[0] if files else None

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
        message_placeholder.markdown("Respondendo na velocidade da luz...") 
        image_url = None 
        
        if is_image_request: 
            prompt_encoded = urllib.parse.quote(prompt) 
            image_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}" 
            resposta = f"Toma aí a sua obra-prima gerada na base do caos: '{prompt}'" 
            message_placeholder.markdown(resposta) 
            st.image(image_url) 
        else: 
            resposta = gerar_resposta_gemini(mensagens_atuais, arquivo_objeto) 
            message_placeholder.markdown(resposta) 
            
        msg_dict = {"role": "assistant", "content": resposta, "file_info": file_name_display} 
        if image_url: 
            msg_dict["image_url"] = image_url 
            
        st.session_state.historico_chats[st.session_state.chat_ativo].append(msg_dict) 
        st.rerun()

import streamlit as st 
import g4f 
import asyncio 
import urllib.parse 
import uuid
import io
import zipfile
import urllib.request

st.set_page_config(page_title="Assistente Grok-like com Arquivos ZIP", page_icon="🤖", layout="centered") 

if "device_id" not in st.session_state:
    st.session_state.device_id = str(uuid.uuid4())

if "historico_chats" not in st.session_state:
    st.session_state.historico_chats = {
        "Chat Principal": [
            {
                "role": "system", 
                "content": (
                    "Você é um assistente com a personalidade do Grok. "
                    "Seja irônico, sarcástico, direto ao ponto e sem enrolação corporativa. "
                    "Responda sempre em português do Brasil."
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

for idx, message in enumerate(mensagens_atuais): 
    if message["role"] == "system": 
        continue 
    with st.chat_message(message["role"]): 
        st.markdown(message["content"]) 
        if "image_url" in message and message["image_url"]: 
            st.image(message["image_url"]) 
        if "file_info" in message and message["file_info"]:
            st.info(f"Arquivo anexado: {message['file_info']}")
        
        if "gerar_arquivo" in message and message["gerar_arquivo"]:
            arq = message["gerar_arquivo"]
            st.download_button(
                label=f"📥 Baixar arquivo: {arq['nome']}",
                data=arq["conteudo"],
                file_name=arq["nome"],
                mime=arq.get("mime", "application/zip"),
                key=f"dl_history_{idx}"
            )

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
        return f"Deu ruim ao conectar com a IA gratuita: {e}" 

chat_input_dict = st.chat_input("Mande sua braba, peça um arquivo ou um .zip...", accept_file="multiple")

if chat_input_dict:
    prompt = chat_input_dict.text if hasattr(chat_input_dict, "text") else chat_input_dict.get("text", "")
    files = chat_input_dict.files if hasattr(chat_input_dict, "files") else chat_input_dict.get("files", [])
    
    file_name_display = files[0].name if files else None

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
        message_placeholder.markdown("Processando...") 
        image_url = None 
        dados_arquivo = None
        
        # Identifica se pediu um arquivo ZIP diretamente no texto
        is_zip_request = prompt and any(k in prompt.lower() for k in [".zip", "zip", "compactado"])
        
        if is_image_request and not is_zip_request: 
            prompt_encoded = urllib.parse.quote(prompt) 
            image_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}" 
            resposta = f"Toma aí a sua obra-prima gerada na base do caos: '{prompt}'" 
            message_placeholder.markdown(resposta) 
            st.image(image_url) 
        elif is_zip_request:
            # Tratamento automático via Python para criar arquivos .zip (mesmo se envolver imagens)
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                if "banana" in prompt.lower():
                    try:
                        # Baixa uma foto de banana automaticamente para dentro do zip
                        img_url = "https://image.pollinations.ai/prompt/banana%20realistic"
                        req = urllib.request.urlopen(img_url, timeout=5)
                        zip_file.writestr("banana.jpg", req.read())
                    except Exception:
                        zip_file.writestr("info.txt", "Não foi possível baixar a imagem da banana no momento.")
                
                # Se houver arquivos enviados pelo usuário, inclui todos no ZIP
                if files:
                    for f in files:
                        zip_file.writestr(f.name, f.getvalue())
                
                # Adiciona um txt genérico caso o zip estivesse vazio
                zip_file.writestr("pedido.txt", f"Solicitação do usuário: {prompt}")

            zip_buffer.seek(0)
            resposta = "Toma aí o seu arquivo .zip empacotado na marra."
            message_placeholder.markdown(resposta)
            
            dados_arquivo = {
                "nome": "arquivo_solicitado.zip",
                "conteudo": zip_buffer.getvalue(),
                "mime": "application/zip"
            }
            st.download_button(
                label="📥 Baixar arquivo .ZIP compactado",
                data=zip_buffer.getvalue(),
                file_name="arquivo_solicitado.zip",
                mime="application/zip",
                key="dl_current_zip"
            )
        else: 
            formatted_messages = [{"role": m["role"], "content": m["content"]} for m in mensagens_atuais if "content" in m] 
            resposta = gerar_resposta_ia(formatted_messages) 
            message_placeholder.markdown(resposta) 
            
        msg_dict = {"role": "assistant", "content": resposta, "file_info": file_name_display} 
        if image_url: 
            msg_dict["image_url"] = image_url 
        if dados_arquivo:
            msg_dict["gerar_arquivo"] = dados_arquivo
            
        st.session_state.historico_chats[st.session_state.chat_ativo].append(msg_dict) 
        st.rerun()

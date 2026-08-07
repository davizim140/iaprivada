import streamlit as st 
import g4f 
import asyncio 
import urllib.parse 
import uuid
import io
import zipfile

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
        
        # Exibe botão de download de arquivo individual ou ZIP salvo no histórico
        if "gerar_arquivo" in message and message["gerar_arquivo"]:
            arq = message["gerar_arquivo"]
            st.download_button(
                label=f"📥 Baixar arquivo: {arq['nome']}",
                data=arq["conteudo"],
                file_name=arq["nome"],
                mime=arq.get("mime", "text/plain"),
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
            
            if prompt and any(cmd in prompt.lower() for cmd in ["crie um arquivo", "salve", "faça um arquivo", "gere um arquivo", ".zip", "compactado"]):
                # Verifica se o usuário pediu especificamente um arquivo .zip
                if ".zip" in prompt.lower() or "compactado" in prompt.lower():
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        # Adiciona o texto gerado dentro de um arquivo padrão dentro do ZIP
                        zip_file.writestr("conteudo_gerado.txt", resposta)
                        # Se houver arquivo enviado pelo usuário, compacta ele junto no ZIP
                        if files:
                            for f in files:
                                zip_file.writestr(f.name, f.getvalue())
                    
                    zip_buffer.seek(0)
                    dados_arquivo = {
                        "nome": "projeto_assistente.zip",
                        "conteudo": zip_buffer.getvalue(),
                        "mime": "application/zip"
                    }
                    st.download_button(
                        label="📥 Baixar arquivo .ZIP compactado",
                        data=zip_buffer.getvalue(),
                        file_name="projeto_assistente.zip",
                        mime="application/zip",
                        key="dl_current_zip"
                    )
                else:
                    # Arquivo de texto comum (.txt, .py, etc)
                    nome_arquivo = "resposta_assistente.txt"
                    if "." in prompt:
                        for p in prompt.split():
                            if "." in p and len(p) > 3:
                                nome_arquivo = p.strip(".,'\"?!")
                                break
                    
                    dados_arquivo = {
                        "nome": nome_arquivo,
                        "conteudo": resposta.encode("utf-8"),
                        "mime": "text/plain"
                    }
                    st.download_button(
                        label=f"📥 Baixar arquivo: {nome_arquivo}",
                        data=resposta,
                        file_name=nome_arquivo,
                        mime="text/plain",
                        key="dl_current_txt"
                    )
            
        msg_dict = {"role": "assistant", "content": resposta, "file_info": file_name_display} 
        if image_url: 
            msg_dict["image_url"] = image_url 
        if dados_arquivo:
            msg_dict["gerar_arquivo"] = dados_arquivo
            
        st.session_state.historico_chats[st.session_state.chat_ativo].append(msg_dict) 
        st.rerun()

import streamlit as st
import g4f
import asyncio
import urllib.parse

st.set_page_config(page_title="Assistente Multimídia", page_icon="🎨", layout="centered")

st.title("🤖 Assistente com Imagens e Arquivos")
st.write("Digite o que quiser para conversar, peça imagens ou baixe as respostas em arquivo!")

if "messages" not in st.session_state:
    st.session_state.messages = []

for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        if "image_url" in message and message["image_url"]:
            st.image(message["image_url"])
            
        if message["role"] == "assistant" and "content" in message:
            st.download_button(
                label="📥 Baixar resposta (.txt)",
                data=message["content"],
                file_name=f"resposta_ia_{idx}.txt",
                mime="text/plain",
                key=f"download_{idx}"
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
        return f"Erro: {e}"

if prompt := st.chat_input("Digite sua dúvida ou peça uma imagem..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    is_image_request = any(palavra in prompt.lower() for palavra in ["gere uma imagem", "crie uma imagem", "desenhe", "gerar imagem"])

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Processando...")
        
        image_url = None
        
        if is_image_request:
            prompt_encoded = urllib.parse.quote(prompt)
            image_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}"
            resposta = f"Aqui está a imagem gerada com base no seu pedido: '{prompt}'"
            message_placeholder.markdown(resposta)
            st.image(image_url)
        else:
            formatted_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if "content" in m]
            resposta = gerar_resposta_ia(formatted_messages)
            message_placeholder.markdown(resposta)
        
        msg_dict = {"role": "assistant", "content": resposta}
        if image_url:
            msg_dict["image_url"] = image_url
            
        st.session_state.messages.append(msg_dict)
        st.rerun()
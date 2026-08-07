import streamlit as st
from google import genai

st.set_page_config(page_title="IA Privada Multimodal", page_icon="🤖", layout="centered")

st.title("🤖 Minha IA Privada")
st.write("Converse com sua IA localmente e envie imagens ou arquivos para análise.")

# Inicialização do cliente Gemini (certifique-se de configurar sua chave de API nas variáveis de ambiente)
@st.cache_resource
def carregar_cliente():
    return genai.Client()

try:
    client = carregar_cliente()
except Exception as e:
    st.error(f"Erro ao inicializar o cliente da IA: {e}")

# Campo de upload de arquivos e imagens na interface
uploaded_file = st.file_uploader(
    "Envie uma imagem ou arquivo para a IA analisar:", 
    type=["png", "jpg", "jpeg", "pdf", "txt", "csv"]
)

# Histórico de mensagens no chat
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

# Exibir mensagens anteriores
for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

# Entrada do usuário
prompt_usuario = st.chat_input("Digite sua mensagem para a IA...")

if prompt_usuario:
    # Exibe a mensagem do usuário na tela
    st.session_state.mensagens.append({"role": "user", "content": prompt_usuario})
    with st.chat_message("user"):
        st.markdown(prompt_usuario)

    # Processamento da resposta com a IA
    with st.chat_message("assistant"):
        with st.spinner("A IA está pensando..."):
            try:
                conteudo_envio = [prompt_usuario]
                
                # Se o usuário enviou um arquivo ou imagem, tratamos para enviar junto
                if uploaded_file is not None:
                    bytes_arquivo = uploaded_file.read()
                    
                    # Verificação simples do tipo de arquivo para o Gemini
                    if uploaded_file.type in ["image/png", "image/jpeg", "image/jpg"]:
                        parte_arquivo = {
                            "mime_type": uploaded_file.type,
                            "data": bytes_arquivo
                        }
                        conteudo_envio.append(parte_arquivo)
                    else:
                        # Para arquivos de texto, PDF, etc., podemos usar o File API do Gemini ou extrair texto
                        # Exemplo genérico enviando os bytes do arquivo suportado
                        parte_arquivo = {
                            "mime_type": uploaded_file.type,
                            "data": bytes_arquivo
                        }
                        conteudo_envio.append(parte_arquivo)

                # Chamada ao modelo Gemini (utilizando o modelo padrão recomendado)
                resposta = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=conteudo_envio
                )
                
                texto_resposta = resposta.text
                st.markdown(texto_resposta)
                st.session_state.mensagens.append({"role": "assistant", "content": texto_resposta})
                
            except Exception as e:
                st.error(f"Ocorreu um erro ao processar a solicitação: {e}")

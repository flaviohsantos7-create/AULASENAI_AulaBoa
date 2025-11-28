import streamlit as st
from pymongo import MongoClient
import gridfs
from PIL import Image
import io
import numpy as np # Importar NumPy para o processamento da imagem

# Conexão com o MongoDB Atlas
uri = "mongodb+srv://flaviohsantos7_db_user:WLbSt2qeevHviMIv@cluster0.fvhruh9.mongodb.net/?appName=Cluster0"
client = MongoClient(uri)
db = client['midias']
fs = gridfs.GridFS(db)

st.title("Analisador de Imagens com Câmera e GridFS")

# =============================================================
# NOVO: Seção de Captura e Análise de Imagem
# =============================================================
st.header("1. Captura e Análise de Imagem")

# O st.camera_input cuida da permissão e da captura da imagem.
# Quando uma foto é tirada, ele retorna um objeto UploadedFile.
picture = st.camera_input("Clique para abrir a câmera e tirar uma foto para análise:")

if picture:
    # Exibe a foto capturada
    st.image(picture, caption="Foto Capturada", use_container_width=True)

    # Início do Processamento da Imagem (Baseado no notebook)
    st.subheader("Resultados do Processamento")
    try:
        # 1. Ler os dados brutos e converter para objeto PIL Image
        image_data = picture.read()
        image = Image.open(io.BytesIO(image_data))
        
        # 2. Aplicar processamento (Exemplo: converter para array NumPy em escala de cinza)
        # O notebook demonstrou a conversão para escala de cinza ('L') e para array NumPy.
        grayscale_image = image.convert("L") 
        img_array = np.array(grayscale_image) 
        
        # 3. Exibir os resultados da análise
        st.write("Processamento concluído.")
        st.write(f"Formato da imagem original: **{image.format}**")
        st.write(f"Modo de cor: **{image.mode}**")
        st.write(f"Dimensões do Array NumPy (Altura, Largura): **{img_array.shape}**")
        st.write(f"Tipo de dados do Array: **{img_array.dtype}**")
        
        st.image(grayscale_image, caption="Imagem Processada (Escala de Cinza)", use_container_width=True)
        
        st.success("Análise de imagem em tempo real concluída!")

    except Exception as e:
        st.error(f"Ocorreu um erro durante o processamento da imagem: {e}")

st.markdown("---")
# =============================================================
# EXISTENTE: Seção do Visualizador de Imagens do GridFS
# =============================================================
st.header("2. Visualizador de Imagens do GridFS")

# Buscar todos os arquivos armazenados no GridFS
arquivos = list(fs.find())

if not arquivos:
    st.warning("Nenhuma imagem encontrada no GridFS.")
else:
    st.write(f"Total de imagens armazenadas: {len(arquivos)}")

    # Exibir imagens em colunas
    cols = st.columns(3)  # 3 imagens por linha
    for i, arquivo in enumerate(arquivos):
        dados = arquivo.read()
        imagem = Image.open(io.BytesIO(dados))

        with cols[i % 3]:
            st.image(imagem, caption=arquivo.filename, use_container_width=True)
            st.download_button(
                label="Baixar",
                data=dados,
                file_name=arquivo.filename,
                mime="image/jpeg"
            )

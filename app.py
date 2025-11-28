import streamlit as st
from pymongo import MongoClient
import gridfs
from PIL import Image
import io
import numpy as np # Necessário para processamento e comparação

# --- Funções de Processamento de Imagem ---

# Define um tamanho fixo para comparação (Ex: 128x128 pixels)
COMPARISON_SIZE = (128, 128) 

def preprocess_image(image: Image.Image) -> np.ndarray:
    """Converte e redimensiona a imagem para Escala de Cinza e para um array NumPy."""
    # 1. Converte para Escala de Cinza ('L')
    # 2. Redimensiona para o tamanho fixo
    image = image.convert("L").resize(COMPARISON_SIZE)
    # 3. Converte para array NumPy
    return np.array(image)

def calculate_mse(img_array1: np.ndarray, img_array2: np.ndarray) -> float:
    """Calcula a Média do Erro Quadrático (MSE) entre dois arrays NumPy."""
    # Garante que os arrays têm o mesmo formato
    if img_array1.shape != img_array2.shape:
        return float('inf') 
    
    # Subtrai e eleva ao quadrado a diferença, depois soma e tira a média
    err = np.sum((img_array1.astype("float") - img_array2.astype("float")) ** 2)
    err /= float(img_array1.shape[0] * img_array1.shape[1])
    return err

# --- Conexão e Configuração ---

# Conexão com o MongoDB Atlas
# (Mantendo o seu código de conexão)
uri = "mongodb+srv://flaviohsantos7_db_user:WLbSt2qeevHviMIv@cluster0.fvhruh9.mongodb.net/?appName=Cluster0"
client = MongoClient(uri)
db = client['midias']
fs = gridfs.GridFS(db)

st.title("Analisador de Imagens com Câmera e GridFS")
st.markdown("---")

# =============================================================
# SEÇÃO 1: Captura e Análise de Similaridade
# =============================================================
st.header("1. Captura e Análise de Imagem")

picture = st.camera_input("Clique para abrir a câmera e tirar uma foto para análise:")

# Busca todas as imagens do GridFS UMA VEZ para comparação
arquivos = list(fs.find())

if picture:
    st.image(picture, caption="Foto Capturada", use_container_width=True)

    st.subheader("Resultado da Análise de Similaridade")
    
    # 1. Pré-processar a imagem capturada
    try:
        image_data = picture.read()
        captured_image_pil = Image.open(io.BytesIO(image_data))
        captured_image_array = preprocess_image(captured_image_pil)
    except Exception as e:
        st.error(f"Erro ao pré-processar a imagem capturada: {e}")
        st.stop()

    best_match_filename = None
    lowest_mse = float('inf') # Inicializa com o maior valor possível
    best_match_image_data = None
    total_comparisons = 0

    # O Streamlit exibe um indicador de carregamento durante o loop
    with st.spinner(f"Comparando com {len(arquivos)} imagens do banco de dados..."):
        # 2. Loop de Comparação com Imagens do GridFS
        for arquivo in arquivos:
            try:
                # Ler e abrir a imagem do GridFS
                db_image_data = arquivo.read()
                db_image_pil = Image.open(io.BytesIO(db_image_data))
                
                # Pré-processar a imagem do banco de dados
                db_image_array = preprocess_image(db_image_pil)
                
                # Calcular a Média do Erro Quadrático (MSE)
                mse = calculate_mse(captured_image_array, db_image_array)
                total_comparisons += 1
                
                # Verificar se este é o novo melhor "match" (menor MSE)
                if mse < lowest_mse:
                    lowest_mse = mse
                    best_match_filename = arquivo.filename
                    best_match_image_data = db_image_data
                    
            except Exception as e:
                # Mensagem de aviso, mas continua o loop
                st.warning(f"Erro ao processar a imagem '{arquivo.filename}': {e}. Pulando...")
                continue
    
    # 3. Exibir o Resultado Final
    if best_match_filename:
        # A maior diferença possível para imagens de 8-bit (0 a 255) é 255*255
        MAX_POSSIBLE_MSE = 255**2 
        # Cria uma métrica de "similaridade" em percentual para melhor visualização
        similarity_score = (1 - (lowest_mse / MAX_POSSIBLE_MSE)) * 100
        
        st.success(f"Comparação concluída com **{total_comparisons}** imagens.")
        st.info(f"A imagem mais similar encontrada é: **{best_match_filename}**")
        
        st.metric(
            label="Pontuação de Similaridade (Baseada em MSE)", 
            value=f"{similarity_score:.2f}%", 
            help="Pontuação onde 100% significa imagens idênticas. Calculado com base na Média do Erro Quadrático (MSE)."
        )

        # Exibir a melhor correspondência
        st.subheader(f"Melhor Correspondência no Banco de Dados: {best_match_filename}")
        best_match_image_pil = Image.open(io.BytesIO(best_match_image_data))
        st.image(best_match_image_pil, caption=f"MSE (Distância): {lowest_mse:.2f}", use_container_width=True)

    else:
        st.error("Nenhuma imagem do banco de dados pôde ser processada para comparação.")

st.markdown("---")
# =============================================================
# SEÇÃO 2: Visualizador de Imagens do GridFS (Existente)
# =============================================================
st.header("2. Visualizador de Imagens do GridFS")

if not arquivos:
    st.warning("Nenhuma imagem encontrada no GridFS.")
else:
    st.write(f"Total de imagens armazenadas: {len(arquivos)}")

    # Exibir imagens em colunas
    cols = st.columns(3)
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

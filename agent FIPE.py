import streamlit as st
import requests
import logging
import socket
import platform
from bs4 import BeautifulSoup

# Configuração do logger
logging.basicConfig(level=logging.INFO)

# FIPE API endpoints
BASE_URL = "https://parallelum.com.br/fipe/api/v1/carros"

def get_marcas():
    r = requests.get(f"{BASE_URL}/marcas")
    st.session_state['last_response'] = r
    return r.json() if r.status_code == 200 else []

def get_modelos(marca_id):
    r = requests.get(f"{BASE_URL}/marcas/{marca_id}/modelos")
    return r.json()["modelos"] if r.status_code == 200 else []

def get_anos(marca_id, modelo_id):
    r = requests.get(f"{BASE_URL}/marcas/{marca_id}/modelos/{modelo_id}/anos")
    return r.json() if r.status_code == 200 else []

def get_preco(marca_id, modelo_id, ano_id):
    r = requests.get(f"{BASE_URL}/marcas/{marca_id}/modelos/{modelo_id}/anos/{ano_id}")
    return r.json() if r.status_code == 200 else {}

def get_yamaha_bikes():
    url = "https://www.tabelafipebrasil.com/motos/YAMAHA"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    bikes = []
    for row in soup.select("table tbody tr"):
        cols = row.find_all("td")
        if len(cols) >= 3:
            modelo = cols[0].get_text(strip=True)
            ano = cols[1].get_text(strip=True)
            preco = cols[2].get_text(strip=True)
            bikes.append({"Modelo": modelo, "Ano": ano, "Preço": preco})
    return bikes

# Sidebar UI
st.sidebar.title("Busca FIPE")
tipo_veiculo = st.sidebar.radio("Tipo de Veículo", ["Carro", "Moto (Yamaha)"])

if tipo_veiculo == "Carro":
    marcas = get_marcas()
    marca_nome = st.sidebar.selectbox("Marca", [m["nome"] for m in marcas])
    marca_id = next((m["codigo"] for m in marcas if m["nome"] == marca_nome), None)

    modelos = get_modelos(marca_id) if marca_id else []
    modelo_nome = st.sidebar.selectbox("Modelo", [m["nome"] for m in modelos]) if modelos else ("",)
    modelo_id = next((m["codigo"] for m in modelos if m["nome"] == modelo_nome), None)

    anos = get_anos(marca_id, modelo_id) if (marca_id and modelo_id) else []
    ano_nome = st.sidebar.selectbox("Ano", [a["nome"] for a in anos]) if anos else ("",)
    ano_id = next((a["codigo"] for a in anos if a["nome"] == ano_nome), None)

    if st.sidebar._button_group("Buscar Preço"):
        preco = get_preco(marca_id, modelo_id, ano_id)
        logging.info(f"Output - API Response: {preco}")
        st.markdown("#### Debug: Saída da API FIPE")
        st.json(preco)
        if preco:
            # Professional card UI
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #23272f 60%, #3498DB 100%);
                border-radius: 18px;
                box-shadow: 0 4px 24px rgba(44,62,80,0.18);
                padding: 2rem 2.5rem;
                margin: 2rem 0;
                color: #f1f1f1;
                max-width: 480px;
            ">
                <h2 style="margin-top:0; margin-bottom:0.5rem; font-size:2rem; letter-spacing:-1px;">
                    🚗 {preco.get('Marca','')} {preco.get('Modelo','')}
                </h2>
                <div style="font-size:1.1rem; margin-bottom:1.2rem;">
                    <b>Ano:</b> {preco.get('AnoModelo','')} &nbsp;|&nbsp;
                    <b>Combustível:</b> {preco.get('Combustivel','')}
                </div>
                <div style="font-size:1.3rem; margin-bottom:0.7rem;">
                    <b>Preço FIPE:</b> <span style="color:#4FD1C5; font-size:2rem;">{preco.get('Valor','')}</span>
                </div>
                <div style="font-size:1rem; color:#b0b8c1;">
                    <b>Código FIPE:</b> {preco.get('CodigoFipe','')}<br>
                    <b>Mês de Referência:</b> {preco.get('MesReferencia','')}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Não foi possível obter o preço tene uma nova api.")
else:
    st.sidebar.markdown("### Motos Nacionais (Tabela FIPE Brasil)")
    bikes = get_yamaha_bikes()
    modelos = sorted(set(b["Modelo"] for b in bikes))

    busca_modelo = st.sidebar.text_input("Buscar modelo", "")
    # Filtro de modelos
    if busca_modelo:
        modelos_filtrados = [m for m in modelos if busca_modelo.lower() in m.lower()]
    else:
        modelos_filtrados = modelos

    if modelos_filtrados:
        modelo_escolhido = st.sidebar.selectbox("Modelo", modelos_filtrados)
        anos = sorted(set(b["Ano"] for b in bikes if b["Modelo"] == modelo_escolhido))
        ano_escolhido = st.sidebar.selectbox("Ano", anos)
        resultado = next((b for b in bikes if b["Modelo"] == modelo_escolhido and b["Ano"] == ano_escolhido), None)
        if resultado:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #23272f 60%, #3498DB 100%);
                border-radius: 18px;
                box-shadow: 0 4px 24px rgba(44,62,80,0.18);
                padding: 2rem 2.5rem;
                margin: 2rem 0;
                color: #f1f1f1;
                max-width: 480px;
            ">
                <h2 style="margin-top:0; margin-bottom:0.5rem; font-size:2rem; letter-spacing:-1px;">
                    🏍️ Yamaha {resultado['Modelo']}
                </h2>
                <div style="font-size:1.1rem; margin-bottom:1.2rem;">
                    <b>Ano:</b> {resultado['Ano']}
                </div>
                <div style="font-size:1.3rem; margin-bottom:0.7rem;">
                    <b>Preço FIPE:</b> <span style="color:#4FD1C5; font-size:2rem;">{resultado['Preço']}</span>
                </div>
                <div style="font-size:1rem; color:#b0b8c1;">
                    <img src="https://www.tabelafipebrasil.com/site/images/logos/png/small/yamaha.png" alt="Yamaha" style="height:40px;">
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Nenhum resultado encontrado para este modelo/ano Yamaha.")
    else:
        st.warning("Nenhum modelo Yamaha encontrado com esse filtro.")

# Após as seleções do usuário
st.markdown("#### Debug: Entradas do Usuário")
if tipo_veiculo == "Carro":
    st.write("Marca selecionada:", marca_nome, "| ID:", marca_id)
    st.write("Modelo selecionado:", modelo_nome, "| ID:", modelo_id)
    st.write("Ano selecionado:", ano_nome, "| ID:", ano_id)
    logging.info(f"Input - Marca: {marca_nome} ({marca_id}), Modelo: {modelo_nome} ({modelo_id}), Ano: {ano_nome} ({ano_id})")
else:
    st.write("Modelo selecionado:", modelo_escolhido)
    st.write("Ano selecionado:", ano_escolhido)
    logging.info(f"Input - Moto Yamaha: Modelo: {modelo_escolhido}, Ano: {ano_escolhido}")

st.markdown("### 🛠️ Infraestrutura do Sistema")
st.write("Hostname:", socket.gethostname())
st.write("IP Local:", socket.gethostbyname(socket.gethostname()))
st.write("Sistema Operacional:", platform.system(), platform.release())
st.write("Versão Python:", platform.python_version())

# Headers da última requisição FIPE
if 'last_response' in st.session_state:
    st.markdown("#### Headers da última resposta FIPE")
    st.json(dict(st.session_state['last_response'].headers))

def scan_ports(host="localhost", ports=[80, 443, 8501]):
    results = {}
    for port in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        try:
            s.connect((host, port))
            results[port] = "Aberta"
        except:
            results[port] = "Fechada"
        s.close()
    return results

st.markdown("#### Portas Comuns no Servidor")
st.write(scan_ports())
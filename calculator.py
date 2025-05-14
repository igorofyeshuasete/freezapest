import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import locale
import os  # Add missing import
from user_manager import UserManager
import time
import requests
import secrets
import string

# Set Brazilian Portuguese locale for currency formatting
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    locale.setlocale(locale.LC_ALL, '')

def format_currency(value):
    """Format number to Brazilian currency format"""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Setup
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

LOCKOUT_FILE = data_dir / "login_lockouts.csv"
AUDIT_LOG_FILE = data_dir / "audit_log.csv"

def load_lockouts():
    if LOCKOUT_FILE.exists():
        return pd.read_csv(LOCKOUT_FILE)
    return pd.DataFrame(columns=["username", "attempts", "last_attempt"])

def save_lockouts(df):
    df.to_csv(LOCKOUT_FILE, index=False, encoding="utf-8")

def log_event(username, action, details=""):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = pd.DataFrame([{
        "timestamp": now,
        "username": username,
        "action": action,
        "details": details
    }])
    if AUDIT_LOG_FILE.exists():
        log_entry.to_csv(AUDIT_LOG_FILE, mode="a", header=False, index=False, encoding="utf-8")
    else:
        log_entry.to_csv(AUDIT_LOG_FILE, index=False, encoding="utf-8")

st.set_page_config(
    page_title="Calculadora de Descontos Bancários",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize user manager
if 'user_manager' not in st.session_state:
    st.session_state.user_manager = UserManager()

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None

# Session timeout handling
if 'last_active' not in st.session_state:
    st.session_state.last_active = time.time()
if st.session_state.user:
    if time.time() - st.session_state.last_active > 900:  # 15 minutos
        st.session_state.user = None
        st.warning("Sessão expirada por inatividade.")
        st.rerun()
    else:
        st.session_state.last_active = time.time()

# Theme selection
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'
theme = st.sidebar.selectbox("Tema", ["light", "dark"], index=0 if st.session_state.theme == 'light' else 1)
st.session_state.theme = theme
if theme == "dark":
    st.markdown(
        """
        <style>
        .stApp { background: #23272f !important; color: #f1f1f1 !important; }
        .stCard { background: #2c2f36 !important; color: #f1f1f1 !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

# Temas disponíveis
THEMES = {
    "Claro": {
        "background": "#ECF0F1",
        "card": "#FFFFFF",
        "text": "#2C3E50",
        "accent": "#3498DB"
    },
    "Escuro": {
        "background": "#23272f",
        "card": "#2c2f36",
        "text": "#f1f1f1",
        "accent": "#4FD1C5"
    },
    "Custom": {
        "background": "#1a1a2e",
        "card": "#16213e",
        "text": "#e94560",
        "accent": "#0f3460"
    }
}

# Sidebar para seleção de tema e papel de parede
with st.sidebar:
    st.markdown("### 🎨 Personalização Visual")
    theme_map = {"Claro": "Claro", "Escuro": "Escuro", "Custom": "Custom"}
    theme_choice = st.radio("Tema", list(theme_map.keys()), key="theme_radio")
    st.session_state.theme = theme_map[theme_choice]

    # Escolha de papel de parede
    st.markdown("#### 🖼️ Papel de Parede (Unsplash)")
    wallpaper_query = st.text_input("Buscar imagem (ex: nature, city, abstract)", value="abstract", key="wallpaper_query")
    if st.button("Buscar Wallpaper"):
        # Busca uma imagem aleatória do Unsplash
        url = f"https://source.unsplash.com/1600x900/?{wallpaper_query}"
        st.session_state.wallpaper_url = url
    # Exibe preview
    wallpaper_url = st.session_state.get("wallpaper_url", f"https://source.unsplash.com/1600x900/?{wallpaper_query}")
    st.image(wallpaper_url, use_container_width=True, caption="Preview do Papel de Parede")

def login_page():
    # Persistent lockout tracking
    lockouts = load_lockouts()
    
    # Create login form
    with st.form("login_form"):
        username = st.text_input("Usuário", key="username")
        password = st.text_input("Senha", type="password", key="password")
        submitted = st.form_submit_button("Entrar")

        if submitted:
            # Find user lockout info
            user_lock = lockouts[lockouts["username"] == username]
            now = datetime.now()

            if not user_lock.empty:
                attempts = int(user_lock.iloc[0]["attempts"])
                last_attempt = pd.to_datetime(user_lock.iloc[0]["last_attempt"])
                time_diff = (now - last_attempt).total_seconds()
                if attempts >= 3 and time_diff < 300:
                    seconds_left = int(300 - time_diff)
                    st.warning(f"Por favor, aguarde {seconds_left//60}:{seconds_left%60:02d} minutos para tentar novamente.")
                    st.info(f"Tentativas restantes: 0")
                    return
                elif attempts >= 3 and time_diff >= 300:
                    # Reset after 5 minutes
                    lockouts.loc[lockouts["username"] == username, ["attempts"]] = 0
                    save_lockouts(lockouts)
                    attempts = 0

            user = st.session_state.user_manager.authenticate(username, password)
            if user:
                st.session_state.user = user
                log_event(user['username'], "login")
                # Reset lockout info on success
                lockouts = lockouts[lockouts["username"] != username]
                save_lockouts(lockouts)
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                # Update lockout info
                if user_lock.empty:
                    new_row = pd.DataFrame([{
                        "username": username,
                        "attempts": 1,
                        "last_attempt": now.strftime("%Y-%m-%d %H:%M:%S")
                    }])
                    lockouts = pd.concat([lockouts, new_row], ignore_index=True)
                else:
                    lockouts.loc[lockouts["username"] == username, "attempts"] = attempts + 1
                    lockouts.loc[lockouts["username"] == username, "last_attempt"] = now.strftime("%Y-%m-%d %H:%M:%S")
                save_lockouts(lockouts)
                remaining = max(0, 3 - (attempts + 1))
                st.error("Usuário ou senha inválidos")
                st.info(f"Tentativas restantes: {remaining}")

def admin_page():
    st.title("🛠️ Gerenciamento de Usuários")
    
    # Create new user
    with st.expander("➕ Criar Novo Usuário"):
        with st.form("create_user"):
            new_username = st.text_input("Nome de Usuário")
            new_password = st.text_input("Senha", type="password")
            new_name = st.text_input("Nome Completo")
            new_role = st.selectbox("Perfil", ["user", "admin"])
            if st.form_submit_button("Criar Usuário"):
                success, msg = st.session_state.user_manager.create_user(
                    new_username, new_password, new_name, new_role
                )
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

    # List and manage users - Updated with unique keys
    st.subheader("📋 Usuários Cadastrados")
    for user in st.session_state.user_manager.users:
        with st.expander(f"👤 {user['username']} - {user['name']}"):
            col1, col2 = st.columns(2)
            with col1:
                # Use admin_del prefix for user management deletion buttons
                if st.button("🗑️ Excluir", key=f"admin_del_{user['id']}"):
                    if user['username'] != 'admin':
                        success, msg = st.session_state.user_manager.delete_user(user['id'])
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.error("Não é possível excluir o usuário admin")
            
            with col2:
                # Use admin_reset prefix for reset buttons
                if st.button("🔄 Resetar Senha", key=f"admin_reset_{user['id']}"):
                    success, msg = st.session_state.user_manager.update_user(
                        user['id'], password="123456"
                    )
                    if success:
                        st.success(f"Senha resetada para: 123456")
                    else:
                        st.error(msg)

def show_history():
    if st.checkbox("📋 Mostrar Histórico"):
        filename = data_dir / 'historico_descontos.csv'
        try:
            if filename.exists():
                df_historico = pd.read_csv(filename)
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("📝 Histórico de Cálculos (Editar/Deletar)")

                if df_historico.empty:
                    st.info("Nenhum histórico disponível ainda.")
                else:
                    # Add filters at the top
                    col_filter1, col_filter2 = st.columns(2)
                    with col_filter1:
                        date_filter = st.date_input("Filtrar por data", key="history_date_filter")
                    with col_filter2:
                        value_filter = st.number_input("Valor mínimo", key="history_value_filter")

                    for idx, row in df_historico.iterrows():
                        with st.expander(f"🕒 {row['data_calculo']} | Original: {row['valor_original']} | Proposto: {row['valor_proposto']}"):
                            col1, col2, col3 = st.columns([3,1,1])
                            with col1:
                                # Use hist_edit prefix for editing fields
                                novo_valor_original = st.text_input(
                                    "Valor Original", 
                                    value=row['valor_original'], 
                                    key=f"hist_edit_orig_{idx}"
                                )
                                novo_valor_proposto = st.text_input(
                                    "Valor Proposto", 
                                    value=row['valor_proposto'], 
                                    key=f"hist_edit_prop_{idx}"
                                )
                                # Use hist_save prefix for save buttons
                                if st.button("💾 Salvar", key=f"hist_save_{idx}"):
                                    try:
                                        valor_orig = float(novo_valor_original.replace(".", "").replace(",", "."))
                                        valor_prop = float(novo_valor_proposto.replace(".", "").replace(",", "."))
                                        desconto = ((valor_orig - valor_prop) / valor_orig) * 100
                                        economia = valor_orig - valor_prop
                                        df_historico.at[idx, 'valor_original'] = novo_valor_original
                                        df_historico.at[idx, 'valor_proposto'] = novo_valor_proposto
                                        df_historico.at[idx, 'desconto_percentual'] = f"{desconto:.2f}"
                                        df_historico.at[idx, 'economia'] = format_currency(economia)
                                        df_historico.to_csv(filename, index=False, encoding='utf-8')
                                        st.success("Alteração salva!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao salvar: {e}")
                            with col2:
                                # Use hist_del prefix for history deletion buttons
                                if st.button("🗑️ Deletar", key=f"hist_del_{idx}"):
                                    if st.warning("Tem certeza que deseja excluir este registro?"):
                                        df_historico = df_historico.drop(idx).reset_index(drop=True)
                                        df_historico.to_csv(filename, index=False, encoding='utf-8')
                                        st.success("Registro deletado!")
                                        st.rerun()
                            with col3:
                                st.write(f"Desconto: {row['desconto_percentual']}%")
                                st.write(f"Economia: {row['economia']}")

                    if not df_historico.empty:
                        st.info(f"Total de registros: {len(df_historico)}")
                        st.info(f"Média de desconto: {df_historico['desconto_percentual'].astype(float).mean():.2f}%")
                        st.info(f"Maior economia: {df_historico['economia'].max()}")

                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("Nenhum histórico disponível ainda.")
        except Exception as e:
            st.error(f"Erro ao carregar histórico: {e}")

def show_audit_log():
    if AUDIT_LOG_FILE.exists():
        df_audit = pd.read_csv(AUDIT_LOG_FILE)
        st.markdown("### 📅 Histórico de Acesso e Uso")
        # Filtros
        users = ["Todos"] + sorted(df_audit["username"].unique())
        user_filter = st.selectbox("Filtrar por usuário", users)
        action_filter = st.multiselect("Filtrar por ação", sorted(df_audit["action"].unique()), default=sorted(df_audit["action"].unique()))
        date_filter = st.date_input("Filtrar por data", [])
        df_filtered = df_audit.copy()
        if user_filter != "Todos":
            df_filtered = df_filtered[df_filtered["username"] == user_filter]
        if action_filter:
            df_filtered = df_filtered[df_filtered["action"].isin(action_filter)]
        if date_filter:
            if isinstance(date_filter, list) and len(date_filter) == 2:
                start, end = date_filter
                df_filtered = df_filtered[
                    (pd.to_datetime(df_filtered["timestamp"]).dt.date >= start) &
                    (pd.to_datetime(df_filtered["timestamp"]).dt.date <= end)
                ]
            else:
                df_filtered = df_filtered[
                    pd.to_datetime(df_filtered["timestamp"]).dt.date == date_filter
                ]
        st.dataframe(df_filtered.sort_values("timestamp", ascending=False), use_container_width=True)
    else:
        st.info("Nenhum histórico de auditoria disponível ainda.")

# Strong password generator
def generate_strong_password(length=16):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        # Ensure password has at least one lowercase, one uppercase, one digit, and one symbol
        if (any(c.islower() for c in password) and
            any(c.isupper() for c in password) and
            any(c.isdigit() for c in password) and
            any(c in string.punctuation for c in password)):
            return password

# Add logout button to sidebar
if st.session_state.user:
    with st.sidebar:
        st.write(f"👤 Usuário: {st.session_state.user['name']}")
        if st.button("📤 Logout"):
            st.session_state.user = None
            st.rerun()

    st.markdown("""
        <div class="sidebar-profile">
            <div class="profile-avatar">
                <img src="https://api.dicebear.com/7.x/initials/svg?seed=IJ" alt="User Avatar"/>
            </div>
            <div class="user-info">
                <h3>👤 {}</h3>
                <p>Status: Online</p>
                <div class="user-stats">
                    <span>🔢 Cálculos: 24</span>
                    <span>📅 Último acesso: Hoje</span>
                </div>
            </div>
        </div>

        <div class="sidebar-settings">
            <div class="setting-item">
                <i class="fas fa-moon"></i>
                <span>Modo Escuro</span>
                <div class="toggle-switch"></div>
            </div>
            <div class="setting-item">
                <i class="fas fa-bell"></i>
                <span>Notificações</span>
            </div>
            <div class="setting-item">
                <i class="fas fa-language"></i>
                <span>Idioma</span>
            </div>
        </div>

        <button class="sidebar-button logout-button" onclick="handleLogout()">
            <i class="fas fa-sign-out-alt"></i> Logout
        </button>
    """.format(st.session_state.user['name']), unsafe_allow_html=True)

    # Add custom JavaScript for interactions
    st.markdown("""
        <script>
        function handleLogout() {
            // Add your logout logic here
            window.location.reload();
        }

        // Add smooth animations
        document.addEventListener('DOMContentLoaded', () => {
            const sidebarElements = document.querySelectorAll('.sidebar-profile, .sidebar-settings, .sidebar-button');
            sidebarElements.forEach((el, index) => {
                el.style.animation = `slideIn 0.5s ease forwards ${index * 0.1}s`;
            });
        });
        </script>
    """, unsafe_allow_html=True)

def calculator_ui():
    # Add custom CSS with modern design system
    st.markdown("""
        <style>
        /* Modern Color Palette */
        :root {
            --primary: #2C3E50;
            --secondary: #3498DB;
            --accent: #E74C3C;
            --background: #ECF0F1;
            --success: #2ECC71;
            --warning: #F1C40F;
            --text-primary: #2C3E50;
            --text-secondary: #7F8C8D;
        }

        /* Background with Modern Grid */
        .stApp {
            background: linear-gradient(135deg, #2C3E50 0%, #3498DB 100%);
            background-image: 
                linear-gradient(rgba(52, 152, 219, 0.1) 1px, transparent 1px),
                linear-gradient(90deg, rgba(52, 152, 219, 0.1) 1px, transparent 1px);
            background-size: 50px 50px;
            background-position: center center;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        }

        /* Glass Morphism Cards */
        .stCard {
            background: rgba(255, 255, 255, 0.95) !important;
            backdrop-filter: blur(10px) !important;
            border-radius: 20px !important;
            border: 1px solid rgba(255, 255, 255, 0.5) !important;
            padding: 2rem !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
            transition: all 0.3s ease !important;
        }

        .stCard:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15) !important;
        }

        /* Modern Typography */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif !important;
            font-weight: 700 !important;
            color: var(--text-primary) !important;
            letter-spacing: -0.5px !important;
        }

        h1 {
            font-size: 2.5rem !important;
            background: linear-gradient(135deg, #2C3E50, #3498DB);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* Input Fields */
        .stTextInput input, .stNumberInput input {
            border-radius: 12px !important;
            border: 2px solid rgba(52, 152, 219, 0.2) !important;
            padding: 1rem !important;
            font-size: 1.1rem !important;
            transition: all 0.3s ease !important;
            background: rgba(255, 255, 255, 0.9) !important;
        }

        .stTextInput input:focus, .stNumberInput input:focus {
            border-color: var(--secondary) !important;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.2) !important;
        }

        /* Buttons */
        .stButton button {
            border-radius: 12px !important;
            padding: 0.75rem 2rem !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            background: linear-gradient(135deg, #2C3E50, #3498DB) !important;
            border: none !important;
        }

        .stButton button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 20px rgba(52, 152, 219, 0.3) !important;
        }

        /* Metrics and Results */
        .css-1xarl3l {
            background: rgba(255, 255, 255, 0.95) !important;
            border-radius: 16px !important;
            padding: 1.5rem !important;
            border: 1px solid rgba(52, 152, 219, 0.2) !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1) !important;
        }

        /* Sidebar */
        .css-1d391kg {
            background: rgba(44, 62, 80, 0.95) !important;
            backdrop-filter: blur(10px) !important;
        }

        /* Tables */
        .stDataFrame {
            background: rgba(255, 255, 255, 0.98) !important;
            border-radius: 16px !important;
            overflow: hidden !important;
            border: 1px solid rgba(52, 152, 219, 0.2) !important;
        }

        /* Expander */
        .streamlit-expander {
            border-radius: 12px !important;
            border: 1px solid rgba(52, 152, 219, 0.2) !important;
            background: rgba(255, 255, 255, 0.95) !important;
        }

        /* Success/Error Messages */
        .stSuccess, .stError {
            border-radius: 12px !important;
            padding: 1rem !important;
            font-weight: 500 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Update the title with custom HTML
    st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">
                🏦 Calculadora de Desconto Bancário
            </h1>
            <p style="color: white; font-size: 1.2rem; opacity: 0.9;">
                Sistema Profissional de Análise de Propostas de Quitação
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Wrap the main content in a card
    st.markdown('<div class="stCard">', unsafe_allow_html=True)

    # Title and Description
    st.title("🏦 Calculadora de Desconto Bancário")
    st.markdown("""
        ### Análise de Proposta de Quitação
        Insira os valores para calcular o desconto oferecido pelo banco e analisar a proposta de quitação.
    """)

    # Create two columns for input
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Dados do Débito")
        valor_original_str = st.text_input(
            "Valor Original da Dívida",
            value="47.687,85",
            help="Digite o valor total da dívida (ex: 47.687,85)"
        )
        try:
            valor_original = float(valor_original_str.replace(".", "").replace(",", "."))
            if valor_original < 0:
                raise ValueError
        except ValueError:
            st.error("Por favor, insira um valor original válido e positivo.")
            valor_original = 0.0

    with col2:
        st.subheader("Proposta do Banco")
        valor_proposto_str = st.text_input(
            "Valor Proposto para Quitação",
            value="9.537,60",
            help="Digite o valor oferecido pelo banco (ex: 9.537,60)"
        )
        try:
            valor_proposto = float(valor_proposto_str.replace(".", "").replace(",", "."))
            if valor_proposto < 0:
                raise ValueError
        except ValueError:
            st.error("Por favor, insira um valor proposto válido e positivo.")
            valor_proposto = 0.0

    # Calculate only if both are valid and positive
    if valor_original > 0 and valor_proposto >= 0:
        desconto_percentual = ((valor_original - valor_proposto) / valor_original) * 100
        economia = valor_original - valor_proposto
    else:
        desconto_percentual = 0
        economia = 0

    # Display Results
    st.markdown("---")
    st.subheader("📊 Análise da Proposta")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Desconto Oferecido",
            f"{desconto_percentual:.2f}%",
            delta=format_currency(economia)
        )

    with col2:
        st.metric(
            "Valor Original",
            format_currency(valor_original)
        )

    with col3:
        st.metric(
            "Valor Final",
            format_currency(valor_proposto)
        )

    # Save calculation with proper formatting and error handling
    if st.button("💾 Salvar Cálculo"):
        if valor_original > 0 and valor_proposto >= 0:
            log = {
                'data_calculo': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'valor_original': valor_original_str,
                'valor_proposto': valor_proposto_str,
                'desconto_percentual': f"{desconto_percentual:.2f}",
                'economia': format_currency(economia)
            }
            df_log = pd.DataFrame([log])
            filename = data_dir / 'historico_descontos.csv'
            try:
                if not filename.exists():
                    df_log.to_csv(filename, index=False, encoding='utf-8')
                else:
                    df_log.to_csv(filename, mode='a', header=False, index=False, encoding='utf-8')
                # Log the calculation event here!
                log_event(
                    st.session_state.user['username'],
                    "calculation",
                    f"Original: {valor_original_str}, Proposto: {valor_proposto_str}"
                )
                st.success("✅ Cálculo salvo com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar o cálculo: {e}")
        else:
            st.error("Preencha valores válidos antes de salvar.")

    # Close the card div before the history section
    st.markdown('</div>', unsafe_allow_html=True)

    # Show History with edit/delete options
    show_history()

    # Add a footer
    st.markdown("""
        <div style="text-align: center; padding: 2rem 0; color: white; opacity: 0.8;">
            <p>Desenvolvido por Igor de Jesus © 2024</p>
            <p style="font-size: 0.8rem;">Versão 2.0.0</p>
        </div>
    """, unsafe_allow_html=True)

# Main app logic
if not st.session_state.user:
    login_page()
else:
    if st.session_state.user['role'] == 'admin':
        tab1, tab2 = st.tabs(["📊 Calculadora", "⚙️ Administração"])
        with tab1:
            calculator_ui()
            # Password generator section (admin only)
            st.markdown("### 🔐 Gerador de Senha Forte")
            if st.button("Gerar Senha Forte"):
                strong_password = generate_strong_password()
                st.success(f"Sua senha forte: `{strong_password}`")
                st.code(strong_password, language="text")
        with tab2:
            admin_page()
            show_audit_log()
    else:
        calculator_ui()


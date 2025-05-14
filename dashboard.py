from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
import pandas as pd
import json
from pathlib import Path
import base64
import logging
import traceback
import numpy as np
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Required for sessions
app.config['SESSION_TYPE'] = 'filesystem'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.name = user_data['name']
        self.role = user_data['role']
        self.password_hash = user_data['password']

class DataLoader:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        
    def load_csv(self):
        try:
            if not self.file_path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {self.file_path}")
            
            # Try different encodings
            encodings = ['utf-8', 'latin1', 'iso-8859-1']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(
                        self.file_path,
                        encoding=encoding,
                        parse_dates=['DATA', 'RESOLUÇÃO'],
                        dayfirst=True  # Brazilian date format
                    )
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logging.error(f"Erro ao tentar encoding {encoding}: {str(e)}")
            
            if df is None:
                raise ValueError("Não foi possível ler o arquivo CSV com nenhuma codificação")
                
            return self._validate_and_clean_data(df)
            
        except Exception as e:
            logging.error(f"Erro ao carregar CSV: {str(e)}\n{traceback.format_exc()}")
            raise

    def _validate_and_clean_data(self, df):
        required_columns = {
            'DATA': datetime,
            'RESOLUÇÃO': datetime,
            'CONTRATO': str,
            'VALOR DO CLIENTE': str,
            'CONTATO': str,
            'NEGOCIAÇÃO': str,
            'SITUAÇÃO': str,
            'OBSERVAÇÃO': str,
            'CAMPANHA': str
        }
        
        # Validate columns
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Colunas obrigatórias faltando: {', '.join(missing)}")

        # Clean data
        df['CONTRATO'] = df['CONTRATO'].astype(str).str.strip()
        df['SITUAÇÃO'] = df['SITUAÇÃO'].astype(str).str.upper().str.strip()
        df['CAMPANHA'] = df['CAMPANHA'].astype(str).str.upper().str.strip()
        
        return df

class DashboardManager:
    def __init__(self):
        self.users_file = Path("users.json")
        self.setup_logging()
        self.load_users()
        self.data_loader = DataLoader("(JULIO) LISTAS INDIVIDUAIS - IGOR.csv")
        
    def setup_logging(self):
        logging.basicConfig(
            filename='dashboard.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def load_users(self):
        if self.users_file.exists():
            with open(self.users_file, 'r', encoding='utf-8') as f:
                self.users = json.load(f)
        else:
            # Default credentials
            self.users = [
                {
                    "id": 1,
                    "username": "admin",
                    "password": generate_password_hash("admin123"),
                    "name": "Administrador",
                    "role": "admin"
                }
            ]
            self.save_users()

    def save_users(self):
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=4)

    def analyze_contracts(self):
        """
        Analisa o arquivo CSV de contratos e retorna estatísticas para o dashboard.
        """
        try:
            df = self.data_loader.load_csv()
            if df.empty:
                return self._get_empty_stats()
            
            # Clean and convert financial values
            df['VALOR_CLEANED'] = pd.to_numeric(
                df['VALOR DO CLIENTE'].astype(str)
                .str.replace('R$', '')
                .str.replace('.', '')
                .str.replace(',', '.')
                .str.extract(r'(\d+\.?\d*)', expand=False),
                errors='coerce'
            ).fillna(0)

            # Calculate basic stats
            total_contracts = len(df)
            legacy_mask = df['CONTRATO'].astype(str).str.match(r'^[12]\d{5,6}$')
            legacy_contracts = df[legacy_mask]
            num_legacy = len(legacy_contracts)
            percent_legacy = round((num_legacy / total_contracts) * 100, 2) if total_contracts else 0

            # Calculate situation distribution
            status_counts = legacy_contracts['SITUAÇÃO'].value_counts().to_dict()
            approved_count = status_counts.get('APROVADO', 0) + status_counts.get('VERIFICADO', 0)
            
            # Calculate financial metrics
            financial_stats = {
                "total_value": float(legacy_contracts['VALOR_CLEANED'].sum()),
                "average_value": float(legacy_contracts['VALOR_CLEANED'].mean()),
                "max_value": float(legacy_contracts['VALOR_CLEANED'].max()),
                "min_value": float(legacy_contracts['VALOR_CLEANED'].min()),
                "sem_sucesso": len(legacy_contracts[legacy_contracts['CONTATO'] == 'SEM SUCESSO'])
            }

            # Calculate performance metrics
            performance_stats = {
                "taxa_aprovacao": (approved_count / num_legacy * 100) if num_legacy > 0 else 0,
                "media_dias_resolucao": (legacy_contracts['RESOLUÇÃO'] - legacy_contracts['DATA']).dt.days.mean(),
                "contratos_sim": len(legacy_contracts[legacy_contracts['CAMPANHA'] == 'SIM']),
                "contratos_nao": len(legacy_contracts[legacy_contracts['CAMPANHA'] == 'NÃO'])
            }

            # Calculate negotiator performance
            negotiator_stats = {}
            for negotiator in legacy_contracts['NEGOCIAÇÃO'].unique():
                if pd.isna(negotiator):
                    continue
                
                negotiator_data = legacy_contracts[legacy_contracts['NEGOCIAÇÃO'] == negotiator]
                approved = len(negotiator_data[negotiator_data['SITUAÇÃO'].isin(['APROVADO', 'VERIFICADO'])])
                
                negotiator_stats[negotiator] = {
                    "total_contratos": len(negotiator_data),
                    "aprovados": approved,
                    "taxa_sucesso": (approved / len(negotiator_data) * 100) if len(negotiator_data) > 0 else 0,
                    "valor_total": float(negotiator_data['VALOR_CLEANED'].sum())
                }

            return {
                "total_contracts": total_contracts,
                "legacy_contracts": num_legacy,
                "percent_legacy": percent_legacy,
                "status_counts": status_counts,
                "financial": financial_stats,
                "performance": performance_stats,
                "negotiators": negotiator_stats,
                "bank_distribution": legacy_contracts['CONTATO'].value_counts().to_dict(),
                "campaign_distribution": legacy_contracts['CAMPANHA'].value_counts().to_dict()
            }

        except Exception as e:
            logging.error(f"Error in analyze_contracts: {str(e)}\n{traceback.format_exc()}")
            return self._get_empty_stats()

    def _get_empty_stats(self):
        """Helper method to return empty statistics structure"""
        return {
            "total_contracts": 0,
            "legacy_contracts": 0,
            "percent_legacy": 0,
            "status_counts": {},
            "financial": {
                "total_value": 0,
                "average_value": 0,
                "max_value": 0,
                "min_value": 0,
                "sem_sucesso": 0
            },
            "performance": {
                "taxa_aprovacao": 0,
                "media_dias_resolucao": 0,
                "contratos_sim": 0,
                "contratos_nao": 0
            },
            "negotiators": {},
            "bank_distribution": {},
            "campaign_distribution": {}
        }

dashboard = DashboardManager()

@login_manager.user_loader
def load_user(user_id):
    user_data = next((u for u in dashboard.users if u['id'] == int(user_id)), None)
    return User(user_data) if user_data else None

@app.route('/')
@login_required
def home():
    try:
        stats = dashboard.analyze_contracts()
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        logging.error(f"Error in home route: {str(e)}\n{traceback.format_exc()}")
        return render_template('error.html', error=str(e)), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        try:
            user = next(
                (u for u in dashboard.users if u['username'] == username),
                None
            )
            
            if user and check_password_hash(user['password'], password):
                login_user(User(user))
                return jsonify({
                    'success': True,
                    'user': {
                        'id': user['id'],
                        'name': user['name'],
                        'role': user['role']
                    }
                })
            
            return jsonify({
                'success': False,
                'message': 'Usuário ou senha inválidos'
            }), 401
            
        except Exception as e:
            logging.error(f"Erro no login: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Erro no servidor'
            }), 500
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

@app.route('/api/auth', methods=['POST'])
def authenticate():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    try:
        user_data = next(
            (u for u in dashboard.users if u['username'] == username),
            None
        )
        
        if user_data and check_password_hash(user_data['password'], password):
            return jsonify({
                'success': True,
                'user': {
                    'id': user_data['id'],
                    'name': user_data['name'],
                    'role': user_data['role']
                }
            })
        return jsonify({'success': False, 'message': 'Credenciais inválidas'})
    
    except Exception as e:
        logging.error(f"Erro na autenticação: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro no servidor'})

@app.route('/api/users', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_users():
    if request.method == 'GET':
        return jsonify(dashboard.users)
    
    if request.method == 'POST':
        data = request.json
        try:
            new_user = {
                'id': max(u['id'] for u in dashboard.users) + 1,
                'username': data['username'],
                'password': generate_password_hash(data['password']),
                'name': data['name'],
                'role': data['role']
            }
            dashboard.users.append(new_user)
            dashboard.save_users()
            return jsonify({'success': True, 'message': 'Usuário criado com sucesso'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error='Página não encontrada'), 404

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Internal error: {str(error)}\n{traceback.format_exc()}")
    return render_template('error.html', error='Erro interno do servidor'), 500

if __name__ == '__main__':
    try:
        # Create required directories
        os.makedirs('static', exist_ok=True)
        os.makedirs('templates', exist_ok=True)
        
        # Install required packages if not present
        try:
            import flask
            import pandas
            import flask_login
        except ImportError:
            subprocess.check_call([
                "pip", "install", 
                "flask", "pandas", "flask-login",
                "werkzeug", "jinja2"
            ])
        
        # Initialize the dashboard
        dashboard = DashboardManager()
        
        # Run the application
        app.run(debug=True, port=5000, host='0.0.0.0')
        
    except Exception as e:
        logging.error(f"Startup error: {str(e)}\n{traceback.format_exc()}")
        raise
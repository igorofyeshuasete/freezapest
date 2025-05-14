import hashlib
import os
from datetime import datetime, timedelta
import json
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
import logging

class UserManager:
    def __init__(self):
        self.users_file = Path("data/users.json")
        self.users_file.parent.mkdir(exist_ok=True)
        self.failed_attempts = {}
        self.setup_logging()
        self.load_users()

    def setup_logging(self):
        logging.basicConfig(
            filename='security.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def load_users(self):
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            except json.JSONDecodeError:
                logging.error("Corrupt users file detected")
                self.users = self._create_default_admin()
        else:
            self.users = self._create_default_admin()

    def create_user(self, username, password, name, role="user"):
        """Create a new user"""
        try:
            # Validate inputs
            if not all([username, password, name]):
                return False, "Todos os campos são obrigatórios"
            
            # Check if username already exists
            if any(u['username'].lower() == username.lower() for u in self.users):
                return False, "Nome de usuário já existe"
            
            # Create new user
            new_user = {
                "id": max(u['id'] for u in self.users) + 1,
                "username": username,
                "password": generate_password_hash(password),
                "name": name,
                "role": role,
                "created_at": datetime.now().isoformat(),
                "last_login": None
            }
            
            # Add user and save
            self.users.append(new_user)
            if self.save_users():
                logging.info(f"New user created: {username}")
                return True, "Usuário criado com sucesso"
            else:
                return False, "Erro ao salvar usuário"
                
        except Exception as e:
            logging.error(f"Error creating user: {str(e)}")
            return False, "Erro ao criar usuário"

    def save_users(self):
        """Save users to JSON file"""
        try:
            # Create backup before saving
            if self.users_file.exists():
                backup_path = self.users_file.with_suffix('.json.bak')
                self.users_file.rename(backup_path)

            # Save new data
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=4, ensure_ascii=False)
            
            # Remove backup if save was successful
            if Path(str(self.users_file) + '.bak').exists():
                Path(str(self.users_file) + '.bak').unlink()
            
            logging.info("Users data saved successfully")
            return True
        except Exception as e:
            logging.error(f"Error saving users data: {str(e)}")
            # Restore from backup if save failed
            if Path(str(self.users_file) + '.bak').exists():
                Path(str(self.users_file) + '.bak').rename(self.users_file)
            return False

    def delete_user(self, user_id):
        """Delete a user by ID"""
        try:
            initial_count = len(self.users)
            self.users = [u for u in self.users if u['id'] != user_id]
            
            if len(self.users) < initial_count:
                if self.save_users():
                    logging.info(f"User deleted: {user_id}")
                    return True, "Usuário excluído com sucesso"
            return False, "Usuário não encontrado"
            
        except Exception as e:
            logging.error(f"Error deleting user: {str(e)}")
            return False, "Erro ao excluir usuário"

    def update_user(self, user_id, password=None, name=None):
        """Update user information"""
        try:
            user = next((u for u in self.users if u['id'] == user_id), None)
            if not user:
                return False, "Usuário não encontrado"
            
            if password:
                user['password'] = generate_password_hash(password)
            if name:
                user['name'] = name
                
            if self.save_users():
                logging.info(f"User updated: {user_id}")
                return True, "Usuário atualizado com sucesso"
            return False, "Erro ao atualizar usuário"
            
        except Exception as e:
            logging.error(f"Error updating user: {str(e)}")
            return False, "Erro ao atualizar usuário"

    def _create_default_admin(self):
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        return [{
            "id": 1,
            "username": "admin",
            "password": generate_password_hash(admin_password, method='pbkdf2:sha256:260000'),
            "role": "admin",
            "name": "Administrador",
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }]

    def authenticate(self, username, password):
        # Sanitize input
        username = str(username).strip().lower()[:50]
        
        # Check for brute force
        if self._is_account_locked(username):
            logging.warning(f"Login attempt on locked account: {username}")
            return None

        user = next((u for u in self.users if u['username'].lower() == username), None)
        
        if user and check_password_hash(user['password'], password):
            # Reset failed attempts on success
            if username in self.failed_attempts:
                del self.failed_attempts[username]
            
            # Update last login
            user['last_login'] = datetime.now().isoformat()
            self.save_users()
            
            logging.info(f"Successful login: {username}")
            return user
        
        # Track failed attempt
        self._record_failed_attempt(username)
        logging.warning(f"Failed login attempt for user: {username}")
        return None

    def _is_account_locked(self, username):
        if username not in self.failed_attempts:
            return False
            
        attempts = self.failed_attempts[username]
        if len(attempts) >= 3:
            last_attempt = datetime.fromisoformat(attempts[-1])
            if datetime.now() - last_attempt < timedelta(minutes=5):
                return True
            # Reset attempts after lockout period
            self.failed_attempts[username] = []
        return False

    def _record_failed_attempt(self, username):
        if username not in self.failed_attempts:
            self.failed_attempts[username] = []
        self.failed_attempts[username].append(datetime.now().isoformat())
from pathlib import Path
import json
from werkzeug.security import generate_password_hash

def reset_admin_password():
    users_file = Path("data/users.json")
    
    if not users_file.exists():
        print("❌ Arquivo de usuários não encontrado!")
        return
    
    try:
        # Ler arquivo de usuários
        with open(users_file, 'r', encoding='utf-8') as f:
            users = json.load(f)
        
        # Encontrar usuário admin
        admin_user = next((u for u in users if u['username'] == 'admin'), None)
        
        if admin_user:
            # Resetar senha para o padrão
            admin_user['password'] = generate_password_hash('admin123')
            
            # Salvar alterações
            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=4, ensure_ascii=False)
            
            print("✅ Senha do admin resetada com sucesso!")
            print("Username: admin")
            print("Nova senha: admin123")
        else:
            print("❌ Usuário admin não encontrado!")
            
    except Exception as e:
        print(f"❌ Erro ao resetar senha: {str(e)}")

if __name__ == "__main__":
    reset_admin_password()
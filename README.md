Calculadora de Descontos Bancários
Sistema profissional para análise de propostas de quitação de dívidas bancárias, com interface moderna, autenticação segura e histórico completo de ações.

🚀 Visão Geral
A Calculadora de Descontos Bancários é uma aplicação desenvolvida em Python com Streamlit, projetada para facilitar a análise de propostas de quitação, calcular descontos e manter um histórico detalhado de todas as operações. O sistema oferece autenticação robusta, proteção contra ataques, backup automático e uma experiência de usuário aprimorada.

🛠️ Funcionalidades Principais
Autenticação Segura: Controle de acesso por usuário e senha, com proteção contra força bruta e senhas criptografadas.
Análise de Dados: Cálculo automático de descontos, economia e percentual de abatimento.
Histórico Completo: Registro detalhado de todos os cálculos e ações dos usuários.
Logs de Segurança: Auditoria de login, logout e uso da calculadora.
Backup Automático: Garante a integridade dos dados.
Validação de Dados: Sanitização e checagem de todos os inputs.
Interface Moderna: Layout responsivo, temas claros/escuros e experiência aprimorada.
Gerador de Senha Forte: Ferramenta integrada para criação de senhas seguras.


📦 Instalação

# Crie um ambiente virtual
python -m venv venv
.\venv\Scripts\Activate

# Instale as dependências
pip install streamlit pandas python-dotenv beautifulsoup4 requests.


▶️ Como Usar
Execute o aplicativo:


streamlit run calculator.py

Acesse no navegador:
http://localhost:8501

Credenciais padrão:

Usuário: admin
Senha: admin123
Realize cálculos de desconto:

Informe o valor original e o valor proposto.
O sistema calcula o desconto percentual e a economia.
Salve e acompanhe o histórico de operações.


💡 Exemplo de Cálculo

valor_original = 47687.85
valor_proposto = 9537.60

desconto = ((valor_original - valor_proposto) / valor_original) * 100
economia = valor_original - valor_proposto

🔒 Segurança
Proteção contra força bruta
Senhas criptografadas
Sanitização de inputs
Logs de segurança
Backup automático
Validação de dados
Controle de acesso
Histórico de ações detalhado
📊 Histórico e Auditoria
O sistema registra automaticamente:

Login e logout de cada usuário
Todos os cálculos realizados
Data e hora de cada ação
Filtros por usuário, ação e período disponíveis para administradores
📚 Documentação Completa
Acesse a documentação visual e exemplos em:
index.html ou abra no navegador

👨‍💻 Autor
Desenvolvido por Igor de Jesus
© 2025 — Versão 2.0.0

Sinta-se à vontade para contribuir, sugerir melhorias ou relatar problemas!

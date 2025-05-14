import os
from pathlib import Path

class Config:
    # SSL Configuration
    SSL_CERT = Path("cert.pem")
    SSL_KEY = Path("key.pem")
    
    # Server Configuration
    SERVER_ADDRESS = "localhost"
    SERVER_PORT = 8501
    
    # Security Configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
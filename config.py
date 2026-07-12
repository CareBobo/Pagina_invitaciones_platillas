import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Llave secreta para cookies y sesiones
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key_invitaciones_premium_2026')
    
    # Base de datos: PostgreSQL en Render, MySQL o SQLite fallback
    DATABASE_URL = os.getenv('DATABASE_URL')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME')
    
    if DATABASE_URL:
        # Render a veces usa postgres:// que es obsoleto en SQLAlchemy 1.4+
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    elif DB_USER and DB_NAME:
        # URI de conexión de MySQL usando PyMySQL
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    else:
        # Fallback local a SQLite para desarrollo y pruebas portátiles
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'invitaciones.db')}"
        
    # Supabase Configuration (Base de datos y Storage)
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Directorio de subida de archivos
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MEDIA_FOLDER = os.path.join(UPLOAD_FOLDER, 'media') # Fotos, videos, música
    QR_FOLDER = os.path.join(UPLOAD_FOLDER, 'qrs') # Códigos QR individuales
    
    # Extensiones permitidas para subidas
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg'}
    ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a'}
    ALLOWED_EXCEL_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # Límite máximo de carga 50MB (para videos)

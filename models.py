import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(50), nullable=False, default='ADMIN_ORGANIZADOR') # 'SUPER_ADMIN' o 'ADMIN_ORGANIZADOR'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    invitaciones = db.relationship('Invitacion', backref='creador', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Invitacion(db.Model):
    __tablename__ = 'invitaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    tipo_evento = db.Column(db.String(50), nullable=False) # 'Boda', 'Quinceañero', 'Cumpleaños', 'Bautizo', 'Otro'
    plantilla = db.Column(db.String(50), nullable=False, default='elegance-gold')
    fondo_portada_url = db.Column(db.String(300), nullable=True)
    sello_portada_url = db.Column(db.String(300), nullable=True)
    decoracion_bordes_url = db.Column(db.String(300), nullable=True)
    decoracion_centro_url = db.Column(db.String(300), nullable=True)
    musica_url = db.Column(db.String(300), nullable=True)
    video_url = db.Column(db.String(300), nullable=True)
    fecha_evento = db.Column(db.DateTime, nullable=False)
    lugar_nombre = db.Column(db.String(200), nullable=True)
    lugar_direccion = db.Column(db.String(300), nullable=True)
    lugar_gmaps_url = db.Column(db.Text, nullable=True)
    historia = db.Column(db.Text, nullable=True)
    historia_foto_1_url = db.Column(db.String(300), nullable=True)
    historia_foto_2_url = db.Column(db.String(300), nullable=True)
    historia_foto_3_url = db.Column(db.String(300), nullable=True)
    codigo_vestimenta = db.Column(db.String(100), nullable=True)
    codigo_vestimenta_detalles = db.Column(db.Text, nullable=True)
    regalos_banco = db.Column(db.String(150), nullable=True)
    regalos_cuenta = db.Column(db.String(100), nullable=True)
    regalos_nequi = db.Column(db.String(50), nullable=True)
    regalos_daviplata = db.Column(db.String(50), nullable=True)
    regalos_lista_url = db.Column(db.Text, nullable=True)
    mensaje_final = db.Column(db.Text, nullable=True)
    whatsapp_confirmacion = db.Column(db.String(50), nullable=True) # Celular al cual el botón de Whatsapp dirige
    instagram_url = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    cronograma = db.relationship('CronogramaItem', backref='invitacion', cascade='all, delete-orphan', order_by='CronogramaItem.orden')
    invitados = db.relationship('Invitado', backref='invitacion', cascade='all, delete-orphan')
    fotos = db.relationship('FotoGaleria', backref='invitacion', cascade='all, delete-orphan')
    canciones_sugeridas = db.relationship('MusicaSugerida', backref='invitacion', cascade='all, delete-orphan')


class CronogramaItem(db.Model):
    __tablename__ = 'cronograma_items'
    
    id = db.Column(db.Integer, primary_key=True)
    invitacion_id = db.Column(db.Integer, db.ForeignKey('invitaciones.id', ondelete='CASCADE'), nullable=False)
    hora = db.Column(db.String(50), nullable=False) # Ej: "05:00 PM"
    titulo = db.Column(db.String(100), nullable=False) # Ej: "Ceremonia"
    descripcion = db.Column(db.String(255), nullable=True)
    icono = db.Column(db.String(50), nullable=True, default='clock') # 'clock', 'church', 'glass', 'utensils', 'music', 'camera'
    orden = db.Column(db.Integer, default=0)


class Invitado(db.Model):
    __tablename__ = 'invitados'
    
    id = db.Column(db.Integer, primary_key=True)
    invitacion_id = db.Column(db.Integer, db.ForeignKey('invitaciones.id', ondelete='CASCADE'), nullable=False)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    nombre = db.Column(db.String(200), nullable=False)
    correo = db.Column(db.String(150), nullable=True)
    telefono = db.Column(db.String(50), nullable=True)
    cupos_asignados = db.Column(db.Integer, default=1)
    cupos_confirmados = db.Column(db.Integer, default=0)
    mesa = db.Column(db.String(50), default='Por asignar')
    mensaje_bienvenida = db.Column(db.Text, nullable=True)
    qr_path = db.Column(db.String(255), nullable=True)
    estado_rsvp = db.Column(db.String(20), default='Pendiente') # 'Pendiente', 'Confirmado', 'Rechazado'
    mensaje_rsvp = db.Column(db.Text, nullable=True)
    fecha_rsvp = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def generate_qr(self, app_domain):
        """Genera el código QR asociado a la URL única del invitado"""
        import qrcode
        import os
        from flask import current_app
        
        # URL de acceso seguro usando el UUID del invitado
        qr_url = f"{app_domain}/invitacion/acceso/{self.uuid}"
        
        # Crear directorio si no existe
        qr_dir = current_app.config['QR_FOLDER']
        if not os.path.exists(qr_dir):
            os.makedirs(qr_dir)
            
        # Generar QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        filename = f"{self.uuid}.png"
        filepath = os.path.join(qr_dir, filename)
        img.save(filepath)
        
        # Registrar la ruta relativa
        self.qr_path = f"uploads/qrs/{filename}"


class FotoGaleria(db.Model):
    __tablename__ = 'galeria_fotos'
    
    id = db.Column(db.Integer, primary_key=True)
    invitacion_id = db.Column(db.Integer, db.ForeignKey('invitaciones.id', ondelete='CASCADE'), nullable=False)
    foto_url = db.Column(db.String(300), nullable=False) # Ruta de la foto subida
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MusicaSugerida(db.Model):
    __tablename__ = 'musica_sugerida'
    
    id = db.Column(db.Integer, primary_key=True)
    invitacion_id = db.Column(db.Integer, db.ForeignKey('invitaciones.id', ondelete='CASCADE'), nullable=False)
    cancion = db.Column(db.String(200), nullable=False)
    artista = db.Column(db.String(200), nullable=False)
    sugerido_por = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

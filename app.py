import os
import zipfile
import io
import re
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from werkzeug.utils import secure_filename
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from config import Config
from models import db, Usuario, Invitacion, CronogramaItem, Invitado, FotoGaleria, MusicaSugerida

from supabase import create_client, Client

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar Base de Datos con la App
db.init_app(app)

# Inicializar Supabase
supabase: Client = None
supabase_url = app.config.get('SUPABASE_URL')
supabase_key = app.config.get('SUPABASE_KEY')

if supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
        print("Supabase inicializado correctamente.")
    except Exception as e:
        print(f"Error inicializando Supabase: {e}")
else:
    print("ADVERTENCIA: SUPABASE_URL o SUPABASE_KEY no están configurados.")

# --- FILTROS PERSONALIZADOS JINJA2 ---
@app.template_filter('slugify')
def slugify_filter(value):
    """Convierte texto en un slug amigable para nombres de archivos"""
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)

@app.template_filter('media_url')
def media_url_filter(value):
    """Si es URL de Firebase (http) la retorna tal cual, sino le agrega /static/"""
    if not value:
        return ""
    if value.startswith('http'):
        return value
    return f"/static/{value}"

# Inyectar variables globales en las plantillas Jinja2
@app.context_processor
def inject_globals():
    usuario_id = session.get('usuario_id')
    usuario_actual = None
    if usuario_id:
        usuario_actual = db.session.get(Usuario, usuario_id)
    return dict(usuario_actual=usuario_actual)


# --- DECORADOR DE AUTENTICACIÓN ---
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Por favor inicia sesión para acceder.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# ==========================================================================
# RUTAS PÚBLICAS DE INVITADOS (ACCESO VÍA UUID)
# ==========================================================================

@app.route('/invitacion/acceso/<uuid_invitado>')
def acceso_portada(uuid_invitado):
    """Visualización de la Portada (Página 1) personalizada por UUID del invitado"""
    invitado = Invitado.query.filter_by(uuid=uuid_invitado).first()
    if not invitado:
        return render_template('404.html'), 404
        
    invitacion = db.session.get(Invitacion, invitado.invitacion_id)
    
    # Limpieza dinámica de archivos vacíos para el fallback
    if invitacion.musica_url and not invitacion.musica_url.startswith('http'):
        full_path = os.path.join(app.root_path, 'static', invitacion.musica_url)
        if not os.path.exists(full_path) or os.path.getsize(full_path) == 0:
            invitacion.musica_url = None
            
    if invitacion.plantilla == 'champagne-interactivo':
        return render_template('portada_champagne.html', invitacion=invitacion, invitado=invitado)
    
    if invitacion.plantilla == 'video-portada':
        return render_template('portada_video.html', invitacion=invitacion, invitado=invitado)
        
    if invitacion.plantilla == 'libro-3d':
        return redirect(url_for('acceso_invitacion', uuid_invitado=uuid_invitado))
    
    return render_template('portada.html', invitacion=invitacion, invitado=invitado)

@app.route('/invitacion/<uuid_invitado>/detalles')
def acceso_invitacion(uuid_invitado):
    """Visualización de la Invitación Completa (Página 2) personalizada"""
    invitado = Invitado.query.filter_by(uuid=uuid_invitado).first()
    if not invitado:
        return render_template('404.html'), 404
        
    invitacion = db.session.get(Invitacion, invitado.invitacion_id)
    
    # Limpieza dinámica de archivos vacíos para el fallback
    if invitacion.video_url and not invitacion.video_url.startswith('http'):
        full_path = os.path.join(app.root_path, 'static', invitacion.video_url)
        if not os.path.exists(full_path) or os.path.getsize(full_path) == 0:
            invitacion.video_url = None
            
    if invitacion.musica_url and not invitacion.musica_url.startswith('http'):
        full_path = os.path.join(app.root_path, 'static', invitacion.musica_url)
        if not os.path.exists(full_path) or os.path.getsize(full_path) == 0:
            invitacion.musica_url = None
            
    if invitacion.plantilla == 'con-fotos':
        return render_template('invitacion_con_fotos.html', invitacion=invitacion, invitado=invitado)
    elif invitacion.plantilla == 'libro-3d':
        return render_template('invitacion_libro.html', invitacion=invitacion, invitado=invitado)
    else:
        return render_template('invitacion.html', invitacion=invitacion, invitado=invitado)


@app.route('/invitacion/confirmar', methods=['POST'])
def confirmar_asistencia():
    """Procesamiento de RSVP vía AJAX"""
    data = request.get_json()
    if not data or 'uuid' not in data:
        return jsonify({'success': False, 'message': 'Faltan datos de confirmación'}), 400
        
    invitado = Invitado.query.filter_by(uuid=data['uuid']).first()
    if not invitado:
        return jsonify({'success': False, 'message': 'Invitado no encontrado'}), 404
        
    try:
        invitado.telefono = data.get('telefono', invitado.telefono)
        invitado.estado_rsvp = data.get('estado_rsvp', 'Confirmado')
        
        # Procesar cupos confirmados
        if invitado.estado_rsvp == 'Rechazado':
            invitado.cupos_confirmados = 0
        else:
            cupos_c = int(data.get('cupos_confirmados', invitado.cupos_asignados))
            # Validar que no exceda el límite asignado
            if cupos_c > invitado.cupos_asignados:
                cupos_c = invitado.cupos_asignados
            invitado.cupos_confirmados = cupos_c
            
        invitado.mensaje_rsvp = data.get('mensaje_rsvp', '')
        invitado.fecha_rsvp = datetime.now()
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'RSVP guardado con éxito'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/invitacion/sugerir-musica', methods=['POST'])
def sugerir_musica():
    """Endpoint para que los invitados sugieran una canción"""
    data = request.get_json()
    if not data or 'uuid' not in data or 'cancion' not in data or 'artista' not in data:
        return jsonify({'success': False, 'message': 'Faltan datos de la sugerencia'}), 400
        
    invitado = Invitado.query.filter_by(uuid=data['uuid']).first()
    if not invitado:
        return jsonify({'success': False, 'message': 'Invitado no encontrado'}), 404
        
    try:
        nueva_sugerencia = MusicaSugerida(
            invitacion_id=invitado.invitacion_id,
            cancion=data['cancion'].strip(),
            artista=data['artista'].strip(),
            sugerido_por=invitado.nombre
        )
        db.session.add(nueva_sugerencia)
        db.session.commit()
        return jsonify({'success': True, 'message': '¡Canción sugerida con éxito!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ==========================================================================
# RUTAS DE ADMINISTRACIÓN (LOGIN, LOGOUT, DASHBOARD)
# ==========================================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'usuario_id' in session:
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        usuario = Usuario.query.filter_by(username=username).first()
        if usuario and usuario.check_password(password):
            session['usuario_id'] = usuario.id
            session['rol'] = usuario.rol
            flash(f'¡Bienvenido de nuevo, {usuario.nombre}!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
            
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Sesión cerrada correctamente.', 'success')
    return redirect(url_for('admin_login'))


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    usuario_id = session['usuario_id']
    usuario = db.session.get(Usuario, usuario_id)
    
    # Obtener todas las invitaciones de este usuario, o todas si es Super Admin
    if usuario.rol == 'SUPER_ADMIN':
        todas_invitaciones = Invitacion.query.all()
    else:
        todas_invitaciones = Invitacion.query.filter_by(usuario_id=usuario_id).all()
        
    # Obtener invitación activa de la petición o usar la primera
    inv_id = request.args.get('inv_id', type=int)
    invitacion_activa = None
    
    if todas_invitaciones:
        if inv_id:
            invitacion_activa = next((i for i in todas_invitaciones if i.id == inv_id), todas_invitaciones[0])
        else:
            invitacion_activa = todas_invitaciones[0]
            
    stats = {}
    ultimos_invitados = []
    
    if invitacion_activa:
        # Calcular estadísticas reales
        total_inv = len(invitacion_activa.invitados)
        confirmados = sum(1 for i in invitacion_activa.invitados if i.estado_rsvp == 'Confirmado')
        pendientes = sum(1 for i in invitacion_activa.invitados if i.estado_rsvp == 'Pendiente')
        rechazados = sum(1 for i in invitacion_activa.invitados if i.estado_rsvp == 'Rechazado')
        
        # Calcular cupos confirmados totales
        total_cupos_confirmados = sum(i.cupos_confirmados for i in invitacion_activa.invitados if i.estado_rsvp == 'Confirmado')
        
        stats = {
            'total_invitados': total_inv,
            'total_confirmados': total_cupos_confirmados,
            'total_pendientes': sum(i.cupos_asignados for i in invitacion_activa.invitados if i.estado_rsvp == 'Pendiente'),
            'total_rechazados': rechazados,
            'porcentaje_asistencia': round((confirmados / total_inv * 100), 1) if total_inv > 0 else 0
        }
        
        # Últimas confirmaciones
        ultimos_invitados = Invitado.query.filter_by(invitacion_id=invitacion_activa.id)\
                            .order_by(Invitado.fecha_rsvp.desc(), Invitado.created_at.desc())\
                            .limit(5).all()
                            
        # Canciones sugeridas
        canciones_sugeridas = MusicaSugerida.query.filter_by(invitacion_id=invitacion_activa.id)\
                            .order_by(MusicaSugerida.created_at.desc()).all()
    else:
        canciones_sugeridas = []
                            
    return render_template(
        'admin/dashboard.html', 
        todas_invitaciones=todas_invitaciones, 
        invitacion_activa=invitacion_activa, 
        stats=stats, 
        ultimos_invitados=ultimos_invitados,
        canciones_sugeridas=canciones_sugeridas
    )


@app.route('/admin/musica-sugerida/<int:id>/eliminar')
@login_required
def eliminar_musica_sugerida(id):
    sugerencia = db.session.get(MusicaSugerida, id)
    if sugerencia:
        inv_id = sugerencia.invitacion_id
        try:
            db.session.delete(sugerencia)
            db.session.commit()
            flash('Sugerencia musical eliminada correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al eliminar la sugerencia: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard', inv_id=inv_id))
    return redirect(url_for('admin_dashboard'))


# ==========================================================================
# CRUD DE INVITACIONES (CREAR, EDITAR, ELIMINAR FOTOS Y MÚSICA)
# ==========================================================================

def save_media_file(file_obj, folder_name):
    """Guarda archivos en Supabase Storage (si está configurado) o localmente de forma segura"""
    if file_obj and file_obj.filename != '':
        filename = secure_filename(f"{uuid.uuid4().hex}_{file_obj.filename}")
        
        if supabase:
            try:
                file_content = file_obj.read()
                blob_path = f"media/{folder_name}/{filename}"
                
                supabase.storage.from_("archivos").upload(
                    path=blob_path,
                    file=file_content,
                    file_options={"content-type": file_obj.content_type}
                )
                
                public_url = supabase.storage.from_("archivos").get_public_url(blob_path)
                return public_url
            except Exception as e:
                print(f"Error subiendo a Supabase: {e}")
                # Fallback a local si falla Supabase
                
        # Fallback local
        save_path = os.path.join(app.config['MEDIA_FOLDER'], folder_name)
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        # Si se intentó subir a Supabase, el puntero del archivo puede estar al final
        file_obj.seek(0)
        file_obj.save(os.path.join(save_path, filename))
        return f"uploads/media/{folder_name}/{filename}"
    return None


@app.route('/admin/invitacion/nueva', methods=['GET', 'POST'])
@login_required
def crear_invitacion():
    if request.method == 'POST':
        try:
            # Asegurar unicidad del slug
            base_slug = request.form['slug'].strip()
            slug = base_slug
            counter = 1
            while Invitacion.query.filter_by(slug=slug).first() is not None:
                slug = f"{base_slug}-{counter}"
                counter += 1

            nueva_inv = Invitacion(
                usuario_id=session['usuario_id'],
                slug=slug,
                titulo=request.form['titulo'],
                tipo_evento=request.form['tipo_evento'],
                plantilla=request.form['plantilla'],
                fecha_evento=datetime.strptime(request.form['fecha_evento'], '%Y-%m-%dT%H:%M'),
                lugar_nombre=request.form.get('lugar_nombre'),
                lugar_direccion=request.form.get('lugar_direccion'),
                lugar_gmaps_url=request.form.get('lugar_gmaps_url'),
                historia=request.form.get('historia'),
                codigo_vestimenta=request.form.get('codigo_vestimenta'),
                codigo_vestimenta_detalles=request.form.get('codigo_vestimenta_detalles'),
                regalos_banco=request.form.get('regalos_banco'),
                regalos_cuenta=request.form.get('regalos_cuenta'),
                regalos_nequi=request.form.get('regalos_nequi'),
                regalos_daviplata=request.form.get('regalos_daviplata'),
                regalos_lista_url=request.form.get('regalos_lista_url'),
                mensaje_final=request.form.get('mensaje_final'),
                whatsapp_confirmacion=request.form.get('whatsapp_confirmacion'),
                instagram_url=request.form.get('instagram_url')
            )

            # Subir Música & Video si se proveen
            if 'musica' in request.files:
                nueva_inv.musica_url = save_media_file(request.files['musica'], 'musica')
            if 'video' in request.files:
                nueva_inv.video_url = save_media_file(request.files['video'], 'video')

            # Subir Imágenes de Diseño (Multitema)
            if 'fondo_portada' in request.files and request.files['fondo_portada'].filename != '':
                nueva_inv.fondo_portada_url = save_media_file(request.files['fondo_portada'], 'diseno')
            if 'sello_portada' in request.files and request.files['sello_portada'].filename != '':
                nueva_inv.sello_portada_url = save_media_file(request.files['sello_portada'], 'diseno')
            if 'decoracion_bordes' in request.files and request.files['decoracion_bordes'].filename != '':
                nueva_inv.decoracion_bordes_url = save_media_file(request.files['decoracion_bordes'], 'diseno')
            if 'decoracion_centro' in request.files and request.files['decoracion_centro'].filename != '':
                nueva_inv.decoracion_centro_url = save_media_file(request.files['decoracion_centro'], 'diseno')
            
            # Subir Fotos de Historia
            if 'historia_foto_1' in request.files and request.files['historia_foto_1'].filename != '':
                nueva_inv.historia_foto_1_url = save_media_file(request.files['historia_foto_1'], 'fotos')
            if 'historia_foto_2' in request.files and request.files['historia_foto_2'].filename != '':
                nueva_inv.historia_foto_2_url = save_media_file(request.files['historia_foto_2'], 'fotos')
            if 'historia_foto_3' in request.files and request.files['historia_foto_3'].filename != '':
                nueva_inv.historia_foto_3_url = save_media_file(request.files['historia_foto_3'], 'fotos')

            db.session.add(nueva_inv)
            db.session.commit()

            # Subir Galería de Fotos Múltiple
            if 'fotos' in request.files:
                for file in request.files.getlist('fotos'):
                    if file and file.filename != '':
                        foto_url = save_media_file(file, 'fotos')
                        if foto_url:
                            db.session.add(FotoGaleria(invitacion_id=nueva_inv.id, foto_url=foto_url))
            
            # Guardar items del Cronograma
            horas = request.form.getlist('cronograma_hora[]')
            titulos = request.form.getlist('cronograma_titulo[]')
            descs = request.form.getlist('cronograma_desc[]')
            iconos = request.form.getlist('cronograma_icono[]')
            
            for i in range(len(horas)):
                if horas[i] and titulos[i]:
                    db.session.add(CronogramaItem(
                        invitacion_id=nueva_inv.id,
                        hora=horas[i],
                        titulo=titulos[i],
                        descripcion=descs[i],
                        icono=iconos[i],
                        orden=i
                    ))

            db.session.commit()
            flash('¡Invitación creada con éxito!', 'success')
            return redirect(url_for('admin_dashboard', inv_id=nueva_inv.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la invitación: {str(e)}', 'danger')

    return render_template('admin/invitacion_form.html', invitacion=None)


@app.route('/admin/invitacion/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_invitacion(id):
    invitacion = db.session.get(Invitacion, id)
    if not invitacion:
        flash('Invitación no encontrada.', 'danger')
        return redirect(url_for('admin_dashboard'))

    # Verificar que el usuario sea dueño o Super Admin
    if session['rol'] != 'SUPER_ADMIN' and invitacion.usuario_id != session['usuario_id']:
        flash('No tienes permiso para editar esta invitación.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        try:
            invitacion.slug = request.form['slug']
            invitacion.titulo = request.form['titulo']
            invitacion.tipo_evento = request.form['tipo_evento']
            invitacion.plantilla = request.form['plantilla']
            invitacion.fecha_evento = datetime.strptime(request.form['fecha_evento'], '%Y-%m-%dT%H:%M')
            invitacion.lugar_nombre = request.form.get('lugar_nombre')
            invitacion.lugar_direccion = request.form.get('lugar_direccion')
            invitacion.lugar_gmaps_url = request.form.get('lugar_gmaps_url')
            invitacion.historia = request.form.get('historia')
            invitacion.codigo_vestimenta = request.form.get('codigo_vestimenta')
            invitacion.codigo_vestimenta_detalles = request.form.get('codigo_vestimenta_detalles')
            invitacion.regalos_banco = request.form.get('regalos_banco')
            invitacion.regalos_cuenta = request.form.get('regalos_cuenta')
            invitacion.regalos_nequi = request.form.get('regalos_nequi')
            invitacion.regalos_daviplata = request.form.get('regalos_daviplata')
            invitacion.regalos_lista_url = request.form.get('regalos_lista_url')
            invitacion.mensaje_final = request.form.get('mensaje_final')
            invitacion.whatsapp_confirmacion = request.form.get('whatsapp_confirmacion')
            invitacion.instagram_url = request.form.get('instagram_url')

            # Subir Música & Video nuevos
            if 'musica' in request.files and request.files['musica'].filename != '':
                invitacion.musica_url = save_media_file(request.files['musica'], 'musica')
            if 'video' in request.files and request.files['video'].filename != '':
                invitacion.video_url = save_media_file(request.files['video'], 'video')

            # Subir Imágenes de Diseño (Multitema) nuevos
            if 'fondo_portada' in request.files and request.files['fondo_portada'].filename != '':
                invitacion.fondo_portada_url = save_media_file(request.files['fondo_portada'], 'diseno')
            if 'sello_portada' in request.files and request.files['sello_portada'].filename != '':
                invitacion.sello_portada_url = save_media_file(request.files['sello_portada'], 'diseno')
            if 'decoracion_bordes' in request.files and request.files['decoracion_bordes'].filename != '':
                invitacion.decoracion_bordes_url = save_media_file(request.files['decoracion_bordes'], 'diseno')
            if 'decoracion_centro' in request.files and request.files['decoracion_centro'].filename != '':
                invitacion.decoracion_centro_url = save_media_file(request.files['decoracion_centro'], 'diseno')
                
            # Subir Fotos de Historia nuevas
            if 'historia_foto_1' in request.files and request.files['historia_foto_1'].filename != '':
                invitacion.historia_foto_1_url = save_media_file(request.files['historia_foto_1'], 'fotos')
            if 'historia_foto_2' in request.files and request.files['historia_foto_2'].filename != '':
                invitacion.historia_foto_2_url = save_media_file(request.files['historia_foto_2'], 'fotos')
            if 'historia_foto_3' in request.files and request.files['historia_foto_3'].filename != '':
                invitacion.historia_foto_3_url = save_media_file(request.files['historia_foto_3'], 'fotos')

            # Agregar Fotos Nuevas
            if 'fotos' in request.files:
                for file in request.files.getlist('fotos'):
                    if file and file.filename != '':
                        foto_url = save_media_file(file, 'fotos')
                        if foto_url:
                            db.session.add(FotoGaleria(invitacion_id=invitacion.id, foto_url=foto_url))

            # Actualizar Cronograma (Limpiar anteriores y recrear)
            CronogramaItem.query.filter_by(invitacion_id=invitacion.id).delete()
            
            horas = request.form.getlist('cronograma_hora[]')
            titulos = request.form.getlist('cronograma_titulo[]')
            descs = request.form.getlist('cronograma_desc[]')
            iconos = request.form.getlist('cronograma_icono[]')
            
            for i in range(len(horas)):
                if horas[i] and titulos[i]:
                    db.session.add(CronogramaItem(
                        invitacion_id=invitacion.id,
                        hora=horas[i],
                        titulo=titulos[i],
                        descripcion=descs[i],
                        icono=iconos[i],
                        orden=i
                    ))

            db.session.commit()
            
            # Regenerar QRs de los invitados si el dominio o URL cambió (opcional, se delega a cambios manuales)
            
            flash('¡Invitación actualizada con éxito!', 'success')
            return redirect(url_for('admin_dashboard', inv_id=invitacion.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar los cambios: {str(e)}', 'danger')

    return render_template('admin/invitacion_form.html', invitacion=invitacion)


@app.route('/admin/invitacion/<int:id>/foto/<int:foto_id>/eliminar')
@login_required
def eliminar_foto(id, foto_id):
    foto = db.session.get(FotoGaleria, foto_id)
    if foto:
        try:
            # Eliminar archivo físico
            file_path = os.path.join(app.root_path, 'static', foto.foto_url)
            if os.path.exists(file_path):
                os.remove(file_path)
            db.session.delete(foto)
            db.session.commit()
            flash('Foto eliminada de la galería.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al eliminar la foto: {str(e)}', 'danger')
            
    return redirect(url_for('editar_invitacion', id=id))


# ==========================================================================
# GESTIÓN DE INVITADOS (CRUD, IMPORTADOR MASIVO, ZIP QRS, EXPORTADOR LISTAS)
# ==========================================================================

@app.route('/admin/invitacion/<int:id>/invitados')
@login_required
def lista_invitados(id):
    invitacion = db.session.get(Invitacion, id)
    if not invitacion:
        flash('Invitación no encontrada.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    invitados = Invitado.query.filter_by(invitacion_id=id).order_by(Invitado.nombre.asc()).all()
    return render_template('admin/invitados.html', invitacion=invitacion, invitados=invitados)


@app.route('/admin/invitacion/<int:id>/invitados/agregar', methods=['POST'])
@login_required
def agregar_invitado(id):
    invitacion = db.session.get(Invitacion, id)
    if not invitacion:
        flash('Invitación no encontrada.', 'danger')
        return redirect(url_for('admin_dashboard'))

    try:
        nuevo = Invitado(
            invitacion_id=id,
            nombre=request.form['nombre'],
            mesa=request.form.get('mesa', 'Por asignar') or 'Por asignar',
            cupos_asignados=int(request.form.get('cupos_asignados', 1)),
            telefono=request.form.get('telefono'),
            correo=request.form.get('correo')
        )
        db.session.add(nuevo)
        db.session.commit()

        # Generar QR dinámicamente usando el host del request actual
        nuevo.generate_qr(request.host_url.rstrip('/'))
        db.session.commit()

        flash('Invitado agregado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear el invitado: {str(e)}', 'danger')

    return redirect(url_for('lista_invitados', id=id))


@app.route('/admin/invitado/<int:id>/eliminar')
@login_required
def eliminar_invitado(id):
    invitado = db.session.get(Invitado, id)
    if invitado:
        inv_id = invitado.invitacion_id
        try:
            # Eliminar QR físico
            if invitado.qr_path:
                file_path = os.path.join(app.root_path, 'static', invitado.qr_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
            db.session.delete(invitado)
            db.session.commit()
            flash('Invitado eliminado correctamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al eliminar invitado: {str(e)}', 'danger')
        return redirect(url_for('lista_invitados', id=inv_id))
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/invitacion/<int:id>/invitados/importar', methods=['POST'])
@login_required
def importar_invitados(id):
    invitacion = db.session.get(Invitacion, id)
    if not invitacion:
        flash('Invitación no encontrada.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if 'file' not in request.files:
        flash('No se subió ningún archivo.', 'danger')
        return redirect(url_for('lista_invitados', id=id))

    file = request.files['file']
    if file.filename == '':
        flash('Archivo no seleccionado.', 'danger')
        return redirect(url_for('lista_invitados', id=id))

    try:
        # Detectar formato del archivo
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        
        if ext == 'csv':
            df = pd.read_csv(file)
        elif ext in ['xlsx', 'xls']:
            df = pd.read_excel(file)
        else:
            flash('Formato no soportado. Sube un XLSX, XLS o CSV.', 'danger')
            return redirect(url_for('lista_invitados', id=id))

        # Estandarizar nombres de columnas (limpiar acentos, minúsculas, espacios)
        df.columns = df.columns.str.strip().str.lower()
        
        # Mapeo flexible de columnas comunes
        col_mapping = {
            'nombre': ['nombre', 'guest name', 'invitado', 'name'],
            'mesa': ['mesa', 'table', 'n mesa', 'nro mesa'],
            'cupos': ['cupos', 'cupos asignados', 'seats', 'tickets', 'cantidad'],
            'telefono': ['teléfono', 'telefono', 'celular', 'phone', 'whatsapp'],
            'correo': ['correo', 'correo electrónico', 'email', 'mail']
        }
        
        def find_col(target):
            for col in df.columns:
                if col in col_mapping[target]:
                    return col
            return None

        name_col = find_col('nombre')
        if not name_col:
            flash('El archivo debe tener una columna llamada "Nombre" o "Invitado".', 'danger')
            return redirect(url_for('lista_invitados', id=id))

        mesa_col = find_col('mesa')
        cupos_col = find_col('cupos')
        tel_col = find_col('telefono')
        mail_col = find_col('correo')

        creados = 0
        duplicados = 0
        errores = 0

        host_url = request.host_url.rstrip('/')

        for _, row in df.iterrows():
            nombre = str(row[name_col]).strip()
            if not nombre or nombre == 'nan':
                errores += 1
                continue

            # Validar duplicados en la base de datos para esta invitación
            existe = Invitado.query.filter_by(invitacion_id=id, nombre=nombre).first()
            if existe:
                duplicados += 1
                continue

            try:
                # Extraer y formatear datos
                mesa = str(row[mesa_col]).strip() if mesa_col and not pd.isna(row[mesa_col]) else 'Por asignar'
                if mesa == 'nan': mesa = 'Por asignar'
                
                cupos = int(row[cupos_col]) if cupos_col and not pd.isna(row[cupos_col]) else 2
                
                tel = str(row[tel_col]).strip() if tel_col and not pd.isna(row[tel_col]) else None
                if tel == 'nan': tel = None
                
                mail = str(row[mail_col]).strip() if mail_col and not pd.isna(row[mail_col]) else None
                if mail == 'nan': mail = None

                nuevo = Invitado(
                    invitacion_id=id,
                    nombre=nombre,
                    mesa=mesa,
                    cupos_asignados=cupos,
                    telefono=tel,
                    correo=mail
                )
                db.session.add(nuevo)
                db.session.commit()

                # Generar el código QR
                nuevo.generate_qr(host_url)
                db.session.commit()
                creados += 1
            except Exception as e:
                db.session.rollback()
                errores += 1
                print("Error al importar fila:", e)

        flash(f"<b>Resumen de Importación:</b><br>"
              f"✔️ Creados con éxito: {creados}<br>"
              f"⚠️ Duplicados omitidos: {duplicados}<br>"
              f"❌ Filas con error: {errores}", "success")
        
    except Exception as e:
        flash(f'Error al procesar el archivo: {str(e)}', 'danger')

    return redirect(url_for('lista_invitados', id=id))


@app.route('/admin/invitacion/<int:id>/invitados/descargar-qrs')
@login_required
def descargar_todos_qrs(id):
    """Agrupa todos los QRs de la invitación en un archivo ZIP para descarga directa"""
    invitacion = db.session.get(Invitacion, id)
    if not invitacion:
        return "Invitación no encontrada", 404

    # Crear buffer en memoria
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for invitado in invitacion.invitados:
            if invitado.qr_path:
                file_path = os.path.join(app.root_path, 'static', invitado.qr_path)
                if os.path.exists(file_path):
                    # Nombre del archivo dentro del ZIP
                    slug_name = slugify_filter(invitado.nombre)
                    zip_filename = f"{slug_name}_qr.png"
                    zf.write(file_path, zip_filename)

    memory_file.seek(0)
    zip_name = f"QRs_{slugify_filter(invitacion.titulo)}.zip"
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_name
    )


@app.route('/admin/invitacion/<int:id>/exportar/<formato>')
@login_required
def exportar_lista_invitados(id, formato):
    """Exportación de la lista de confirmaciones de invitados a Excel, CSV o PDF"""
    invitacion = db.session.get(Invitacion, id)
    if not invitacion:
        return "Invitación no encontrada", 404

    invitados = Invitado.query.filter_by(invitacion_id=id).order_by(Invitado.nombre.asc()).all()
    
    # Crear estructura de datos
    data = []
    for inv in invitados:
        data.append({
            'Nombre': inv.nombre,
            'Mesa': inv.mesa,
            'Cupos Asignados': inv.cupos_asignados,
            'Cupos Confirmados': inv.cupos_confirmados,
            'Teléfono': inv.telefono or 'N/A',
            'Correo': inv.correo or 'N/A',
            'Estado RSVP': inv.estado_rsvp,
            'Mensaje RSVP': inv.mensaje_rsvp or ''
        })
    df = pd.DataFrame(data)

    filename_base = f"Lista_{slugify_filter(invitacion.titulo)}"

    # 1. EXPORTACIÓN A EXCEL
    if formato == 'xlsx':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Invitados')
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{filename_base}.xlsx"
        )

    # 2. EXPORTACIÓN A CSV
    elif formato == 'csv':
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"{filename_base}.csv"
        )

    # 3. EXPORTACIÓN A PDF (Usando ReportLab)
    elif formato == 'pdf':
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=15
        )
        
        story.append(Paragraph(f"Lista de Invitados - {invitacion.titulo}", title_style))
        story.append(Spacer(1, 10))
        
        # Tabla de Datos
        table_data = [['Nombre', 'Mesa', 'Cupos Asig.', 'Cupos Conf.', 'Teléfono', 'RSVP']]
        for inv in invitados:
            table_data.append([
                inv.nombre[:25], # Limitar longitud de texto
                inv.mesa,
                str(inv.cupos_asignados),
                str(inv.cupos_confirmados),
                inv.telefono or 'N/A',
                inv.estado_rsvp
            ])
            
        t = Table(table_data, colWidths=[180, 60, 70, 70, 90, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('ALIGN', (0,1), (0,-1), 'LEFT'), # Alinear nombre a la izquierda
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8fafc')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f1f5f9')]),
        ]))
        
        story.append(t)
        doc.build(story)
        output.seek(0)
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{filename_base}.pdf"
        )
        
    return "Formato no válido", 400


# ==========================================================================
# RUTAS DE ADMINISTRACIÓN DE USUARIOS (SUPER ADMIN)
# ==========================================================================

@app.route('/admin/usuarios')
@login_required
def lista_usuarios():
    # Verificar que el usuario actual tenga rol de SUPER ADMIN
    if session.get('rol') != 'SUPER_ADMIN':
        flash('No tienes permiso para ver esta sección.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    usuarios = Usuario.query.order_by(Usuario.username.asc()).all()
    return render_template('admin/usuarios.html', usuarios=usuarios)


@app.route('/admin/usuarios/agregar', methods=['POST'])
@login_required
def agregar_usuario():
    if session.get('rol') != 'SUPER_ADMIN':
        flash('No tienes permiso para realizar esta acción.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    try:
        nuevo = Usuario(
            username=request.form['username'],
            nombre=request.form['nombre'],
            rol=request.form['rol']
        )
        nuevo.set_password(request.form['password'])
        db.session.add(nuevo)
        db.session.commit()
        flash('Usuario administrador agregado con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear el usuario admin: {str(e)}', 'danger')
        
    return redirect(url_for('lista_usuarios'))


@app.route('/admin/usuarios/<int:id>/eliminar')
@login_required
def eliminar_usuario(id):
    if session.get('rol') != 'SUPER_ADMIN':
        flash('No tienes permiso para realizar esta acción.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    usuario = db.session.get(Usuario, id)
    if usuario:
        # Prevenir auto-eliminación
        if usuario.id == session['usuario_id']:
            flash('No puedes eliminar tu propio usuario en sesión.', 'danger')
            return redirect(url_for('lista_usuarios'))
            
        try:
            db.session.delete(usuario)
            db.session.commit()
            flash('Usuario administrador eliminado con éxito.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al eliminar el usuario: {str(e)}', 'danger')
            
    return redirect(url_for('lista_usuarios'))


# ==========================================================================
# INICIALIZACIÓN DE LA APLICACIÓN (SQLITE FALLBACK & SEEDING)
# ==========================================================================

def init_db_seeds():
    """Crea un usuario administrador inicial 'admin' si la base de datos está vacía"""
    with app.app_context():
        db.create_all()
        
        # Verificar si hay usuarios creados
        if not Usuario.query.first():
            # Crear Super Admin inicial por defecto
            admin = Usuario(
                username='admin',
                nombre='Super Administrador',
                rol='SUPER_ADMIN'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Crear carpetas estáticas requeridas si no existen
            for folder in [app.config['MEDIA_FOLDER'], app.config['QR_FOLDER']]:
                if not os.path.exists(folder):
                    os.makedirs(folder)
            
            db.session.commit()
            print("Base de datos inicializada. Usuario por defecto creado: admin / admin123")

if __name__ == '__main__':
    init_db_seeds()
    # Ejecución del servidor Flask local
    app.run(debug=True, host='0.0.0.0', port=5000)

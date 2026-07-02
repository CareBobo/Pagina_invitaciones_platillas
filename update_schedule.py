from app import app, db, CronogramaItem, Invitacion

with app.app_context():
    # Obtener la invitacion
    inv = Invitacion.query.first()
    if inv:
        # Limpiar cronograma existente
        CronogramaItem.query.filter_by(invitacion_id=inv.id).delete()
        
        # Añadir nuevos items solicitados
        items = [
            CronogramaItem(invitacion_id=inv.id, hora="04:00 PM", titulo="¡Sí, quiero!", descripcion="La ceremonia principal", icono="ring", orden=1),
            CronogramaItem(invitacion_id=inv.id, hora="05:30 PM", titulo="Sesión de Fotos", descripcion="Capturando recuerdos", icono="camera", orden=2),
            CronogramaItem(invitacion_id=inv.id, hora="06:30 PM", titulo="Aperitivos y Brindis", descripcion="Salud por los novios", icono="glass-cheers", orden=3),
            CronogramaItem(invitacion_id=inv.id, hora="08:00 PM", titulo="Cena / Comida", descripcion="Banquete de celebración", icono="utensils", orden=4),
            CronogramaItem(invitacion_id=inv.id, hora="10:00 PM", titulo="Corte del Pastel", descripcion="Un dulce momento", icono="birthday-cake", orden=5)
        ]
        db.session.add_all(items)
        db.session.commit()
        print("Cronograma actualizado con éxito.")
    else:
        print("No se encontró ninguna invitación.")

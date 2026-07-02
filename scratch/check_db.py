import sqlite3
import os

db_path = 'invitaciones.db'
if not os.path.exists(db_path):
    print("Database file not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", [t[0] for t in tables])
    
    # Check Usuarios
    cursor.execute("SELECT id, username, nombre, rol FROM usuarios;")
    usuarios = cursor.fetchall()
    print("\n=== Usuarios ===")
    for u in usuarios:
        print(f"ID: {u[0]}, Username: {u[1]}, Nombre: {u[2]}, Rol: {u[3]}")
        
    # Check Invitaciones
    cursor.execute("SELECT id, titulo, slug, plantilla, instagram_url FROM invitaciones;")
    invitaciones = cursor.fetchall()
    print("\n=== Invitaciones ===")
    for inv in invitaciones:
        print(f"ID: {inv[0]}, Titulo: {inv[1]}, Slug: {inv[2]}, Plantilla: {inv[3]}, Instagram: {inv[4]}")
        
    # Check Invitados
    cursor.execute("SELECT id, nombre, uuid, invitacion_id FROM invitados LIMIT 5;")
    invitados = cursor.fetchall()
    print("\n=== Invitados (primeros 5) ===")
    for i in invitados:
        print(f"ID: {i[0]}, Nombre: {i[1]}, UUID: {i[2]}, Invitacion ID: {i[3]}")
        
except Exception as e:
    print("Error:", e)
finally:
    conn.close()

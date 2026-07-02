from app import app, db

def migrate():
    with app.app_context():
        with db.engine.connect() as conn:
            try:
                conn.execute(db.text("ALTER TABLE invitaciones ADD COLUMN fondo_portada_url VARCHAR(300)"))
                print("Added fondo_portada_url")
            except Exception as e:
                print(e)
            
            try:
                conn.execute(db.text("ALTER TABLE invitaciones ADD COLUMN sello_portada_url VARCHAR(300)"))
                print("Added sello_portada_url")
            except Exception as e:
                print(e)
                
            try:
                conn.execute(db.text("ALTER TABLE invitaciones ADD COLUMN decoracion_bordes_url VARCHAR(300)"))
                print("Added decoracion_bordes_url")
            except Exception as e:
                print(e)
                
            try:
                conn.execute(db.text("ALTER TABLE invitaciones ADD COLUMN decoracion_centro_url VARCHAR(300)"))
                print("Added decoracion_centro_url")
            except Exception as e:
                print(e)
                
            try:
                conn.execute(db.text("ALTER TABLE invitaciones ADD COLUMN instagram_url VARCHAR(300)"))
                print("Added instagram_url")
            except Exception as e:
                print(e)

if __name__ == '__main__':
    migrate()

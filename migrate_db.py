import sqlite3
import os

db_dir = os.path.join(os.path.dirname(__file__), 'data')
db_path = os.path.join(db_dir, 'logtracker.db')

def migrate_database():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Sauvegarde des données existantes
        cursor.execute("SELECT id, key, title, is_active, ticket_number FROM tickets")
        old_tickets = cursor.fetchall()
        
        # Suppression de la table existante
        cursor.execute("DROP TABLE tickets")
        
        # Création de la nouvelle structure
        cursor.execute("""
            CREATE TABLE tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                ticket_number TEXT NOT NULL,
                title TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                UNIQUE(project_id, ticket_number)
            )
        """)
        
        # Migration des données
        for ticket in old_tickets:
            old_id, key, title, is_active, ticket_number = ticket
            # On utilise le ticket_number s'il existe, sinon on utilise la clé
            final_ticket_number = ticket_number if ticket_number else key
            cursor.execute("""
                INSERT INTO tickets (id, ticket_number, title, is_active)
                VALUES (?, ?, ?, ?)
            """, (old_id, final_ticket_number, title, is_active or 1))
        
        conn.commit()
        print("Migration réussie !")
        
    except Exception as e:
        conn.rollback()
        print(f"Erreur pendant la migration : {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()

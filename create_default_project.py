import sqlite3
import os

db_dir = os.path.join(os.path.dirname(__file__), 'data')
db_path = os.path.join(db_dir, 'logtracker.db')

def create_default_project():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Crée un projet par défaut
        cursor.execute("""
            INSERT INTO projects (name) 
            VALUES ('Default')
        """)
        
        project_id = cursor.lastrowid
        
        # Associe tous les tickets sans projet au projet par défaut
        cursor.execute("""
            UPDATE tickets 
            SET project_id = ?
            WHERE project_id IS NULL
        """, (project_id,))
        
        conn.commit()
        print("Projet par défaut créé et tickets associés !")
        
    except Exception as e:
        conn.rollback()
        print(f"Erreur pendant la création du projet : {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    create_default_project()

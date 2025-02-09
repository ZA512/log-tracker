import sqlite3
import os

db_dir = os.path.join(os.path.dirname(__file__), 'data')
db_path = os.path.join(db_dir, 'logtracker.db')

def associate_projects():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Récupère tous les tickets qui n'ont pas de project_id
        cursor.execute("SELECT id, ticket_number FROM tickets WHERE project_id IS NULL")
        tickets = cursor.fetchall()
        
        # Récupère tous les projets
        cursor.execute("SELECT id, name FROM projects")
        projects = cursor.fetchall()
        
        if not projects:
            print("Aucun projet trouvé dans la base de données.")
            return
        
        # Par défaut, on associe tous les tickets au premier projet
        default_project_id = projects[0][0]
        
        # Met à jour les tickets
        for ticket_id, ticket_number in tickets:
            # Cherche si le ticket_number commence par un préfixe de projet
            project_id = default_project_id
            for proj_id, proj_name in projects:
                if ticket_number and ticket_number.upper().startswith(proj_name.upper()):
                    project_id = proj_id
                    break
            
            cursor.execute("""
                UPDATE tickets 
                SET project_id = ?
                WHERE id = ?
            """, (project_id, ticket_id))
        
        conn.commit()
        print("Association des projets réussie !")
        
    except Exception as e:
        conn.rollback()
        print(f"Erreur pendant l'association : {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    associate_projects()

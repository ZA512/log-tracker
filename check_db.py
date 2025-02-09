import sqlite3
import os

db_dir = os.path.join(os.path.dirname(__file__), 'data')
db_path = os.path.join(db_dir, 'logtracker.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Vérifie la structure de la table tickets
cursor.execute("PRAGMA table_info(tickets)")
print("Structure de la table tickets:")
for col in cursor.fetchall():
    print(col)

# Vérifie les données dans la table tickets
cursor.execute("SELECT * FROM tickets LIMIT 5")
print("\nDonnées de la table tickets:")
for row in cursor.fetchall():
    print(row)

conn.close()

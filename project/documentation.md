# Documentation Technique LogTracker

## Architecture du Système

### 1. Vue d'Ensemble
L'application est construite selon une architecture MVC (Modèle-Vue-Contrôleur) avec les composants suivants :
- Interface utilisateur (Vue)
- Logique métier (Contrôleur)
- Stockage des données (Modèle)

### 2. Composants Principaux

#### 2.1 Interface Utilisateur (src/ui/)
- `main_window.py` : Fenêtre principale de l'application
- `config_window.py` : Interface de configuration
- `notification.py` : Système de notifications

#### 2.2 Logique Métier (src/core/)
- `project_manager.py` : Gestion des projets
- `ticket_manager.py` : Gestion des tickets JIRA
- `entry_manager.py` : Gestion des entrées de journal
- `time_tracker.py` : Suivi du temps

#### 2.3 Utilitaires (src/utils/)
- `database.py` : Opérations base de données
- `jira_api.py` : Intégration JIRA
- `config.py` : Gestion de la configuration
- `logger.py` : Système de logging

### 3. Base de Données

#### 3.1 Schéma
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    jira_key TEXT
);

CREATE TABLE tickets (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    ticket_number TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (project_id) REFERENCES projects (id)
);

CREATE TABLE entries (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    project_id INTEGER,
    ticket_id INTEGER,
    description TEXT NOT NULL,
    duration INTEGER,
    synced_to_jira BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (project_id) REFERENCES projects (id),
    FOREIGN KEY (ticket_id) REFERENCES tickets (id)
);
```

### 4. API JIRA

#### 4.1 Endpoints Utilisés
- GET /rest/api/2/project : Liste des projets
- GET /rest/api/2/issue/{key} : Détails d'un ticket
- POST /rest/api/2/issue/{key}/worklog : Ajout de temps

#### 4.2 Authentication
- Basic Auth ou Token
- Configuration dans config.ini

### 5. Configuration

#### 5.1 Fichier config.ini
```ini
[UI]
window_size = 300x200
always_on_top = true
notification_duration = 3

[JIRA]
base_url = https://jira.example.com
api_token = 
username = 

[Database]
path = data/logtracker.db

[Notification]
reminder_interval = 30
```

### 6. Tests

#### 6.1 Structure
- tests/unit/ : Tests unitaires
- tests/integration/ : Tests d'intégration
- tests/fixtures/ : Données de test

#### 6.2 Exécution
```bash
pytest tests/
pytest tests/ --cov=src/
```

### 7. Limitations Connues

#### 7.1 Interface Utilisateur
- **Treeview et texte multi-lignes** : Le widget Treeview de Tkinter ne supporte pas nativement l'ajustement automatique de la hauteur des lignes en fonction du contenu. Solutions possibles :
  1. Créer un widget personnalisé
  2. Utiliser une alternative (frames + labels)
  3. Calculer manuellement la hauteur

#### 7.2 Performance
- **Chargement des données** : Les entrées sont chargées en mémoire, ce qui pourrait poser problème avec un grand volume de données
- **Rafraîchissement de l'interface** : Le rafraîchissement complet du Treeview pourrait être optimisé

### 8. Internationalisation

#### 8.1 Structure
```
src/
  locale/
    en/
      LC_MESSAGES/
        messages.po
        messages.mo
    fr/
      LC_MESSAGES/
        messages.po
        messages.mo
```

#### 8.2 Utilisation
```python
import gettext

# Configuration
gettext.bindtextdomain('logtracker', 'locale')
gettext.textdomain('logtracker')
_ = gettext.gettext

# Exemple d'utilisation
print(_("Sauvegarder"))
```

### 9. Sécurité

#### 9.1 Stockage des Données
- Base SQLite chiffrée
- Pas de stockage de données sensibles
- Validation des entrées utilisateur

#### 9.2 GDPR
- Pas de collecte de données personnelles
- Données stockées localement uniquement
- Export des données possible
- Suppression des données sur demande
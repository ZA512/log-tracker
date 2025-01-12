# LogTracker

LogTracker est une application de gestion et d'analyse de logs avancée. Elle permet de suivre, analyser et gérer efficacement les logs de différentes sources.

## Installation

### Prérequis
- Python 3.8 ou supérieur
- Git
- Un compte Jira (pour les fonctionnalités de synchronisation)

### Installation de la version stable (v1.0)

1. Cloner le dépôt avec la version spécifique :
```bash
git clone https://github.com/ZA512/log-tracker.git
cd log-tracker
git checkout v1.0
```

### Configuration de l'environnement virtuel

#### Windows
```bash
# Création de l'environnement virtuel
python -m venv venv

# Activation de l'environnement virtuel
.\venv\Scripts\activate

# Installation des dépendances
pip install -r requirements.txt
```

#### macOS/Linux
```bash
# Création de l'environnement virtuel
python3 -m venv venv

# Activation de l'environnement virtuel
source venv/bin/activate

# Installation des dépendances
pip install -r requirements.txt
```

## Installation des Exécutables

### Windows
1. Téléchargez `LogTracker-Windows.exe` depuis la [page des releases](https://github.com/ZA512/log-tracker/releases)
2. Double-cliquez sur l'exécutable pour lancer l'application

### macOS
1. Téléchargez `LogTracker-Mac.app` depuis la [page des releases](https://github.com/ZA512/log-tracker/releases)
2. Déplacez l'application dans votre dossier Applications
3. Double-cliquez sur l'application pour la lancer

Note : Lors du premier lancement sur macOS, vous devrez peut-être autoriser l'application dans Préférences Système > Sécurité et confidentialité.

## Création des Exécutables (pour les développeurs)

### Prérequis
- Python 3.8 ou supérieur
- Les dépendances du projet installées (`pip install -r requirements.txt`)

### Windows
```bash
# Activation de l'environnement virtuel
.\venv\Scripts\activate

# Création de l'exécutable
pyinstaller logtracker.spec
```
L'exécutable sera créé dans le dossier `dist/LogTracker.exe`

### macOS
```bash
# Activation de l'environnement virtuel
source venv/bin/activate

# Création de l'exécutable
pyinstaller logtracker.spec
```
L'application sera créée dans le dossier `dist/LogTracker.app`

## Structure du Projet

```
logtracker/
├── project/                    # Documentation du projet
│   ├── specifications.md       # Spécifications détaillées
│   ├── guidelines.md          # Lignes directrices de développement
│   ├── documentation.md       # Documentation technique
│   ├── devbook.md            # Journal de développement
│   └── mindmap_functionality.md# Carte des fonctionnalités
├── src/                       # Code source
│   ├── core/                  # Fonctionnalités principales
│   ├── ui/                    # Interface utilisateur
│   └── utils/                 # Utilitaires
├── tests/                     # Tests unitaires et d'intégration
└── requirements.txt           # Dépendances du projet
```

## Utilisation

### Configuration initiale
1. Lancez l'application pour la première fois :
   ```bash
   # Windows
   python src/qt_main.py

   # macOS/Linux
   python3 src/qt_main.py
   ```

2. Dans la fenêtre de configuration qui s'ouvre :
   - Renseignez vos identifiants Jira
   - Configurez le chemin vers vos fichiers de logs
   - Sauvegardez la configuration

### Utilisation quotidienne
1. Assurez-vous que l'environnement virtuel est activé
2. Lancez l'application avec la commande ci-dessus
3. L'interface principale vous permet de :
   - Visualiser les logs en temps réel
   - Synchroniser avec Jira
   - Filtrer et rechercher dans les logs
   - Exporter les données

## Contribution

Les contributions sont les bienvenues ! Veuillez consulter notre guide de contribution pour plus de détails.

## Licence

[À venir]

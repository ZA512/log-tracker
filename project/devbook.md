# Devbook : Application de Journalisation Minimaliste

### Objectif
Créer une application Python minimaliste avec une interface utilisateur Tkinter, permettant de journaliser des actions quotidiennes avec des fonctionnalités de gestion de projet et d'intégration de tickets JIRA.

---

## Découpage du Projet en Étapes

### 1. Initialisation du Projet
- [x] Créer un environnement Python virtuel pour isoler le projet.
- [x] Installer les bibliothèques nécessaires (Tkinter, sqlite3, pynotifier, requests pour l'API JIRA).
- [x] Initialiser une structure de fichiers : 
  - `main.py` (point d'entrée de l'application)
  - `db_manager.py` (gestion de la base SQLite)
  - `jira_integration.py` (intégration API JIRA)
  - `ui_manager.py` (gestion de l'interface utilisateur)

### 2. Création de la Base de Données SQLite
- [x] Concevoir une base de données SQLite avec les tables suivantes :
  - `projects` : contient les noms des projets.
  - `tickets` : associe des tickets JIRA à des projets.
  - `entries` : journal des actions réalisées (timestamp, description, projet, ticket, durée).
- [ ] Implémenter des fonctions pour :
  - Ajouter/modifier/supprimer un projet.
  - Ajouter/modifier/supprimer un ticket.
  - Ajouter/modifier/supprimer une entrée de journalisation.

### 3. Interface Utilisateur (UI)
#### Fenêtre de Base
- [x] Créer une fenêtre Tkinter minimaliste flottante.
- [x] Ajouter des options pour rendre la fenêtre toujours au premier plan et déplaçable.

#### Champs de Saisie
- [x] Ajouter trois champs de saisie :
  - **Nom du projet** (optionnel, avec suggestions automatiques).
  - **Numéro de ticket JIRA** (optionnel, dépendant du projet sélectionné).
  - **Description de l'action** (obligatoire).
  - **Durée en minutes** (optionnel).
- [x] Implémenter une logique pour vérifier que le champ "Description" est rempli avant de sauvegarder.

#### Boutons
- [x] Ajouter un bouton "Sauvegarder" qui :
  - Valide les champs.
  - Enregistre l'entrée dans la base SQLite.
  - Affiche le message "Enregistrement réalisé" pendant 3 secondes.
- [x] Ajouter un bouton "Afficher les entrées du jour" qui :
  - Récupère les données de la journée depuis SQLite.
  - Affiche les entrées dans une nouvelle fenêtre ou un tableau.
- [x] Ajouter un bouton "Exporter" pour exporter les données en CSV, JSON ou TXT.

### 4. Gestion des Suggestions et Auto-Complétion
- [x] Ajouter une logique pour afficher les projets existants dans une liste déroulante.
- [x] Si un projet est sélectionné, afficher les tickets associés dans une autre liste déroulante.
- [x] Implémenter la création automatique de nouveaux projets ou tickets si aucun n’est trouvé.

### 5. Notifications
- [x] Ajouter une fonctionnalité qui vérifie si aucune action n’a été saisie depuis 30 minutes.
- [x] Utiliser Pynotifier pour afficher un rappel de journalisation.

### 6. Intégration API JIRA
- [x] Implémenter une fonction dans `jira_integration.py` pour envoyer des entrées à JIRA via l'API.
- [x] Ajouter une option pour marquer une entrée comme envoyée à JIRA.
- [x] Ajouter un mécanisme pour éviter les doublons lors de l’envoi.

### 7. Tests et Débogage
- [x] Tester les fonctionnalités de base de l’interface utilisateur.
- [x] Vérifier l’intégrité de la base de données (ajout, modification, suppression).
- [x] Tester l’intégration JIRA avec des tickets fictifs.
- [x] Valider les exportations (CSV, JSON, TXT).
- [x] Simuler des cas où l’utilisateur oublie de remplir certains champs.

### 8. Documentation et Livraison
- [x] Documenter chaque fichier et fonction dans le code.
- [x] Créer un guide d'utilisation simple pour les utilisateurs finaux.
- [x] Préparer un fichier README.md décrivant le projet, ses fonctionnalités et comment l'utiliser.

### Points à améliorer

#### Interface Utilisateur
- [ ] Améliorer l'affichage des descriptions multi-lignes dans le Treeview
  - Explorer des alternatives au widget Treeview pour un meilleur support des textes longs
  - Ou implémenter un widget personnalisé basé sur Treeview avec hauteur adaptative
- [ ] Optimiser la taille de la fenêtre d'ajout d'entrée
  - Ajuster la hauteur du champ description (5 lignes)
  - Ajouter le retour à la ligne par mot

#### Ergonomie
- [ ] Déplier automatiquement tous les groupes dans la vue des entrées
- [ ] Améliorer la visibilité de la dernière entrée
  - Correction du tri pour afficher la dernière entrée
  - Mise à jour en temps réel du résumé

#### Internationalisation
- [ ] Implémenter le support multilingue (l18n)
  - Extraire tous les textes dans des fichiers de traduction
  - Ajouter le support pour le changement de langue
  - Commencer avec le français et l'anglais

# Journal de Développement

## 2025-01-02

### 15:05 - Initialisation du projet
- [x] Création de la structure du projet
- [x] Mise en place des fichiers de documentation :
  - README.md : Vue d'ensemble du projet
  - specifications.md : Spécifications détaillées
  - guidelines.md : Standards de développement
  - mindmap_functionality.md : Carte des fonctionnalités
  - documentation.md : Documentation technique

### 15:16 - Mise en place de l'environnement virtuel
- [x] Création de l'environnement virtuel avec `python -m venv venv`
- [x] Configuration du fichier requirements.txt avec les dépendances initiales
- [x] Installation des dépendances dans l'environnement virtuel

### 15:20 - Implémentation TDD de la classe Entry
- [x] Création de la structure des tests (unit, integration, fixtures)
- [x] Implémentation des premiers tests pour la classe Entry
- [x] Implémentation de la classe Entry avec validation
- [x] Exécution réussie des tests unitaires

### 15:27 - Implémentation de la base de données
- [x] Création du dossier data pour la base de données
- [x] Implémentation de la classe Database dans src/utils/database.py
- [x] Création des tests pour la base de données dans tests/unit/test_database.py
- [x] Tests réussis pour :
  - Création des tables
  - Ajout/récupération de projets
  - Ajout/récupération de tickets
  - Ajout/récupération d'entrées
  - Filtrage par date
  - Contraintes d'unicité

## 2025-01-03

### 12:25 - Améliorations de l'interface
- [x] Augmentation de la hauteur du champ description à 5 lignes
- [x] Ajout du retour à la ligne par mot dans le champ description
- [x] Correction de l'affichage de la dernière entrée dans le résumé
- [x] Dépliage automatique des groupes dans la vue des entrées

### 14:00 - Mise à jour de la documentation
- [x] Mise à jour du devbook avec les nouvelles fonctionnalités
- [x] Ajout d'une section "Points à améliorer"
- [x] Documentation des limitations actuelles (Treeview)
- [x] Mise à jour du journal de développement
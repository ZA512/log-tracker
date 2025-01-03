# Guidelines de Développement

## 1. Standards de Code

### 1.1 Style de Code
- Suivre PEP 8 pour Python
- Utiliser Black pour le formatage automatique
- Longueur maximale des lignes : 88 caractères
- Utiliser des noms explicites pour les variables et fonctions

### 1.2 Documentation
- Docstrings pour toutes les classes et fonctions publiques
- README à jour pour chaque module
- Commentaires pertinents pour le code complexe
- Documentation en français

### 1.3 Tests
- Coverage minimum de 80%
- Tests unitaires pour chaque nouvelle fonctionnalité
- Tests d'intégration pour les flux principaux
- Utilisation de pytest

## 2. Workflow de Développement

### 2.1 Gestion des Branches
- main : code de production
- develop : développement principal
- feature/* : nouvelles fonctionnalités
- bugfix/* : corrections de bugs
- release/* : préparation des releases

### 2.2 Commits
- Messages clairs et descriptifs
- Un commit = une modification logique
- Référencer les numéros d'issues

### 2.3 Revue de Code
- Revue obligatoire avant merge
- Vérification des tests
- Validation de la documentation

## 3. Architecture

### 3.1 Structure du Projet
- Modules indépendants et réutilisables
- Séparation claire UI/logique métier
- Utilisation de design patterns appropriés

### 3.2 Gestion des Dépendances
- Requirements.txt à jour
- Versions fixées des dépendances
- Minimiser les dépendances externes

## 4. Sécurité

### 4.1 Bonnes Pratiques
- Pas de secrets dans le code
- Validation des entrées utilisateur
- Gestion appropriée des erreurs

### 4.2 Logging
- Logs structurés et cohérents
- Niveaux de log appropriés
- Rotation des fichiers de log

- le projet doit-être géré avec la méthode TDD
- le projet doit-être Security by design
- le projet doit-être GDPR by design
- le projet doit-être multilingue il faut donc prévoir le l18n
- le fichier "devbook.md" doit-être maintenu à jour, il doit cocher la case à chaque fois qu'une fonctionnalités est implémenté, si des nouvelles idées apparaissent ou de nouveau critère basé sur les fonctionnalités déjà mise en place, il faut compléter le fichier en ajoutant "Points à améliorer"
- le projet doit tourner sous windows, linux et mac, il faut donc choisir un framework qui soit compatible.
- des tests unitaires doivent être mise en place.
- après l'ajout de chaque nouvelle fonctionnalités, il faut effectuer une analyse statique avec "Pylint"
- le projet maintient à jour le fichier "documentation.md"
- le projet maintient à jour le fichier "mindmap_functionality.md" en "mermaid"
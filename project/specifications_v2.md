# Cahier des Charges - Log Tracker

## 1. Description Générale
Log Tracker est une application de suivi du temps de travail avec synchronisation vers un outil externe (Jira).

## 2. Fonctionnalités Principales

### 2.1. Gestion des Entrées de Temps
- Saisie d'entrées de temps avec :
  - Date et heure
  - Projet
  - Numéro de ticket
  - Description
  - Tâches à faire (todo)
  - Durée
- Vue en temps réel du temps écoulé
- Alerte visuelle pour rappeler la saisie des temps
- Possibilité de voir l'historique des entrées
- Option de saisie séquentielle du temps

### 2.2. Gestion des Projets
- Création et gestion de projets
- Association avec des préfixes de tickets
- Liste des tickets par projet
- Gestion de l'état actif/inactif des tickets

### 2.3. Synchronisation
- Synchronisation vers Jira
- Suivi de l'état de synchronisation des entrées
- Gestion des identifiants de tâches externes

### 2.4. Configuration
- Paramètres de connexion Jira (URL, token, email)
- Horaires de travail (début, fin)
- Nombre d'heures quotidiennes
- Gestion des tokens d'authentification
- Option de saisie séquentielle du temps

## 3. Règles de Gestion

### 3.1. Gestion du Temps
- Le temps est suivi en minutes
- Une journée de travail standard est configurable (par défaut 8 heures)
- Les horaires de travail sont configurables (par défaut 8h-18h)
- Alerte visuelle si aucune entrée n'a été saisie depuis un certain temps
- Le temps total des entrées est comparé au temps quotidien attendu

### 3.2. Projets et Tickets
- Un projet doit avoir un nom unique
- Les tickets sont uniques par projet (combinaison projet_id + ticket_number)
- Les tickets peuvent être marqués comme actifs ou inactifs
- Les tickets conservent un historique de leurs titres

### 3.3. Synchronisation
- Les entrées sont marquées comme synchronisées une fois envoyées vers Jira/Planner
- Conservation des ID externes (planner_task_id) pour le suivi
- Vérification de la validité du token d'authentification
- Les entrées peuvent être synchronisées en bloc ou individuellement

### 3.4. Interface Utilisateur
- L'application reste toujours au premier plan
- Interface sombre pour le confort visuel
- Icônes intuitives pour les principales actions
- Barre d'état pour les informations importantes
- Auto-complétion pour les champs de saisie

### 3.5. Stockage des Données
- Utilisation d'une base SQLite locale
- Structure de données :
  - Table settings : paramètres globaux
  - Table projects : projets et leurs configurations
  - Table tickets : tickets liés aux projets
  - Table entries : entrées de temps

### 3.6. Sécurité
- Les tokens d'authentification sont stockés localement
- Gestion de l'expiration des tokens
- Pas de stockage en clair des informations sensibles

## 4. Contraintes Techniques
- Développé en Python avec PyQt6
- Base de données SQLite
- Interface avec l'API Jira
- Interface avec l'API Microsoft Planner
- Gestion des ressources (icônes SVG)
- Compatibilité Windows
- Support du mode exécutable (packaging)


# Révision du projet
- on laisse tomber la partie planner
- on va investir plus dans Jira
- dans la zone de création d'une entrée il y a la zone de saisie fait qui va dans le ticket dans la partie journal de temps et il faudrait le mettre aussi dans les commentaires du ticket.
- dans la zone à faire doit au final créer un ticket dans jira, la question est de savoir à quel Epic et quelle fonctionnalité je place la sous tache. il faut un système qui permet de choisir l'epic et la fonctionnalité en théorie pour un projet précis il devrait y avoir une liste assez courte d'epic/fonctionnalités. il faut pouvoir choisir dans une liste. comme dans le projet jira il y a beaucoup de ticket qui ne nous appartienne pas, il faut un écran qui permet d'afficher une liste réduite de ticket, on peut utiliser le jql pour réduire à quelques epic et fonctionnalités. et en plus on peut rajouter une gestion coté application cette fois ci la possibilité de rendre visible ou invisible car dans l'équipe tout n'est pas de notre ressort.
- pour résumer, un écran pour indiquer un filtre jira puis l'affichage de la liste que l'on peut ensuite rendre visible ou invisible selon les besoins.
- et dans l'écran de saisie d'une entrée, au dessus de la zone à faire le moyen de selectionner le bon epic et la fonctionnalité.
- et tout comme pour la gestion des tickets utilisé pour la zone de saisie "fait" ou l'on garde en mémoire les tickets utilisés on pourrait de la même manière utiliser les epic et fonctionnalités choisi dans un ticket pour présenter ce tuple là aussi pour faciliter.
- on pourrait aussi sur la même ligne ou il y a le selecteur de ticket enregistré pour le projet courant, avoir un champs en mode recherche textuelle sur les epics et fonctionnalités pour trouver et associé un nouveau ticket, aujourd'hui je suis obligé d'aller dans jira trouver le bon ticket pour coller le ticket, là je pourrais faire une recherche et le coller ensuite dans le selecteur ticket.
- pour que cela soit parfais, on pourrait aussi permettre la création d'un ticket, dans certains cas on fait une action sans avoir le ticket créé à l'avance, et comme je veux pouvoir créer des tickets facilement pour la zone "à faire" on pourrait permettre de fair la création, maintenant il faut savoir comment agencer tout ça dans l'écran pour que cela soit fluide et ne parraisse pas trop complexe visuellement, la création d'un ticket pourrait se faire au travers d'un autre écran qui s'ouvre depuis l'écran de saisie?
- il va en falloir de l'autocompletion et le rendre simple.
# Carte des Fonctionnalités LogTracker

```mermaid
mindmap
  root((LogTracker))
    Interface Utilisateur
      Fenêtre Principale
        Zone de Saisie
          Projet
          Ticket
          Description
          Durée
        Résumé
          Dernière Entrée
          Temps Total
        Boutons
          Nouvelle Entrée
          Voir Entrées
      Vue des Entrées
        Filtres
          Journée
          8 Jours
        Modes
          Chronologique
          Par Projet
        Colonnes
          Date/Heure
          Projet
          Ticket
          Durée
          Description
    Gestion des Données
      Base de Données
        Tables
          Projets
          Tickets
          Entrées
        Opérations
          CRUD Projets
          CRUD Tickets
          CRUD Entrées
      Auto-complétion
        Projets
        Tickets
    Internationalisation
      Langues
        Français
        Anglais
      Composants
        Interface
        Messages
        Dates
    Sécurité
      GDPR
        Stockage Local
        Export Données
        Suppression
      Protection
        Validation Entrées
        Base Chiffrée
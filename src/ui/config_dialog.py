#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QTimeEdit,
    QComboBox, QGroupBox, QFormLayout, QCheckBox,
    QProgressDialog, QApplication
)
from PyQt6.QtCore import QTime, Qt, QThread, pyqtSignal
import os
import json
from datetime import datetime
from utils.database import Database
from utils.jira_client import JiraClient
from ui.theme import Theme
import time

class JiraImportThread(QThread):
    """Thread pour l'import des tickets Jira."""
    finished = pyqtSignal(bool, str, float, int)  # success, message, time, count
    
    def __init__(self, jira_client, jql):
        super().__init__()
        self.jira = jira_client
        self.jql = jql
        self.db = Database()
        
    def run(self):
        """Exécute l'import des tickets."""
        try:
            start_time = time.time()
            
            # Récupère les tickets
            issues = self.jira.get_issue_hierarchy(self.jql)
            
            if not issues:
                self.finished.emit(False, "Aucun ticket trouvé avec ce JQL", 0, 0)
                return
                
            # Dictionnaire pour stocker les chemins
            paths = {}
            
            # Premier passage : construire le dictionnaire des tickets
            tickets_dict = {issue['key']: issue for issue in issues}
            
            # Deuxième passage : construire les chemins
            for issue in issues:
                if issue['type'].lower() == 'sub-task':
                    continue
                path = ConfigDialog.build_path(issue, tickets_dict)
                if path:
                    paths[issue['key']] = path
                    
            # Enregistre dans la base
            try:
                self.db.connect()
                self.db.cursor.execute("DELETE FROM jira_paths")
                self.db.cursor.execute("DELETE FROM jira_subtasks")
                
                # Insère les chemins
                for issue in issues:
                    if issue['type'].lower() != 'sub-task' and issue['key'] in paths:
                        self.db.cursor.execute(
                            "INSERT INTO jira_paths (path, ticket_key) VALUES (?, ?)",
                            (paths[issue['key']], issue['key'])
                        )
                
                # Insère les sous-tâches
                for issue in issues:
                    if issue['type'].lower() == 'sub-task' and issue['parent_key'] in paths:
                        self.db.cursor.execute(
                            "INSERT INTO jira_subtasks (path, title, ticket_key) VALUES (?, ?, ?)",
                            (paths[issue['parent_key']], issue['title'], issue['key'])
                        )
                
                self.db.conn.commit()
                time_elapsed = time.time() - start_time
                self.finished.emit(True, "Import terminé", time_elapsed, len(issues))
                
            except Exception as e:
                if self.db.conn:
                    self.db.conn.rollback()
                self.finished.emit(False, str(e), 0, 0)
            finally:
                self.db.disconnect()
                
        except Exception as e:
            self.finished.emit(False, str(e), 0, 0)

class ConfigDialog(QDialog):
    """Fenêtre de configuration pour les paramètres de l'application."""
    
    theme_changed = pyqtSignal(str)  # Signal émis quand le thème change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.init_ui()
        self.load_config()
        self.resize(400, 500)

    def init_ui(self):
        """Initialise l'interface utilisateur."""
        layout = QVBoxLayout()
        
        # Groupe Paramètres généraux
        general_group = QGroupBox("Paramètres généraux")
        general_layout = QFormLayout()
        
        # Heures de travail
        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("HH:mm")
        general_layout.addRow("Heure de début:", self.start_time)
        
        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("HH:mm")
        general_layout.addRow("Heure de fin:", self.end_time)
        
        self.hours_per_day = QLineEdit()
        self.hours_per_day.setPlaceholderText("8")
        general_layout.addRow("Heures de travail par jour:", self.hours_per_day)
        
        # Sélecteur d'incrément de temps
        self.time_increment_combo = QComboBox()
        for increment in [1, 5, 10, 15, 30]:
            self.time_increment_combo.addItem(f"{increment} minutes", increment)
        general_layout.addRow("Incrément de temps:", self.time_increment_combo)
        
        self.use_sequential_time = QCheckBox("Utiliser l'heure séquentielle")
        general_layout.addRow(self.use_sequential_time)
        
        # Sélecteur de thème
        self.theme_combo = QComboBox()
        themes = Theme.get_available_themes()
        for theme_name in themes.keys():
            self.theme_combo.addItem(theme_name)
        current_theme = self.db.get_setting('theme', 'dark')
        index = self.theme_combo.findText(current_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
        general_layout.addRow("Thème:", self.theme_combo)
        
        # Sélecteur du type d'écran de saisie
        self.entry_type_combo = QComboBox()
        self.entry_type_combo.addItem("Saisir du temps", "time_only")
        self.entry_type_combo.addItem("Saisir temps et tâche à faire", "time_and_todo")
        current_entry_type = self.db.get_setting('entry_screen_type', 'time_only')
        index = self.entry_type_combo.findData(current_entry_type)
        if index >= 0:
            self.entry_type_combo.setCurrentIndex(index)
        general_layout.addRow("Type d'écran de saisie:", self.entry_type_combo)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # Groupe Jira
        jira_group = QGroupBox("Configuration Jira")
        jira_layout = QFormLayout()
        
        self.jira_url = QLineEdit()
        self.jira_url.setPlaceholderText("https://your-domain.atlassian.net")
        jira_layout.addRow("URL Jira:", self.jira_url)
        
        self.jira_token = QLineEdit()
        self.jira_token.setPlaceholderText("Votre token Jira")
        self.jira_token.setEchoMode(QLineEdit.EchoMode.Password)
        jira_layout.addRow("Token Jira:", self.jira_token)
        
        self.jira_user = QLineEdit()
        self.jira_user.setPlaceholderText("prenom.nom@email.com")
        jira_layout.addRow("Utilisateur Jira:", self.jira_user)
        
        # Ajout des champs JQL
        self.ticket_jql = QLineEdit()
        self.ticket_jql.setPlaceholderText("JQL pour la sélection des tickets")
        load_tickets_button = QPushButton("Charger")
        load_tickets_button.clicked.connect(self.load_tickets_hierarchy)
        jql_layout = QHBoxLayout()
        jql_layout.addWidget(self.ticket_jql)
        jql_layout.addWidget(load_tickets_button)
        jira_layout.addRow("JQL Tickets:", jql_layout)
        
        self.project_jql = QLineEdit()
        self.project_jql.setPlaceholderText("JQL pour la sélection des projets/epics")
        load_projects_button = QPushButton("Charger")
        load_projects_button.clicked.connect(self.load_projects_hierarchy)
        project_jql_layout = QHBoxLayout()
        project_jql_layout.addWidget(self.project_jql)
        project_jql_layout.addWidget(load_projects_button)
        jira_layout.addRow("JQL Projets:", project_jql_layout)
        
        
        
        jira_group.setLayout(jira_layout)
        layout.addWidget(jira_group)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.save_config)
        
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def load_config(self):
        """Charge la configuration depuis la base de données."""
        # Paramètres généraux
        start_time = self.db.get_setting('start_time', '09:00')
        self.start_time.setTime(QTime.fromString(start_time, "HH:mm"))
        
        end_time = self.db.get_setting('end_time', '17:00')
        self.end_time.setTime(QTime.fromString(end_time, "HH:mm"))
        
        hours = self.db.get_setting('hours_per_day', '8')
        self.hours_per_day.setText(hours)
        
        use_sequential = self.db.get_setting('use_sequential_time', '0')
        self.use_sequential_time.setChecked(use_sequential == '1')
        
        # Sélecteur d'incrément de temps
        time_increment = self.db.get_setting('time_increment', '5')
        index = self.time_increment_combo.findData(int(time_increment))
        if index >= 0:
            self.time_increment_combo.setCurrentIndex(index)
        
        # Configuration Jira
        config = self.db.get_jira_config()
        self.jira_url.setText(config.get('jira_base_url', ''))
        self.jira_token.setText(config.get('jira_token', ''))
        self.jira_user.setText(config.get('jira_email', ''))
        
        # JQL configuration
        self.ticket_jql.setText(self.db.get_setting('ticket_selection_jql', ''))
        self.project_jql.setText(self.db.get_setting('project_selection_jql', ''))

    def save_config(self):
        """Enregistre la configuration dans la base de données."""
        try:
            # Paramètres généraux
            self.db.save_setting('start_time', self.start_time.time().toString("HH:mm"))
            self.db.save_setting('end_time', self.end_time.time().toString("HH:mm"))
            self.db.save_setting('hours_per_day', self.hours_per_day.text())
            self.db.save_setting('use_sequential_time', '1' if self.use_sequential_time.isChecked() else '0')
            self.db.save_setting('time_increment', str(self.time_increment_combo.currentData()))
            self.db.save_setting('theme', self.theme_combo.currentText())
            self.db.save_setting('entry_screen_type', self.entry_type_combo.currentData())
            
            # Configuration Jira
            self.db.save_setting('jira_base_url', self.jira_url.text())
            self.db.save_setting('jira_token', self.jira_token.text())
            self.db.save_setting('jira_email', self.jira_user.text())
            
            # JQL configuration
            self.db.save_setting('ticket_selection_jql', self.ticket_jql.text())
            self.db.save_setting('project_selection_jql', self.project_jql.text())
            
            QMessageBox.information(self, "Succès", "Configuration enregistrée avec succès")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement : {str(e)}")

    @staticmethod
    def build_path(issue, tickets_dict):
        """Construit le chemin projet/epic/fonctionnalité."""
        if not issue:
            return None
            
        path_parts = []
        current_key = issue['key']
        
        # Remonter la hiérarchie pour construire le chemin
        while current_key:
            current = tickets_dict.get(current_key)
            if not current:
                break
                
            path_parts.insert(0, current['title'])
            current_key = current['parent_key']
        
        # Si on n'a pas de chemin du tout
        if not path_parts:
            return None
            
        # Si c'est une fonctionnalité (ni projet, ni epic)
        if issue['type'].lower() not in ['project', 'epic']:
            if len(path_parts) >= 3:
                return f"{path_parts[0]}/{path_parts[1]}/{path_parts[2]}"
            elif len(path_parts) == 2:
                return f"{path_parts[0]}/{path_parts[1]}/"
            else:
                return f"{path_parts[0]}//"
                
        # Si c'est un epic
        elif issue['type'].lower() == 'epic':
            if len(path_parts) >= 2:
                return f"{path_parts[0]}/{path_parts[1]}//"
            else:
                return f"{path_parts[0]}//"
                
        # Si c'est un projet
        else:  # project
            return f"{path_parts[0]}//"

    def load_projects_hierarchy(self):
        """Charge la hiérarchie des projets depuis Jira."""
        try:
            if not self.check_jira_config():
                return
                
            jql = self.project_jql.text()
            if not jql:
                QMessageBox.warning(self, "Attention", "Veuillez entrer un JQL pour les projets")
                return
                
            # Crée une simple fenêtre d'attente
            progress = QDialog(self)
            progress.setWindowTitle("Import des projets")
            progress.setFixedSize(300, 100)
            progress.setWindowModality(Qt.WindowModality.ApplicationModal)
            progress.setStyleSheet("""
                QDialog {
                    background-color: #2b2b2b;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 12px;
                    margin: 10px;
                }
            """)
            
            layout = QVBoxLayout(progress)
            label = QLabel("Import des projets en cours...\nVeuillez patienter", progress)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            
            progress.show()
            QApplication.processEvents()
            time.sleep(0.5)
            
            try:
                start_time = time.time()
                
                # Initialise le client Jira
                jira = JiraClient(self.jira_url.text(), self.jira_token.text(), self.jira_user.text())
                
                # Récupère les projets
                issues = jira.get_issue_hierarchy(jql)
                
                if not issues:
                    progress.close()
                    QMessageBox.warning(self, "Aucun résultat", "Aucun projet trouvé avec ce JQL")
                    return
                    
                # Dictionnaire pour stocker les chemins
                paths = {}
                
                # Construit les chemins des projets
                tickets_dict = {issue['key']: issue for issue in issues}
                for issue in issues:
                    path = ConfigDialog.build_path(issue, tickets_dict)
                    if path:
                        paths[issue['key']] = path
                        
                # Enregistre dans la base
                self.db.connect()
                self.db.cursor.execute("DELETE FROM jira_paths")
                
                # Insère uniquement les chemins de projets
                for issue in issues:
                    if issue['key'] in paths:
                        self.db.cursor.execute(
                            "INSERT INTO jira_paths (path, ticket_key) VALUES (?, ?)",
                            (paths[issue['key']], issue['key'])
                        )
                
                self.db.conn.commit()
                time_elapsed = time.time() - start_time
                
                progress.close()
                QMessageBox.information(self, "Succès", 
                    f"{len(paths)} projets chargés avec succès\nTemps écoulé : {time_elapsed:.1f}s")
                
            except Exception as e:
                progress.close()
                if self.db.conn:
                    self.db.conn.rollback()
                QMessageBox.critical(self, "Erreur", f"Échec du chargement des projets : {str(e)}")
            finally:
                self.db.disconnect()
                
        except Exception as e:
            if 'progress' in locals():
                progress.close()
            QMessageBox.critical(self, "Erreur", f"Échec du chargement des projets : {str(e)}")
            
    def load_tickets_hierarchy(self):
        """Charge la hiérarchie des tickets depuis Jira."""
        try:
            if not self.check_jira_config():
                return
                
            jql = self.ticket_jql.text()
            if not jql:
                QMessageBox.warning(self, "Attention", "Veuillez entrer un JQL pour les tickets")
                return
                
            # Crée une simple fenêtre d'attente
            progress = QDialog(self)
            progress.setWindowTitle("Import des tickets")
            progress.setFixedSize(300, 100)
            progress.setWindowModality(Qt.WindowModality.ApplicationModal)
            progress.setStyleSheet("""
                QDialog {
                    background-color: #2b2b2b;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 12px;
                    margin: 10px;
                }
            """)
            
            layout = QVBoxLayout(progress)
            label = QLabel("Import des tickets en cours...\nVeuillez patienter", progress)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            
            progress.show()
            QApplication.processEvents()
            time.sleep(0.5)
            
            try:
                start_time = time.time()
                
                # Initialise le client Jira
                jira = JiraClient(self.jira_url.text(), self.jira_token.text(), self.jira_user.text())
                
                # Récupère les tickets
                issues = jira.get_issue_hierarchy(jql)
                
                if not issues:
                    progress.close()
                    QMessageBox.warning(self, "Aucun résultat", "Aucun ticket trouvé avec ce JQL")
                    return
                    
                # Dictionnaire pour stocker les chemins des parents
                parent_paths = {}
                subtasks_count = 0
                
                # Récupère d'abord tous les chemins existants de la table jira_paths
                self.db.connect()
                self.db.cursor.execute("SELECT path, ticket_key FROM jira_paths")
                for row in self.db.cursor.fetchall():
                    parent_paths[row[1]] = row[0]
                
                # Nettoie la table des sous-tâches
                self.db.cursor.execute("DELETE FROM jira_subtasks")
                
                # Insère uniquement les sous-tâches
                for issue in issues:
                    # Vérifie si c'est une sous-tâche et si son parent existe
                    if issue['type'].lower() in ['sous-tâche', 'sub-task'] and issue.get('parent_key'):
                        parent_key = issue['parent_key']
                        if parent_key in parent_paths:
                            self.db.cursor.execute(
                                "INSERT INTO jira_subtasks (path, title, ticket_key) VALUES (?, ?, ?)",
                                (parent_paths[parent_key], issue['title'], issue['key'])
                            )
                            subtasks_count += 1
                
                self.db.conn.commit()
                time_elapsed = time.time() - start_time
                
                progress.close()
                QMessageBox.information(self, "Succès", 
                    f"{subtasks_count} sous-tâches chargées avec succès\nTemps écoulé : {time_elapsed:.1f}s")
                
            except Exception as e:
                progress.close()
                if self.db.conn:
                    self.db.conn.rollback()
                QMessageBox.critical(self, "Erreur", f"Échec du chargement des tickets : {str(e)}")
            finally:
                self.db.disconnect()
                
        except Exception as e:
            if 'progress' in locals():
                progress.close()
            QMessageBox.critical(self, "Erreur", f"Échec du chargement des tickets : {str(e)}")

    def get_issue_project(self, issue, tickets_dict):
        """Récupère le projet d'un ticket en remontant la hiérarchie."""
        current = issue
        while current and current.get('parent_key'):
            parent_key = current['parent_key']
            current = tickets_dict.get(parent_key)
        return current if current else issue

    def on_import_finished(self, success, message, time_elapsed, count):
        """Appelé quand l'import est terminé."""
        if success:
            QMessageBox.information(self, "Succès", 
                f"{count} éléments chargés avec succès\nTemps écoulé : {time_elapsed:.1f}s")
        else:
            QMessageBox.warning(self, "Erreur", f"Échec du chargement : {message}")

    def check_jira_config(self):
        """Vérifie que la configuration Jira est complète."""
        if not self.jira_url.text() or not self.jira_token.text() or not self.jira_user.text():
            QMessageBox.warning(self, "Attention", 
                "Veuillez configurer les paramètres Jira (URL, Token, Utilisateur)")
            return False
        return True

    def apply_theme(self, theme_name: str):
        """Applique le thème sélectionné à la fenêtre de configuration."""
        theme = Theme(theme_name)
        self.setStyleSheet(theme.get_stylesheet())
        self.theme_changed.emit(theme_name)  # Émet le signal avec le nouveau thème
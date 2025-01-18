#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QFrame, QSpinBox, QComboBox, QRadioButton, QButtonGroup, QGroupBox,
    QSplitter, QDialog, QFormLayout, QStyle, QToolButton, QDialogButtonBox, QMessageBox,
    QDateEdit, QTimeEdit
)
from PyQt6.QtCore import Qt, QTimer, QSize, QDate, QTime
from PyQt6.QtGui import QFont, QIcon, QPainter, QColor
import os

from utils.database import Database
from utils.autocomplete import AutocompleteLineEdit
from ui.ticket_combo import TicketComboBox
from ui.project_combo import ProjectComboBox

class EntriesDialog(QDialog):
    """Fenêtre d'affichage des entrées."""

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setup_ui()
        self.update_entries_view()

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Entrées")
        self.resize(800, 500)

        # Layout principal
        layout = QVBoxLayout()

        # Contrôles dans un layout horizontal
        controls_layout = QHBoxLayout()

        # Groupe de boutons radio pour la période
        period_group = QGroupBox("Période")
        period_layout = QHBoxLayout()
        self.period_day = QRadioButton("Journée")
        self.period_8days = QRadioButton("8 jours")
        self.period_day.setChecked(True)
        period_layout.addWidget(self.period_day)
        period_layout.addWidget(self.period_8days)
        period_group.setLayout(period_layout)
        controls_layout.addWidget(period_group)

        # Groupe de boutons radio pour le type de vue
        self.view_group = QGroupBox("Présentation")
        self.view_group.setVisible(False)
        view_layout = QHBoxLayout()
        self.view_by_day = QRadioButton("Jour par jour")
        self.view_by_project = QRadioButton("Par projet")
        self.view_by_day.setChecked(True)
        view_layout.addWidget(self.view_by_day)
        view_layout.addWidget(self.view_by_project)
        self.view_group.setLayout(view_layout)
        controls_layout.addWidget(self.view_group)

        # Ajoute un stretch pour que les groupes restent à gauche
        controls_layout.addStretch()

        # Ajoute les contrôles au layout principal
        layout.addLayout(controls_layout)

        # Configuration du QTreeWidget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Projet", "Ticket", "Durée", "Description", "Date", "Heure", ""])  # Colonne vide pour le retour à la ligne
        self.tree.setColumnWidth(0, 150)  # Projet
        self.tree.setColumnWidth(1, 100)  # Ticket
        self.tree.setColumnWidth(2, 80)   # Durée
        self.tree.setColumnWidth(3, 400)  # Description
        self.tree.setColumnWidth(4, 100)  # Date
        self.tree.setColumnWidth(5, 60)   # Heure
        self.tree.setColumnWidth(6, 10)   # Colonne vide
        self.tree.setWordWrap(True)
        layout.addWidget(self.tree)

        self.setLayout(layout)

        # Connexion des signaux
        self.period_day.toggled.connect(self.update_entries_view)
        self.period_8days.toggled.connect(lambda checked: self.view_group.setVisible(checked))
        self.view_by_day.toggled.connect(self.update_entries_view)
        self.view_by_project.toggled.connect(self.update_entries_view)

    def update_entries_view(self):
        """Met à jour l'affichage des entrées."""
        self.tree.clear()

        # Calcul de la période
        today = datetime.now().date()
        if self.period_day.isChecked():
            start_date = today
            end_date = today
        else:
            start_date = today - timedelta(days=7)
            end_date = today

        try:
            if self.period_day.isChecked():
                # Vue journée groupée par projet
                entries = self.db.get_entries_by_date_range(start_date, end_date)
                if not entries:
                    return

                # Organise les entrées par projet
                entries_by_project = {}
                for entry in entries:
                    project = entry.get('project_name', 'Sans projet')
                    if project not in entries_by_project:
                        entries_by_project[project] = []
                    entries_by_project[project].append(entry)

                # Crée les éléments de l'arbre
                for project, project_entries in entries_by_project.items():
                    project_item = QTreeWidgetItem(self.tree)
                    project_item.setText(0, project)
                    total_duration = sum(entry.get('duration', 0) for entry in project_entries)
                    project_item.setText(2, f"{total_duration}m")

                    for entry in project_entries:
                        entry_item = QTreeWidgetItem(project_item)
                        entry_item.setText(0, "")  # Projet déjà affiché dans le parent
                        
                        # Ticket en bleu
                        ticket = entry.get('ticket_number', '')
                        entry_item.setText(1, ticket)
                        if ticket:
                            entry_item.setForeground(1, QColor("#64b5f6"))
                        
                        # Durée en vert
                        duration = entry.get('duration', 0)
                        entry_item.setText(2, f"{duration}m")
                        entry_item.setForeground(2, QColor("#81c784"))
                        
                        entry_item.setText(3, entry.get('description', ''))
                        entry_item.setText(4, entry.get('date', ''))
                        entry_item.setText(5, entry.get('time', ''))

                        for col in range(7):
                            entry_item.setTextAlignment(col, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

                self.tree.expandAll()

            elif self.view_by_day.isChecked():
                # Vue sur 8 jours chronologique
                entries = self.db.get_entries_by_date_range(start_date, end_date)
                if not entries:
                    return

                # Organise les entrées par date
                entries_by_date = {}
                for entry in entries:
                    entry_timestamp = datetime.strptime(f"{entry.get('date', '')} {entry.get('time', '')}", "%Y-%m-%d %H:%M")
                    entry_date = entry_timestamp.date()
                    if entry_date not in entries_by_date:
                        entries_by_date[entry_date] = []
                    entries_by_date[entry_date].append(entry)

                # Noms des jours en français
                jours = {
                    0: 'Lundi',
                    1: 'Mardi',
                    2: 'Mercredi',
                    3: 'Jeudi',
                    4: 'Vendredi',
                    5: 'Samedi',
                    6: 'Dimanche'
                }

                # Crée les éléments de l'arbre
                for date in sorted(entries_by_date.keys(), reverse=True):
                    date_entries = entries_by_date[date]
                    jour = jours[date.weekday()]
                    date_item = QTreeWidgetItem(self.tree)
                    date_item.setText(0, f"{jour} {date.strftime('%d/%m/%Y')}")
                    total_duration = sum(entry.get('duration', 0) for entry in date_entries)
                    date_item.setText(2, f"{total_duration}m")

                    for entry in date_entries:
                        entry_timestamp = datetime.strptime(f"{entry.get('date', '')} {entry.get('time', '')}", "%Y-%m-%d %H:%M")
                        entry_item = QTreeWidgetItem(date_item)
                        entry_item.setText(0, entry.get('project_name', ''))
                        
                        # Ticket en bleu
                        ticket = entry.get('ticket_number', '')
                        entry_item.setText(1, ticket)
                        if ticket:
                            entry_item.setForeground(1, QColor("#64b5f6"))
                        
                        # Durée en vert
                        duration = entry.get('duration', 0)
                        entry_item.setText(2, f"{duration}m")
                        entry_item.setForeground(2, QColor("#81c784"))
                        
                        entry_item.setText(3, entry.get('description', ''))
                        entry_item.setText(4, entry.get('date', ''))
                        entry_item.setText(5, entry.get('time', ''))

                        for col in range(7):
                            entry_item.setTextAlignment(col, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

                self.tree.expandAll()

            else:  # Vue par projet sur 8 jours
                entries_by_project = self.db.get_entries_by_project(start_date, end_date)
                if not entries_by_project:
                    return

                for project_name, entries in entries_by_project.items():
                    project_item = QTreeWidgetItem(self.tree)
                    project_item.setText(0, project_name or 'Sans projet')
                    total_duration = sum(entry.get('duration', 0) for entry in entries)
                    project_item.setText(2, f"{total_duration}m")

                    for entry in entries:
                        entry_timestamp = datetime.strptime(f"{entry.get('date', '')} {entry.get('time', '')}", "%Y-%m-%d %H:%M")
                        entry_item = QTreeWidgetItem(project_item)
                        entry_item.setText(0, "")  # Projet déjà affiché dans le parent
                        
                        # Ticket en bleu
                        ticket = entry.get('ticket_number', '')
                        entry_item.setText(1, ticket)
                        if ticket:
                            entry_item.setForeground(1, QColor("#64b5f6"))
                        
                        # Durée en vert
                        duration = entry.get('duration', 0)
                        entry_item.setText(2, f"{duration}m")
                        entry_item.setForeground(2, QColor("#81c784"))
                        
                        entry_item.setText(3, entry.get('description', ''))
                        entry_item.setText(4, entry.get('date', ''))
                        entry_item.setText(5, entry.get('time', ''))

                        for col in range(7):
                            entry_item.setTextAlignment(col, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

                self.tree.expandAll()

        except Exception as e:
            print(f"Erreur lors de la mise à jour de la vue : {str(e)}")
            import traceback
            traceback.print_exc()

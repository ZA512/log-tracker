#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QLabel
from PyQt6.QtCore import pyqtSignal, QTime, Qt
from PyQt6.QtGui import QWheelEvent

class MinuteComboBox(QComboBox):
    """ComboBox personnalisée pour les minutes avec gestion de la molette."""
    
    def wheelEvent(self, event: QWheelEvent):
        """Gère l'événement de la molette de souris."""
        current_minute = self.currentData()
        
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Avec CTRL : on va au multiple de 5 le plus proche
            direction = 1 if event.angleDelta().y() > 0 else -1
            
            # Calcule le prochain multiple de 5
            if direction > 0:
                # En montant : on va au prochain multiple de 5
                next_minute = ((current_minute + 4) // 5) * 5
                if next_minute == current_minute:
                    next_minute += 5
            else:
                # En descendant : on va au multiple de 5 précédent
                next_minute = (current_minute // 5) * 5
                if next_minute == current_minute:
                    next_minute -= 5
            
            # Assure que la valeur reste entre 0 et 55
            next_minute = max(0, min(55, next_minute))
        else:
            # Sans CTRL : incrémente/décrémente de 1 minute
            delta = 1 if event.angleDelta().y() > 0 else -1
            next_minute = (current_minute + delta) % 60
            
        self.setCurrentIndex(next_minute)
        event.accept()

class TimeSelector(QWidget):
    """Widget personnalisé pour sélectionner l'heure avec deux listes déroulantes."""
    
    timeChanged = pyqtSignal(QTime)  # Signal émis quand l'heure change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Initialise l'interface utilisateur."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Sélecteur d'heures
        self.hour_combo = QComboBox()
        for hour in range(24):
            self.hour_combo.addItem(f"{hour:02d}", hour)
        
        # Sélecteur de minutes avec gestion spéciale de la molette
        self.minute_combo = MinuteComboBox()
        for minute in range(60):
            self.minute_combo.addItem(f"{minute:02d}", minute)
            
        # Connexion des signaux
        self.hour_combo.currentIndexChanged.connect(self._on_time_changed)
        self.minute_combo.currentIndexChanged.connect(self._on_time_changed)
        
        # Ajout des widgets au layout
        layout.addWidget(self.hour_combo)
        layout.addWidget(QLabel(":"))  # Séparateur
        layout.addWidget(self.minute_combo)
        
        self.setLayout(layout)
        
    def setTime(self, time):
        """Définit l'heure affichée."""
        if isinstance(time, str):
            time = QTime.fromString(time, "HH:mm")
        
        hour = time.hour()
        minute = time.minute()
        
        self.hour_combo.setCurrentIndex(hour)
        self.minute_combo.setCurrentIndex(minute)
        
    def time(self):
        """Retourne l'heure sélectionnée."""
        hour = self.hour_combo.currentData()
        minute = self.minute_combo.currentData()
        return QTime(hour, minute)
        
    def _on_time_changed(self):
        """Appelé quand l'heure ou les minutes changent."""
        self.timeChanged.emit(self.time())

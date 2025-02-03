import os
from typing import Dict
from PyQt6.QtGui import QColor

class Theme:
    """Classe représentant un thème pour l'application."""
    
    def __init__(self, name: str = None):
        self.name = name
        self.window_background = "#2b2b2b"
        self.text_color = "#ffffff"
        self.button_background = "#3c3f41"
        self.button_text = "#ffffff"
        self.button_border = "#323232"
        self.input_background = "#45494A"
        self.input_text = "#ffffff"
        self.input_border = "#323232"
        self.group_title_color = "#ffffff"
        self.group_box_border = "#323232"
        self.link_color = "#589df6"
        
        if name:
            self.load_from_file(name)
    
    @staticmethod
    def get_available_themes() -> Dict[str, str]:
        """Retourne un dictionnaire des thèmes disponibles (nom: chemin)."""
        themes = {}
        template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")
        if os.path.exists(template_dir):
            for file in os.listdir(template_dir):
                if file.endswith(".theme"):
                    name = os.path.splitext(file)[0]
                    themes[name] = os.path.join(template_dir, file)
        return themes
    
    def load_from_file(self, name: str):
        """Charge le thème depuis un fichier."""
        themes = self.get_available_themes()
        if name in themes:
            with open(themes[name], 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=')
                        if hasattr(self, key):
                            setattr(self, key, value)
    
    def get_stylesheet(self) -> str:
        """Retourne la feuille de style Qt pour ce thème."""
        return f"""
            QWidget {{
                background-color: {self.window_background};
                color: {self.text_color};
            }}
            
            QPushButton {{
                background-color: {self.button_background};
                color: {self.button_text};
                border: 1px solid {self.button_border};
                padding: 5px;
                border-radius: 3px;
            }}
            
            QPushButton:hover {{
                background-color: {self.button_background};
                border: 1px solid {self.link_color};
            }}
            
            QLineEdit, QTextEdit, QComboBox {{
                background-color: {self.input_background};
                color: {self.input_text};
                border: 1px solid {self.input_border};
                padding: 5px;
                border-radius: 3px;
            }}
            
            QGroupBox {{
                border: 1px solid {self.group_box_border};
                margin-top: 0.5em;
                padding-top: 0.5em;
            }}
            
            QGroupBox::title {{
                color: {self.group_title_color};
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {self.input_background};
                color: {self.input_text};
                selection-background-color: {self.button_background};
                selection-color: {self.button_text};
            }}
        """

def get_stylesheet(theme: Theme) -> str:
    """Génère le stylesheet Qt pour un thème donné."""
    return f"""
        QDialog {{
            background-color: {theme.window_background};
        }}
        
        QLineEdit, QTextEdit, QComboBox {{
            background-color: {theme.input_background};
            color: {theme.input_text};
            border: 1px solid {theme.input_border};
            border-radius: 3px;
            padding: 2px 5px;
            font-size: 11px;
        }}
        
        QLabel {{
            color: {theme.text_color};
            font-size: 11px;
        }}
        
        QPushButton {{
            background-color: {theme.button_background};
            color: {theme.button_text};
            border: 1px solid {theme.button_border};
            border-radius: 3px;
            padding: 3px 8px;
            font-size: 11px;
        }}
        
        QPushButton:hover {{
            background-color: {QColor(theme.button_background).lighter(120).name()};
            border: 1px solid {QColor(theme.button_border).lighter(120).name()};
        }}
        
        QPushButton:pressed {{
            background-color: {QColor(theme.button_background).darker(120).name()};
        }}
        
        QGroupBox {{
            border: 1px solid {theme.group_box_border};
            border-radius: 5px;
            margin-top: 1em;
            padding: 8px;
            background-color: {QColor(theme.window_background).darker(110).name()};
        }}
        
        QGroupBox::title {{
            color: {theme.group_title_color};
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 3px;
            font-size: 12px;
            font-weight: bold;
            background-color: {QColor(theme.window_background).darker(110).name()};
        }}
        
        TimeButton {{
            min-width: 25px;
            max-width: 25px;
            min-height: 25px;
            max-height: 25px;
            font-size: 10px;
            padding: 0;
        }}
        
        TimeButton:checked {{
            background-color: {QColor(theme.button_border).name()};
            border: 1px solid {QColor(theme.button_border).lighter(130).name()};
        }}
    """

# Thème moderne (style Steam/Discord)
DEFAULT_THEME = Theme(
    name="Modern Dark",
)

# Thème clair (optionnel)
LIGHT_THEME = Theme(
    name="Light",
)

# Thème sombre
DARK_THEME = Theme(
    name="Dark",
)

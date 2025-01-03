import tkinter as tk
from typing import Optional

class Toast:
    """Widget de notification temporaire de style toast."""
    
    def __init__(self, parent: tk.Tk, message: str, duration: int = 2000):
        """
        Initialise un toast.
        
        Args:
            parent: Fenêtre parente
            message: Message à afficher
            duration: Durée d'affichage en millisecondes
        """
        self.parent = parent
        
        # Création de la fenêtre du toast
        self.window = tk.Toplevel(parent)
        self.window.overrideredirect(True)  # Supprime la barre de titre
        
        # Style du toast
        self.window.configure(bg='#333333')
        
        # Label avec le message
        self.label = tk.Label(
            self.window,
            text=message,
            fg='white',
            bg='#333333',
            padx=20,
            pady=10,
            font=('Arial', 10)
        )
        self.label.pack()
        
        # Positionnement du toast
        self.position_toast()
        
        # Disparition automatique
        self.window.after(duration, self.hide)
    
    def position_toast(self):
        """Positionne le toast en bas à droite de la fenêtre parente."""
        # Attend que la fenêtre soit mise à jour pour obtenir sa taille réelle
        self.window.update_idletasks()
        
        # Obtient les dimensions de la fenêtre parente et du toast
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        toast_width = self.window.winfo_width()
        toast_height = self.window.winfo_height()
        
        # Calcule la position
        x = parent_x + parent_width - toast_width - 10
        y = parent_y + 10
        
        # Positionne le toast
        self.window.geometry(f'+{x}+{y}')
    
    def hide(self):
        """Cache et détruit le toast."""
        self.window.destroy()

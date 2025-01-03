import tkinter as tk
from tkinter import ttk
from typing import List, Callable

class AutocompleteEntry(ttk.Entry):
    """Widget d'entrée avec autocomplétion."""
    
    def __init__(self, master, completevalues: List[str] = None, **kwargs):
        """
        Initialise une entrée avec autocomplétion.
        
        Args:
            master: Widget parent
            completevalues: Liste des valeurs pour l'autocomplétion
            **kwargs: Arguments supplémentaires pour ttk.Entry
        """
        super().__init__(master, **kwargs)
        self.completevalues = completevalues or []
        
        # Liste déroulante pour les suggestions
        self.listbox = None
        self.listbox_window = None
        
        # Bindings
        self.bind('<KeyRelease>', self._on_keyrelease)
        self.bind('<FocusOut>', self._on_focus_out)
        self.bind('<Return>', self._on_return)
        self.bind('<Up>', self._on_arrow_up)
        self.bind('<Down>', self._on_arrow_down)
        
    def set_completevalues(self, values: List[str]):
        """Met à jour la liste des valeurs d'autocomplétion."""
        self.completevalues = values
    
    def _on_keyrelease(self, event):
        """Gère l'événement de relâchement d'une touche."""
        # Ignore certaines touches spéciales
        if event.keysym in ('Up', 'Down', 'Return', 'Tab'):
            return
            
        self._show_suggestions()
    
    def _show_suggestions(self):
        """Affiche les suggestions d'autocomplétion."""
        value = self.get().lower()
        
        if not value:
            self._hide_listbox()
            return
        
        # Filtre les valeurs correspondantes
        matches = [v for v in self.completevalues if value in v.lower()]
        
        if not matches:
            self._hide_listbox()
            return
        
        # Crée ou met à jour la liste déroulante
        if not self.listbox_window:
            self.listbox_window = tk.Toplevel(self)
            self.listbox_window.overrideredirect(True)
            self.listbox_window.attributes('-topmost', True)
            
            self.listbox = tk.Listbox(
                self.listbox_window,
                height=min(len(matches), 5),
                selectmode=tk.SINGLE
            )
            self.listbox.pack(fill=tk.BOTH, expand=True)
        
        # Met à jour la position
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        self.listbox_window.geometry(f"+{x}+{y}")
        
        # Met à jour les suggestions
        self.listbox.delete(0, tk.END)
        for match in matches:
            self.listbox.insert(tk.END, match)
    
    def _hide_listbox(self):
        """Cache la liste déroulante."""
        if self.listbox_window:
            self.listbox_window.destroy()
            self.listbox_window = None
            self.listbox = None
    
    def _on_focus_out(self, event):
        """Gère l'événement de perte de focus."""
        # Petit délai pour permettre la sélection avec la souris
        self.after(100, self._hide_listbox)
    
    def _on_return(self, event):
        """Gère l'événement d'appui sur Entrée."""
        if self.listbox and self.listbox.curselection():
            self.delete(0, tk.END)
            self.insert(0, self.listbox.get(self.listbox.curselection()))
            self._hide_listbox()
            return "break"
    
    def _on_arrow_up(self, event):
        """Gère l'événement flèche haut."""
        if self.listbox:
            if self.listbox.curselection():
                current = self.listbox.curselection()[0]
                if current > 0:
                    self.listbox.selection_clear(current)
                    self.listbox.selection_set(current - 1)
            else:
                self.listbox.selection_set(self.listbox.size() - 1)
            return "break"
    
    def _on_arrow_down(self, event):
        """Gère l'événement flèche bas."""
        if self.listbox:
            if self.listbox.curselection():
                current = self.listbox.curselection()[0]
                if current < self.listbox.size() - 1:
                    self.listbox.selection_clear(current)
                    self.listbox.selection_set(current + 1)
            else:
                self.listbox.selection_set(0)
            return "break"

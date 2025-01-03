import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Callable

class TicketEntry(ttk.Frame):
    """Widget personnalisé pour la saisie et la sélection de tickets."""
    
    def __init__(self, master, textvariable: tk.StringVar, width: int = 20):
        """
        Initialise le widget de saisie de ticket.
        
        Args:
            master: Widget parent
            textvariable: Variable Tkinter pour stocker la valeur
            width: Largeur du champ de saisie
        """
        super().__init__(master)
        
        self.textvariable = textvariable
        self.tickets: List[str] = []
        self.popup = None
        
        # Frame pour le champ de saisie et le compteur
        input_frame = ttk.Frame(self)
        input_frame.pack(fill=tk.X, expand=True)
        
        # Champ de saisie
        self.entry = ttk.Entry(input_frame, textvariable=textvariable, width=width)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Label pour le nombre de tickets
        self.count_label = ttk.Label(input_frame, text="")
        self.count_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Bouton pour afficher la liste (initialement caché)
        self.dropdown_button = ttk.Label(input_frame, text="▼", cursor="hand2")
        self.dropdown_button.pack(side=tk.LEFT, padx=(2, 5))
        self.dropdown_button.bind('<Button-1>', self.show_popup)
        self.dropdown_button.pack_forget()  # Caché par défaut
        
        # Bindings
        self.entry.bind('<Down>', self.show_popup)
        self.entry.bind('<Return>', self.validate_entry)
    
    def set_tickets(self, tickets: List[str], current_ticket: Optional[str] = None):
        """
        Met à jour la liste des tickets disponibles.
        
        Args:
            tickets: Liste des tickets disponibles
            current_ticket: Ticket actuel à sélectionner
        """
        self.tickets = tickets
        
        # Met à jour l'affichage du compteur
        if len(tickets) > 0:
            self.count_label.config(text=f"({len(tickets)})")
            if len(tickets) > 1:
                self.dropdown_button.pack(side=tk.LEFT, padx=(2, 5))
            else:
                self.dropdown_button.pack_forget()
        else:
            self.count_label.config(text="")
            self.dropdown_button.pack_forget()
        
        # Sélectionne le ticket actuel ou le dernier utilisé
        if current_ticket:
            self.textvariable.set(current_ticket)
        elif tickets and not self.textvariable.get():
            self.textvariable.set(tickets[0])
    
    def show_popup(self, event=None):
        """Affiche la liste déroulante des tickets."""
        if not self.tickets or len(self.tickets) <= 1:
            return
        
        if self.popup:
            self.popup.destroy()
        
        # Crée la fenêtre popup
        self.popup = tk.Toplevel(self)
        self.popup.overrideredirect(True)
        self.popup.attributes('-topmost', True)
        
        # Calcule la position
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        
        # Liste des tickets
        listbox = tk.Listbox(
            self.popup,
            height=min(len(self.tickets), 5),
            width=self.entry.winfo_width() // 7  # Approximation de la largeur en caractères
        )
        listbox.pack(fill=tk.BOTH, expand=True)
        
        # Remplit la liste
        current = self.textvariable.get()
        for i, ticket in enumerate(self.tickets):
            listbox.insert(tk.END, ticket)
            if ticket == current:
                listbox.selection_set(i)
                listbox.see(i)
        
        # Positionne la popup
        self.popup.geometry(f"+{x}+{y}")
        
        # Bindings
        listbox.bind('<Return>', lambda e: self.select_ticket(listbox))
        listbox.bind('<Double-Button-1>', lambda e: self.select_ticket(listbox))
        listbox.bind('<Escape>', lambda e: self.popup.destroy())
        listbox.bind('<FocusOut>', lambda e: self.popup.destroy())
        
        # Focus sur la liste
        listbox.focus_set()
    
    def select_ticket(self, listbox):
        """Sélectionne un ticket dans la liste."""
        if listbox.curselection():
            self.textvariable.set(listbox.get(listbox.curselection()))
        self.popup.destroy()
    
    def validate_entry(self, event=None):
        """Valide la saisie d'un nouveau ticket."""
        # Si le ticket n'existe pas dans la liste, on l'ajoute
        ticket = self.textvariable.get().strip()
        if ticket and ticket not in self.tickets:
            self.tickets.append(ticket)
            self.set_tickets(self.tickets, ticket)
        return "break"  # Empêche la propagation de l'événement

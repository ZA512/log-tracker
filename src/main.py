import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import sys
import os
import locale

# Ajouter le répertoire parent au PYTHONPATH pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.database import Database
from src.ui.toast import Toast
from src.ui.autocomplete import AutocompleteEntry
from src.ui.ticket_entry import TicketEntry

class LogTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LogTracker")
        self.root.attributes('-topmost', True)
        
        # Configure la localisation en français
        try:
            locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_TIME, 'fra_fra')
            except locale.Error:
                print("Impossible de définir la locale en français")
        
        # Initialisation de la base de données
        self.db = Database()
        
        # État de l'interface
        self.entry_window = None
        
        # Configuration de la fenêtre principale (minimale)
        self.root.geometry("250x80")
        
        # Création des widgets de la fenêtre principale
        self.create_minimal_widgets()
        
        # Mise à jour du résumé
        self.update_summary()
    
    def create_minimal_widgets(self):
        """Crée les widgets de la fenêtre minimale."""
        self.main_frame = ttk.Frame(self.root, padding="5")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame pour les boutons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=0, column=0, pady=5, sticky=(tk.W, tk.E))
        
        # Boutons sur la même ligne
        ttk.Button(button_frame, text="Ajouter", command=self.show_entry_window).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="Voir", command=self.show_entries).grid(row=0, column=1)
        
        # Label pour la dernière entrée et le temps total sur une ligne
        self.summary_label = ttk.Label(self.main_frame, text="")
        self.summary_label.grid(row=1, column=0, pady=5)
        self.summary_label.bind('<Button-1>', self.show_entry_window)
        
        # Configure le redimensionnement
        self.main_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
    
    def update_summary(self):
        """Met à jour le résumé des entrées."""
        try:
            # Récupère les entrées du jour
            today = datetime.now().date()
            entries = self.db.get_entries_for_day(today)
            
            if entries:
                # Dernière entrée (première de la liste car triée par ordre décroissant)
                last_entry = entries[0]
                time_str = datetime.fromisoformat(last_entry['timestamp']).strftime("%H:%M")
                
                # Temps total
                total_time = sum(entry['duration'] or 0 for entry in entries)
                hours = total_time // 60
                minutes = total_time % 60
                
                # Affiche tout sur une ligne
                summary_text = f"Dernier : {time_str} | aujourd'hui {hours}h{minutes:02d}"
                self.summary_label.config(text=summary_text)
            else:
                self.summary_label.config(text="Aucune entrée aujourd'hui")
        except Exception as e:
            print(f"Erreur lors de la mise à jour du résumé : {str(e)}")
    
    def project_changed(self, *args):
        """Appelé lorsque le projet change pour mettre à jour les suggestions de tickets."""
        project_name = self.project_var.get().strip()
        if project_name:
            projects = self.db.get_projects()
            project = next((p for p in projects if p['name'] == project_name), None)
            if project:
                # Récupère tous les tickets du projet
                tickets = self.db.get_project_tickets(project['id'])
                self.ticket_entry.set_tickets(tickets)
            else:
                self.ticket_entry.set_tickets([])
        else:
            self.ticket_entry.set_tickets([])
    
    def create_entry_widgets(self):
        """Crée les widgets de la fenêtre de saisie."""
        frame = ttk.Frame(self.entry_window, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Projet (optionnel)
        ttk.Label(frame, text="Projet:").grid(row=0, column=0, sticky=tk.W)
        self.project_var = tk.StringVar()
        self.project_entry = AutocompleteEntry(
            frame,
            textvariable=self.project_var,
            completevalues=self.get_project_suggestions()
        )
        self.project_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Observe les changements de projet
        self.project_var.trace_add("write", self.project_changed)
        
        # Bouton pour effacer projet et ticket
        ttk.Button(frame, text="✕", width=3, command=self.clear_project_ticket).grid(row=0, column=2, padx=5)
        
        # Ticket (optionnel)
        ttk.Label(frame, text="Ticket:").grid(row=1, column=0, sticky=tk.W)
        self.ticket_var = tk.StringVar()
        self.ticket_entry = TicketEntry(frame, textvariable=self.ticket_var)
        self.ticket_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Description (obligatoire)
        ttk.Label(frame, text="Description:").grid(row=2, column=0, sticky=tk.W)
        self.description_text = tk.Text(frame, height=5, width=30, wrap=tk.WORD)
        self.description_text.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Durée (optionnelle)
        ttk.Label(frame, text="Durée (min):").grid(row=3, column=0, sticky=tk.W)
        self.duration_var = tk.StringVar()
        self.duration_entry = ttk.Entry(frame, textvariable=self.duration_var)
        self.duration_entry.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Bouton de sauvegarde
        ttk.Button(frame, text="Sauvegarder", command=self.save_entry).grid(row=4, column=0, columnspan=3, pady=10)
        
        # Configuration de la tabulation
        self.project_entry.bind('<Tab>', lambda e: self._focus_next(self.ticket_entry.entry))
        self.ticket_entry.entry.bind('<Tab>', lambda e: self._focus_next(self.description_text))
        self.description_text.bind('<Tab>', lambda e: self._focus_next(self.duration_entry))
        self.duration_entry.bind('<Tab>', lambda e: self._focus_next(self.project_entry))
    
    def _focus_next(self, widget):
        """Déplace le focus vers le widget suivant."""
        widget.focus_set()
        return "break"
    
    def clear_project_ticket(self):
        """Efface les champs projet et ticket."""
        self.project_var.set("")
        self.ticket_var.set("")
    
    def show_entry_window(self, event=None):
        """Affiche la fenêtre de saisie."""
        if self.entry_window is None:
            self.entry_window = tk.Toplevel(self.root)
            self.entry_window.title("Nouvelle entrée")
            self.entry_window.attributes('-topmost', True)
            self.entry_window.geometry("350x300")  # Augmentation de la hauteur
            
            self.create_entry_widgets()
            
            # Gestion de la fermeture de la fenêtre
            self.entry_window.protocol("WM_DELETE_WINDOW", self.hide_entry_window)
            
            # Focus sur le premier champ
            self.project_entry.focus_set()
    
    def hide_entry_window(self):
        """Cache la fenêtre de saisie."""
        if self.entry_window:
            self.entry_window.destroy()
            self.entry_window = None
            # Met à jour le résumé quand on ferme la fenêtre
            self.update_summary()
    
    def save_entry(self):
        """Sauvegarde une nouvelle entrée."""
        description = self.description_text.get("1.0", tk.END).strip()
        if not description:
            Toast(self.root, "La description est obligatoire", 2000)
            return
        
        try:
            # Gestion du projet
            project_id = None
            project_name = self.project_var.get().strip()
            if project_name:
                projects = self.db.get_projects()
                project = next((p for p in projects if p['name'] == project_name), None)
                if project:
                    project_id = project['id']
                else:
                    project_id = self.db.add_project(project_name)
            
            # Gestion du ticket
            ticket_id = None
            ticket_number = self.ticket_var.get().strip()
            if ticket_number and project_id:
                tickets = self.db.get_tickets(project_id)
                ticket = next((t for t in tickets if t['ticket_number'] == ticket_number), None)
                if ticket:
                    ticket_id = ticket['id']
                else:
                    ticket_id = self.db.add_ticket(project_id, ticket_number)
            
            # Gestion de la durée
            duration = None
            duration_str = self.duration_var.get().strip()
            if duration_str:
                duration = int(duration_str)
            
            # Ajout de l'entrée
            self.db.add_entry(description, project_id, ticket_id, duration)
            
            # Affiche un toast de confirmation
            Toast(self.root, "Entrée enregistrée", 2000)
            
            # Réinitialise les champs
            self.description_text.delete("1.0", tk.END)
            self.duration_var.set("")
            
            # Met à jour le résumé
            self.update_summary()
            
            # Cache la fenêtre de saisie
            self.hide_entry_window()
            
        except Exception as e:
            Toast(self.root, f"Erreur : {str(e)}", 3000)
    
    def show_entries(self):
        """Affiche les entrées dans une nouvelle fenêtre."""
        entries_window = tk.Toplevel(self.root)
        entries_window.title("Entrées")
        entries_window.geometry("800x500")
        
        # Frame pour les boutons de contrôle
        control_frame = ttk.Frame(entries_window, padding="5")
        control_frame.pack(fill=tk.X)
        
        # Variables de contrôle
        self.period_var = tk.StringVar(value="day")
        self.view_var = tk.StringVar(value="chronological")
        
        # Boutons pour la période
        period_frame = ttk.LabelFrame(control_frame, text="Période", padding="5")
        period_frame.pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(period_frame, text="Journée", value="day", 
                       variable=self.period_var, command=self.update_entries_view).pack(side=tk.LEFT)
        ttk.Radiobutton(period_frame, text="8 jours", value="week", 
                       variable=self.period_var, command=self.update_entries_view).pack(side=tk.LEFT)
        
        # Boutons pour le type de vue (uniquement visible pour la vue 8 jours)
        self.view_frame = ttk.LabelFrame(control_frame, text="Présentation", padding="5")
        ttk.Radiobutton(self.view_frame, text="Jour par jour", value="chronological", 
                       variable=self.view_var, command=self.update_entries_view).pack(side=tk.LEFT)
        ttk.Radiobutton(self.view_frame, text="Par projet", value="by_project", 
                       variable=self.view_var, command=self.update_entries_view).pack(side=tk.LEFT)
        
        # Création du style personnalisé pour le Treeview
        style = ttk.Style()
        style.configure("Custom.Treeview", rowheight=60)  # Hauteur par défaut plus grande
        style.configure("Group.Custom.Treeview.Item", font=("TkDefaultFont", 10, "bold"))
        
        # Création du Treeview avec le style personnalisé
        tree_frame = ttk.Frame(entries_window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tree = ttk.Treeview(tree_frame, columns=("time", "project", "ticket", "duration", "description"),
                                style="Custom.Treeview")
        
        # Configuration des colonnes
        self.tree.column("#0", width=150)  # Colonne pour le projet/date
        self.tree.column("time", width=100, anchor="w")
        self.tree.column("project", width=100, anchor="w")
        self.tree.column("ticket", width=100, anchor="w")
        self.tree.column("duration", width=80, anchor="e")
        self.tree.column("description", width=300, anchor="w")
        
        # En-têtes des colonnes
        self.tree.heading("#0", text="Projet/Date")
        self.tree.heading("time", text="Date/Heure")
        self.tree.heading("project", text="Projet")
        self.tree.heading("ticket", text="Ticket")
        self.tree.heading("duration", text="Durée")
        self.tree.heading("description", text="Description")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Placement des widgets
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mise à jour initiale
        self.update_entries_view()
        
        # Gestion de la visibilité des contrôles de vue
        self.period_var.trace_add("write", self.on_period_changed)
        self.on_period_changed()
    
    def update_entries_view(self):
        """Met à jour l'affichage des entrées selon les paramètres sélectionnés."""
        # Efface le contenu actuel
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Ajuste les en-têtes et la visibilité des colonnes selon le mode
        is_day_view = self.period_var.get() == "day"
        is_chronological = self.view_var.get() == "chronological"
        
        # Gère la visibilité de la colonne projet
        if is_day_view or not is_chronological:
            self.tree.heading("project", text="")
            self.tree.column("project", width=0)  # Cache la colonne
        else:
            self.tree.heading("project", text="Projet")
            self.tree.column("project", width=100)  # Montre la colonne
        
        self.tree.heading("time", text="Date/Heure")
        self.tree.heading("#0", text="Projet" if is_day_view else "Projet/Date")
        
        # Calcul de la période
        today = datetime.now().date()
        if is_day_view:
            start_date = today
            end_date = today
        else:  # week
            start_date = today - timedelta(days=7)
            end_date = today
        
        try:
            if is_day_view:
                # Vue journée groupée par projet
                entries = self.db.get_entries_by_date_range(start_date, end_date)
                if not entries:
                    self.tree.insert("", "end", text="Aucune entrée pour cette période")
                else:
                    # Organise les entrées par projet
                    entries_by_project = {}
                    for entry in entries:
                        project_name = entry['project_name'] or 'Sans projet'
                        if project_name not in entries_by_project:
                            entries_by_project[project_name] = []
                        entries_by_project[project_name].append(entry)
                    
                    # Liste pour stocker les IDs des groupes
                    group_ids = []
                    
                    # Affiche les entrées groupées par projet
                    for project_name, project_entries in entries_by_project.items():
                        project_node = self.tree.insert("", "end", text=project_name, tags=("group",))
                        group_ids.append(project_node)
                        
                        # Trie les entrées par ordre chronologique inverse
                        project_entries.sort(key=lambda x: x['timestamp'], reverse=True)
                        
                        for entry in project_entries:
                            entry_date = datetime.fromisoformat(entry['timestamp']).date()
                            entry_time = datetime.fromisoformat(entry['timestamp']).strftime("%H:%M")
                            
                            # Remplace les retours à la ligne par des espaces pour le calcul de la hauteur
                            description = entry['description'].replace('\n', ' \n ')
                            
                            values = (
                                f"{entry_date.strftime('%d/%m')} {entry_time}",
                                "",  # Projet (caché en mode journée)
                                f"#{entry['ticket_number']}" if entry['ticket_number'] else "",
                                f"{entry['duration']}min" if entry['duration'] else "",
                                description
                            )
                            self.tree.insert(project_node, "end", values=values)
                    
                    # Déplie tous les groupes
                    for group_id in group_ids:
                        self.tree.item(group_id, open=True)
            
            elif is_chronological:
                # Vue sur 8 jours chronologique
                entries = self.db.get_entries_by_date_range(start_date, end_date)
                if not entries:
                    self.tree.insert("", "end", text="Aucune entrée pour cette période")
                else:
                    # Trie d'abord par projet puis par date/heure
                    entries.sort(key=lambda x: (x['project_name'] or 'Sans projet', x['timestamp']))
                    
                    current_date = None
                    date_node = None
                    group_ids = []
                    
                    for entry in entries:
                        entry_date = datetime.fromisoformat(entry['timestamp']).date()
                        entry_time = datetime.fromisoformat(entry['timestamp']).strftime("%H:%M")
                        
                        if entry_date != current_date:
                            current_date = entry_date
                            # Utilise %A pour le jour en français et capitalise la première lettre
                            date_str = entry_date.strftime('%A %d/%m')
                            date_str = date_str[0].upper() + date_str[1:]
                            date_node = self.tree.insert("", "end", text=date_str, tags=("group",))
                            group_ids.append(date_node)
                        
                        # Remplace les retours à la ligne par des espaces pour le calcul de la hauteur
                        description = entry['description'].replace('\n', ' \n ')
                        
                        values = (
                            f"{entry_date.strftime('%d/%m')} {entry_time}",
                            entry['project_name'] or 'Sans projet',
                            f"#{entry['ticket_number']}" if entry['ticket_number'] else "",
                            f"{entry['duration']}min" if entry['duration'] else "",
                            description
                        )
                        self.tree.insert(date_node, "end", values=values)
                    
                    # Déplie tous les groupes
                    for group_id in group_ids:
                        self.tree.item(group_id, open=True)
            
            else:  # Vue par projet sur 8 jours
                entries_by_project = self.db.get_entries_by_project(start_date, end_date)
                if not entries_by_project:
                    self.tree.insert("", "end", text="Aucune entrée pour cette période")
                else:
                    group_ids = []
                    
                    for project_name, entries in entries_by_project.items():
                        project_node = self.tree.insert("", "end", text=project_name, tags=("group",))
                        group_ids.append(project_node)
                        
                        # Trie les entrées par ordre chronologique inverse
                        entries.sort(key=lambda x: x['timestamp'], reverse=True)
                        
                        for entry in entries:
                            entry_date = datetime.fromisoformat(entry['timestamp']).date()
                            entry_time = datetime.fromisoformat(entry['timestamp']).strftime("%H:%M")
                            
                            # Remplace les retours à la ligne par des espaces pour le calcul de la hauteur
                            description = entry['description'].replace('\n', ' \n ')
                            
                            values = (
                                f"{entry_date.strftime('%d/%m')} {entry_time}",
                                "",  # Projet (caché en mode par projet)
                                f"#{entry['ticket_number']}" if entry['ticket_number'] else "",
                                f"{entry['duration']}min" if entry['duration'] else "",
                                description
                            )
                            self.tree.insert(project_node, "end", values=values)
                    
                    # Déplie tous les groupes
                    for group_id in group_ids:
                        self.tree.item(group_id, open=True)
            
        except Exception as e:
            self.tree.insert("", "end", text=f"Erreur : {str(e)}")
    
    def on_period_changed(self, *args):
        """Gère la visibilité des contrôles de vue selon la période."""
        if self.period_var.get() == "week":
            self.view_frame.pack(side=tk.LEFT, padx=5)
        else:
            self.view_frame.pack_forget()
            self.view_var.set("chronological")
    
    def format_entry(self, entry, show_project=True):
        """
        Formate une entrée pour l'affichage.
        
        Args:
            entry: L'entrée à formater
            show_project: Si True, inclut le nom du projet dans la ligne
        """
        time_str = datetime.fromisoformat(entry['timestamp']).strftime("%H:%M")
        date_str = datetime.fromisoformat(entry['timestamp']).strftime("%d/%m")
        
        # Formate chaque partie avec une largeur fixe
        date_time = f"{date_str} {time_str}".ljust(12)
        ticket = f"#{entry['ticket_number']}".ljust(15) if entry['ticket_number'] else " " * 15
        duration = f"({entry['duration']}min)".ljust(10) if entry['duration'] else " " * 10
        
        if show_project:
            project = f"[{entry['project_name']}]".ljust(20) if entry['project_name'] else " " * 20
            return f"{date_time} {project} {ticket} {duration} {entry['description']}\n"
        else:
            return f"  {date_time} {ticket} {duration} {entry['description']}\n"
    
    def get_project_suggestions(self):
        """Récupère la liste des projets pour l'autocomplétion."""
        try:
            projects = self.db.get_projects()
            return [p['name'] for p in projects]
        except Exception:
            return []

def main():
    root = tk.Tk()
    app = LogTrackerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

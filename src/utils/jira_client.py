import requests
from datetime import datetime


class JiraClient:
    """Client pour l'API Jira."""
    
    def __init__(self, base_url, token):
        """Initialise le client Jira.
        
        Args:
            base_url: URL de base de l'instance Jira (ex: https://your-domain.atlassian.net)
            token: Token d'accès à l'API Jira
        """
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def get_issue_details(self, issue_key):
        """Récupère les détails d'un ticket.
        
        Args:
            issue_key: Identifiant du ticket (ex: PROJ-123)
            
        Returns:
            dict: Détails du ticket ou None si erreur
        """
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/2/issue/{issue_key}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return {
                'key': data['key'],
                'summary': data['fields']['summary'],
                'description': data['fields']['description']
            }
        except Exception as e:
            print(f"Erreur lors de la récupération du ticket {issue_key}: {str(e)}")
            return None
    
    def add_worklog(self, issue_key, time_spent_minutes, comment):
        """Ajoute un temps passé sur un ticket.
        
        Args:
            issue_key: Identifiant du ticket (ex: PROJ-123)
            time_spent_minutes: Temps passé en minutes
            comment: Commentaire à ajouter
            
        Returns:
            bool: True si succès, False si erreur
        """
        try:
            # Convertit les minutes en format Jira (ex: 2h 30m)
            hours = time_spent_minutes // 60
            minutes = time_spent_minutes % 60
            time_spent = ""
            if hours > 0:
                time_spent += f"{hours}h"
            if minutes > 0:
                time_spent += f" {minutes}m"
            time_spent = time_spent.strip()
            
            data = {
                'timeSpent': time_spent,
                'comment': comment,
                'started': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000+0100')
            }
            
            response = requests.post(
                f"{self.base_url}/rest/api/2/issue/{issue_key}/worklog",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'ajout du temps sur le ticket {issue_key}: {str(e)}")
            return False

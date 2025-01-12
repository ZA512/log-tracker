import requests
from datetime import datetime
import base64


class JiraClient:
    """Client pour l'API Jira."""
    
    def __init__(self, base_url, token, email):
        """Initialise le client Jira.
        
        Args:
            base_url: URL de base de l'instance Jira (ex: mycompany.atlassian.net)
            token: Token d'accès à l'API Jira
            email: Email associé au compte Jira
        """
        # Nettoie l'URL de base
        base_url = base_url.strip().rstrip('/')
        
        # Si l'URL ne commence pas par http/https, on ajoute https://
        if not base_url.startswith(('http://', 'https://')):
            base_url = f'https://{base_url}'
            
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Basic {self._encode_credentials(email, token)}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _encode_credentials(self, email, token):
        """Encode les identifiants en Base64 pour l'authentification Basic."""
        credentials = f"{email}:{token}"
        return base64.b64encode(credentials.encode()).decode()
    
    def get_issue_details(self, issue_key):
        """Récupère les détails d'un ticket.
        
        Args:
            issue_key: Identifiant du ticket (ex: PROJ-123)
            
        Returns:
            dict: Détails du ticket ou None si erreur
        """
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/issue/{issue_key}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                'key': data['key'],
                'summary': data['fields']['summary'],
                'description': data['fields'].get('description', '')
            }
        except Exception as e:
            if isinstance(e, requests.exceptions.RequestException):
                print(f"Erreur API Jira pour {issue_key} - Status: {e.response.status_code}, Response: {e.response.text}")
            else:
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

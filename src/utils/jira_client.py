import requests
from datetime import datetime
import base64
import os
import json


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
    
    def add_worklog(self, issue_key, time_spent_minutes, comment, started_datetime=None):
        """Ajoute un temps passé sur un ticket.
        
        Args:
            issue_key: Identifiant du ticket (ex: PROJ-123)
            time_spent_minutes: Temps passé en minutes
            comment: Commentaire à ajouter
            started_datetime: Date et heure de début du travail (datetime)
            
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
            
            # Utilise la date fournie ou la date actuelle
            if started_datetime is None:
                started_datetime = datetime.now()
            
            data = {
                'timeSpent': time_spent,
                'comment': comment,
                'started': started_datetime.strftime('%Y-%m-%dT%H:%M:%S.000+0100')
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
            
    def search_issues(self, jql, fields=None, max_results=1000):
        """Recherche des tickets selon un JQL.
        
        Args:
            jql: Requête JQL
            fields: Liste des champs à récupérer
            max_results: Nombre maximum de résultats à récupérer
            
        Returns:
            list: Liste des tickets trouvés
        """
        try:
            if fields is None:
                fields = [
                    'key',
                    'summary',
                    'issuetype',
                    'parent',
                    'customfield_10014',  # Epic link
                    'project',
                    'issuelinks',
                    'status'
                ]
                
            start_at = 0
            all_issues = []
            
            while True:
                response = requests.post(
                    f"{self.base_url}/rest/api/3/search",
                    headers=self.headers,
                    json={
                        'jql': jql,
                        'fields': fields,
                        'startAt': start_at,
                        'maxResults': min(100, max_results - len(all_issues)),
                        'expand': ['names', 'schema', 'transitions']
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                issues = data['issues']
                if not issues:
                    break
                    
                for issue in issues:
                    issue_type = issue['fields']['issuetype']['name'].lower()
                    parent_key = None
                    
                    # Pour les sous-tâches, le parent est dans le champ 'parent'
                    if 'parent' in issue['fields'] and issue['fields']['parent']:
                        parent_key = issue['fields']['parent']['key']
                    
                    # Pour les stories/tasks, le parent est l'epic
                    elif 'customfield_10014' in issue['fields'] and issue['fields']['customfield_10014']:
                        parent_key = issue['fields']['customfield_10014']
                    
                    # Pour les epics, on cherche un lien vers un autre epic
                    elif issue_type == 'epic' and 'issuelinks' in issue['fields']:
                        for link in issue['fields']['issuelinks']:
                            # On cherche les liens de type "is part of" ou similaire
                            if 'inwardIssue' in link and link.get('type', {}).get('name', '').lower() in ['is part of', 'belongs to', 'implements']:
                                parent_key = link['inwardIssue']['key']
                                break
                    
                    # Si aucun parent n'est trouvé et que ce n'est pas un projet
                    if parent_key is None and issue_type != 'project':
                        # Pour les epics sans parent, on met le projet comme parent
                        if issue_type == 'epic':
                            parent_key = issue['fields']['project']['key']
                        # Pour les autres types, on essaie de trouver l'epic parent via une requête supplémentaire
                        else:
                            try:
                                epic_response = requests.get(
                                    f"{self.base_url}/rest/agile/1.0/issue/{issue['key']}/epic",
                                    headers=self.headers
                                )
                                if epic_response.status_code == 200:
                                    epic_data = epic_response.json()
                                    if 'key' in epic_data:
                                        parent_key = epic_data['key']
                                    else:
                                        parent_key = issue['fields']['project']['key']
                                else:
                                    parent_key = issue['fields']['project']['key']
                            except:
                                parent_key = issue['fields']['project']['key']
                    
                    all_issues.append({
                        'key': issue['key'],
                        'title': issue['fields']['summary'],
                        'type': issue_type,
                        'parent_key': parent_key,
                        'status': issue['fields']['status']['name']
                    })
                
                start_at += len(issues)
                
                if len(all_issues) >= max_results or len(issues) < 100:
                    break
                    
            return all_issues
            
        except Exception as e:
            print(f"Erreur lors de la recherche des tickets: {str(e)}")
            if isinstance(e, requests.exceptions.RequestException):
                print(f"Réponse de l'API: {e.response.text}")
            return []
            
    def get_issue_hierarchy(self, jql, max_results=1000):
        """Récupère la hiérarchie complète des tickets selon un JQL.
        
        Args:
            jql: Requête JQL
            max_results: Nombre maximum de résultats à récupérer
            
        Returns:
            list: Liste des tickets avec leur niveau dans la hiérarchie
        """
        try:
            # Récupère tous les tickets
            issues = self.search_issues(jql, max_results=max_results)
            if not issues:
                return []
                
            # Construit un dictionnaire des tickets par clé
            issues_by_key = {issue['key']: issue for issue in issues}
            
            # Calcule le niveau de chaque ticket dans la hiérarchie
            for issue in issues:
                level = 0
                current_key = issue['parent_key']
                
                # Remonte la hiérarchie jusqu'à la racine
                while current_key and current_key in issues_by_key:
                    level += 1
                    current_key = issues_by_key[current_key]['parent_key']
                
                issue['level'] = level
                
            return issues
            
        except Exception as e:
            print(f"Erreur lors de la récupération de la hiérarchie: {str(e)}")
            return []

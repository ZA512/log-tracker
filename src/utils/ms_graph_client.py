import msal
import requests
import json
from PyQt6.QtCore import QObject, pyqtSignal

class MSGraphClient(QObject):
    """Client pour l'API Microsoft Graph."""
    
    auth_error = pyqtSignal(str)  # Signal émis en cas d'erreur d'authentification
    
    def __init__(self, client_id, tenant_id):
        super().__init__()
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.access_token = None
        
        # Configuration de l'application MSAL
        self.app = msal.PublicClientApplication(
            client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            token_cache=msal.SerializableTokenCache()
        )
        
    def authenticate(self):
        """Authentifie l'utilisateur via le flux interactif."""
        try:
            print("Début de l'authentification...")
            # Les scopes nécessaires pour Microsoft Graph avec le format complet
            scopes = [
                "https://graph.microsoft.com/.default"
            ]
            print(f"Scopes demandés: {scopes}")
            
            # Tente d'obtenir un token depuis le cache
            accounts = self.app.get_accounts()
            print(f"Comptes trouvés dans le cache: {len(accounts)}")
            
            if accounts:
                print("Tentative d'utilisation du token en cache...")
                result = self.app.acquire_token_silent(scopes, account=accounts[0])
            else:
                print("Aucun compte dans le cache")
                result = None
                
            # Si pas de token dans le cache, demande une authentification interactive
            if not result:
                print("Démarrage de l'authentification interactive...")
                try:
                    # Configuration pour l'authentification interactive
                    result = self.app.acquire_token_interactive(
                        scopes=scopes,
                        prompt="select_account"
                    )
                    print("Résultat de l'authentification interactive obtenu")
                    
                    if result and "access_token" in result:
                        print("Token d'accès obtenu avec succès")
                        self.access_token = result["access_token"]
                        return True
                    else:
                        error_msg = result.get('error_description', 'Erreur inconnue') if result else "Pas de résultat d'authentification"
                        print(f"Échec de l'authentification: {error_msg}")
                        if "error" in result:
                            print(f"Code d'erreur: {result['error']}")
                        self.auth_error.emit(f"Erreur d'authentification: {error_msg}")
                        return False
                        
                except Exception as e:
                    print(f"Exception pendant l'authentification interactive: {str(e)}")
                    self.auth_error.emit(f"Erreur lors de l'authentification: {str(e)}")
                    return False
            
            return True
                
        except Exception as e:
            print(f"Exception lors de l'authentification: {str(e)}")
            self.auth_error.emit(f"Erreur lors de l'authentification: {str(e)}")
            return False
            
    def get_plans(self):
        """Récupère les plans depuis Microsoft Graph."""
        if not self.access_token:
            if not self.authenticate():
                return []

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        try:
            # Première tentative : récupérer les plans via /me/planner
            print("\nTentative 1: Récupération via /me/planner...")
            me_plans_url = "https://graph.microsoft.com/v1.0/me/planner/tasks"
            try:
                response = requests.get(me_plans_url, headers=headers)
                if response.status_code == 200:
                    tasks = response.json().get('value', [])
                    print(f"Tâches trouvées: {len(tasks)}")
                    
                    # Récupérer les plans uniques à partir des tâches
                    plan_ids = set(task['planId'] for task in tasks if 'planId' in task)
                    print(f"Plans uniques trouvés: {len(plan_ids)}")
                    
                    # Récupérer les détails de chaque plan
                    formatted_plans = []
                    for plan_id in plan_ids:
                        plan_url = f"https://graph.microsoft.com/v1.0/planner/plans/{plan_id}"
                        try:
                            plan_response = requests.get(plan_url, headers=headers)
                            if plan_response.status_code == 200:
                                plan = plan_response.json()
                                # Formater le plan selon le format attendu
                                formatted_plan = {
                                    "id": plan.get('id'),
                                    "title": plan.get('title', 'Sans titre'),
                                    "owner": plan.get('owner', ''),  # ID du groupe propriétaire
                                    "group_name": ""  # Sera rempli plus tard si possible
                                }
                                
                                # Tenter de récupérer le nom du groupe
                                if formatted_plan["owner"]:
                                    try:
                                        group_url = f"https://graph.microsoft.com/v1.0/groups/{formatted_plan['owner']}"
                                        group_response = requests.get(group_url, headers=headers)
                                        if group_response.status_code == 200:
                                            group = group_response.json()
                                            formatted_plan["group_name"] = group.get('displayName', '')
                                    except Exception as e:
                                        print(f"Impossible de récupérer le nom du groupe: {str(e)}")
                                
                                formatted_plans.append(formatted_plan)
                                print(f"- Plan trouvé: {formatted_plan['title']} (Groupe: {formatted_plan['group_name']})")
                        except Exception as e:
                            print(f"Erreur lors de la récupération du plan {plan_id}: {str(e)}")
                            continue
                    
                    if formatted_plans:
                        print(f"\nTotal des plans trouvés: {len(formatted_plans)}")
                        return formatted_plans
                    
            except Exception as e:
                print(f"Erreur lors de la première tentative: {str(e)}")

            # Si la première tentative échoue, on ne continue pas avec la deuxième
            # car nous avons déjà trouvé des plans
            return []

        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la requête HTTP: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Détails de l'erreur: {e.response.text}")
            return []

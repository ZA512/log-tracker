import msal
import requests
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
            authority=f"https://login.microsoftonline.com/{tenant_id}"
        )
        
    def authenticate(self):
        """Authentifie l'utilisateur via le flux interactif."""
        try:
            # Les scopes nécessaires pour Planner
            scopes = ["Tasks.Read", "Tasks.Read.Shared", "Group.Read.All"]
            
            # Tente d'obtenir un token depuis le cache
            accounts = self.app.get_accounts()
            if accounts:
                result = self.app.acquire_token_silent(scopes, account=accounts[0])
            else:
                result = None
                
            # Si pas de token dans le cache, demande une authentification interactive
            if not result:
                result = self.app.acquire_token_interactive(scopes)
                
            if "access_token" in result:
                self.access_token = result["access_token"]
                return True
            else:
                self.auth_error.emit(f"Erreur d'authentification: {result.get('error_description', 'Erreur inconnue')}")
                return False
                
        except Exception as e:
            self.auth_error.emit(f"Erreur lors de l'authentification: {str(e)}")
            return False
            
    def get_plans(self):
        """Récupère la liste des plans Planner accessibles.
        
        Returns:
            list: Liste des plans au format [{id, title, group_id, group_name}]
        """
        if not self.access_token:
            if not self.authenticate():
                return []
                
        try:
            # Récupère d'abord tous les groupes
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            groups_response = requests.get(
                "https://graph.microsoft.com/v1.0/me/memberOf",
                headers=headers
            )
            groups_response.raise_for_status()
            groups = {g["id"]: g["displayName"] 
                     for g in groups_response.json()["value"] 
                     if g["@odata.type"] == "#microsoft.graph.group"}
            
            # Récupère tous les plans
            plans_response = requests.get(
                "https://graph.microsoft.com/v1.0/planner/plans",
                headers=headers
            )
            plans_response.raise_for_status()
            
            # Combine les informations
            plans = []
            for plan in plans_response.json()["value"]:
                group_id = plan.get("owner")
                if group_id in groups:
                    plans.append({
                        "id": plan["id"],
                        "title": plan["title"],
                        "group_id": group_id,
                        "group_name": groups[group_id]
                    })
                    
            return plans
            
        except Exception as e:
            self.auth_error.emit(f"Erreur lors de la récupération des plans: {str(e)}")
            return []

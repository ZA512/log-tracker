from datetime import datetime
from typing import Optional

class Entry:
    """
    Représente une entrée de journal dans l'application.
    
    Attributes:
        description (str): Description de l'activité
        timestamp (datetime): Horodatage de l'entrée
        project_id (Optional[int]): ID du projet associé
        ticket_id (Optional[int]): ID du ticket JIRA associé
        duration (Optional[int]): Durée en minutes
        synced_to_jira (bool): Indique si l'entrée a été synchronisée avec JIRA
    """
    
    def __init__(
        self,
        description: str,
        project_id: Optional[int] = None,
        ticket_id: Optional[int] = None,
        duration: Optional[int] = None
    ):
        """
        Initialise une nouvelle entrée de journal.
        
        Args:
            description (str): Description de l'activité
            project_id (Optional[int], optional): ID du projet. Defaults to None.
            ticket_id (Optional[int], optional): ID du ticket. Defaults to None.
            duration (Optional[int], optional): Durée en minutes. Defaults to None.
            
        Raises:
            ValueError: Si la description est vide ou si la durée est négative
        """
        if not description:
            raise ValueError("La description ne peut pas être vide")
            
        if duration is not None and duration < 0:
            raise ValueError("La durée ne peut pas être négative")
            
        self.description = description
        self.timestamp = datetime.now()
        self.project_id = project_id
        self.ticket_id = ticket_id
        self.duration = duration
        self.synced_to_jira = False

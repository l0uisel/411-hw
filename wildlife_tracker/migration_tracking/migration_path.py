from typing import Optional

from wildlife_tracker.migration_managment.migration import Migration
from wildlife_tracker.migration_management.MigrationPath import MigrationPath
from wildlife_tracker.habitat_management.habitat import Habitat

class MigrationPath:

#migration_path_id: int

    def __init__(self,
                path_id: int,
                start_location: Habitat,
                destination: Habitat,
                species: str,
                duration: Optional[int] = None) -> None:
        self.path_id = path_id
        self.start_location = Habitat
        self.destination = Habitat
        self.species = species

def get_migration_path_details(path_id) -> dict:
    pass

def update_migration_path_details(path_id: int, **kwargs) -> None:
    pass
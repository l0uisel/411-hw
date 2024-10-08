from typing import Any, Optional

class Animal:

    def __init__(self,
                animal_id: int,
                species:str,
                age: Optional[int] = None,
                health_status: Optional[str] = None) -> None:

        self.animal_id = animal_id
        self.health_status = health_status or []
        self.species = species
        self.age = age or []

def get_animal_details(animal_id) -> dict[str, Any]:
    pass

def update_animal_details(animal_id: int, **kwargs: Any) -> None:
    pass
from typing import Optional


class MigrationManager:
    
def cancel_migration(migration_id: int) -> None:
    pass

def schedule_migration(migration_path: MigrationPath) -> None:
    pass

def get_migration_by_id(migration_id: int) -> Migration:
    pass

def get_migrations() -> list[Migration]:
    pass

def get_migrations_by_current_location(current_location: str) -> list[Migration]:
    pass

def get_migrations_by_migration_path(migration_path_id: int) -> list[Migration]:
    pass

def get_migrations_by_start_date(start_date: str) -> list[Migration]:
    pass

def get_migrations_by_status(status: str) -> list[Migration]:
    pass


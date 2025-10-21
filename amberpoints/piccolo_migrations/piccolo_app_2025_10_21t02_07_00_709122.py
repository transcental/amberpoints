from piccolo.apps.migrations.auto.migration_manager import MigrationManager


ID = "2025-10-21T02:07:00:709122"
VERSION = "1.29.0"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="piccolo_app", description=DESCRIPTION
    )

    manager.rename_table(
        old_class_name="User",
        old_tablename="user",
        new_class_name="Person",
        new_tablename="person",
        schema=None,
    )

    manager.rename_column(
        table_class_name="Purchase",
        tablename="purchase",
        old_column_name="user",
        new_column_name="person",
        old_db_column_name="user",
        new_db_column_name="person",
        schema=None,
    )

    return manager

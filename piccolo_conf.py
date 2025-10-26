from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine

from amberpoints.config import config


DB = PostgresEngine(config={"dsn": config.database_url.encoded_string()})


# A list of paths to piccolo apps
# e.g. ['blog.piccolo_app']
APP_REGISTRY = AppRegistry(
    apps=["amberpoints.piccolo_app", "piccolo_admin.piccolo_app"]
)

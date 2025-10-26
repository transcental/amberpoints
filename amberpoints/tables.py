from piccolo.columns import ForeignKey
from piccolo.columns import Integer
from piccolo.columns import Timestamp
from piccolo.columns import Varchar
from piccolo.columns.column_types import Boolean
from piccolo.columns.defaults import TimestampNow
from piccolo.table import Table


class Person(Table):
    slack_id = Varchar(length=50, unique=True)
    points = Integer(default=0)
    admin = Boolean(default=False)
    banned = Boolean(default=False)
    ban_reason = Varchar(length=255, null=True)


class ShopItem(Table):
    name = Varchar(length=100)
    description = Varchar(length=255)
    cost = Integer()
    stock = Integer(null=True)  # null means unlimited stock
    max_per_user = Integer(null=True)  # null means no limit
    image_url = Varchar(length=255)  # URL to an image representing the item
    active = Boolean(default=True)  # Whether the item is available for purchase


class Purchase(Table):
    person = ForeignKey(Person)
    item = ForeignKey(ShopItem)
    quantity = Integer(default=1)
    total_cost = Integer()
    timestamp = Varchar(length=50)  # ISO formatted timestamp of purchase


class AuditLog(Table):
    timestamp = Timestamp(default=TimestampNow())
    user_id = Varchar(length=50)  # who performed the action
    action = Varchar(length=50)  # e.g., "ban", "give", "subtract", "donate"
    target_user = Varchar(length=50, null=True)
    amount = Integer(null=True)
    reason = Varchar(length=255, null=True)

from piccolo.columns import ForeignKey, Varchar
from piccolo.columns import Integer
from piccolo.columns.column_types import Boolean
from piccolo.table import Table

class Person(Table):
    slack_id = Varchar(length=50, unique=True)
    points = Integer(default=0)
    admin = Boolean(default=False)


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
    
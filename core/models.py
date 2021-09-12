from tortoise import fields
from tortoise.models import Model


class Guilds(Model):
    id = fields.BigIntField(pk=True, generated=False)

    class Meta:
        table = "guilds"

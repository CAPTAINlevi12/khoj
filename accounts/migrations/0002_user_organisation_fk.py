"""Turn User.organisation from a typed name into a ForeignKey.

An AlterField cannot do this in one step: existing rows hold '' and Postgres
refuses to cast an empty string to a bigint. So the column is dropped and a
new one added.

That is destructive of the old values, which is acceptable here only because
no responder accounts exist yet — the field was blank on every row. A
deployment with real data would need a three-phase migration instead: add the
new column, backfill it by matching names to Organisation rows, then drop the
old one.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("registry", "0005_unidentifiedrecord_recordphoto_and_more"),
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="organisation",
        ),
        migrations.AddField(
            model_name="user",
            name="organisation",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="staff",
                to="registry.organisation",
            ),
        ),
    ]

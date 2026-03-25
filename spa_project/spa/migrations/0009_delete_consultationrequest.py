# Generated migration to remove ConsultationRequest model
# Part of removing consultation feature

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('spa', '0008_add_indexes_constraints'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ConsultationRequest',
        ),
    ]
# Generated by Django 3.0.7 on 2020-07-11 08:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_tagconfigurationtemplate'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificate',
            name='tag_configuration_id',
            field=models.IntegerField(default=-1),
        ),
    ]

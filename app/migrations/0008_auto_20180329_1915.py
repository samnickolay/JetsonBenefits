# Generated by Django 2.0.2 on 2018-03-29 19:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_health_question_options_question'),
    ]

    operations = [
        migrations.RenameField(
            model_name='health_question_options',
            old_name='question_id',
            new_name='health_question_id',
        ),
    ]

# Generated by Django 5.2 on 2025-04-05 09:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('moodtracker', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='moodentry',
            old_name='date',
            new_name='timestamp',
        ),
        migrations.AlterField(
            model_name='moodentry',
            name='mood',
            field=models.CharField(choices=[('happy', '😊 Happy'), ('sad', '😢 Sad'), ('angry', '😠 Angry'), ('anxious', '😰 Anxious'), ('excited', '🤩 Excited'), ('neutral', '😐 Neutral')], max_length=20),
        ),
        migrations.AlterField(
            model_name='moodentry',
            name='note',
            field=models.TextField(blank=True, null=True),
        ),
    ]

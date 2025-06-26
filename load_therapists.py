# load_therapists.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bloom.settings")
django.setup()

from django.core.management import call_command

try:
    call_command('loaddata', 'therapists.json')
    print("✅ Therapist data loaded successfully!")
except Exception as e:
    print(f"❌ Error loading data: {e}")

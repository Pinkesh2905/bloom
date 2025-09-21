import sys
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from journal.models import JournalEntry, Tag

class Command(BaseCommand):
    help = 'Seeds the database with sample journal entries and tags for a specific user.'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='The username of the user to assign the journal entries to.')

    def handle(self, *args, **options):
        username = options['username']
        User = get_user_model()

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist. Please create the user first.')

        self.stdout.write(self.style.WARNING(f'Deleting old journal data for user "{username}"...'))
        JournalEntry.objects.filter(user=user).delete()
        
        self.stdout.write('Creating sample tags...')
        sample_tags = ["work", "project-bloom", "personal", "reflection", "ideas", "learning", "gratitude"]
        tag_map = {}
        for tag_name in sample_tags:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            tag_map[tag_name] = tag
            if created:
                self.stdout.write(f'  - Created tag: {tag_name}')

        self.stdout.write('Creating sample journal entries...')
        
        sample_entries = [
            # ... (Sample data dictionaries from your original script) ...
            {
                "title": "First Day on the Bloom Project",
                "content": "Today was the first day I started working on the 'Bloom' journal app...",
                "mood": JournalEntry.Mood.EXCITED, "tags": ["work", "project-bloom", "learning"], "is_favorite": True,
            },
            {
                "title": "A Moment of Reflection",
                "content": "Took a long walk this evening to clear my head. The sunset was beautiful...",
                "mood": JournalEntry.Mood.CALM, "tags": ["personal", "reflection"], "is_favorite": False,
            },
            {
                "title": "Struggling with a Bug",
                "content": "Spent almost three hours trying to fix a CSS bug... A good reminder to pay attention to details.",
                "mood": JournalEntry.Mood.SAD, "tags": ["work", "project-bloom"], "is_favorite": False,
            },
            {
                "title": "New Feature Idea: Analytics",
                "content": "Had an idea for a new feature: a simple analytics page that shows mood trends over time...",
                "mood": JournalEntry.Mood.NEUTRAL, "tags": ["ideas", "project-bloom"], "is_favorite": True,
            },
            {
                "title": "Feeling Grateful Today",
                "content": "A friend called me out of the blue... Feeling very grateful for the wonderful people in my life.",
                "mood": JournalEntry.Mood.HAPPY, "tags": ["personal", "gratitude"], "is_favorite": False,
            },
            {
                "title": "Learning about Django Class-Based Views",
                "content": "Dived deep into Django's Class-Based Views (CBVs) today...",
                "mood": JournalEntry.Mood.NEUTRAL, "tags": ["learning", "work"], "is_favorite": False,
            }
        ]
        
        for data in sample_entries:
            entry = JournalEntry.objects.create(
                user=user,
                title=data["title"],
                content=data["content"],
                mood=data["mood"],
                is_favorite=data["is_favorite"]
            )
            for tag_name in data["tags"]:
                entry.tags.add(tag_map[tag_name])
            self.stdout.write(f'  - Created entry: "{entry.title}"')

        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully seeded journal data for user "{username}".'))

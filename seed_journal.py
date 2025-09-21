
from django.contrib.auth import get_user_model
from journal.models import JournalEntry, Tag

USERNAME = "Pinkesh" 

# --- Sample Data ---
sample_tags = ["work", "project-bloom", "personal", "reflection", "ideas", "learning", "gratitude"]

sample_entries = [
    {
        "title": "First Day on the Bloom Project",
        "content": "Today was the first day I started working on the 'Bloom' journal app. The initial setup with Django was smooth. I'm excited to see how this project evolves. The goal is to create something truly personal and useful.",
        "mood": JournalEntry.Mood.EXCITED,
        "tags": ["work", "project-bloom", "learning"],
        "is_favorite": True,
    },
    {
        "title": "A Moment of Reflection",
        "content": "Took a long walk this evening to clear my head. The sunset was beautiful. It's important to take these moments to disconnect from the screen and just be present. Feeling much calmer now.",
        "mood": JournalEntry.Mood.CALM,
        "tags": ["personal", "reflection"],
        "is_favorite": False,
    },
    {
        "title": "Struggling with a Bug",
        "content": "Spent almost three hours trying to fix a CSS bug in the journal list view. It was frustrating, but I finally figured it out. The issue was a small typo in a class name. A good reminder to pay attention to details.",
        "mood": JournalEntry.Mood.SAD,
        "tags": ["work", "project-bloom"],
        "is_favorite": False,
    },
    {
        "title": "New Feature Idea: Analytics",
        "content": "Had an idea for a new feature: a simple analytics page that shows mood trends over time. It could be a cool way to visualize emotional patterns. I should sketch out the UI for this tomorrow.",
        "mood": JournalEntry.Mood.NEUTRAL,
        "tags": ["ideas", "project-bloom"],
        "is_favorite": True,
    },
    {
        "title": "Feeling Grateful Today",
        "content": "A friend called me out of the blue, and we had a great chat. It's the small things that often make the biggest difference. Feeling very grateful for the wonderful people in my life.",
        "mood": JournalEntry.Mood.HAPPY,
        "tags": ["personal", "gratitude"],
        "is_favorite": False,
    },
    {
        "title": "Learning about Django Class-Based Views",
        "content": "Dived deep into Django's Class-Based Views (CBVs) today. They feel a bit abstract at first, but I can see how they reduce boilerplate code and make the views more reusable. The ListView and DetailView are particularly powerful.",
        "mood": JournalEntry.Mood.NEUTRAL,
        "tags": ["learning", "work"],
        "is_favorite": False,
    }
]


def run_seed():
    """
    Populates the database with sample journal entries and tags.
    """
    User = get_user_model()
    try:
        user = User.objects.get(username=USERNAME)
    except User.DoesNotExist:
        print(f"--- ERROR: User '{USERNAME}' not found. ---")
        print("Please create this user (e.g., `python manage.py createsuperuser`) or change the USERNAME variable in this script.")
        return

    print("Deleting old journal data...")
    # Optional: Clear existing entries for the user to avoid duplicates
    JournalEntry.objects.filter(user=user).delete()

    print("Creating new tags...")
    tag_map = {}
    for tag_name in sample_tags:
        tag, _ = Tag.objects.get_or_create(name=tag_name)
        tag_map[tag_name] = tag

    print(f"Creating {len(sample_entries)} new journal entries for user '{user.username}'...")

    for data in sample_entries:
        entry = JournalEntry.objects.create(
            user=user,
            title=data["title"],
            content=data["content"],
            mood=data["mood"],
            is_favorite=data["is_favorite"]
        )

        # Add tags to the entry
        for tag_name in data["tags"]:
            if tag_name in tag_map:
                entry.tags.add(tag_map[tag_name])
            else:
                new_tag, _ = Tag.objects.get_or_create(name=tag_name)
                entry.tags.add(new_tag)
                tag_map[tag_name] = new_tag

    print("\n✅ Seeding complete!")
    print(f"Log in as '{USERNAME}' to see the new journal entries.")

# Execute the function
run_seed()

from django.contrib import admin
from .models import JournalEntry, Tag

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin configuration for the Tag model."""
    search_fields = ('name',)

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    """Admin configuration for the JournalEntry model."""
    list_display = ('title', 'user', 'date_created', 'mood', 'is_favorite')
    list_filter = ('mood', 'is_favorite', 'date_created', 'user')
    search_fields = ('title', 'content')
    raw_id_fields = ('user',)
    date_hierarchy = 'date_created'
    ordering = ('-date_created',)

    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'content')
        }),
        ('Metadata', {
            'fields': ('mood', 'tags', 'is_favorite')
        }),
    )

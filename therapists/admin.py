from django.contrib import admin
from .models import Therapist

class TherapistAdmin(admin.ModelAdmin):
    list_display = ['name', 'specialization', 'experience', 'available']
    search_fields = ['name', 'specialization']
    list_filter = ['specialization', 'experience', 'available']
    
admin.site.register(Therapist, TherapistAdmin)

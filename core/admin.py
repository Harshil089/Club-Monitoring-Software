from django.contrib import admin
from .models import Club, Semester, Event, Ranking, AuditLog
from django.utils.html import format_html

@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_code', 'faculty_incharge', 'student_lead')
    search_fields = ('name', 'short_code')

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_editable = ('is_active',)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'club', 'semester', 'date', 'total_score')
    list_filter = ('semester', 'club')
    search_fields = ('name', 'club__name')
    fieldsets = (
        (None, {
            'fields': ('club', 'semester', 'name', 'date')
        }),
        ('Turnout', {
            'fields': ('expected_turnout', 'actual_turnout')
        }),
        ('Scoring (0-20)', {
            'fields': ('planning_score', 'execution_score', 'documentation_score', 'innovation_score', 'turnout_score'),
            'description': 'Enter scores between 0 and 20 for each metric.'
        }),
    )

@admin.register(Ranking)
class RankingAdmin(admin.ModelAdmin):
    list_display = ('rank', 'club', 'semester', 'cps', 'tier', 'event_count')
    list_filter = ('semester', 'tier')
    readonly_fields = ('cps', 'tier', 'rank', 'event_count', 'avg_planning', 'avg_execution', 'avg_documentation', 'avg_innovation', 'avg_turnout')

    def has_add_permission(self, request):
        return False # Rankings are auto-generated

    def has_change_permission(self, request, obj=None):
        return False # Read-only in admin

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'details_short')
    readonly_fields = ('user', 'action', 'timestamp', 'details')
    list_filter = ('action', 'user')

    def details_short(self, obj):
        return obj.details[:50]

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

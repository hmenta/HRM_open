from django.contrib import admin
from .models import Position, Candidate, Application, StageLog

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("title", "client", "status", "owner", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "client", "description")

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "current_title", "source", "created_at")
    list_filter = ("source", "consent_given", "created_at")
    search_fields = ("first_name", "last_name", "email", "skills")

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("candidate", "position", "stage", "updated_at")
    list_filter = ("stage", "created_at")

@admin.register(StageLog)
class StageLogAdmin(admin.ModelAdmin):
    list_display = ("application", "from_stage", "to_stage", "changed_by", "changed_at")
    list_filter = ("to_stage", "changed_at")
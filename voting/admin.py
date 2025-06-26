from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, VoterProfile, CandidateProfile, Election, Vote

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role',)}),
    )

@admin.register(VoterProfile)
class VoterProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'has_voted', 'email_verified')
    list_filter = ('has_voted', 'email_verified')
    search_fields = ('user__username', 'user__email')

@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'votes_received')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('votes_received',)

@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('voter', 'candidate', 'election', 'timestamp')
    list_filter = ('election', 'timestamp')
    search_fields = ('voter__user__username', 'candidate__user__username')
    readonly_fields = ('timestamp',)
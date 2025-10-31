from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, VoterProfile, CandidateProfile, Election, Vote, LoginToken

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
    list_display = ('user', 'slogan', 'votes_received')
    search_fields = ('user__username', 'user__email', 'slogan')
    readonly_fields = ('votes_received',)
    fields = ('user', 'slogan', 'manifesto', 'votes_received')
    
    # Optional: Show slogan preview in list
    def slogan_preview(self, obj):
        return obj.slogan[:50] + '...' if len(obj.slogan) > 50 else obj.slogan
    slogan_preview.short_description = 'Slogan'

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
@admin.register(LoginToken)
class LoginTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token_preview', 'created_at', 'expires_at', 'is_used', 'used_at')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'user__username', 'token')
    readonly_fields = ('token', 'created_at', 'used_at')
    date_hierarchy = 'created_at'
    
    def token_preview(self, obj):
        '''Show first 16 characters of token for preview'''
        return f"{obj.token[:16]}..." if obj.token else ""
    token_preview.short_description = 'Token Preview'
    
    actions = ['cleanup_expired_tokens']
    
    def cleanup_expired_tokens(self, request, queryset):
        '''Admin action to cleanup expired tokens'''
        LoginToken.cleanup_expired()
        self.message_user(request, "Expired and used tokens cleaned up successfully.")
    cleanup_expired_tokens.short_description = "Clean up expired/used tokens"

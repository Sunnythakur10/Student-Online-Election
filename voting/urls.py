from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('send-verification/', views.send_verification_view, name='send_verification'),
    path('verify-login/', views.verify_login_view, name='verify_login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('vote/', views.vote_view, name='vote'),
    path('submit-vote/', views.submit_vote_view, name='submit_vote'),
    path('results/', views.election_results, name='election_results'),
    path('results/<int:election_id>/', views.election_results, name='election_results_specific'),
    path('candidate/dashboard/', views.candidate_dashboard_view, name='candidate_dashboard'),
    path('candidate/profile/', views.candidate_profile_view, name='candidate_profile'),
    path('admin-panel/', views.admin_panel_view, name='admin_panel'),
    path('promote-candidate/', views.promote_candidate_view, name='promote_candidate'),
    path('logout/', views.logout_view, name='logout'),
    path('manage-elections/', views.manage_elections_view, name='manage_elections'),
    path('create-election/', views.create_election_view, name='create_election'),
    path('toggle-election/<int:election_id>/', views.toggle_election_status_view, name='toggle_election'),
    path('delete-election/<int:election_id>/', views.delete_election_view, name='delete_election'),
]

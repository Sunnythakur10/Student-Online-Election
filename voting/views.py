from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.signing import Signer, BadSignature
import secrets
from .models import CustomUser, VoterProfile, CandidateProfile, Election, Vote, LoginToken
from django.contrib import messages
from django.urls import reverse

# ===============================================
# Basic Views
# ===============================================

def login_view(request):
    return render(request, 'voting/login.html')

def register_view(request):
    if request.method == 'GET':
        return render(request, 'voting/register.html')
    
    name = request.POST.get('name')
    email = request.POST.get('email')
    branch = request.POST.get('branch')
    year_of_study = request.POST.get('year_of_study')

    if not name or not email or not branch or not year_of_study:
        messages.error(request, 'All fields are required.')
        return render(request, 'voting/register.html')
    
    if CustomUser.objects.filter(email=email).exists():
        messages.error(request, 'An account with this email already exists.')
        return render(request, 'voting/register.html')

    username = email.split('@')[0]
    counter = 1
    original_username = username
    while CustomUser.objects.filter(username=username).exists():
        username = f"{original_username}{counter}"
        counter += 1

    try:
        name_parts = name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password='defaultpassword123',
            first_name=first_name,
            last_name=last_name,
            role='voter',
            branch=branch,
            year_of_study=year_of_study
        )

        print("this is working")
        messages.success(request, 'Registration successful! You can now log in.')
        return redirect('login')

    except Exception as e:
        messages.error(request, f'Registration failed: {str(e)}')
        return render(request, 'voting/register.html')
    

def send_verification_view(request):
    """
    Send email login link with secure token.
    Uses LoginToken model for stateless, expiring, single-use tokens.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            
            # Create a new login token (15 minute expiry by default)
            login_token = LoginToken.create_token(user, expiry_minutes=15)
            
            # Sign the token for additional security (prevents tampering)
            signer = Signer()
            signed_token = signer.sign(login_token.token)
            
            # Build verification URL with signed token
            verification_url = f"{request.build_absolute_uri('/verify-login/')}?token={signed_token}"
            
            # Send email with timeout and error handling
            try:
                send_mail(
                    'Login Link - Voting System',
                    f'Click this link to login: {verification_url}\n\nThis link will expire in 15 minutes and can only be used once.',
                    settings.EMAIL_HOST_USER if hasattr(settings, 'EMAIL_HOST_USER') else 'noreply@votingsystem.com',
                    [email],
                    fail_silently=False,
                )
                messages.success(request, 'Verification link sent! Check your email. Link expires in 15 minutes.')
            except Exception as email_error:
                # If email fails, show the link in the message (development fallback)
                print(f"Email error: {email_error}")
                print(f"Login link for {email}: {verification_url}")
                if settings.DEBUG:
                    messages.warning(request, f'Email failed. Development link: {verification_url}')
                else:
                    messages.error(request, 'Failed to send email. Please try again or contact support.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'Email not found.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    return redirect('login')

def verify_login_view(request):
    """
    Verify login token from email link.
    Validates signature, checks token validity, enforces single-use.
    """
    signed_token = request.GET.get('token')
    
    if not signed_token:
        messages.error(request, 'No token provided.')
        return redirect('login')
    
    try:
        # Verify signature
        signer = Signer()
        token = signer.unsign(signed_token)
        
        # Look up token in database
        try:
            login_token = LoginToken.objects.get(token=token)
        except LoginToken.DoesNotExist:
            messages.error(request, 'Invalid login link.')
            return redirect('login')
        
        # Check if token is valid (not expired, not used)
        if not login_token.is_valid():
            if login_token.is_used:
                messages.error(request, 'This login link has already been used.')
            else:
                messages.error(request, 'This login link has expired.')
            return redirect('login')
        
        # Mark token as used (single-use enforcement)
        login_token.mark_as_used()
        
        # Log the user in
        user = login_token.user
        login(request, user)
        
        messages.success(request, f'Welcome back, {user.first_name or user.username}!')
        
        # Redirect based on role
        if user.role == 'candidate':
            return redirect('/candidate/dashboard/')
        # All users (including admins) go to dashboard
        return redirect('dashboard')
        
    except BadSignature:
        messages.error(request, 'Invalid or tampered login link.')
        return redirect('login')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('login')

@login_required
def dashboard_view(request):
    user = request.user
    has_voted = False
    
    if user.role == 'voter':
        try:
            voter_profile = VoterProfile.objects.get(user=user)
            active_elections = Election.objects.filter(is_active=True)
            has_voted = any(Vote.objects.filter(voter=voter_profile, election=e).exists() 
                          for e in active_elections)
        except VoterProfile.DoesNotExist:
            pass
    
    context = {
        'user': {
            'name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'is_admin': user.role == 'admin',
            'is_candidate': user.role == 'candidate',
            'has_voted': has_voted
        }
    }
    return render(request, 'voting/dashboard.html', context)

# ===============================================
# Admin Views
# ===============================================

def admin_required(view_func):
    """Decorator to check admin access"""
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'admin':
            messages.error(request, 'Admin access required.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@admin_required
def manage_elections_view(request):
    context = {
        'elections': Election.objects.all().order_by('-start_date'),
        'candidates': CandidateProfile.objects.all()
    }
    return render(request, 'voting/manage_elections.html', context)

@login_required
@admin_required
def create_election_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        try:
            from django.utils.dateparse import parse_datetime
            start_datetime = parse_datetime(start_date)
            end_datetime = parse_datetime(end_date)
            
            if start_datetime >= end_datetime:
                messages.error(request, 'End date must be after start date.')
                return redirect('manage_elections')
            
            Election.objects.all().update(is_active=False)  # Deactivate others
            Election.objects.create(
                name=title,
                start_date=start_datetime,
                end_date=end_datetime,
                is_active=True
            )
            messages.success(request, f'Election "{title}" created!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('manage_elections')

@login_required
@admin_required
def toggle_election_status_view(request, election_id):
    try:
        election = Election.objects.get(id=election_id)
        if not election.is_active:
            Election.objects.all().update(is_active=False)
            election.is_active = True
        else:
            election.is_active = False
        election.save()
        
        status = "activated" if election.is_active else "deactivated"
        messages.success(request, f'Election {status}.')
    except Election.DoesNotExist:
        messages.error(request, 'Election not found.')
    return redirect('manage_elections')

@login_required
@admin_required
def delete_election_view(request, election_id):
    try:
        election = Election.objects.get(id=election_id)
        election.delete()
        messages.success(request, 'Election deleted.')
    except Election.DoesNotExist:
        messages.error(request, 'Election not found.')
    return redirect('manage_elections')

@login_required
@admin_required
def admin_panel_view(request):
    voters = CustomUser.objects.filter(role='voter', year_of_study__in=['3', '4'])
    return render(request, 'voting/admin_panel.html', {'voters': voters})

@login_required
@admin_required
def promote_candidate_view(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        try:
            user = CustomUser.objects.get(id=user_id)
            user.role = 'candidate'
            user.save()
            CandidateProfile.objects.get_or_create(user=user)
            messages.success(request, f'{user.first_name} {user.last_name} promoted to candidate.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    return redirect('admin_panel')

# ===============================================
# Candidate Views
# ===============================================

def candidate_required(view_func):
    """Decorator to check candidate access"""
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'candidate':
            messages.error(request, 'Only candidates can access this page.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@candidate_required
def candidate_dashboard_view(request):
    """Candidate dashboard showing profile and stats"""
    try:
        candidate_profile = CandidateProfile.objects.get(user=request.user)
        
        # Get current vote count
        current_votes = Vote.objects.filter(candidate=candidate_profile).count()
        
        # Get active election info
        active_election = Election.objects.filter(is_active=True).first()
        
        context = {
            'candidate_profile': candidate_profile,
            'current_votes': current_votes,
            'active_election': active_election,
            'user_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
        }
        return render(request, 'voting/candidate_dashboard.html', context)
        
    except CandidateProfile.DoesNotExist:
        messages.error(request, 'Candidate profile not found.')
        return redirect('dashboard')

@login_required
@candidate_required
def candidate_profile_view(request):
    """View and edit candidate profile"""
    try:
        candidate_profile = CandidateProfile.objects.get(user=request.user)
    except CandidateProfile.DoesNotExist:
        messages.error(request, 'Candidate profile not found.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Update profile fields
        manifesto = request.POST.get('manifesto', '').strip()
        slogan = request.POST.get('slogan', '').strip()
        
        candidate_profile.manifesto = manifesto
        candidate_profile.slogan = slogan
        candidate_profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('candidate_dashboard')
    
    context = {
        'candidate_profile': candidate_profile,
        'user_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
    }
    return render(request, 'voting/candidate_profile.html', context)

# ===============================================
# Voting Views
# ===============================================

def voter_required(view_func):
    """Decorator to check voter access"""
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'voter':
            messages.error(request, 'Only voters can access this page.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@voter_required
def vote_view(request):
    try:
        voter_profile = VoterProfile.objects.get(user=request.user)
        active_election = Election.objects.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).first()
        
        if not active_election:
            messages.error(request, 'No active elections.')
            return redirect('dashboard')
        
        if Vote.objects.filter(voter=voter_profile, election=active_election).exists():
            messages.error(request, 'You have already voted.')
            return redirect('dashboard')
        
        candidates = []
        for c in CandidateProfile.objects.all():
            candidate_info = {
                'id': c.id,
                'name': f"{c.user.first_name} {c.user.last_name}".strip() or c.user.username,
                'party': getattr(c, 'party', 'Independent'),
                'slogan': getattr(c, 'slogan', ''),
                'manifesto': c.manifesto[:200] + '...' if len(c.manifesto) > 200 else c.manifesto
            }
            candidates.append(candidate_info)
        
        return render(request, 'voting/vote.html', {
            'candidates': candidates,
            'election': active_election
        })
    except VoterProfile.DoesNotExist:
        messages.error(request, 'Voter profile not found.')
        return redirect('dashboard')

@login_required
@voter_required
def submit_vote_view(request):
    if request.method != 'POST':
        return redirect('vote')
    
    try:
        voter_profile = VoterProfile.objects.get(user=request.user)
        candidate_id = request.POST.get('candidate_id')
        
        if not candidate_id:
            messages.error(request, 'Please select a candidate.')
            return redirect('vote')
        
        active_election = Election.objects.filter(is_active=True).first()
        if not active_election:
            messages.error(request, 'No active elections.')
            return redirect('dashboard')
        
        candidate = get_object_or_404(CandidateProfile, id=candidate_id)
        
        if Vote.objects.filter(voter=voter_profile, election=active_election).exists():
            messages.error(request, 'You have already voted.')
            return redirect('dashboard')
        
        with transaction.atomic():
            Vote.objects.create(
                voter=voter_profile,
                candidate=candidate,
                election=active_election
            )
            if hasattr(voter_profile, 'has_voted'):
                voter_profile.has_voted = True
                voter_profile.save()
        
        return render(request, 'voting/vote_success.html')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('vote')

@login_required
def election_results(request, election_id=None):
    election = (get_object_or_404(Election, id=election_id) if election_id 
               else Election.objects.filter(is_active=True).first())
    
    if not election:
        return render(request, 'voting/no_active_election.html')
    
    if request.user.role != 'admin' and not election.has_ended():
        raise PermissionDenied("Results viewable by admins only or after election ends.")
    
    candidates_with_votes = []
    for candidate in CandidateProfile.objects.all():
        vote_count = Vote.objects.filter(candidate=candidate, election=election).count()
        candidates_with_votes.append({
            'candidate': candidate,
            'votes': vote_count,
            'percentage': 0
        })
    
    total_votes = sum(item['votes'] for item in candidates_with_votes)
    for item in candidates_with_votes:
        if total_votes > 0:
            item['percentage'] = round((item['votes'] / total_votes) * 100, 2)
    
    candidates_with_votes.sort(key=lambda x: x['votes'], reverse=True)
    
    total_eligible_voters = VoterProfile.objects.count()
    voter_turnout = round((total_votes / total_eligible_voters) * 100, 2) if total_eligible_voters > 0 else 0
    
    return render(request, 'voting/results.html', {
        'election': election,
        'candidates_with_votes': candidates_with_votes,
        'total_votes': total_votes,
        'total_eligible_voters': total_eligible_voters,
        'voter_turnout': voter_turnout,
        'election_ended': election.has_ended(),
        'election_active': election.is_voting_open(),
    })

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('login')
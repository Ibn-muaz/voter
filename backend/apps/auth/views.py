from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from .forms import LoginForm
from .models import UserSession


def login_view(request):
    """
    Handle user login with session tracking.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user is not None and user.is_active_officer:
                login(request, user)

                # Create session record
                UserSession.objects.create(
                    user=user,
                    session_key=request.session.session_key,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                )

                # Update last login IP
                user.last_login_ip = get_client_ip(request)
                user.save(update_fields=['last_login_ip'])

                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid credentials or account is inactive.')
    else:
        form = LoginForm()

    return render(request, 'auth/login.html', {'form': form})


@login_required
def logout_view(request):
    """
    Handle user logout with session cleanup.
    """
    # Update session record
    try:
        session = UserSession.objects.get(
            user=request.user,
            session_key=request.session.session_key,
            is_active=True
        )
        session.logout_time = timezone.now()
        session.is_active = False
        session.save()
    except UserSession.DoesNotExist:
        pass

    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def dashboard(request):
    """
    Admin dashboard view.
    """
    context = {
        'user': request.user,
        'role': request.user.get_role_display(),
    }
    return render(request, 'admin/dashboard.html', context)


def get_client_ip(request):
    """
    Get the client's IP address from the request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
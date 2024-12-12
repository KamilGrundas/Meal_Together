from django.shortcuts import render, redirect


def redirect_to_sessions_or_login(request):
    if request.user.is_authenticated:
        return redirect('session_list')
    return redirect('login')

def no_permission_view(request):
    return render(request, 'general/no_permission.html', status=403)


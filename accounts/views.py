from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import capability_required
from .forms import ManagedUserCreationForm, ManagedUserUpdateForm
from .roles import can_manage_users, ensure_role_groups, get_user_role, set_user_role

User = get_user_model()


@capability_required(can_manage_users)
def user_list_view(request):
    ensure_role_groups()
    query = request.GET.get('q', '').strip()
    users = User.objects.all().order_by('username')
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    rows = []
    for user in users:
        rows.append({
            'user': user,
            'role': get_user_role(user) or 'Sin rol',
        })

    return render(request, 'accounts/user_list.html', {
        'rows': rows,
        'query': query,
    })


@capability_required(can_manage_users)
def user_create_view(request):
    ensure_role_groups()
    if request.method == 'POST':
        form = ManagedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            set_user_role(user, form.cleaned_data['role'])
            messages.success(request, f'Usuario “{user.username}” creado correctamente.')
            return redirect('user_list')
    else:
        form = ManagedUserCreationForm()

    return render(request, 'accounts/user_form.html', {
        'form': form,
        'action': 'Crear',
        'title': 'Nuevo usuario',
    })


@capability_required(can_manage_users)
def user_update_view(request, pk):
    ensure_role_groups()
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = ManagedUserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            new_password = form.cleaned_data.get('new_password')
            if new_password:
                user.set_password(new_password)
            user.save()
            set_user_role(user, form.cleaned_data['role'])
            messages.success(request, f'Usuario “{user.username}” actualizado.')
            return redirect('user_list')
    else:
        form = ManagedUserUpdateForm(instance=user)

    return render(request, 'accounts/user_form.html', {
        'form': form,
        'action': 'Guardar',
        'title': f'Editar usuario: {user.username}',
        'edited_user': user,
    })


@capability_required(can_manage_users)
def user_toggle_active_view(request, pk):
    if request.method != 'POST':
        return redirect('user_list')

    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'No podés desactivar tu propio usuario.')
        return redirect('user_list')

    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    estado = 'activado' if user.is_active else 'desactivado'
    messages.success(request, f'Usuario “{user.username}” {estado}.')
    return redirect('user_list')

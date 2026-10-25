from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q
from .models import Employee
from .forms import EmployeeForm

@login_required
def dashboard_view(request):
    total_employees = Employee.objects.filter(is_active=True).count()
    context = {
        'total_employees': total_employees,
    }
    return render(request, 'dashboard/index.html', context)

@login_required
def employee_list_view(request):
    query = request.GET.get('q', '')
    employees = Employee.objects.all()
    if query:
        employees = employees.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(position__icontains=query) |
            Q(department__icontains=query) |
            Q(dni__icontains=query) |
            Q(employee_leg__icontains=query)
        )
    return render(request, 'employees/employee_list.html', {'employees': employees, 'query': query})

@login_required
def employee_create_view(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'action': 'Crear'})

@login_required
def employee_update_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'employees/employee_form.html', {'form': form, 'action': 'Editar'})
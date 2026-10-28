from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Employee
from .forms import EmployeeForm


# ==========================================
# 0. VISTA DEL PANEL PRINCIPAL (DASHBOARD)
# ==========================================
@login_required
def dashboard_view(request):
    """
    Renderiza y dirige al panel principal (dashboard) del sistema.
    """
    return render(request, 'dashboard.html')


# ==========================================
# 1. VISTA DE LISTADO Y BUSCADOR DE LEGAJOS
# ==========================================
@login_required
def employee_list_view(request):
    """
    Muestra la lista de todos los empleados y permite filtrar 
    según el término de búsqueda ingresado (nombre, apellido, cargo, DNI, legajo).
    """
    query = request.GET.get('q', '')
    
    if query:
        employees = Employee.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(position__icontains=query) |
            Q(dni__icontains=query) |
            Q(employee_leg__icontains=query)
        )
    else:
        employees = Employee.objects.all()
        
    return render(request, 'employees/employee_list.html', {'employees': employees, 'query': query})


# ==========================================
# 2. VISTA DE CREACIÓN DE NUEVO LEGAJO
# ==========================================
@login_required
def employee_create_view(request):
    """
    Gestiona el formulario para dar de alta un nuevo empleado.
    Procesa datos de texto y archivos multimedia (request.FILES).
    """
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm()
        
    return render(request, 'employees/employee_form.html', {'form': form, 'action': 'Crear'})


# ==========================================
# 3. VISTA DE EDICIÓN DE LEGAJO EXISTENTE
# ==========================================
@login_required
def employee_update_view(request, pk):
    """
    Permite modificar los datos y archivos de un empleado específico.
    Utiliza 'instance=employee' para actualizar en lugar de duplicar.
    """
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=employee)
        
    return render(request, 'employees/employee_form.html', {
        'form': form, 
        'action': 'Editar', 
        'employee': employee
    })


# ==========================================
# 4. VISTA DE DETALLE / VISUALIZACIÓN DE LEGAJO
# ==========================================
@login_required
def employee_detail_view(request, pk):
    """
    Muestra la ficha completa y detallada de un empleado en modo lectura.
    """
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, 'employees/employee_detail.html', {'employee': employee})
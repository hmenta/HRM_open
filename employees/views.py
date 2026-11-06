from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Employee
from .forms import EmployeeForm, EmployeeDocumentFormSet
from .models import AbsenceCertificate, AbsenceCertificateDocument
from .forms import AbsenceCertificateForm, AbsenceDocumentFormSet


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
    Gestiona el formulario para dar de alta un nuevo empleado junto con 
    su respectivo formset de múltiples documentos adjuntos.
    """
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        formset = EmployeeDocumentFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            employee = form.save()          # Guardamos primero el empleado principal
            formset.instance = employee     # Vinculamos el formset con el empleado recién creado
            formset.save()                  # Guardamos los documentos adjuntos
            return redirect('employee_detail', pk=employee.pk)
    else:
        form = EmployeeForm()
        formset = EmployeeDocumentFormSet()
        
    return render(request, 'employees/employee_form.html', {
        'form': form, 
        'formset': formset, 
        'action': 'Crear'
    })


# ==========================================
# 3. VISTA DE EDICIÓN DE LEGAJO EXISTENTE
# ==========================================
@login_required
def employee_update_view(request, pk):
    """
    Permite modificar los datos, la foto y los documentos múltiples de un empleado específico.
    Utiliza 'instance=employee' para actualizar en lugar de duplicar registros.
    """
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        formset = EmployeeDocumentFormSet(request.POST, request.FILES, instance=employee)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('employee_detail', pk=employee.pk)
    else:
        form = EmployeeForm(instance=employee)
        formset = EmployeeDocumentFormSet(instance=employee)
        
    return render(request, 'employees/employee_form.html', {
        'form': form, 
        'formset': formset,
        'action': 'Editar', 
        'employee': employee
    })


# ==========================================
# 4. VISTA DE DETALLE / VISUALIZACIÓN DE LEGAJO
# ==========================================
@login_required
def employee_detail_view(request, pk):
    """
    Muestra la ficha completa y detallada de un empleado en modo lectura,
    incluyendo el listado de documentos múltiples adjuntos.
    """
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, 'employees/employee_detail.html', {'employee': employee})

# ==========================================
# 5. VISTA GRAL. DEL PANEL DE AUSENCIAS
# ==========================================

@login_required
def absence_list_view(request):
    """Panel principal de ausencias con búsqueda por Legajo (ID) o Nombre/Apellido"""
    query = request.GET.get('q', '').strip()
    certificates = AbsenceCertificate.objects.select_related('employee').all()

    if query:
        certificates = certificates.filter(
            Q(employee__id__exact=query if query.isdigit() else None) |
            Q(employee__first_name__icontains=query) |
            Q(employee__last_name__icontains=query) |
            Q(employee__dni__icontains=query)
        )

    context = {
        'certificates': certificates,
        'query': query,
    }
    return render(request, 'absences/absence_list.html', context)

# Ver detalle del certificado.
@login_required
def absence_detail_view(request, pk):
    certificate = get_object_or_404(AbsenceCertificate, pk=pk)
    return render(request, 'absences/absence_detail.html', {'certificate': certificate})


# ==========================================
# 5. VISTA DEL PANEL DE CARGA DE CERTIFICADOS DE AUSENCIAS
# ==========================================

'''OLD 
# Editar el detalle.
@login_required
def absence_update_view(request, pk):
    certificate = get_object_or_404(AbsenceCertificate, pk=pk)
    
    if request.method == 'POST':
        form = AbsenceCertificateForm(request.POST, request.FILES, instance=certificate)
        formset = AbsenceDocumentFormSet(request.POST, request.FILES, instance=certificate)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('absence_detail', pk=certificate.pk)
    else:
        # Pasa la instancia tanto al form como al formset para mantener los datos y adjuntos existentes
        form = AbsenceCertificateForm(instance=certificate)
        formset = AbsenceDocumentFormSet(instance=certificate)
    
    return render(request, 'absences/absence_form.html', {
        'form': form, 
        'formset': formset, 
        'certificate': certificate
    })


@login_required
def absence_create_view(request):
    """Vista de alta de certificado de ausencia con carga de adjuntos múltiples"""
    employee_id = request.GET.get('employee_id')
    initial_data = {}
    
    if employee_id:
        employee = get_object_or_404(Employee, id=employee_id)
        initial_data['employee'] = employee

    if request.method == 'POST':
        form = AbsenceCertificateForm(request.POST)
        formset = AbsenceDocumentFormSet(request.POST, request.FILES)
        
        if form.is_valid():
            certificate = form.save()
            formset = AbsenceDocumentFormSet(request.POST, request.FILES, instance=certificate)
            if formset.is_valid():
                formset.save()
                return redirect('absence_list')
    else:
        form = AbsenceCertificateForm(initial=initial_data)
        formset = AbsenceDocumentFormSet()

    context = {
        'form': form,
        'formset': formset,
    }
    return render(request, 'absences/absence_form.html', context)
'''

@login_required
def absence_create_view(request):
    if request.method == 'POST':
        form = AbsenceCertificateForm(request.POST, request.FILES)
        formset = AbsenceDocumentFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            certificate = form.save()
            formset.instance = certificate
            formset.save()
            return redirect('absence_list')
    else:
        form = AbsenceCertificateForm()
        formset = AbsenceDocumentFormSet()
        
    return render(request, 'absences/absence_form.html', {
        'form': form,
        'formset': formset
    })

@login_required
def absence_update_view(request, pk):
    certificate = get_object_or_404(AbsenceCertificate, pk=pk)
    if request.method == 'POST':
        form = AbsenceCertificateForm(request.POST, request.FILES, instance=certificate)
        formset = AbsenceDocumentFormSet(request.POST, request.FILES, instance=certificate)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('absence_detail', pk=certificate.pk)
    else:
        form = AbsenceCertificateForm(instance=certificate)
        formset = AbsenceDocumentFormSet(instance=certificate)
        
    return render(request, 'absences/absence_form.html', {
        'form': form,
        'formset': formset,
        'certificate': certificate
    })
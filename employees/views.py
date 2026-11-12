from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Employee
from .forms import EmployeeForm, EmployeeDocumentFormSet
from .models import AbsenceCertificate, AbsenceCertificateDocument
from .forms import AbsenceCertificateForm, AbsenceDocumentFormSet

# ESPECIFICOS PARA EXPORTACION E IMPORTACION DE DATOS #
import csv
import io
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render
from .forms import CSVImportForm


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

#####################################################################
# --- FUNCIONES DE EXPORTACIÓN E IMPORTACIÓN DE DATOS - LEGAJOS --- #
#####################################################################

from django.contrib.admin.views.decorators import staff_member_required

@login_required
@staff_member_required
def export_employees_csv(request):
    """Exporta todos los empleados activos/inactivos a un CSV UTF-8 compatible con Excel."""
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="empleados_hrm.csv"'
    
    writer = csv.writer(response, delimiter=';')
    # Cabeceras del CSV
    writer.writerow([
        'Legajo', 'DNI', 'CUIL', 'Nombre', 'Apellido', 'Email', 
        'Teléfono', 'Puesto', 'Ciudad', 'Activo', 'Fecha Ingreso'
    ])
    
    employees = Employee.objects.all().values_list(
        'employee_leg', 'dni', 'cuil', 'first_name', 'last_name', 
        'email', 'phone', 'position', 'city', 'is_active', 'hire_date'
    )
    
    for emp in employees:
        writer.writerow(emp)
        
    return response


@login_required
@staff_member_required
def import_employees_csv(request):
    """Importa empleados masivamente desde un archivo CSV con delimitador por punto y coma o coma."""
    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            # Validar extensión
            if not csv_file.name.endswith('.csv'):
                messages.error(request, "El archivo debe tener formato .csv")
                return redirect('import_employees_csv')
            
            try:
                # Decodificar el archivo respetando UTF-8 - se utiliza sig para que no se rompa por los caracteres latinos.
                decoded_file = csv_file.read().decode('utf-8-sig')
                io_string = io.StringIO(decoded_file)
                
                # Detectar delimitador automáticamente (coma o punto y coma)
                sample = io_string.read(2048)
                io_string.seek(0)
                sniffer = csv.Sniffer()
                delimiter = ';' if ';' in sample else ','
                
                reader = csv.reader(io_string, delimiter=delimiter)
                header = next(reader) # Saltar cabecera
                
                success_count = 0
                error_count = 0
                
                with transaction.atomic():
                    for row in reader:
                        if not row or len(row) < 5:
                            continue
                        try:
                            # Mapeo básico de columnas esperadas:
                            # [Legajo, DNI, CUIL, Nombre, Apellido, Email, Teléfono, Puesto, Ciudad, Activo, Fecha Ingreso]
                            leg, dni, cuil, first_name, last_name = row[0], row[1], row[2], row[3], row[4]
                            email = row[5] if len(row) > 5 else ''
                            phone = row[6] if len(row) > 6 else ''
                            position = row[7] if len(row) > 7 else ''
                            city = row[8] if len(row) > 8 else ''
                            is_active = True if (len(row) > 9 and row[9].lower() in ['true', '1', 'si', 'sí', 'yes']) else True
                            hire_date = row[10] if (len(row) > 10 and row[10]) else None
                            
                            Employee.objects.update_or_create(
                                dni=dni,
                                defaults={
                                    'employee_leg': leg,
                                    'cuil': cuil,
                                    'first_name': first_name,
                                    'last_name': last_name,
                                    'email': email,
                                    'phone': phone,
                                    'position': position,
                                    'city': city,
                                    'is_active': is_active,
                                    'hire_date': hire_date if hire_date else None,
                                }
                            )
                            success_count += 1
                        except Exception as e:
                            error_count += 1
                            
                messages.success(request, f"Importación exitosa. Procesados correctamente: {success_count}. Errores: {error_count}.")
                return redirect('employee_list')
                
            except Exception as e:
                messages.error(request, f"Error al procesar el archivo CSV: {e}")
                return redirect('import_employees_csv')
    else:
        form = CSVImportForm()
        
    return render(request, 'employees/csv_import.html', {'form': form, 'title': 'Importar Empleados desde CSV'})

###############################################################
## --- TEMPLATE PARA DESCARGA E IMPORTACIÓN DE EMPLEADOS --- ##
###############################################################


@login_required
@staff_member_required
def download_employee_template(request):
    """Genera y descarga un archivo CSV modelo para la importación masiva de empleados."""
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="plantilla_empleados_hrm.csv"'
    
    writer = csv.writer(response, delimiter=';')
    
    # Cabeceras requeridas por el importador
    writer.writerow([
        'Legajo', 'DNI', 'CUIL', 'Nombre', 'Apellido', 'Email', 
        'Teléfono', 'Puesto', 'Ciudad', 'Activo', 'Fecha Ingreso'
    ])
    
    # Fila de ejemplo orientativa para el usuario
    writer.writerow([
        'LEG-001', '35123456', '20-35123456-9', 'Juan', 'Pérez', 'juan.perez@example.com', 
        '1122334455', 'Analista de RRHH', 'Buenos Aires', 'True', '2025-01-15'
    ])
    
    return response

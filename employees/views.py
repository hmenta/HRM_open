from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from accounts.decorators import capability_required
from accounts.roles import (
    can_manage_absences,
    can_manage_employees,
    can_import_export_employees,
    can_view_reports,
    can_view_payslips,
    can_upload_payslips,
)
from .models import Employee, Payslip
from .forms import EmployeeForm, EmployeeDocumentFormSet
from .models import AbsenceCertificate, AbsenceCertificateDocument
from .forms import (
    AbsenceCertificateForm,
    AbsenceDocumentFormSet,
    PayslipUploadForm,
    PayslipBulkUploadForm,
)
from .payslip_matching import build_employee_lookup, iter_pdf_uploads, match_employee_for_filename

# ESPECIFICOS PARA EXPORTACION E IMPORTACION DE DATOS #
import csv
import io
from django.contrib import messages
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import redirect, render
from django.core.exceptions import PermissionDenied
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
EMPLOYEE_SORT_FIELDS: dict[str, str] = {
    "leg": "employee_leg",
    "-leg": "-employee_leg",
    "name": "last_name",
    "-name": "-last_name",
    "position": "position",
    "-position": "-position",
    "hire_date": "hire_date",
    "-hire_date": "-hire_date",
    "status": "is_active",
    "-status": "-is_active",
}

EMPLOYEE_SORT_OPTIONS: list[tuple[str, str]] = [
    ("name", "Apellido y Nombre (A-Z)"),
    ("-name", "Apellido y Nombre (Z-A)"),
    ("leg", "Legajo (ascendente)"),
    ("-leg", "Legajo (descendente)"),
    ("-hire_date", "Fecha de ingreso (recientes primero)"),
    ("hire_date", "Fecha de ingreso (antiguas primero)"),
    ("position", "Cargo (A-Z)"),
    ("-position", "Cargo (Z-A)"),
    ("-status", "Estado (Activos primero)"),
    ("status", "Estado (Inactivos primero)"),
]


@capability_required(can_manage_employees)
def employee_list_view(request):
    """
    Muestra la lista de empleados con búsqueda, filtro por estado y ordenamiento seguro.
    """
    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    current_sort = request.GET.get("sort", "name").strip()

    employees = Employee.objects.all()

    if query:
        employees = employees.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(position__icontains=query) |
            Q(dni__icontains=query) |
            Q(employee_leg__icontains=query)
        )

    if status_filter == "active":
        employees = employees.filter(is_active=True)
    elif status_filter == "inactive":
        employees = employees.filter(is_active=False)

    order_field = EMPLOYEE_SORT_FIELDS.get(current_sort, "last_name")
    if order_field in ("last_name", "-last_name"):
        employees = employees.order_by(order_field, "first_name")
    else:
        employees = employees.order_by(order_field, "last_name", "first_name")

    return render(request, "employees/employee_list.html", {
        "employees": employees,
        "query": query,
        "status_filter": status_filter,
        "current_sort": current_sort,
        "sort_options": EMPLOYEE_SORT_OPTIONS,
    })


# ==========================================
# 2. VISTA DE CREACIÓN DE NUEVO LEGAJO
# ==========================================
@capability_required(can_manage_employees)
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
@capability_required(can_manage_employees)
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
@capability_required(can_manage_employees)
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

### -------- FILTRADO DE CERTIFICADOS DE AUSENCIAS ------ ###

ABSENCE_SORT_FIELDS: dict[str, str] = {
    "created_at": "created_at",
    "-created_at": "-created_at",
    "employee": "employee__last_name",
    "-employee": "-employee__last_name",
    "reason": "reason",
    "-reason": "-reason",
    "start_date": "start_date",
    "-start_date": "-start_date",
    "end_date": "end_date",
    "-end_date": "-end_date",
}

ABSENCE_SORT_OPTIONS: list[tuple[str, str]] = [
    ("-created_at", "Fecha de carga (recientes primero)"),
    ("created_at", "Fecha de carga (antiguas primero)"),
    ("-start_date", "Inicio ausencia (recientes primero)"),
    ("start_date", "Inicio ausencia (antiguas primero)"),
    ("-end_date", "Fin ausencia (recientes primero)"),
    ("end_date", "Fin ausencia (antiguas primero)"),
    ("employee", "Empleado (A-Z)"),
    ("-employee", "Empleado (Z-A)"),
    ("reason", "Motivo (A-Z)"),
    ("-reason", "Motivo (Z-A)"),
]


@capability_required(can_manage_absences)
def absence_list_view(request):
    """Panel principal de ausencias con búsqueda por Legajo (ID) o Nombre/Apellido y ordenamiento."""
    query = request.GET.get('q', '').strip()
    current_sort = request.GET.get('sort', '-created_at').strip()

    certificates = AbsenceCertificate.objects.select_related('employee').prefetch_related('documents')

    if query:
        certificates = certificates.filter(
            Q(employee__id__exact=query if query.isdigit() else None) |
            Q(employee__first_name__icontains=query) |
            Q(employee__last_name__icontains=query) |
            Q(employee__dni__icontains=query)
        )

    order_field = ABSENCE_SORT_FIELDS.get(current_sort, '-created_at')
    if order_field in ('employee__last_name', '-employee__last_name'):
        certificates = certificates.order_by(order_field, 'employee__first_name', '-created_at')
    else:
        certificates = certificates.order_by(order_field, '-id')

    context = {
        'certificates': certificates,
        'query': query,
        'current_sort': current_sort,
        'sort_options': ABSENCE_SORT_OPTIONS,
    }
    return render(request, 'absences/absence_list.html', context)




# ==========================================
# 5. VISTA DEL PANEL DE CARGA DE CERTIFICADOS DE AUSENCIAS
# ==========================================

@capability_required(can_manage_absences)
def absence_detail_view(request, pk):
    certificate = get_object_or_404(AbsenceCertificate, pk=pk)
    return render(request, 'absences/absence_detail.html', {'certificate': certificate})

'''OLD 
# Editar el detalle.
@capability_required(can_manage_absences)
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


@capability_required(can_manage_absences)
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

@capability_required(can_manage_absences)
def absence_create_view(request):
    if request.method == 'POST':
        form = AbsenceCertificateForm(request.POST, request.FILES)
        formset = AbsenceDocumentFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            certificate = form.save()
            formset.instance = certificate
            formset.save()
            try:
                from core.notifications import notify_certificate_uploaded
                notify_certificate_uploaded(certificate)
            except Exception:
                pass
            return redirect('absence_list')
    else:
        form = AbsenceCertificateForm()
        formset = AbsenceDocumentFormSet()
        
    return render(request, 'absences/absence_form.html', {
        'form': form,
        'formset': formset
    })

@capability_required(can_manage_absences)
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

@capability_required(can_import_export_employees)
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


@capability_required(can_import_export_employees)
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


@capability_required(can_import_export_employees)
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


# ==========================================
# REPORTES Y KPIs
# ==========================================
def _month_start_n_months_ago(today, months_back):
    """Devuelve el día 1 del mes correspondiente a `months_back` meses atrás."""
    from datetime import date
    year = today.year
    month = today.month - months_back
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


def _add_one_month(d):
    """Avanza un mes manteniendo el día 1."""
    from datetime import date
    if d.month == 12:
        return date(d.year + 1, 1, 1)
    return date(d.year, d.month + 1, 1)


@capability_required(can_view_reports)
def reports_view(request):
    """Panel de reportes: KPIs de nómina, rotación, contratación y ausentismo + gráficos."""
    import json
    from calendar import monthrange
    from collections import defaultdict
    from datetime import date
    from django.db.models import Count

    from recruitment.models import Application, StageLog

    today = date.today()
    period_start = _month_start_n_months_ago(today, 11)
    year_start = today.replace(month=1, day=1)

    employees = list(
        Employee.objects.select_related('area_rel').only(
            'id', 'hire_date', 'termination_date', 'is_active', 'area_rel__name'
        )
    )

    active_count = sum(1 for e in employees if e.is_active)
    inactive_count = sum(1 for e in employees if not e.is_active)
    total_headcount = len(employees)

    # Rotación anual: bajas en el año / nómina promedio * 100
    terminations_ytd = sum(
        1 for e in employees
        if e.termination_date and e.termination_date >= year_start and e.termination_date <= today
    )
    headcount_at_year_start = sum(
        1 for e in employees
        if e.hire_date and e.hire_date <= year_start
        and (not e.termination_date or e.termination_date > year_start)
    )
    avg_headcount = max((headcount_at_year_start + active_count) / 2, 1)
    turnover_rate = round((terminations_ytd / avg_headcount) * 100, 1)

    # Tiempo de contratación: promedio de días desde postulación hasta etapa "contratado"
    hire_days = []
    hired_logs = StageLog.objects.filter(to_stage=Application.Stage.HIRED).select_related('application')
    for log in hired_logs:
        start = log.application.created_at.date() if log.application and log.application.created_at else None
        end = log.changed_at.date() if log.changed_at else None
        if start and end and end >= start:
            hire_days.append((end - start).days)
    if not hire_days:
        for app in Application.objects.filter(stage=Application.Stage.HIRED):
            if app.created_at and app.updated_at:
                delta = (app.updated_at.date() - app.created_at.date()).days
                if delta >= 0:
                    hire_days.append(delta)
    avg_time_to_hire = round(sum(hire_days) / len(hire_days), 1) if hire_days else None

    # Ausentismo: días de ausencia YTD / (activos * días corridos del año) * 100
    absences = AbsenceCertificate.objects.filter(
        start_date__lte=today,
        end_date__gte=year_start,
    )
    absence_days = 0
    for abs_cert in absences:
        start = max(abs_cert.start_date, year_start)
        end = min(abs_cert.end_date, today)
        if end >= start:
            absence_days += (end - start).days + 1
    days_elapsed = (today - year_start).days + 1
    possible_days = max(active_count, 1) * days_elapsed
    absenteeism_rate = round((absence_days / possible_days) * 100, 2)

    # --- Serie mensual: activos vs inactivos (últimos 12 meses) ---
    month_names_es = [
        '', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
        'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic',
    ]
    month_labels = []
    active_series = []
    inactive_series = []
    cursor = period_start
    first_of_current = today.replace(day=1)
    while cursor <= first_of_current:
        last_day = date(cursor.year, cursor.month, monthrange(cursor.year, cursor.month)[1])
        if last_day > today:
            last_day = today
        month_labels.append(f'{month_names_es[cursor.month]} {cursor.year}')
        act = 0
        ina = 0
        for e in employees:
            if not e.hire_date or e.hire_date > last_day:
                continue
            if e.termination_date and e.termination_date <= last_day:
                ina += 1
            else:
                act += 1
        active_series.append(act)
        inactive_series.append(ina)
        cursor = _add_one_month(cursor)

    # --- Torta: nómina por área/departamento ---
    area_counts = defaultdict(int)
    for e in employees:
        if not e.is_active:
            continue
        label = e.area_rel.name if e.area_rel_id and e.area_rel else 'Sin área'
        area_counts[label] += 1
    if not area_counts and total_headcount:
        area_counts['Sin área'] = total_headcount
    area_labels = list(area_counts.keys())
    area_values = list(area_counts.values())

    # --- Reclutamiento por estado ---
    stage_map = dict(Application.Stage.choices)
    stage_qs = (
        Application.objects.values('stage')
        .annotate(total=Count('id'))
        .order_by('stage')
    )
    recruitment_labels = [stage_map.get(row['stage'], row['stage']) for row in stage_qs]
    recruitment_values = [row['total'] for row in stage_qs]

    context = {
        'kpi_total_nomina': active_count,
        'kpi_total_inactivos': inactive_count,
        'kpi_turnover': turnover_rate,
        'kpi_terminations_ytd': terminations_ytd,
        'kpi_time_to_hire': avg_time_to_hire,
        'kpi_absenteeism': absenteeism_rate,
        'kpi_absence_days': absence_days,
        'chart_months': json.dumps(month_labels, ensure_ascii=False),
        'chart_active': json.dumps(active_series),
        'chart_inactive': json.dumps(inactive_series),
        'chart_area_labels': json.dumps(area_labels, ensure_ascii=False),
        'chart_area_values': json.dumps(area_values),
        'chart_recruitment_labels': json.dumps(recruitment_labels, ensure_ascii=False),
        'chart_recruitment_values': json.dumps(recruitment_values),
    }
    return render(request, 'reports/reports.html', context)


# ==========================================
# RECIBOS DE SUELDO
# ==========================================

def _user_employee(user):
    return getattr(user, 'employee_profile', None)


def _can_access_payslip(user, payslip):
    if can_upload_payslips(user):
        return True
    emp = _user_employee(user)
    return bool(emp and payslip.employee_id == emp.id)


@capability_required(can_view_payslips)
def payslip_list_view(request):
    """Lista recibos: propios para colaborador; todos (filtrables) para admin/operador."""
    can_upload = can_upload_payslips(request.user)
    qs = Payslip.objects.select_related('employee').order_by('-year', '-month', 'employee__last_name')

    if can_upload:
        q = request.GET.get('q', '').strip()
        year = request.GET.get('year', '').strip()
        month = request.GET.get('month', '').strip()
        if q:
            qs = qs.filter(
                Q(employee__first_name__icontains=q) |
                Q(employee__last_name__icontains=q) |
                Q(employee__dni__icontains=q) |
                Q(employee__employee_leg__icontains=q)
            )
        if year.isdigit():
            qs = qs.filter(year=int(year))
        if month.isdigit():
            qs = qs.filter(month=int(month))
        linked_employee = None
        own_qs = None
        emp = _user_employee(request.user)
        if emp:
            own_qs = Payslip.objects.filter(employee=emp).order_by('-year', '-month')
            linked_employee = emp
    else:
        emp = _user_employee(request.user)
        linked_employee = emp
        if not emp:
            qs = Payslip.objects.none()
            messages.warning(
                request,
                'Tu usuario no está vinculado a un legajo. Pedile a un administrador que lo asocie para ver tus recibos.',
            )
        else:
            qs = qs.filter(employee=emp)
        q = year = month = ''
        own_qs = None

    return render(request, 'payslips/payslip_list.html', {
        'payslips': qs,
        'can_upload': can_upload,
        'query': q if can_upload else '',
        'filter_year': year if can_upload else '',
        'filter_month': month if can_upload else '',
        'linked_employee': linked_employee,
        'own_payslips': own_qs,
    })


@capability_required(can_upload_payslips)
def payslip_upload_view(request):
    if request.method == 'POST':
        form = PayslipUploadForm(request.POST, request.FILES)
        if form.is_valid():
            payslip = form.save(commit=False)
            payslip.uploaded_by = request.user
            payslip.original_filename = getattr(request.FILES.get('file'), 'name', '') or ''
            existing = Payslip.objects.filter(
                employee=payslip.employee, year=payslip.year, month=payslip.month
            ).first()
            if existing:
                existing.file.delete(save=False)
                existing.file = payslip.file
                existing.original_filename = payslip.original_filename
                existing.uploaded_by = request.user
                existing.save()
                saved = existing
                messages.success(request, f'Recibo actualizado: {existing.period_label} — {existing.employee}.')
            else:
                payslip.save()
                saved = payslip
                messages.success(request, f'Recibo cargado: {payslip.period_label} — {payslip.employee}.')
            try:
                from core.notifications import notify_payslip_available
                notify_payslip_available(saved)
            except Exception:
                pass
            return redirect('payslip_list')
    else:
        form = PayslipUploadForm()

    return render(request, 'payslips/payslip_upload.html', {
        'form': form,
        'title': 'Cargar recibo individual',
    })


@capability_required(can_upload_payslips)
def payslip_bulk_upload_view(request):
    """
    Carga masiva: elegís período + PDFs o ZIP.
    Cada archivo se asocia automáticamente por DNI / CUIL / legajo en el nombre.
    Ejemplos: 30123456.pdf, 20-30123456-9.pdf, LEG-001_202411.pdf
    """
    results = None
    if request.method == 'POST':
        form = PayslipBulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            year = form.cleaned_data['year']
            month = form.cleaned_data['month']
            replace_existing = form.cleaned_data['replace_existing']
            pdf_files = request.FILES.getlist('pdf_files')
            zip_file = form.cleaned_data.get('zip_file')

            lookup = build_employee_lookup()
            matched = []
            unmatched = []
            replaced = 0
            created = 0

            seen_employees = {}
            for filename, django_file in iter_pdf_uploads(pdf_files, zip_file):
                employee, match_by = match_employee_for_filename(filename, lookup)
                if not employee:
                    unmatched.append({'filename': filename, 'reason': 'No se encontró legajo'})
                    continue

                # Si hay varios archivos para el mismo empleado, gana el último
                seen_employees[employee.id] = (employee, filename, django_file, match_by)

            for employee_id, (employee, filename, django_file, match_by) in seen_employees.items():
                existing = Payslip.objects.filter(employee=employee, year=year, month=month).first()
                if existing and not replace_existing:
                    unmatched.append({
                        'filename': filename,
                        'reason': f'Ya existe recibo para {employee} en ese período',
                    })
                    continue

                if existing:
                    existing.file.delete(save=False)
                    existing.file = django_file
                    existing.original_filename = filename
                    existing.uploaded_by = request.user
                    existing.save()
                    saved = existing
                    replaced += 1
                    status = 'reemplazado'
                else:
                    saved = Payslip.objects.create(
                        employee=employee,
                        year=year,
                        month=month,
                        file=django_file,
                        original_filename=filename,
                        uploaded_by=request.user,
                    )
                    created += 1
                    status = 'creado'

                try:
                    from core.notifications import notify_payslip_available
                    notify_payslip_available(saved)
                except Exception:
                    pass

                matched.append({
                    'filename': filename,
                    'employee': str(employee),
                    'match_by': match_by,
                    'status': status,
                })

            results = {
                'matched': matched,
                'unmatched': unmatched,
                'created': created,
                'replaced': replaced,
                'year': year,
                'month': month,
            }
            if created or replaced:
                messages.success(
                    request,
                    f'Carga masiva: {created} nuevo(s), {replaced} reemplazado(s), {len(unmatched)} sin asociar.',
                )
            elif unmatched:
                messages.warning(request, 'No se pudo asociar ningún archivo. Revisá los nombres.')
            form = PayslipBulkUploadForm(initial={'year': year, 'month': month})
    else:
        form = PayslipBulkUploadForm()

    return render(request, 'payslips/payslip_bulk_upload.html', {
        'form': form,
        'results': results,
        'title': 'Carga masiva de recibos',
    })


@capability_required(can_view_payslips)
def payslip_view_file(request, pk):
    payslip = get_object_or_404(Payslip, pk=pk)
    if not _can_access_payslip(request.user, payslip):
        raise PermissionDenied('No tenés permisos para ver este recibo.')
    if not payslip.file:
        raise Http404('Archivo no encontrado')
    return FileResponse(payslip.file.open('rb'), content_type='application/pdf')


@capability_required(can_view_payslips)
def payslip_download(request, pk):
    payslip = get_object_or_404(Payslip, pk=pk)
    if not _can_access_payslip(request.user, payslip):
        raise PermissionDenied('No tenés permisos para descargar este recibo.')
    if not payslip.file:
        raise Http404('Archivo no encontrado')
    filename = payslip.original_filename or f'recibo_{payslip.year}_{payslip.month:02d}.pdf'
    return FileResponse(
        payslip.file.open('rb'),
        as_attachment=True,
        filename=filename,
        content_type='application/pdf',
    )


@capability_required(can_upload_payslips)
def payslip_delete_view(request, pk):
    payslip = get_object_or_404(Payslip, pk=pk)
    if request.method == 'POST':
        label = f'{payslip.period_label} — {payslip.employee}'
        payslip.file.delete(save=False)
        payslip.delete()
        messages.success(request, f'Recibo eliminado: {label}.')
        return redirect('payslip_list')
    return redirect('payslip_list')

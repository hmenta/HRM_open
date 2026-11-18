"""API de recibos de sueldo para ERPs / sistemas de liquidación."""

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from employees.models import Employee, Payslip
from employees.payslip_matching import (
    build_employee_lookup,
    iter_pdf_uploads,
    match_employee_for_filename,
    normalize_digits,
)
from .api_auth import api_credential_required
from .notifications import notify_payslip_available


def _find_employee(payload):
    """Busca empleado por employee_id, dni, cuil o legajo."""
    if payload.get('employee_id'):
        return Employee.objects.filter(pk=payload['employee_id']).first()

    lookup = build_employee_lookup()
    for key, bucket in (
        ('dni', 'dni'),
        ('cuil', 'cuil'),
        ('legajo', 'leg'),
        ('employee_leg', 'leg'),
    ):
        raw = payload.get(key)
        if not raw:
            continue
        value = str(raw).strip()
        digits = normalize_digits(value)
        table = lookup[bucket]
        if value.lower() in table:
            return table[value.lower()]
        if digits and digits in table:
            return table[digits]
        if bucket == 'dni' and digits in lookup['dni']:
            return lookup['dni'][digits]
    return None


def _upsert_payslip(employee, year, month, uploaded_file, filename, replace=True):
    existing = Payslip.objects.filter(employee=employee, year=year, month=month).first()
    if existing and not replace:
        return existing, False, 'already_exists'
    if existing:
        existing.file.delete(save=False)
        existing.file = uploaded_file
        existing.original_filename = filename
        existing.uploaded_by = None
        existing.save()
        notify_payslip_available(existing)
        return existing, True, 'replaced'
    payslip = Payslip.objects.create(
        employee=employee,
        year=year,
        month=month,
        file=uploaded_file,
        original_filename=filename,
        uploaded_by=None,
    )
    notify_payslip_available(payslip)
    return payslip, True, 'created'


@csrf_exempt
@require_http_methods(['GET'])
@api_credential_required
def api_health(request):
    return JsonResponse({
        'ok': True,
        'service': 'HRM Open Payslip API',
        'credential': request.api_credential.name,
    })


@csrf_exempt
@require_http_methods(['POST'])
@api_credential_required
def api_payslip_upload(request):
    """
    Carga un recibo individual.

    multipart/form-data:
      - file (PDF) [requerido]
      - year, month [requeridos]
      - dni | cuil | legajo | employee_id [uno requerido]
      - replace=true|false (default true)
    """
    year = request.POST.get('year')
    month = request.POST.get('month')
    uploaded = request.FILES.get('file')
    replace = str(request.POST.get('replace', 'true')).lower() in ('1', 'true', 'yes', 'si', 'sí')

    if not year or not month or not uploaded:
        return JsonResponse(
            {'ok': False, 'error': 'Parámetros requeridos: year, month, file.'},
            status=400,
        )
    try:
        year = int(year)
        month = int(month)
        if month < 1 or month > 12:
            raise ValueError
    except ValueError:
        return JsonResponse({'ok': False, 'error': 'year/month inválidos.'}, status=400)

    if not str(uploaded.name).lower().endswith('.pdf'):
        return JsonResponse({'ok': False, 'error': 'El archivo debe ser PDF.'}, status=400)

    employee = _find_employee(request.POST)
    if not employee:
        # Intentar match por nombre de archivo
        employee, _ = match_employee_for_filename(uploaded.name)
    if not employee:
        return JsonResponse(
            {'ok': False, 'error': 'No se encontró el colaborador (dni/cuil/legajo/employee_id).'},
            status=404,
        )

    payslip, changed, status = _upsert_payslip(
        employee, year, month, uploaded, uploaded.name, replace=replace,
    )
    if not changed and status == 'already_exists':
        return JsonResponse({
            'ok': False,
            'error': 'Ya existe un recibo para ese período. Enviá replace=true para sobrescribir.',
            'payslip_id': payslip.id,
        }, status=409)

    return JsonResponse({
        'ok': True,
        'status': status,
        'payslip_id': payslip.id,
        'employee_id': employee.id,
        'employee': str(employee),
        'year': year,
        'month': month,
        'period': payslip.period_label,
    })


@csrf_exempt
@require_http_methods(['POST'])
@api_credential_required
def api_payslip_bulk_upload(request):
    """
    Carga masiva de recibos.

    multipart/form-data:
      - year, month [requeridos]
      - zip_file (ZIP con PDFs) y/o pdf_files
      - replace=true|false
    """
    year = request.POST.get('year')
    month = request.POST.get('month')
    replace = str(request.POST.get('replace', 'true')).lower() in ('1', 'true', 'yes', 'si', 'sí')
    zip_file = request.FILES.get('zip_file')
    pdf_files = request.FILES.getlist('pdf_files') or request.FILES.getlist('files')

    if not year or not month:
        return JsonResponse({'ok': False, 'error': 'Parámetros requeridos: year, month.'}, status=400)
    if not zip_file and not pdf_files:
        return JsonResponse({'ok': False, 'error': 'Enviá zip_file o pdf_files.'}, status=400)

    try:
        year = int(year)
        month = int(month)
        if month < 1 or month > 12:
            raise ValueError
    except ValueError:
        return JsonResponse({'ok': False, 'error': 'year/month inválidos.'}, status=400)

    lookup = build_employee_lookup()
    matched = []
    unmatched = []
    seen = {}

    for filename, django_file in iter_pdf_uploads(pdf_files, zip_file):
        employee, match_by = match_employee_for_filename(filename, lookup)
        if not employee:
            unmatched.append({'filename': filename, 'reason': 'No se encontró legajo'})
            continue
        seen[employee.id] = (employee, filename, django_file, match_by)

    created = replaced = skipped = 0
    for employee, filename, django_file, match_by in seen.values():
        payslip, changed, status = _upsert_payslip(
            employee, year, month, django_file, filename, replace=replace,
        )
        if status == 'created':
            created += 1
        elif status == 'replaced':
            replaced += 1
        else:
            skipped += 1
            unmatched.append({'filename': filename, 'reason': 'Ya existe (replace=false)'})
            continue
        matched.append({
            'filename': filename,
            'employee_id': employee.id,
            'employee': str(employee),
            'match_by': match_by,
            'status': status,
            'payslip_id': payslip.id,
        })

    return JsonResponse({
        'ok': True,
        'year': year,
        'month': month,
        'created': created,
        'replaced': replaced,
        'skipped': skipped,
        'matched': matched,
        'unmatched': unmatched,
    })

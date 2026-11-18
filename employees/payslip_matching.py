"""Asociación automática de archivos de recibo a legajos por nombre de archivo."""

import os
import re
import zipfile
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile

from .models import Employee


def normalize_digits(value):
    if not value:
        return ''
    return re.sub(r'\D+', '', str(value))


def build_employee_lookup():
    """
    Índice de búsqueda: DNI, CUIL (solo dígitos) y legajo (normalizado).
    Prioridad al coincidir: DNI > CUIL > legajo.
    """
    by_dni = {}
    by_cuil = {}
    by_leg = {}

    for emp in Employee.objects.all().only('id', 'dni', 'cuil', 'employee_leg', 'first_name', 'last_name'):
        dni = normalize_digits(emp.dni)
        cuil = normalize_digits(emp.cuil)
        leg = (emp.employee_leg or '').strip().lower()
        leg_digits = normalize_digits(emp.employee_leg)

        if dni:
            by_dni[dni] = emp
        if cuil:
            by_cuil[cuil] = emp
        if leg:
            by_leg[leg] = emp
        if leg_digits:
            by_leg[leg_digits] = emp

    return {'dni': by_dni, 'cuil': by_cuil, 'leg': by_leg}


def extract_candidates_from_filename(filename):
    """Obtiene posibles identificadores desde el nombre del archivo."""
    base = os.path.splitext(os.path.basename(filename))[0]
    base_lower = base.lower()
    digits_runs = re.findall(r'\d{6,}', base)  # DNI/CUIL suelen tener 7-11 dígitos
    tokens = re.split(r'[_\-\s\.]+', base_lower)
    tokens = [t for t in tokens if t]
    return {
        'base': base,
        'base_lower': base_lower,
        'digits_runs': digits_runs,
        'tokens': tokens,
        'all_digits': normalize_digits(base),
    }


def match_employee_for_filename(filename, lookup=None):
    lookup = lookup or build_employee_lookup()
    info = extract_candidates_from_filename(filename)

    # 1) coincidencia exacta por DNI en corridas de dígitos
    for run in info['digits_runs']:
        if run in lookup['dni']:
            return lookup['dni'][run], 'DNI'

    # 2) CUIL completo o que contenga el DNI
    for run in info['digits_runs']:
        if run in lookup['cuil']:
            return lookup['cuil'][run], 'CUIL'
        for cuil, emp in lookup['cuil'].items():
            if len(run) >= 7 and run in cuil:
                return emp, 'CUIL'

    # 3) legajo por token o por dígitos
    for token in info['tokens']:
        if token in lookup['leg']:
            return lookup['leg'][token], 'Legajo'
        token_digits = normalize_digits(token)
        if token_digits and token_digits in lookup['leg']:
            return lookup['leg'][token_digits], 'Legajo'

    # 4) fallback: todo el nombre en dígitos
    if info['all_digits']:
        if info['all_digits'] in lookup['dni']:
            return lookup['dni'][info['all_digits']], 'DNI'
        if info['all_digits'] in lookup['cuil']:
            return lookup['cuil'][info['all_digits']], 'CUIL'
        if info['all_digits'] in lookup['leg']:
            return lookup['leg'][info['all_digits']], 'Legajo'

    return None, None


def iter_pdf_uploads(uploaded_files=None, zip_file=None):
    """
    Genera tuplas (filename, django_file) a partir de PDFs sueltos y/o un ZIP.
    """
    uploaded_files = uploaded_files or []

    for f in uploaded_files:
        name = getattr(f, 'name', '') or ''
        if name.lower().endswith('.pdf'):
            yield os.path.basename(name), f

    if zip_file:
        raw = zip_file.read()
        with zipfile.ZipFile(BytesIO(raw)) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                name = os.path.basename(info.filename)
                if not name.lower().endswith('.pdf'):
                    continue
                if name.startswith('.'):
                    continue
                data = zf.read(info)
                yield name, SimpleUploadedFile(name, data, content_type='application/pdf')

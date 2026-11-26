from django.contrib import messages
from django.db.models import F, Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from cv_agent.parser import parse_cv
from django.conf import settings

from .forms import CandidateForm, PortalApplyForm, PositionForm
from .models import Application, Candidate, Position, StageLog
from .permissions import ADMIN, ALL_ROLES, EDIT_ROLES, RECRUITER, get_user_role, role_required
from .services import (
    enrich_from_cv,
    extract_cv_data_from_upload,
    merge_extracted_into_post_data,
    save_portal_candidate,
)
from .workflow import can_move, next_options


def _form_page(request, form, heading, cancel_url):
    return render(request, "recruitment/form.html", {
        "form": form,
        "heading": heading,
        "cancel_url": cancel_url,
    })


def _handle_cv_prefill(request, candidate=None):
    """Pre-completa el formulario de nuevo postulante desde el CV adjunto con IA."""
    cv_file = request.FILES.get("cv_file")
    extracted = None

    if cv_file:
        try:
            extracted = extract_cv_data_from_upload(cv_file)
        except Exception as exc:
            messages.error(
                request,
                f"No se pudo procesar el CV con la IA local ({exc}).",
            )
    elif candidate and candidate.cv_file and candidate.cv_file.name:
        try:
            extracted = parse_cv(candidate.cv_file.path)
        except Exception as exc:
            messages.error(
                request,
                f"No se pudo procesar el CV adjunto con la IA local ({exc}).",
            )
    else:
        messages.warning(
            request,
            "Seleccioná un archivo de CV (.pdf o .docx) para importar con IA.",
        )

    if extracted is not None:
        merged_data, filled_count = merge_extracted_into_post_data(request.POST, extracted)
        form = CandidateForm(merged_data, request.FILES, instance=candidate)

        if filled_count > 0:
            messages.success(
                request,
                f"CV procesado con IA: se completaron {filled_count} campo(s). Revisá y guardá.",
            )
        else:
            messages.info(
                request,
                "CV procesado, pero no había campos vacíos nuevos para completar.",
            )

        return render(
            request,
            "recruitment/candidate_form.html",
            {
                "form": form,
                "candidate": candidate,
                "is_edit": bool(candidate),
                "cv_text_preview": extracted.get("cv_text", ""),
            },
        )

    form = CandidateForm(request.POST, request.FILES, instance=candidate)
    return render(
        request,
        "recruitment/candidate_form.html",
        {
            "form": form,
            "candidate": candidate,
            "is_edit": bool(candidate),
        },
    )


# TABLERO KANBAN PARA EL PIPELINE DE SELECCIÓN

@role_required(*ALL_ROLES)
def kanban_board_view(request):
    stages = Application.Stage.choices

    board_data = {}
    for key, label in stages:
        board_data[key] = {
            "label": label,
            "applications": Application.objects.filter(stage=key).select_related("candidate", "position"),
        }

    context = {
        "board_data": board_data,
        "stages": stages,
    }
    return render(request, "recruitment/kanban_board.html", context)


@role_required(*EDIT_ROLES)
@require_POST
def update_stage_ajax(request, pk):
    application = get_object_or_404(Application, pk=pk)
    new_stage = request.POST.get("new_stage")

    if can_move(application.stage, new_stage):
        old_stage = application.stage
        application.stage = new_stage
        application.save()
        StageLog.objects.create(
            application=application,
            from_stage=old_stage,
            to_stage=new_stage,
            changed_by=request.user,
        )
        return JsonResponse({"status": "success", "message": "Etapa actualizada."})
    return JsonResponse({"status": "error", "message": "Transición no permitida."}, status=400)


# ---------- Búsquedas ----------


# ---------- Listado de Búsquedas con Filtros ------------- 

POSITION_SORT_FIELDS = {
    "title": ("title", False),
    "-title": ("title", True),
    "client": ("client", False),
    "-client": ("client", True),
    "status": ("status", False),
    "-status": ("status", True),
    "vacancies": ("vacancies", False),
    "-vacancies": ("vacancies", True),
    "start_date": ("start_date", False),
    "-start_date": ("start_date", True),
    "closing_date": ("closing_date", False),
    "-closing_date": ("closing_date", True),
    "created_at": ("created_at", False),
    "-created_at": ("created_at", True),
}

@role_required(*ALL_ROLES)
# Listado simple sin filtros (old)
# def position_list(request):
#    return render(request, "recruitment/positions.html", {"positions": Position.objects.all()})

def position_list(request):
    """Lista búsquedas con recuadro de búsqueda y ordenamiento por campo."""
    q = (request.GET.get("q") or "").strip()
    status_filter = (request.GET.get("status") or "").strip()
    sort = (request.GET.get("sort") or "-created_at").strip()

    positions = Position.objects.select_related("owner")

    if q:
        positions = positions.filter(
            Q(title__icontains=q)
            | Q(client__icontains=q)
            | Q(description__icontains=q)
            | Q(requirements__icontains=q)
        )

    if status_filter and status_filter in Position.Status.values:
        positions = positions.filter(status=status_filter)

    field_name, descending = POSITION_SORT_FIELDS.get(sort, ("created_at", True))
    if field_name in {"start_date", "closing_date"}:
        order_expr = F(field_name).desc(nulls_last=True) if descending else F(field_name).asc(nulls_last=True)
        positions = positions.order_by(order_expr, "-id")
    else:
        prefix = "-" if descending else ""
        positions = positions.order_by(f"{prefix}{field_name}", "-id")

    sort_options = [
        ("-start_date", "Fecha de inicio (recientes primero)"),
        ("start_date", "Fecha de inicio (antiguas primero)"),
        ("closing_date", "Fecha de cierre (próximas primero)"),
        ("-closing_date", "Fecha de cierre (lejanas primero)"),
        ("status", "Estado (A-Z)"),
        ("-status", "Estado (Z-A)"),
        ("title", "Título (A-Z)"),
        ("-title", "Título (Z-A)"),
        ("client", "Cliente / Área (A-Z)"),
        ("-created_at", "Creación (más recientes)"),
        ("-vacancies", "Vacantes (mayor a menor)"),
        ("vacancies", "Vacantes (menor a mayor)"),
    ]

    context = {
        "positions": positions,
        "q": q,
        "status_filter": status_filter,
        "current_sort": sort if sort in POSITION_SORT_FIELDS else "-created_at",
        "sort_options": sort_options,
        "status_choices": Position.Status.choices,
    }
    return render(request, "recruitment/positions.html", context)

@role_required(*EDIT_ROLES)
def position_create(request):
    form = PositionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        position = form.save(commit=False)
        position.owner = request.user
        position.save()
        messages.success(request, "Búsqueda creada.")
        return redirect("recruitment:position_detail", pk=position.pk)
    return _form_page(request, form, "Nueva búsqueda", reverse("recruitment:position_list"))


@role_required(*EDIT_ROLES)
def position_edit(request, pk):
    position = get_object_or_404(Position, pk=pk)
    form = PositionForm(request.POST or None, instance=position)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Búsqueda actualizada.")
        return redirect("recruitment:position_detail", pk=position.pk)
    return _form_page(request, form, "Editar búsqueda", reverse("recruitment:position_list"))


@role_required(*ALL_ROLES)
def position_detail(request, pk):
    position = get_object_or_404(Position, pk=pk)
    apps = list(position.applications.select_related("candidate"))
    columns = [
        (value, label, [a for a in apps if a.stage == value])
        for value, label in Application.Stage.choices
    ]
    return render(request, "recruitment/position_detail.html", {
        "position": position,
        "columns": columns,
    })


# ---------- Postulantes / Candidatos ----------

@role_required(*ALL_ROLES)
def candidate_list(request):
    qs = Candidate.objects.all()
    q = request.GET.get("q", "").strip()
    position = request.GET.get("position", "")
    stage = request.GET.get("stage", "")

    if q:
        qs = qs.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
            | Q(current_title__icontains=q)
            | Q(skills__icontains=q)
            | Q(cv_text__icontains=q)
        )
    if position:
        qs = qs.filter(applications__position_id=position).distinct()
    if stage:
        qs = qs.filter(applications__stage=stage).distinct()

    return render(request, "recruitment/candidates.html", {
        "candidates": qs[:300],
        "q": q,
        "positions": Position.objects.all(),
        "stages": Application.Stage.choices,
        "sel_position": position,
        "sel_stage": stage,
    })


@role_required(*EDIT_ROLES)
@require_POST
def candidate_delete(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    candidate_name = str(candidate)

    if candidate.cv_file and candidate.cv_file.name:
        candidate.cv_file.delete(save=False)

    candidate.delete()

    messages.success(request, f"Postulante '{candidate_name}' eliminado de la base.")
    return redirect("recruitment:candidate_list")


@role_required(*EDIT_ROLES)
def candidate_create(request):
    """Alta de postulante con opción de pre-rellenar con IA o guardar directamente."""
    if request.method == "POST":
        if "parse_cv_now" in request.POST:
            return _handle_cv_prefill(request)

        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save()
            messages.success(request, "Postulante guardado correctamente.")
            return redirect("recruitment:candidate_detail", pk=candidate.pk)
    else:
        form = CandidateForm()

    return render(request, "recruitment/candidate_form.html", {"form": form})


@role_required(*EDIT_ROLES)
def candidate_edit(request, pk):
    """Edita datos, gestiona cv_file sin IA al guardar, y permite importar CV con IA."""
    candidate = get_object_or_404(Candidate, pk=pk)

    if request.method == "POST":
        if "parse_cv_now" in request.POST:
            return _handle_cv_prefill(request, candidate=candidate)

        form = CandidateForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            form.save()
            messages.success(request, "Postulante actualizado.")
            return redirect("recruitment:candidate_detail", pk=candidate.pk)
    else:
        form = CandidateForm(instance=candidate)

    return render(
        request,
        "recruitment/candidate_form.html",
        {
            "form": form,
            "candidate": candidate,
            "is_edit": True,
        },
    )


# Para desafectar a un candidato de una búsqueda.
@role_required(*EDIT_ROLES)
@require_POST
def application_delete(request, pk):
    application = get_object_or_404(Application, pk=pk)
    candidate_pk = application.candidate.pk
    position_title = application.position.title

    old_stage = application.stage

    # En lugar de borrar, pasamos la postulación a estado "baja" para conservar el historial
    application.stage = Application.Stage.BAJA
    application.save()

    # Registramos el movimiento en el historial (StageLog)
    StageLog.objects.create(
        application=application,
        from_stage=old_stage,
        to_stage=Application.Stage.BAJA,
        changed_by=request.user,
        comment="Candidato desafectado de la búsqueda",
    )

    messages.success(
        request,
        f"Candidato desafectado de la búsqueda '{position_title}' (historial conservado).",
    )
    return redirect("recruitment:candidate_detail", pk=candidate_pk)


@role_required(*ALL_ROLES)
def candidate_detail(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)

    # Excluimos las postulaciones cerradas/finalizadas para que solo aparezcan las activas
    applications = list(
        candidate.applications.exclude(
            stage__in=[Application.Stage.BAJA, Application.Stage.NO_APLICA, Application.Stage.HIRED]
        ).select_related("position")
    )

    for app in applications:
        app.next_options = next_options(app.stage) # Lista ordenada con las etapas y sus notas para guardar. 
        notes_dict = dict(app.stage_notes or {})
        app.stage_notes_items = [
            (stage_key, stage_label, notes_dict.get(stage_key, ""))
            for stage_key, stage_label in Application.Stage.choices
        ]

    # El historial (logs) sigue trayendo TODO el recorrido histórico del candidato sin perder nada
    logs = StageLog.objects.filter(application__candidate=candidate).select_related(
        "application__position", "changed_by"
    )

    positions_open = Position.objects.filter(status=Position.Status.OPEN)
    user_role = get_user_role(request.user)
    can_manage_recruitment = user_role in (ADMIN, RECRUITER)

    return render(request, "recruitment/candidate_detail.html", {
        "candidate": candidate,
        "applications": applications,
        "logs": logs,
        "positions_open": positions_open,
        "user_role": user_role,
        "can_manage_recruitment": can_manage_recruitment,
    })

@role_required(*ALL_ROLES)
def candidate_cv(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    if not candidate.cv_file:
        raise Http404("El candidato no tiene CV adjunto.")
    return FileResponse(candidate.cv_file.open("rb"), as_attachment=True)


@role_required(*EDIT_ROLES)
@require_POST
def assign_candidate_position(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    position_id = request.POST.get("position_id")

    if position_id:
        position = get_object_or_404(Position, pk=position_id)

        application = Application.objects.filter(candidate=candidate, position=position).first()

        if application:
            old_stage = application.stage
            application.stage = Application.Stage.NEW
            application.save()

            StageLog.objects.create(
                application=application,
                from_stage=old_stage,
                to_stage=Application.Stage.NEW,
                changed_by=request.user,
                comment="Candidato reasignado / reactivado en la búsqueda",
            )
            messages.success(request, f"Candidato reasignado a la búsqueda '{position.title}'.")
        else:
            application = Application.objects.create(
                candidate=candidate,
                position=position,
                stage=Application.Stage.NEW,
            )
            StageLog.objects.create(
                application=application,
                from_stage="",
                to_stage=Application.Stage.NEW,
                changed_by=request.user,
                comment="Postulación creada",
            )
            messages.success(request, f"Candidato postulado exitosamente a '{position.title}'.")

    return redirect("recruitment:candidate_detail", pk=candidate.pk)


# ---------- Acciones de Flujo y Portal ----------

@role_required(*EDIT_ROLES)
@require_POST
def application_move(request, pk):
    application = get_object_or_404(Application, pk=pk)
    to_stage = request.POST.get("to_stage")
    comment = request.POST.get("comment", "").strip()

    current_stage = str(application.stage).strip().lower()
    target_stage = str(to_stage).strip().lower()

    if target_stage and can_move(current_stage, target_stage):
        old_stage = application.stage
        application.stage = target_stage
        application.save()

        StageLog.objects.create(
            application=application,
            from_stage=old_stage,
            to_stage=target_stage,
            changed_by=request.user,
            comment=comment,
        )
        messages.success(request, "¡Etapa actualizada con éxito!")
    else:
        messages.error(request, f"Transición no permitida de '{current_stage}' a '{target_stage}'.")

    return redirect("recruitment:candidate_detail", pk=application.candidate.pk)


def portal_apply(request):
    """Frontend público de empleo: sin login ni menú del HRM interno."""
    form = PortalApplyForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        save_portal_candidate({
            "first_name": form.cleaned_data["first_name"],
            "last_name": form.cleaned_data["last_name"],
            "email": form.cleaned_data["email"],
            "phone": form.cleaned_data.get("phone", ""),
            "cv_file": form.cleaned_data["cv_file"],
            "position": form.cleaned_data.get("position"),
        })
        return redirect("empleo_thanks")

    open_positions = Position.objects.filter(status=Position.Status.OPEN).order_by("-created_at")[:8]
    return render(request, "portal/apply.html", {
        "form": form,
        "open_positions": open_positions,
    })


def portal_thanks(request):
    return render(request, "portal/thanks.html")


## RELATIVO AL AGENTE DE IA PARA LECTURA DE CVS / Vista candidate_parse_cv
@role_required(*EDIT_ROLES)
@require_POST
def candidate_parse_cv(request, pk):
    """Ejecuta el agente local de IA sobre el CV ya adjunto del postulante."""
    candidate = get_object_or_404(Candidate, pk=pk)

    if not candidate.cv_file:
        messages.warning(request, "El postulante no tiene un CV adjunto.")
        return redirect("recruitment:candidate_detail", pk=candidate.pk)

    overwrite = request.POST.get("overwrite") == "1"
    updated = enrich_from_cv(candidate, overwrite=overwrite)

    if updated:
        messages.success(request, "CV procesado con IA local y perfil actualizado.")
    else:
        messages.warning(
            request,
            "No se actualizaron campos (verificá el texto del CV o que Ollama esté corriendo).",
        )

    return redirect("recruitment:candidate_detail", pk=candidate.pk)

## ---- PARA GUARDAR LAS NOTAS POR ETAPA EN EL PERFIL DEL CANDIDATO ---- ##
@role_required(*EDIT_ROLES)
@require_POST
def application_save_stage_note(request, pk):
    application = get_object_or_404(Application, pk=pk)
    stage_key = (request.POST.get("stage") or "").strip()
    note_text = (request.POST.get("note") or "").strip()

    if stage_key not in set(Application.Stage.values):
        messages.error(request, "Etapa inválida.")
        return redirect("recruitment:candidate_detail", pk=application.candidate.pk)

    notes = dict(application.stage_notes or {})
    if note_text:
        notes[stage_key] = note_text
    else:
        notes.pop(stage_key, None)

    application.stage_notes = notes
    application.save(update_fields=["stage_notes", "updated_at"])
    messages.success(request, "Nota de la etapa guardada.")
    return redirect("recruitment:candidate_detail", pk=application.candidate.pk)


### """Frontend público de empleo: sin login ni menú del HRM interno.""" ###

def portal_apply(request):
    if not getattr(settings, "PORTAL_ENABLED", True):
        raise Http404("Portal de empleo desactivado.")

    form = PortalApplyForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        save_portal_candidate({
            "first_name": form.cleaned_data["first_name"],
            "last_name": form.cleaned_data["last_name"],
            "email": form.cleaned_data["email"],
            "phone": form.cleaned_data.get("phone", ""),
            "cv_file": form.cleaned_data["cv_file"],
            "position": form.cleaned_data.get("position"),
        })
        return redirect("recruitment:portal_thanks")

    open_positions = Position.objects.filter(status=Position.Status.OPEN).order_by("-created_at")[:8]
    return render(request, "portal/apply.html", {
        "form": form,
        "open_positions": open_positions,
    })


def portal_thanks(request):
    if not getattr(settings, "PORTAL_ENABLED", True):
        raise Http404("Portal de empleo desactivado.")

    return render(request, "portal/thanks.html")
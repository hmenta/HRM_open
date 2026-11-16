import os

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import CandidateForm, PortalApplyForm, PositionForm
from .models import Application, Candidate, Position, StageLog
from .permissions import ADMIN, ALL_ROLES, EDIT_ROLES, role_required
from .services import enrich_from_cv, save_portal_candidate
from .workflow import can_move, next_options


def _form_page(request, form, heading, cancel_url):
    return render(request, "recruitment/form.html", {
        "form": form, "heading": heading, "cancel_url": cancel_url,
    })


# ---------- Búsquedas ----------

@role_required(*ALL_ROLES)
def position_list(request):
    return render(request, "recruitment/positions.html", {"positions": Position.objects.all()})


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
        "position": position, "columns": columns,
    })


# ---------- Postulantes ----------

@role_required(*ALL_ROLES)
def candidate_list(request):
    qs = Candidate.objects.all()
    q = request.GET.get("q", "").strip()
    position = request.GET.get("position", "")
    stage = request.GET.get("stage", "")

    if q:
        qs = qs.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q)
            | Q(current_title__icontains=q) | Q(skills__icontains=q) | Q(cv_text__icontains=q)
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
def candidate_create(request):
    form = CandidateForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        candidate = form.save(commit=False)
        candidate.source = Candidate.Source.MANUAL
        candidate.save()
        if candidate.cv_file:
            enrich_from_cv(candidate)
        messages.success(request, "Postulante cargado.")
        return redirect("recruitment:candidate_detail", pk=candidate.pk)
    return _form_page(request, form, "Nuevo postulante", reverse("recruitment:candidate_list"))


@role_required(*EDIT_ROLES)
def candidate_edit(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    form = CandidateForm(request.POST or None, request.FILES or None, instance=candidate)
    if request.method == "POST" and form.is_valid():
        candidate = form.save()
        if "cv_file" in form.changed_data and candidate.cv_file:
            enrich_from_cv(candidate)
        messages.success(request, "Postulante actualizado.")
        return redirect("recruitment:candidate_detail", pk=candidate.pk)
    return _form_page(request, form,

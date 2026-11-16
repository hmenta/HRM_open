# Mapeo de transiciones del pipeline de selección
TRANSITIONS = {
    "nuevo": {"en_revision", "no_aplica"},
    "en_revision": {"entrevista_1", "no_aplica"},
    "entrevista_1": {"entrevista_2", "oferta", "no_aplica"},
    "entrevista_2": {"oferta", "no_aplica"},
    "psico": {"medico", "no_aplica"},
    "medico": {"oferta", "no_aplica"},
    "oferta": {"contratado", "baja"},
    "contratado": set(),
    "no_aplica": {"nuevo"},
    "baja": {"nuevo"},  # Permite reactivar
}


def can_move(current, target):
    if not current or not target:
        return False
    c = str(current).strip().lower()
    t = str(target).strip().lower()
    return t in TRANSITIONS.get(c, set())


def next_options(current):
    from .models import Application
    if not current:
        return []
    c = str(current).strip().lower()
    allowed_set = TRANSITIONS.get(c, set())
    return [(v, label) for v, label in Application.Stage.choices if v in allowed_set]
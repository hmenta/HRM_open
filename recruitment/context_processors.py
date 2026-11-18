"""Compatibilidad: delega en accounts.context_processors.role_context."""

from accounts.context_processors import role_context as recruitment_roles

__all__ = ['recruitment_roles']

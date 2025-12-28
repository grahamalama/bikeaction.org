from django.contrib.sessions.backends.db import SessionStore as DBSessionStore


class SessionStore(DBSessionStore):
    """
    Session store that uses the LazerSession model instead of the default Session model.
    Lazer sessions are only valid for Lazer API routes and have a longer expiry (1 year).
    """

    @classmethod
    def get_model_class(cls):
        from lazer.models import LazerSession

        return LazerSession

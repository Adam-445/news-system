from sqlalchemy.orm import Query, Session
from app.db import models

class SoftDeleteQuery(Query):
    """
    Custom Query class that automatically applies soft-delete filters.
    For non-admin users, this excludes records where is_deleted==True for models that support soft deletion.
    """
    _soft_delete_models = {models.Article, models.User}

    def _apply_soft_delete_filter(self):
        """Return a new query with the soft-delete filter applied if needed."""
        session: Session = self.session
        current_user = session.info.get("current_user", None)
        is_admin = current_user and current_user.role.name == "admin"

        if self.column_descriptions:
            model_class = self.column_descriptions[0].get("entity")
            if model_class in self._soft_delete_models and not is_admin:
                return self.filter(model_class.is_deleted == False)
        return self

    def __iter__(self):
        return super(SoftDeleteQuery, self._apply_soft_delete_filter()).__iter__()
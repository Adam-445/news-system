from sqlalchemy.orm import with_loader_criteria
from app.db import models

def handle_include_deleted(execute_state):
    # Get the pre-computed admin flag from session info
    is_admin = execute_state.session.info.get("is_admin", False)

    if (
        execute_state.is_select
        and not execute_state.execution_options.get("include_deleted", False)
        and not is_admin
    ):
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                models.Article, 
                models.Article.is_deleted == False, 
                include_aliases=True
            ),
            with_loader_criteria(
                models.User, 
                models.User.is_deleted == False, 
                include_aliases=True
            )
        )
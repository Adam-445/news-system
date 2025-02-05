# Not sure about adding this
# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from app.db.database import get_db
# from app.db.models import Role
# from app.schemas import RoleUpdate
# from app.api.dependencies import required_roles

# router = APIRouter()


# @router.put("/roles/{role_name}", response_model=RoleUpdate)
# def update_role(
#     role_name: str,
#     role_update: RoleUpdate,
#     db: Session = Depends(get_db),
#     current_user=Depends(required_roles(["admin"])),
# ):
#     role = db.query(Role).filter(Role.name == role_name).first()
#     if not role:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
#         )
#     # Update fields
#     if role_update.description is not None:
#         role.description = role_update.description
#     db.commit()
#     db.refresh(role)
#     return role

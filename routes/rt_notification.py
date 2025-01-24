from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from models.notification import Notification, KindNotification
from models.user import User
from models.database import SessionLocal

router = APIRouter()  # APIRouter para notificaciones


# Modelo Pydantic para crear una notificación
class CreateNotificationRequest(BaseModel):
    title: str
    message: str
    roles: list[str]
    kind: KindNotification = (
        KindNotification.normal
    )  # El tipo de notificación (puede ser 'urgent', 'normal', etc.)
    user_id: int

    class Config:
        from_attributes = True


# Modelo Pydantic para la respuesta de notificaciones
class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    roles: list[str]
    kind: KindNotification
    created_at: datetime
    user_id: int

    class Config:
        from_attributes = True


# Endpoint para crear una notificación
@router.post("/create-notification", response_model=NotificationResponse)
async def create_notification(data: CreateNotificationRequest):
    db: Session = SessionLocal()

    try:
        # Crear una nueva notificación
        new_notification = Notification(
            title=data.title,
            message=data.message,
            roles=data.roles,
            kind=data.kind,
            user_id=data.user_id,
        )
        db.add(new_notification)
        db.commit()
        db.refresh(new_notification)

        return NotificationResponse(
            id=new_notification.id,  # type: ignore
            title=new_notification.title,  # type: ignore
            message=new_notification.message,  # type: ignore
            roles=new_notification.roles,  # type: ignore
            kind=new_notification.kind,  # type: ignore
            created_at=new_notification.created_at,  # type: ignore
            user_id=new_notification.user_id,  # type: ignore
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al crear la notificación")
    finally:
        db.close()


# Endpoint para obtener notificaciones de un usuario específico
@router.get("/notifications/user/{user_id}", response_model=list[NotificationResponse])
async def get_user_notifications(user_id: int):
    db: Session = SessionLocal()

    try:
        # Obtener el usuario
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Filtrar notificaciones según los roles del usuario
        user_roles = user.roles
        notifications = (
            db.query(Notification)
            .filter(
                Notification.roles.op("@>")(user_roles)  # Filtra por roles compatibles
            )
            .all()
        )

        return [
            NotificationResponse(
                id=notification.id,  # type: ignore
                title=notification.title,  # type: ignore
                message=notification.message,  # type: ignore
                roles=notification.roles,  # type: ignore
                kind=notification.kind,  # type: ignore
                created_at=notification.created_at,  # type: ignore
                user_id=notification.user_id,  # type: ignore
            )
            for notification in notifications
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener notificaciones")
    finally:
        db.close()


# Endpoint para obtener todas las notificaciones
@router.get("/notifications", response_model=list[NotificationResponse])
async def get_all_notifications():
    db: Session = SessionLocal()

    try:
        # Obtener todas las notificaciones
        notifications = db.query(Notification).all()

        return [
            NotificationResponse(
                id=notification.id,  # type: ignore
                title=notification.title,  # type: ignore
                message=notification.message,  # type: ignore
                roles=notification.roles,  # type: ignore
                kind=notification.kind,  # type: ignore
                created_at=notification.created_at,  # type: ignore
                user_id=notification.user_id,  # type: ignore
            )
            for notification in notifications
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Error al obtener todas las notificaciones"
        )
    finally:
        db.close()


# Endpoint para obtener notificaciones por categoría (kind)
@router.get("/notifications/category/{kind}", response_model=list[NotificationResponse])
async def get_notifications_by_category(kind: KindNotification):
    db: Session = SessionLocal()

    try:
        # Filtrar notificaciones por la categoría (kind)
        notifications = db.query(Notification).filter(Notification.kind == kind).all()

        return [
            NotificationResponse(
                id=notification.id,  # type: ignore
                title=notification.title,  # type: ignore
                message=notification.message,  # type: ignore
                roles=notification.roles,  # type: ignore
                kind=notification.kind,  # type: ignore
                created_at=notification.created_at,  # type: ignore
                user_id=notification.user_id,  # type: ignore
            )
            for notification in notifications
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Error al obtener notificaciones por categoría"
        )
    finally:
        db.close()


# Endpoint para obtener las primeras 20 notificaciones
@router.get("/notifications/first-20", response_model=list[NotificationResponse])
async def get_first_20_notifications():
    db: Session = SessionLocal()

    try:
        # Obtener las primeras 20 notificaciones (ordenadas por fecha de creación)
        notifications = (
            db.query(Notification)
            .order_by(Notification.created_at.desc())
            .limit(20)
            .all()
        )

        return [
            NotificationResponse(
                id=notification.id,  # type: ignore
                title=notification.title,  # type: ignore
                message=notification.message,  # type: ignore
                roles=notification.roles,  # type: ignore
                kind=notification.kind,  # type: ignore
                created_at=notification.created_at,  # type: ignore
                user_id=notification.user_id,  # type: ignore
            )
            for notification in notifications
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Error al obtener las primeras 20 notificaciones"
        )
    finally:
        db.close()

"""Seed inicial de datos mínimos para una base de datos vacía."""

from sqlmodel import Session, select

from app.auth.security import hash_password
from app.config import settings
from app.db.database import SessionLocal
from app.models.area import Area
from app.models.auditoria import Auditoria
from app.models.capa import Capa
from app.models.criterio import Criterio
from app.models.frecuencia import Frecuencia
from app.models.rol import Rol
from app.models.usuario import Usuario

_ROLES_INICIALES = ["Administrador", "Supervisor", "Auditor"]
_CAPAS_INICIALES = ["Auditor", "Supervisor", "Gerente"]
_FRECUENCIAS_INICIALES = [
    ("Diaria", "Cada dia"),
    ("Semanal", "Cada semana"),
    ("Quincenal", "Cada quince dias"),
    ("Mensual", "Cada mes"),
    ("Bimestral", "Cada dos meses"),
    ("Trimestral", "Cada tres meses"),
    ("Anual", "Cada año"),
]

_ADMIN_CORREO = "admin@lpa.com"
_ADMIN_NOMBRE = "Administrador"

_AUDITORIA_ENSAMBLE_FINAL_NOMBRE = "Auditoría de Proceso - Ensamble Final"
_AUDITORIA_ENSAMBLE_FINAL_DESCRIPCION = (
    "Auditoría de proceso para Ensamble Final."
)
_AUDITORIA_ENSAMBLE_FINAL_FORMATO = "FOR.QA.018"

_CRITERIOS_ENSAMBLE_FINAL = [
    "Se realiza inspección establecida en cada estación (Check Do Check).",
    "La estación de trabajo se mantiene limpia.",
    "Se realiza la prueba de sonido.",
    "Uso de regleta de entonación.",
    "Digitación.",
    "Se está utilizando el PIM.",
    "Torque de ensamble Cuerpo - Cuello 18 in.lb",
    "Torque de ensamble Pick Guard 12 in.lb",
    "Uso de acetatos para verificar la distancia entre ranuras.",
    "Se usa las bolsas de foam en el 100% de los cuerpos negros y sunbursts.",
    "Se usa el bar code scanner en el área de empaque en el 100% de las unidades.",
    "Se realiza la inspección de 6 pasos.",
    "Verificar que se capture en SAP todo lo encontrado en las células.",
    "Verificar que el material del WIP sea el correcto.",
    "Verificar que se utilice la fixtura de armado de Cuerpo - Cuello.",
]


def _seed_roles(session: Session) -> Rol:
    """Crea los roles que no existan aún. Retorna el rol Administrador."""
    rol_admin = None
    for nombre in _ROLES_INICIALES:
        existente = session.exec(select(Rol).where(Rol.nombre == nombre)).first()
        if existente is None:
            rol = Rol(nombre=nombre, descripcion=f"Rol de {nombre.lower()}")
            session.add(rol)
            session.flush()
            existente = rol

        if nombre == "Administrador":
            rol_admin = existente

    session.commit()
    return rol_admin  # type: ignore[return-value]


def _seed_admin(session: Session, rol_admin: Rol) -> None:
    """Crea el usuario administrador si no existe."""
    existente = session.exec(select(Usuario).where(Usuario.correo == _ADMIN_CORREO)).first()
    if existente is not None:
        return

    admin = Usuario(
        nombre=_ADMIN_NOMBRE,
        correo=_ADMIN_CORREO,
        contrasena_hash=hash_password(settings.default_admin_password),
        activo=True,
        rol_id=rol_admin.id,  # type: ignore[arg-type]
    )
    session.add(admin)
    session.commit()


def _seed_capas(session: Session) -> None:
    """Crea las capas iniciales si no existen. Es idempotente."""
    for nombre in _CAPAS_INICIALES:
        existente = session.exec(select(Capa).where(Capa.nombre == nombre)).first()
        if existente is None:
            capa = Capa(nombre=nombre, descripcion=f"Capa de {nombre.lower()}", activa=True)
            session.add(capa)

    session.commit()


def _seed_frecuencias(session: Session) -> None:
    """Crea las frecuencias iniciales si no existen. Es idempotente."""
    for nombre, descripcion in _FRECUENCIAS_INICIALES:
        existente = session.exec(
            select(Frecuencia).where(Frecuencia.nombre == nombre)
        ).first()
        if existente is None:
            session.add(Frecuencia(nombre=nombre, descripcion=descripcion))

    session.commit()


def _seed_auditoria_ensamble_final(session: Session) -> None:
    """Crea la auditoría de proceso para Ensamble Final con sus 15 criterios.

    Es idempotente: busca por nombre la auditoría y los criterios por
    auditoria_id + orden. No duplica si ya existen. Si faltan criterios,
    crea únicamente los faltantes.
    """
    capa = session.exec(select(Capa).where(Capa.nombre == "Auditor")).first()
    if capa is None:
        raise ValueError("La capa 'Auditor' no existe. Ejecute primero el seed de capas.")

    area = session.exec(select(Area).where(Area.nombre == "Ensamble Final")).first()
    if area is None:
        raise ValueError("El área 'Ensamble Final' no existe.")

    frecuencia = session.exec(select(Frecuencia).where(Frecuencia.nombre == "Diaria")).first()
    if frecuencia is None:
        raise ValueError("La frecuencia 'Diaria' no existe. Ejecute primero el seed de frecuencias.")

    auditoria = session.exec(
        select(Auditoria).where(Auditoria.nombre == _AUDITORIA_ENSAMBLE_FINAL_NOMBRE)
    ).first()

    if auditoria is None:
        auditoria = Auditoria(
            nombre=_AUDITORIA_ENSAMBLE_FINAL_NOMBRE,
            descripcion=_AUDITORIA_ENSAMBLE_FINAL_DESCRIPCION,
            activa=True,
            capa_id=capa.id,
            frecuencia_id=frecuencia.id,
            area_id=area.id,
        )
        session.add(auditoria)
        session.flush()

    for i, descripcion in enumerate(_CRITERIOS_ENSAMBLE_FINAL, start=1):
        existente = session.exec(
            select(Criterio).where(
                Criterio.auditoria_id == auditoria.id,
                Criterio.orden == i,
            )
        ).first()
        if existente is None:
            session.add(
                Criterio(
                    descripcion=descripcion,
                    orden=i,
                    activo=True,
                    auditoria_id=auditoria.id,
                )
            )

    session.commit()


def seed_inicial() -> None:
    """Ejecuta el seed de datos mínimos para que el sistema sea utilizable.

    Es idempotente: no duplica roles, frecuencias, usuario administrador ni capas.
    """
    with SessionLocal() as session:
        rol_admin = _seed_roles(session)
        _seed_admin(session, rol_admin)
        _seed_capas(session)
        _seed_frecuencias(session)
        _seed_auditoria_ensamble_final(session)

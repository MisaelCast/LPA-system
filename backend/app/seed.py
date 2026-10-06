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

_ROLES_INICIALES = ["Administrador", "Gerente", "Supervisor", "Auditor"]
_CAPAS_INICIALES = ["Auditor", "Supervisor", "Gerente"]
_AREAS_INICIALES = [
    ("Ensamble Final", "Área de ensamble final de producto."),
    ("Pulido", "Área de pulido de producto."),
]
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

_AUDITORIA_PULIDO_NOMBRE = "Auditoría de Proceso - Pulido"
_AUDITORIA_PULIDO_DESCRIPCION = "Auditoría de proceso para el área de Pulido."

_PULIDO_SECCION_LIJADO_FRONTAL = "1. LIJADO CARA FRONTAL"
_PULIDO_SECCION_LIJADO_TRASERA = "2. LIJADO CARA TRASERA"
_PULIDO_SECCION_MECANISMO = "3. MECANISMO"

_AUDITORIA_VERIFICACION_SUFIJO = "Auditoría de Verificación"
_AUDITORIA_VERIFICACION_DESCRIPCION = (
    "Verificación semanal del trabajo del Auditor (meta-auditoría)."
)
_AUDITORIA_VERIFICACION_TIPO_RESPUESTA = "cumplimiento"

_CRITERIOS_VERIFICACION_SUPERVISOR = [
    "El Auditor completó el 100% de las auditorías programadas del periodo "
    "y las realizó dentro del plazo establecido.",
    "El Auditor cubrió todas las células/áreas asignadas, sin omitir ninguna.",
    "Las auditorías del Auditor contienen respuesta en todos los criterios "
    "y no presentan registros incompletos.",
    "Los hallazgos del Auditor están correctamente registrados, corresponden "
    "a la situación observada y cuentan con evidencia.",
    "Los hallazgos menores fueron corregidos y cerrados en un máximo de 7 días.",
    "Los hallazgos críticos/recurrentes tienen acción correctiva asignada en "
    "un máximo de 24 horas y seguimiento registrado.",
    "Ningún hallazgo abierto permanece más de 2 días sin actualización o seguimiento.",
    "Los hallazgos cerrados cuentan con evidencia suficiente de que la condición "
    "fue corregida.",
    "Los hallazgos reincidentes están identificados y cuentan con acción "
    "correctiva para evitar su repetición.",
]


def _criterio_pulido(
    texto: str,
    seccion: str,
    subseccion: str | None = None,
    subtitulo: str | None = None,
) -> tuple[str, str, str | None, str | None]:
    """Define un criterio de Pulido con su jerarquía de encabezados.

    Retorna ``(descripcion, seccion, subseccion, subtitulo)`` para que la
    descripción quede limpia y la jerarquía se guarde en campos separados;
    la interfaz la presenta como encabezados/separadores visuales.
    """
    return (texto, seccion, subseccion, subtitulo)


_CRITERIOS_PULIDO = [
    _criterio_pulido(
        "El colaborador está entrenado y cuenta con la hoja de validación.",
        _PULIDO_SECCION_LIJADO_FRONTAL, "1.1 P1000", "Cara",
    ),
    _criterio_pulido(
        "El colaborador realiza la inspección de entrada (Check).",
        _PULIDO_SECCION_LIJADO_FRONTAL, "1.1 P1000", "Cara",
    ),
    _criterio_pulido(
        "Validar que la lijadora orbital cuente con el tope pokayoke para RPM y esté a 3/8 de vuelta.",
        _PULIDO_SECCION_LIJADO_FRONTAL, "1.1 P1000", "Cara",
    ),
    _criterio_pulido(
        "El colaborador inicia con el lijado parte superior del cuerpo (cuernos); tres ciclos (haciendo 2 intervalos de limpieza).",
        _PULIDO_SECCION_LIJADO_FRONTAL, "1.1 P1000", "Cara",
    ),
    _criterio_pulido(
        "El colaborador realiza el lijado de cara con tres ciclos con 8-9 recorridos por ciclo haciendo 2 intervalos de limpieza.",
        _PULIDO_SECCION_LIJADO_FRONTAL, "1.1 P1000", "Cara",
    ),
    _criterio_pulido(
        'El colaborador realiza el método "H" o cruzado haciendo 2 intervalos de limpieza por ciclo.',
        _PULIDO_SECCION_LIJADO_FRONTAL, "1.1 P1000", "Cara",
    ),
    _criterio_pulido(
        "El consumo es de dos caras por lija GRAMO 1000.",
        _PULIDO_SECCION_LIJADO_FRONTAL, "1.1 P1000", "Cara",
    ),
    _criterio_pulido(
        "El colaborador realiza la limpieza de la lija con borrador después de cada ciclo de lijado sin accionar la orbital en la almohadilla.",
        _PULIDO_SECCION_LIJADO_FRONTAL, "1.1 P1000", "Cara",
    ),
    _criterio_pulido(
        "El colaborador realiza la limpieza del cuerpo con trapo después de cada medio ciclo de lijado.",
        _PULIDO_SECCION_LIJADO_FRONTAL, "1.1 P1000", "Cara",
    ),
    _criterio_pulido(
        "Validar que la lijadora orbital cuente con el tope pokayoke para RPM y esté a 3/8 de vuelta.",
        _PULIDO_SECCION_LIJADO_FRONTAL, "1.2 P1200", "Cara",
    ),
    _criterio_pulido(
        "El colaborador inicia con el lijado parte superior del cuerpo (cuernos); tres ciclos (haciendo 2 intervalos de limpieza).",
        _PULIDO_SECCION_LIJADO_FRONTAL, "1.2 P1200", "Cara",
    ),
    _criterio_pulido(
        'El colaborador realiza el método "H" o cruzado haciendo 2 intervalos de limpieza por ciclo.',
        _PULIDO_SECCION_LIJADO_FRONTAL, "1.2 P1200", "Cara",
    ),
    _criterio_pulido(
        "El colaborador realiza el lijado de cara con tres ciclos con 8-9 recorridos por ciclo haciendo 2 intervalos de limpieza.",
        _PULIDO_SECCION_LIJADO_FRONTAL, "1.2 P1200", "Cara",
    ),
    _criterio_pulido(
        "El consumo es de una lija por cara.",
        _PULIDO_SECCION_LIJADO_FRONTAL, "1.2 P1200", "Cara",
    ),
    _criterio_pulido(
        "El colaborador realiza la limpieza de la lija con borrador después de cada ciclo de lijado sin accionar la orbital en la almohadilla.",
        _PULIDO_SECCION_LIJADO_FRONTAL, "1.2 P1200", "Cara",
    ),
    _criterio_pulido(
        "El colaborador realiza la limpieza del cuerpo con trapo después de cada medio ciclo de lijado.",
        _PULIDO_SECCION_LIJADO_FRONTAL, "1.2 P1200", "Cara",
    ),
    _criterio_pulido(
        "El colaborador realiza la inspección de salida (Check).",
        _PULIDO_SECCION_LIJADO_FRONTAL, "1.2 P1200", "Lado",
    ),
    _criterio_pulido(
        "La mesa de trabajo y los IPK's se encuentran en buenas condiciones.",
        _PULIDO_SECCION_LIJADO_FRONTAL, "1.2 P1200", "Lado",
    ),
    _criterio_pulido(
        "La iluminación se encuentra en buen estado.",
        _PULIDO_SECCION_LIJADO_FRONTAL, "1.2 P1200", "Lado",
    ),
    _criterio_pulido(
        "El colaborador está entrenado y cuenta con la hoja de validación.",
        _PULIDO_SECCION_LIJADO_TRASERA, "2.1 P1000", "Cara",
    ),
    _criterio_pulido(
        "El colaborador realiza la inspección de entrada (Check).",
        _PULIDO_SECCION_LIJADO_TRASERA, "2.1 P1000", "Cara",
    ),
    _criterio_pulido(
        "Validar que la lijadora orbital cuente con el tope pokayoke para RPM y esté a 3/8 de vuelta.",
        _PULIDO_SECCION_LIJADO_TRASERA, "2.1 P1000", "Cara",
    ),
    _criterio_pulido(
        "El colaborador inicia con el lijado parte superior del cuerpo (cuernos); tres ciclos (haciendo 2 intervalos de limpieza).",
        _PULIDO_SECCION_LIJADO_TRASERA, "2.1 P1000", "Cara",
    ),
    _criterio_pulido(
        "El colaborador realiza el lijado de cara con tres ciclos con 8-9 recorridos por ciclo haciendo 2 intervalos de limpieza.",
        _PULIDO_SECCION_LIJADO_TRASERA, "2.1 P1000", "Cara",
    ),
    _criterio_pulido(
        'El colaborador realiza el método "H" o cruzado haciendo 2 intervalos de limpieza por ciclo.',
        _PULIDO_SECCION_LIJADO_TRASERA, "2.1 P1000", "Cara",
    ),
    _criterio_pulido(
        "El consumo es de dos caras por lija GRAMO 1000.",
        _PULIDO_SECCION_LIJADO_TRASERA, "2.1 P1000", "Cara",
    ),
    _criterio_pulido(
        "El colaborador realiza la limpieza de la lija con borrador después de cada ciclo de lijado sin accionar la orbital en la almohadilla.",
        _PULIDO_SECCION_LIJADO_TRASERA, "2.1 P1000", "Cara",
    ),
    _criterio_pulido(
        "El colaborador realiza la limpieza del cuerpo con trapo después de cada medio ciclo de lijado.",
        _PULIDO_SECCION_LIJADO_TRASERA, "2.1 P1000", "Cara",
    ),
    _criterio_pulido(
        "Validar que la lijadora orbital cuente con el tope pokayoke para RPM y esté a 3/8 de vuelta.",
        _PULIDO_SECCION_LIJADO_TRASERA, "2.1 P1000", "Lado",
    ),
    _criterio_pulido(
        "Validar que la lijadora orbital cuente con el tope pokayoke para RPM y esté a 3/8 de vuelta.",
        _PULIDO_SECCION_LIJADO_TRASERA, "2.2 P1200", "Cara",
    ),
    _criterio_pulido(
        "El colaborador inicia con el lijado parte superior del cuerpo (cuernos); tres ciclos (haciendo 2 intervalos de limpieza).",
        _PULIDO_SECCION_LIJADO_TRASERA, "2.2 P1200", "Cara",
    ),
    _criterio_pulido(
        'El colaborador realiza el método "H" o cruzado haciendo 2 intervalos de limpieza por ciclo.',
        _PULIDO_SECCION_LIJADO_TRASERA, "2.2 P1200", "Cara",
    ),
    _criterio_pulido(
        "El colaborador realiza el lijado de cara con tres ciclos con 8-9 recorridos por ciclo haciendo 2 intervalos de limpieza.",
        _PULIDO_SECCION_LIJADO_TRASERA, "2.2 P1200", "Cara",
    ),
    _criterio_pulido(
        "El consumo es de una lija por cara.",
        _PULIDO_SECCION_LIJADO_TRASERA, "2.2 P1200", "Cara",
    ),
    _criterio_pulido(
        "El colaborador realiza la limpieza de la lija con borrador después de cada ciclo de lijado sin accionar la orbital en la almohadilla.",
        _PULIDO_SECCION_LIJADO_TRASERA, "2.2 P1200", "Cara",
    ),
    _criterio_pulido(
        "El colaborador realiza la limpieza del cuerpo con trapo después de cada medio ciclo de lijado.",
        _PULIDO_SECCION_LIJADO_TRASERA, "2.2 P1200", "Cara",
    ),
    _criterio_pulido(
        "Validar que la lijadora orbital cuente con el tope pokayoke para RPM y esté a 3/8 de vuelta.",
        _PULIDO_SECCION_LIJADO_TRASERA, "2.2 P1200", "Cara",
    ),
    _criterio_pulido(
        "El colaborador realiza la inspección de salida (Check).",
        _PULIDO_SECCION_LIJADO_TRASERA, "2.2 P1200", "Lado",
    ),
    _criterio_pulido(
        "La mesa de trabajo y los IPK's se encuentran en buenas condiciones.",
        _PULIDO_SECCION_LIJADO_TRASERA, "2.2 P1200", "Lado",
    ),
    _criterio_pulido(
        "La iluminación se encuentra en buen estado.",
        _PULIDO_SECCION_LIJADO_TRASERA, "2.2 P1200", "Lado",
    ),
    _criterio_pulido(
        "El colaborador está entrenado y cuenta con la hoja de validación.",
        _PULIDO_SECCION_MECANISMO,
    ),
    _criterio_pulido(
        "El colaborador realiza la inspección de entrada (Check).",
        _PULIDO_SECCION_MECANISMO,
    ),
    _criterio_pulido(
        "Lijado contornos (Lija 15 M).",
        _PULIDO_SECCION_MECANISMO,
    ),
    _criterio_pulido(
        "El mecanismo tiene las protecciones adecuadas para no generar defectos en la operación.",
        _PULIDO_SECCION_MECANISMO,
    ),
    _criterio_pulido(
        "Validar que los RPM del mecanismo son 850 y que la presión de la plancha es la correcta.",
        _PULIDO_SECCION_MECANISMO,
    ),
    _criterio_pulido(
        "Asegurarse que tenga los insertos y/o cinta adhesiva bien colocados en el caso de necesitarlos.",
        _PULIDO_SECCION_MECANISMO,
    ),
    _criterio_pulido(
        "Pulir caras (solo usar barra Rosa), 4 aplicaciones.",
        _PULIDO_SECCION_MECANISMO,
    ),
    _criterio_pulido(
        "Pulir cuello / neck pocket.",
        _PULIDO_SECCION_MECANISMO,
    ),
    _criterio_pulido(
        "El colaborador realiza la inspección de salida buscando orbitales (Check).",
        _PULIDO_SECCION_MECANISMO,
    ),
]

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


def _seed_areas(session: Session) -> None:
    """Crea las áreas iniciales si no existen. Es idempotente."""
    for nombre, descripcion in _AREAS_INICIALES:
        existente = session.exec(select(Area).where(Area.nombre == nombre)).first()
        if existente is None:
            session.add(Area(nombre=nombre, descripcion=descripcion, activa=True))

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


def _seed_auditoria_pulido(session: Session) -> None:
    """Crea la auditoría de proceso para Pulido con sus 49 criterios.

    Es idempotente y correctiva: busca por nombre la auditoría y los criterios
    por auditoria_id + orden. No duplica si ya existen; si un criterio ya
    existe, sincroniza su descripción y jerarquía para corregir datos previos
    sin crear filas nuevas.
    """
    capa = session.exec(select(Capa).where(Capa.nombre == "Auditor")).first()
    if capa is None:
        raise ValueError("La capa 'Auditor' no existe. Ejecute primero el seed de capas.")

    area = session.exec(select(Area).where(Area.nombre == "Pulido")).first()
    if area is None:
        raise ValueError("El área 'Pulido' no existe.")

    frecuencia = session.exec(select(Frecuencia).where(Frecuencia.nombre == "Diaria")).first()
    if frecuencia is None:
        raise ValueError("La frecuencia 'Diaria' no existe. Ejecute primero el seed de frecuencias.")

    auditoria = session.exec(
        select(Auditoria).where(Auditoria.nombre == _AUDITORIA_PULIDO_NOMBRE)
    ).first()

    if auditoria is None:
        auditoria = Auditoria(
            nombre=_AUDITORIA_PULIDO_NOMBRE,
            descripcion=_AUDITORIA_PULIDO_DESCRIPCION,
            activa=True,
            capa_id=capa.id,
            frecuencia_id=frecuencia.id,
            area_id=area.id,
        )
        session.add(auditoria)
        session.flush()

    for i, (descripcion, seccion, subseccion, subtitulo) in enumerate(
        _CRITERIOS_PULIDO, start=1
    ):
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
                    seccion=seccion,
                    subseccion=subseccion,
                    subtitulo=subtitulo,
                )
            )
        else:
            existente.descripcion = descripcion
            existente.seccion = seccion
            existente.subseccion = subseccion
            existente.subtitulo = subtitulo
            session.add(existente)

    session.commit()


def _seed_auditoria_verificacion_supervisor(session: Session) -> None:
    """Crea la auditoría de verificación del Supervisor para cada área.

    Es idempotente y correctiva: busca por nombre la auditoría y los criterios
    por auditoria_id + orden. No duplica si ya existen; si un criterio ya
    existe, sincroniza su descripción. Las auditorías usan ``tipo_respuesta``
    ``cumplimiento`` (Cumple / No cumple / No aplica).
    """
    capa = session.exec(select(Capa).where(Capa.nombre == "Supervisor")).first()
    if capa is None:
        raise ValueError("La capa 'Supervisor' no existe. Ejecute primero el seed de capas.")

    frecuencia = session.exec(
        select(Frecuencia).where(Frecuencia.nombre == "Semanal")
    ).first()
    if frecuencia is None:
        raise ValueError("La frecuencia 'Semanal' no existe.")

    areas = session.exec(select(Area).where(Area.activa == True)).all()

    for area in areas:
        nombre = f"{_AUDITORIA_VERIFICACION_SUFIJO} - {area.nombre}"

        auditoria = session.exec(
            select(Auditoria).where(Auditoria.nombre == nombre)
        ).first()

        if auditoria is None:
            auditoria = Auditoria(
                nombre=nombre,
                descripcion=_AUDITORIA_VERIFICACION_DESCRIPCION,
                activa=True,
                tipo_respuesta=_AUDITORIA_VERIFICACION_TIPO_RESPUESTA,
                capa_id=capa.id,
                frecuencia_id=frecuencia.id,
                area_id=area.id,
            )
            session.add(auditoria)
            session.flush()
        elif auditoria.tipo_respuesta != _AUDITORIA_VERIFICACION_TIPO_RESPUESTA:
            auditoria.tipo_respuesta = _AUDITORIA_VERIFICACION_TIPO_RESPUESTA
            session.add(auditoria)

        for i, descripcion in enumerate(_CRITERIOS_VERIFICACION_SUPERVISOR, start=1):
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
            else:
                existente.descripcion = descripcion
                session.add(existente)

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
        _seed_areas(session)
        _seed_auditoria_ensamble_final(session)
        _seed_auditoria_pulido(session)
        _seed_auditoria_verificacion_supervisor(session)

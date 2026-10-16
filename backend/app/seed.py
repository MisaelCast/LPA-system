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

_ROLES_INICIALES = ["Administrador", "Gerente", "Supervisor", "Auditor", "Responsable de Manufactura"]
_CAPAS_INICIALES = ["Auditor", "Supervisor", "Gerente"]
_AREAS_INICIALES = [
    ("Ensamble Final", "Área de ensamble final de producto."),
    ("Pulido", "Área de pulido de producto."),
]
_FRECUENCIAS_INICIALES = [
    ("Diaria", "Cada dia", 1),
    ("Semanal", "Cada semana", 7),
    ("Quincenal", "Cada quince dias", 15),
    ("Mensual", "Cada mes", 30),
    ("Bimestral", "Cada dos meses", 60),
    ("Trimestral", "Cada tres meses", 90),
    ("Anual", "Cada año", 365),
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

_AUDITORIA_VERIFICACION_SUFIJO = "Auditoría de Verificación"
_AUDITORIA_VERIFICACION_DESCRIPCION = (
    "Verificación semanal del trabajo del Auditor (meta-auditoría)."
)
_AUDITORIA_VERIFICACION_TIPO_RESPUESTA = "cumplimiento"
_AUDITORIA_VERIFICACION_DIA_SEMANA = 3  # jueves (0=Lunes..6=Domingo)

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

_PULIDO_AUDITORIAS: list[tuple[str, list[str]]] = [
    (
        "Pulido - Lijado de Cara Frontal",
        [
            "El colaborador está entrenado y cuenta con la hoja de validación vigente.",
            "El colaborador realiza la inspección de entrada (Check) de la pieza.",
            "La lijadora orbital cuenta con el tope pokayoke para RPM y está a 3/8 de vuelta.",
            "El colaborador inicia el lijado por la parte superior (cuernos) con tres ciclos e intervalos de limpieza.",
            "El colaborador realiza el lijado de cara frontal con tres ciclos de 8-9 recorridos por ciclo.",
            'Aplica el método "H" o cruzado haciendo dos intervalos de limpieza por ciclo.',
            "Consume dos caras por lija (GRANO 1000) y limpia la lija con borrador después de cada ciclo.",
        ],
    ),
    (
        "Pulido - Lijado de Cara Trasera",
        [
            "El colaborador está entrenado y cuenta con la hoja de validación vigente.",
            "El colaborador realiza la inspección de entrada (Check) de la pieza.",
            "La lijadora orbital cuenta con el tope pokayoke para RPM y está a 3/8 de vuelta.",
            "El colaborador realiza el lijado de cara trasera con el recorrido y los ciclos establecidos.",
            "Mantiene presión y tiempo uniformes para evitar sobre-lijado en la cara trasera.",
            "Limpia la pieza y la lija entre ciclos sin accionar la orbital sobre la almohadilla.",
            "Verifica visualmente la uniformidad y la ausencia de marcas en la cara trasera.",
        ],
    ),
    (
        "Pulido - Lijado de Laterales",
        [
            "El colaborador está entrenado y cuenta con la hoja de validación vigente.",
            "El colaborador realiza la inspección de entrada (Check) de la pieza.",
            "Emplea la herramienta o boquilla adecuada para el lijado de laterales.",
            "Realiza el lijado de laterales con el recorrido y los ciclos definidos.",
            "Evita redondear bordes o aristas fuera de especificación.",
            "Limpia la lija y la pieza entre ciclos.",
            "Confirma un acabado uniforme en ambos laterales.",
        ],
    ),
    (
        "Pulido - Mecanismo y Manejo de la Pieza",
        [
            "El colaborador está entrenado y cuenta con la hoja de validación vigente.",
            "Manipula la pieza con el mecanismo o dispositivo correcto sin dañar la superficie.",
            "Utiliza el equipo de protección personal y el manejo ergonómico establecido.",
            "El dispositivo de sujeción está en buen estado y calibrado.",
            "No acciona la orbital sobre la almohadilla al limpiar la lija.",
            "Sigue la secuencia de manejo de la pieza para evitar re-trabajos.",
            "Verifica que la pieza no presente daños por manejo.",
        ],
    ),
    (
        "Pulido - Inspección Final y Limpieza",
        [
            "El colaborador está entrenado y cuenta con la hoja de validación vigente.",
            "Realiza la inspección de salida (Check) contra el estándar.",
            "Verifica la ausencia de rebaba y marcas, y la uniformidad del acabado.",
            "Confirma que la pieza esté libre de residuos y polvo.",
            "Registra la inspección en el formato correspondiente.",
            "Ordena y limpia el puesto de trabajo al finalizar (5S).",
            "Coloca la pieza en el contenedor o ubicación correcta.",
        ],
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
            capa = Capa(
                nombre=nombre,
                descripcion=f"Capa de {nombre.lower()}",
                activa=True,
                requiere_celula=nombre != "Supervisor",
            )
            session.add(capa)
        elif (nombre == "Supervisor") and existente.requiere_celula:
            existente.requiere_celula = False
            session.add(existente)

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
    for nombre, descripcion, dias in _FRECUENCIAS_INICIALES:
        existente = session.exec(
            select(Frecuencia).where(Frecuencia.nombre == nombre)
        ).first()
        if existente is None:
            session.add(Frecuencia(nombre=nombre, descripcion=descripcion, dias=dias))
        elif existente.dias != dias:
            existente.dias = dias
            session.add(existente)

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
    """Reemplaza la auditoría de Pulido por 5 auditorías semanales.

    Crea (idempotente y correctiva) 5 auditorías de 7 criterios cada una,
    marcadas con ``programacion_semanal`` para que su día se sortee cada
    semana. La auditoría anterior "Auditoría de Proceso - Pulido" se
    desactiva para conservar su historial sin mostrarla.
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

    # Desactiva la auditoría previa de Pulido (conserva historial).
    anterior = session.exec(
        select(Auditoria).where(Auditoria.nombre == _AUDITORIA_PULIDO_NOMBRE)
    ).first()
    if anterior is not None and anterior.activa:
        anterior.activa = False
        session.add(anterior)

    for nombre, criterios in _PULIDO_AUDITORIAS:
        auditoria = session.exec(
            select(Auditoria).where(Auditoria.nombre == nombre)
        ).first()
        if auditoria is None:
            auditoria = Auditoria(
                nombre=nombre,
                descripcion=_AUDITORIA_PULIDO_DESCRIPCION,
                activa=True,
                programacion_semanal=True,
                capa_id=capa.id,
                frecuencia_id=frecuencia.id,
                area_id=area.id,
            )
            session.add(auditoria)
            session.flush()
        elif not auditoria.programacion_semanal:
            auditoria.programacion_semanal = True
            session.add(auditoria)

        for i, descripcion in enumerate(criterios, start=1):
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
                dia_semana=_AUDITORIA_VERIFICACION_DIA_SEMANA,
                capa_id=capa.id,
                frecuencia_id=frecuencia.id,
                area_id=area.id,
            )
            session.add(auditoria)
            session.flush()
        elif auditoria.tipo_respuesta != _AUDITORIA_VERIFICACION_TIPO_RESPUESTA:
            auditoria.tipo_respuesta = _AUDITORIA_VERIFICACION_TIPO_RESPUESTA
            session.add(auditoria)

        if auditoria.dia_semana != _AUDITORIA_VERIFICACION_DIA_SEMANA:
            auditoria.dia_semana = _AUDITORIA_VERIFICACION_DIA_SEMANA
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

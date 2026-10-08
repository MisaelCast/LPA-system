"""Pruebas para la seed de la auditoría de Pulido."""

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.area import Area
from app.models.auditoria import Auditoria
from app.models.capa import Capa
from app.models.criterio import Criterio
from app.models.frecuencia import Frecuencia
from app.models.usuario import Usuario
from app.schemas.ejecucion_auditoria import EjecucionAuditoriaRead
from app.seed import (
    _AUDITORIA_PULIDO_DESCRIPCION,
    _AUDITORIA_PULIDO_NOMBRE,
    _AUDITORIA_VERIFICACION_SUFIJO,
    _CRITERIOS_PULIDO,
    _CRITERIOS_VERIFICACION_SUPERVISOR,
    _seed_areas,
    _seed_auditoria_pulido,
    _seed_auditoria_verificacion_supervisor,
    _seed_capas,
    _seed_frecuencias,
    _seed_roles,
)
from app.services.ejecucion_auditoria_service import EjecucionAuditoriaService


@pytest.fixture
def session():
    """Sesión sobre una base de datos SQLite en memoria con todas las tablas."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


class TestSeedAuditoriaPulido:
    """Pruebas de integración para la seed de la auditoría de Pulido."""

    def _preparar(self, session: Session) -> None:
        _seed_capas(session)
        _seed_frecuencias(session)
        _seed_areas(session)

    def _criterios(self, session: Session, auditoria: Auditoria) -> list[Criterio]:
        return list(
            session.exec(
                select(Criterio)
                .where(Criterio.auditoria_id == auditoria.id)
                .order_by(Criterio.orden)
            ).all()
        )

    def test_crea_auditoria_pulido_correctamente(self, session: Session):
        """Verifica que la auditoría de Pulido se cree con los datos esperados."""
        self._preparar(session)
        _seed_auditoria_pulido(session)

        auditoria = session.exec(
            select(Auditoria).where(Auditoria.nombre == _AUDITORIA_PULIDO_NOMBRE)
        ).first()

        assert auditoria is not None
        assert auditoria.descripcion == _AUDITORIA_PULIDO_DESCRIPCION
        assert auditoria.activa is True

        capa = session.get(Capa, auditoria.capa_id)
        area = session.get(Area, auditoria.area_id)
        frecuencia = session.get(Frecuencia, auditoria.frecuencia_id)

        assert capa.nombre == "Auditor"
        assert area.nombre == "Pulido"
        assert frecuencia.nombre == "Diaria"

    def test_tiene_exactamente_49_criterios_ordenados(self, session: Session):
        """Verifica 49 criterios con orden del 1 al 49."""
        self._preparar(session)
        _seed_auditoria_pulido(session)

        auditoria = session.exec(
            select(Auditoria).where(Auditoria.nombre == _AUDITORIA_PULIDO_NOMBRE)
        ).first()

        criterios = self._criterios(session, auditoria)

        assert len(criterios) == 49
        assert [c.orden for c in criterios] == list(range(1, 50))

    def test_descripciones_limpias_sin_repetir_jerarquia(self, session: Session):
        """Verifica que ningún criterio repita títulos/subtítulos en su descripción."""
        self._preparar(session)
        _seed_auditoria_pulido(session)

        auditoria = session.exec(
            select(Auditoria).where(Auditoria.nombre == _AUDITORIA_PULIDO_NOMBRE)
        ).first()

        criterios = self._criterios(session, auditoria)

        for c in criterios:
            assert " > " not in c.descripcion
            assert "LIJADO CARA FRONTAL" not in c.descripcion
            assert "LIJADO CARA TRASERA" not in c.descripcion
            assert "MECANISMO" not in c.descripcion
            assert "P1000" not in c.descripcion
            assert "P1200" not in c.descripcion

        # Muestra de control: el primer criterio solo contiene su descripción.
        assert criterios[0].descripcion == (
            "El colaborador está entrenado y cuenta con la hoja de validación."
        )

    def test_criterios_conservan_jerarquia_estructurada(self, session: Session):
        """Verifica que la jerarquía se guarde en campos separados."""
        self._preparar(session)
        _seed_auditoria_pulido(session)

        auditoria = session.exec(
            select(Auditoria).where(Auditoria.nombre == _AUDITORIA_PULIDO_NOMBRE)
        ).first()

        criterios = self._criterios(session, auditoria)

        assert criterios[0].seccion == "1. LIJADO CARA FRONTAL"
        assert criterios[0].subseccion == "1.1 P1000"
        assert criterios[0].subtitulo == "Cara"

        assert criterios[16].seccion == "1. LIJADO CARA FRONTAL"
        assert criterios[16].subseccion == "1.2 P1200"
        assert criterios[16].subtitulo == "Lado"

        assert criterios[19].seccion == "2. LIJADO CARA TRASERA"
        assert criterios[19].subseccion == "2.1 P1000"
        assert criterios[19].subtitulo == "Cara"

        assert criterios[40].seccion == "3. MECANISMO"
        assert criterios[40].subseccion is None
        assert criterios[40].subtitulo is None

    def test_seed_es_idempotente(self, session: Session):
        """Verifica que re-ejecutar el seed no duplique auditoría ni criterios."""
        self._preparar(session)
        _seed_auditoria_pulido(session)
        _seed_auditoria_pulido(session)

        auditorias = session.exec(
            select(Auditoria).where(Auditoria.nombre == _AUDITORIA_PULIDO_NOMBRE)
        ).all()
        assert len(auditorias) == 1

        criterios = self._criterios(session, auditorias[0])
        assert len(criterios) == 49
        assert len(_CRITERIOS_PULIDO) == 49

    def test_seed_corrige_descripciones_previas(self, session: Session):
        """Verifica que el seed corrija datos previos con la jerarquía repetida."""
        self._preparar(session)
        _seed_auditoria_pulido(session)

        auditoria = session.exec(
            select(Auditoria).where(Auditoria.nombre == _AUDITORIA_PULIDO_NOMBRE)
        ).first()

        # Simula el formato antiguo: jerarquía embebida y campos nulos.
        primero = self._criterios(session, auditoria)[0]
        primero.descripcion = (
            "1. LIJADO CARA FRONTAL > 1.1 P1000 > Cara: "
            "El colaborador está entrenado y cuenta con la hoja de validación."
        )
        primero.seccion = None
        primero.subseccion = None
        primero.subtitulo = None
        session.add(primero)
        session.commit()

        _seed_auditoria_pulido(session)

        criterios = self._criterios(session, auditoria)
        assert len(criterios) == 49
        assert criterios[0].descripcion == (
            "El colaborador está entrenado y cuenta con la hoja de validación."
        )
        assert criterios[0].seccion == "1. LIJADO CARA FRONTAL"
        assert criterios[0].subseccion == "1.1 P1000"
        assert criterios[0].subtitulo == "Cara"

    def test_jerarquia_se_serializa_en_la_respuesta_de_ejecucion(
        self, session: Session
    ):
        """Verifica que la jerarquía llegue al frontend en los criterios."""
        self._preparar(session)
        _seed_auditoria_pulido(session)

        rol_admin = _seed_roles(session)
        usuario = Usuario(
            nombre="Auditor Test",
            correo="auditor.test@lpa.com",
            contrasena_hash="x",
            activo=True,
            rol_id=rol_admin.id,
        )
        session.add(usuario)
        session.commit()
        session.refresh(usuario)

        auditoria = session.exec(
            select(Auditoria).where(Auditoria.nombre == _AUDITORIA_PULIDO_NOMBRE)
        ).first()

        from app.models.celula import Celula

        celula = Celula(numero=1, activa=True, area_id=auditoria.area_id)
        session.add(celula)
        session.commit()
        session.refresh(celula)

        service = EjecucionAuditoriaService(session)
        ejecucion = service.iniciar(auditoria.id, usuario, celula_id=celula.id)
        ejecucion = service.obtener_por_id(ejecucion.id)

        leido = EjecucionAuditoriaRead.model_validate(ejecucion, from_attributes=True)

        assert len(leido.criterios) == 49
        assert leido.criterios[0].seccion == "1. LIJADO CARA FRONTAL"
        assert leido.criterios[0].subseccion == "1.1 P1000"
        assert leido.criterios[0].subtitulo == "Cara"
        assert leido.criterios[40].seccion == "3. MECANISMO"
        assert leido.criterios[40].subseccion is None
        assert leido.criterios[40].subtitulo is None


class TestSeedAuditoriaVerificacionSupervisor:
    """Pruebas de integración para la seed de verificación del Supervisor."""

    def _preparar(self, session: Session) -> None:
        _seed_capas(session)
        _seed_frecuencias(session)
        _seed_areas(session)

    def test_crea_una_auditoria_por_area(self, session: Session):
        self._preparar(session)
        _seed_auditoria_verificacion_supervisor(session)

        auditorias = session.exec(
            select(Auditoria).where(
                Auditoria.nombre.startswith(_AUDITORIA_VERIFICACION_SUFIJO)
            )
        ).all()

        assert len(auditorias) == 2

        for auditoria in auditorias:
            assert auditoria.tipo_respuesta == "cumplimiento"

            capa = session.get(Capa, auditoria.capa_id)
            frecuencia = session.get(Frecuencia, auditoria.frecuencia_id)
            assert capa.nombre == "Supervisor"
            assert frecuencia.nombre == "Semanal"

    def test_tiene_nueve_criterios_ordenados(self, session: Session):
        self._preparar(session)
        _seed_auditoria_verificacion_supervisor(session)

        auditorias = session.exec(
            select(Auditoria).where(
                Auditoria.nombre.startswith(_AUDITORIA_VERIFICACION_SUFIJO)
            )
        ).all()

        for auditoria in auditorias:
            criterios = list(
                session.exec(
                    select(Criterio)
                    .where(Criterio.auditoria_id == auditoria.id)
                    .order_by(Criterio.orden)
                ).all()
            )
            assert len(criterios) == 9
            assert [c.orden for c in criterios] == list(range(1, 10))
            assert [c.descripcion for c in criterios] == _CRITERIOS_VERIFICACION_SUPERVISOR

    def test_seed_es_idempotente(self, session: Session):
        self._preparar(session)
        _seed_auditoria_verificacion_supervisor(session)
        _seed_auditoria_verificacion_supervisor(session)

        auditorias = session.exec(
            select(Auditoria).where(
                Auditoria.nombre.startswith(_AUDITORIA_VERIFICACION_SUFIJO)
            )
        ).all()
        assert len(auditorias) == 2

        for auditoria in auditorias:
            criterios = list(
                session.exec(
                    select(Criterio).where(Criterio.auditoria_id == auditoria.id)
                ).all()
            )
            assert len(criterios) == 9

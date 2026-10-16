"""Pruebas para la seed de las auditorías de Pulido."""

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.area import Area
from app.models.auditoria import Auditoria
from app.models.capa import Capa
from app.models.criterio import Criterio
from app.models.frecuencia import Frecuencia
from app.seed import (
    _AUDITORIA_PULIDO_DESCRIPCION,
    _AUDITORIA_PULIDO_NOMBRE,
    _AUDITORIA_VERIFICACION_SUFIJO,
    _CRITERIOS_VERIFICACION_SUPERVISOR,
    _PULIDO_AUDITORIAS,
    _seed_areas,
    _seed_auditoria_pulido,
    _seed_auditoria_verificacion_supervisor,
    _seed_capas,
    _seed_frecuencias,
)


@pytest.fixture
def session():
    """Sesión sobre una base de datos SQLite en memoria con todas las tablas."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


class TestSeedAuditoriaPulido:
    """Pruebas de integración para la seed de las 5 auditorías de Pulido."""

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

    def test_crea_cinco_auditorias_con_siete_criterios(self, session: Session):
        self._preparar(session)
        _seed_auditoria_pulido(session)

        for nombre, criterios_esperados in _PULIDO_AUDITORIAS:
            auditoria = session.exec(
                select(Auditoria).where(Auditoria.nombre == nombre)
            ).first()
            assert auditoria is not None
            assert auditoria.activa is True
            assert auditoria.programacion_semanal is True
            assert auditoria.descripcion == _AUDITORIA_PULIDO_DESCRIPCION

            capa = session.get(Capa, auditoria.capa_id)
            area = session.get(Area, auditoria.area_id)
            frecuencia = session.get(Frecuencia, auditoria.frecuencia_id)
            assert capa.nombre == "Auditor"
            assert area.nombre == "Pulido"
            assert frecuencia.nombre == "Diaria"

            criterios = self._criterios(session, auditoria)
            assert len(criterios) == 7
            assert [c.orden for c in criterios] == list(range(1, 8))
            assert [c.descripcion for c in criterios] == criterios_esperados

    def test_desactiva_la_auditoria_anterior_de_pulido(self, session: Session):
        self._preparar(session)
        capa = session.exec(select(Capa).where(Capa.nombre == "Auditor")).first()
        area = session.exec(select(Area).where(Area.nombre == "Pulido")).first()
        frecuencia = session.exec(
            select(Frecuencia).where(Frecuencia.nombre == "Diaria")
        ).first()
        session.add(
            Auditoria(
                nombre=_AUDITORIA_PULIDO_NOMBRE,
                activa=True,
                capa_id=capa.id,
                frecuencia_id=frecuencia.id,
                area_id=area.id,
            )
        )
        session.commit()

        _seed_auditoria_pulido(session)

        anterior = session.exec(
            select(Auditoria).where(Auditoria.nombre == _AUDITORIA_PULIDO_NOMBRE)
        ).first()
        assert anterior.activa is False

    def test_seed_es_idempotente(self, session: Session):
        self._preparar(session)
        _seed_auditoria_pulido(session)
        _seed_auditoria_pulido(session)

        for nombre, _ in _PULIDO_AUDITORIAS:
            auditorias = session.exec(
                select(Auditoria).where(Auditoria.nombre == nombre)
            ).all()
            assert len(auditorias) == 1
            assert len(self._criterios(session, auditorias[0])) == 7

    def test_cinco_auditorias_de_siete_criterios(self):
        assert len(_PULIDO_AUDITORIAS) == 5
        assert all(len(c) == 7 for _, c in _PULIDO_AUDITORIAS)


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

"""Pruebas del sorteo semanal de auditorías (Pulido)."""

from datetime import datetime, timezone

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.area import Area
from app.models.auditoria import Auditoria
from app.models.capa import Capa
from app.models.celula import Celula
from app.models.ejecucion_auditoria import EjecucionAuditoria
from app.models.frecuencia import Frecuencia
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.models.usuario_area import UsuarioArea
from app.services.programacion_semanal_service import (
    asegurar_semana,
    auditoria_del_dia,
    calendario_de_semana,
    lunes_de,
    plan_semanal_usuario,
)
from app.services.programacion_service import generar_pendientes


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _base(session: Session, n: int = 5) -> list[Auditoria]:
    capa = Capa(nombre="Auditor", descripcion="", activa=True, requiere_celula=True)
    frecuencia = Frecuencia(nombre="Diaria", descripcion="", dias=1)
    area = Area(nombre="Pulido", descripcion="", activa=True)
    session.add(capa)
    session.add(frecuencia)
    session.add(area)
    session.commit()
    session.refresh(capa)
    session.refresh(frecuencia)
    session.refresh(area)

    auditorias = []
    for i in range(n):
        a = Auditoria(
            nombre=f"Pulido - Tema {i + 1}",
            activa=True,
            programacion_semanal=True,
            capa_id=capa.id,
            frecuencia_id=frecuencia.id,
            area_id=area.id,
        )
        session.add(a)
        auditorias.append(a)
    session.commit()
    for a in auditorias:
        session.refresh(a)
    return auditorias


# Lunes y viernes de una semana de referencia (2026-10-12 es lunes).
LUNES = datetime(2026, 10, 12, 10, 0, tzinfo=timezone.utc)


class TestSorteo:
    def test_asigna_los_cinco_dias_sin_repetir(self, session: Session):
        auditorias = _base(session)
        filas = asegurar_semana(session, auditorias, lunes_de(LUNES))

        assert len(filas) == 5
        assert {f.dia_semana for f in filas} == {0, 1, 2, 3, 4}
        # Cada auditoría aparece exactamente una vez.
        ids = [f.auditoria_id for f in filas]
        assert sorted(ids) == sorted(a.id for a in auditorias)

    def test_es_idempotente_y_conserva_asignaciones(self, session: Session):
        auditorias = _base(session)
        semana = lunes_de(LUNES)
        primera = {f.dia_semana: f.auditoria_id
                   for f in asegurar_semana(session, auditorias, semana)}

        segunda = {f.dia_semana: f.auditoria_id
                   for f in asegurar_semana(session, auditorias, semana)}

        assert primera == segunda

    def test_nueva_semana_no_modifica_la_anterior(self, session: Session):
        auditorias = _base(session)
        semana1 = lunes_de(LUNES)
        anterior = {f.dia_semana: f.auditoria_id
                    for f in asegurar_semana(session, auditorias, semana1)}

        semana2 = lunes_de(datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc))
        asegurar_semana(session, auditorias, semana2)

        # La semana anterior permanece intacta.
        actual = {f.dia_semana: f.auditoria_id
                  for f in asegurar_semana(session, auditorias, semana1)}
        assert actual == anterior


class TestAuditoriaDelDia:
    def test_mapea_cada_dia_habil(self, session: Session):
        auditorias = _base(session)
        mapa = calendario_de_semana(session, auditorias, LUNES)

        for dia in range(5):
            momento = LUNES.replace(day=12 + dia)
            del_dia = auditoria_del_dia(session, auditorias, momento)
            assert del_dia is not None
            assert del_dia.id == mapa[dia].id

    def test_fin_de_semana_sin_auditoria(self, session: Session):
        auditorias = _base(session)
        sabado = datetime(2026, 10, 17, 10, 0, tzinfo=timezone.utc)
        domingo = datetime(2026, 10, 18, 10, 0, tzinfo=timezone.utc)
        assert auditoria_del_dia(session, auditorias, sabado) is None
        assert auditoria_del_dia(session, auditorias, domingo) is None


class TestGeneracionRespetandoSorteo:
    def _auditor_de_area(self, session: Session, area_id: int) -> Usuario:
        rol = session.exec(select(Rol).where(Rol.nombre == "Auditor")).first()
        if rol is None:
            rol = Rol(nombre="Auditor", descripcion="")
            session.add(rol)
            session.commit()
            session.refresh(rol)
        usuario = Usuario(
            nombre="Auditor Pulido",
            correo="auditor.pulido@lpa.com",
            contrasena_hash="x",
            activo=True,
            rol_id=rol.id,
        )
        session.add(usuario)
        session.commit()
        session.refresh(usuario)
        session.add(UsuarioArea(usuario_id=usuario.id, area_id=area_id))
        session.commit()
        return usuario

    def test_genera_pendiente_solo_del_dia_sorteado(self, session: Session):
        auditorias = _base(session)
        area_id = auditorias[0].area_id
        auditor = self._auditor_de_area(session, area_id)
        session.add(Celula(numero=1, activa=True, area_id=area_id))
        session.commit()

        generar_pendientes(session, LUNES)

        ejecuciones = list(
            session.exec(select(EjecucionAuditoria)).all()
        )
        assert len(ejecuciones) == 1

        del_dia = auditoria_del_dia(session, auditorias, LUNES)
        assert ejecuciones[0].auditoria_id == del_dia.id
        assert ejecuciones[0].usuario_id == auditor.id


class TestPlanSemanal:
    """Pruebas del plan lunes a viernes que se muestra a auditor/supervisor."""

    def _usuario(self, session: Session, rol_nombre: str, area_id: int | None = None) -> Usuario:
        rol = session.exec(select(Rol).where(Rol.nombre == rol_nombre)).first()
        if rol is None:
            rol = Rol(nombre=rol_nombre, descripcion="")
            session.add(rol)
            session.commit()
            session.refresh(rol)
        usuario = Usuario(
            nombre=f"Usuario {rol_nombre}",
            correo=f"{rol_nombre.lower()}@lpa.com",
            contrasena_hash="x",
            activo=True,
            rol_id=rol.id,
        )
        session.add(usuario)
        session.commit()
        session.refresh(usuario)
        if area_id is not None:
            session.add(UsuarioArea(usuario_id=usuario.id, area_id=area_id))
            session.commit()
            session.refresh(usuario)
        return usuario

    def test_muestra_lunes_a_viernes_con_el_sorteo(self, session: Session):
        auditorias = _base(session)
        usuario = self._usuario(session, "Auditor", auditorias[0].area_id)

        plan = plan_semanal_usuario(session, usuario, LUNES)

        assert plan.semana_inicio == "2026-10-12"
        assert plan.semana_fin == "2026-10-18"
        assert [a.area_nombre for a in plan.areas] == ["Pulido"]
        dias = plan.areas[0].dias
        assert [d.nombre_dia for d in dias] == [
            "Lunes", "Martes", "Miércoles", "Jueves", "Viernes",
        ]
        assert {d.auditoria_id for d in dias} == {a.id for a in auditorias}
        assert all(d.auditoria_nombre for d in dias)
        # Solo el día de referencia está marcado como «hoy».
        assert [d.es_hoy for d in dias].count(True) == 1
        assert dias[0].es_hoy is True

    def test_admin_ve_todas_las_areas_con_sorteo(self, session: Session):
        _base(session)
        session.add(Area(nombre="Ensamble Final", descripcion="", activa=True))
        session.commit()
        usuario = self._usuario(session, "Administrador")

        plan = plan_semanal_usuario(session, usuario, LUNES)

        assert [a.area_nombre for a in plan.areas] == ["Pulido"]

    def test_auditor_sin_areas_asignadas_no_ve_plan(self, session: Session):
        _base(session)
        usuario = self._usuario(session, "Auditor")

        plan = plan_semanal_usuario(session, usuario, LUNES)

        assert plan.areas == []

"""Pruebas de programación de auditorías (pendientes, frecuencia, asignación)."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from unittest.mock import patch

from app.models.area import Area
from app.models.auditoria import Auditoria
from app.models.auditoria_dia import AuditoriaDia
from app.models.capa import Capa
from app.models.celula import Celula
from app.models.criterio import Criterio
from app.models.ejecucion_auditoria import EjecucionAuditoria
from app.models.hallazgo import Hallazgo
from app.models.respuesta import Respuesta
from app.models.frecuencia import Frecuencia
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.models.usuario_area import UsuarioArea
from app.models.usuario_celula import UsuarioCelula
from app.models.usuario_supervisor import UsuarioSupervisor
from app.seed import _seed_areas, _seed_auditoria_ensamble_final, _seed_auditoria_verificacion_supervisor, _seed_capas, _seed_frecuencias, _seed_roles
from app.services.ejecucion_auditoria_service import (
    DiaNoHabilitadoError,
    EjecucionAbiertaError,
    EjecucionAuditoriaService,
)
from app.services.hallazgo_service import HallazgoService
from app.services.programacion_service import (
    fecha_habilita,
    generar_pendientes,
    inicio_periodo,
    periodo_auditoria,
    siguiente_habilita,
)
from app.services.programacion_semanal_service import plan_semanal_usuario
from app.services.usuario_service import UsuarioService


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _usuario(session: Session, nombre: str, rol: str) -> Usuario:
    rol_id = session.exec(select(Rol).where(Rol.nombre == rol)).first().id
    usuario = Usuario(
        nombre=nombre, correo=f"{nombre}@lpa.com", contrasena_hash="x",
        activo=True, rol_id=rol_id,
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


class TestInicioPeriodo:
    def test_diaria(self, session: Session):
        freq = Frecuencia(nombre="Diaria", descripcion="", dias=1)
        ahora = datetime(2026, 10, 6, 15, 30, tzinfo=timezone.utc)
        assert inicio_periodo(ahora, freq) == datetime(2026, 10, 6, tzinfo=timezone.utc)

    def test_semanal_inicia_lunes(self, session: Session):
        freq = Frecuencia(nombre="Semanal", descripcion="", dias=7)
        ahora = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)  # jueves
        assert inicio_periodo(ahora, freq) == datetime(2026, 10, 5, tzinfo=timezone.utc)  # lunes

    def test_quincenal(self, session: Session):
        freq = Frecuencia(nombre="Quincenal", descripcion="", dias=15)
        dia_1 = datetime(2026, 10, 5, tzinfo=timezone.utc)
        dia_20 = datetime(2026, 10, 20, tzinfo=timezone.utc)
        assert inicio_periodo(dia_1, freq) == datetime(2026, 10, 1, tzinfo=timezone.utc)
        assert inicio_periodo(dia_20, freq) == datetime(2026, 10, 16, tzinfo=timezone.utc)

    def test_mensual(self, session: Session):
        freq = Frecuencia(nombre="Mensual", descripcion="", dias=30)
        ahora = datetime(2026, 10, 20, tzinfo=timezone.utc)
        assert inicio_periodo(ahora, freq) == datetime(2026, 10, 1, tzinfo=timezone.utc)


class TestGenerarPendientes:
    def _base(self, session: Session) -> tuple[Area, Auditoria]:
        _seed_capas(session)
        _seed_frecuencias(session)
        _seed_roles(session)
        _seed_areas(session)
        area = session.exec(select(Area).where(Area.nombre == "Ensamble Final")).first()
        c1 = Celula(numero=1, activa=True, area_id=area.id)
        c2 = Celula(numero=2, activa=True, area_id=area.id)
        session.add(c1)
        session.add(c2)
        session.commit()
        session.refresh(c1)
        session.refresh(c2)
        return area, c1, c2

    def test_genera_por_celula_para_auditor_asignado(self, session: Session):
        area, c1, c2 = self._base(session)
        auditor = _usuario(session, "Ana Auditora", "Auditor")
        session.add(UsuarioCelula(usuario_id=auditor.id, celula_id=c1.id))
        session.commit()

        from app.seed import _seed_auditoria_ensamble_final
        _seed_auditoria_ensamble_final(session)
        auditoria = session.exec(
            select(Auditoria).where(Auditoria.nombre.like("%Ensamble%"))
        ).first()

        resultado = generar_pendientes(session)
        assert resultado["creadas"] == 1  # solo célula 1 asignada

        pendientes = list(
            session.exec(
                select(EjecucionAuditoria).where(
                    EjecucionAuditoria.estado == "pendiente"
                )
            ).all()
        )
        assert len(pendientes) == 1
        assert pendientes[0].auditoria_id == auditoria.id
        assert pendientes[0].celula_id == c1.id
        assert pendientes[0].usuario_id == auditor.id

    def test_idempotente(self, session: Session):
        area, c1, c2 = self._base(session)
        auditor = _usuario(session, "Ana Auditora", "Auditor")
        session.add(UsuarioCelula(usuario_id=auditor.id, celula_id=c1.id))
        session.commit()
        from app.seed import _seed_auditoria_ensamble_final
        _seed_auditoria_ensamble_final(session)

        generar_pendientes(session)
        generar_pendientes(session)

        pendientes = list(
            session.exec(select(EjecucionAuditoria)).all()
        )
        assert len(pendientes) == 1

    def test_supervisor_no_recibe_pendientes_de_proceso(self, session: Session):
        """El supervisor no recibe pendientes de auditorías de proceso."""
        area, c1, c2 = self._base(session)
        supervisor = _usuario(session, "Sergio Supervisor", "Supervisor")
        session.add(UsuarioArea(usuario_id=supervisor.id, area_id=area.id))
        session.commit()
        from app.seed import _seed_auditoria_ensamble_final
        _seed_auditoria_ensamble_final(session)

        generar_pendientes(session)

        pendientes = list(
            session.exec(
                select(EjecucionAuditoria).where(
                    EjecucionAuditoria.estado == "pendiente"
                )
            ).all()
        )
        assert pendientes == []

    def test_auditor_sin_celulas_especificas_cubre_todas(self, session: Session):
        """Auditor con área asignada y sin células cubre todas las del área."""
        area, c1, c2 = self._base(session)
        auditor = _usuario(session, "Ana Auditora", "Auditor")
        session.add(UsuarioArea(usuario_id=auditor.id, area_id=area.id))
        session.commit()
        from app.seed import _seed_auditoria_ensamble_final
        _seed_auditoria_ensamble_final(session)

        generar_pendientes(session)

        pendientes = list(
            session.exec(
                select(EjecucionAuditoria).where(
                    EjecucionAuditoria.estado == "pendiente"
                )
            ).all()
        )
        assert len(pendientes) == 2  # c1 y c2
        assert {p.celula_id for p in pendientes} == {c1.id, c2.id}


class TestPendientesServicio:
    def test_mis_pendientes_genera_e_inicia(self, session: Session):
        _seed_capas(session)
        _seed_frecuencias(session)
        _seed_roles(session)
        _seed_areas(session)
        ensamble = session.exec(select(Area).where(Area.nombre == "Ensamble Final")).first()
        celula = Celula(numero=1, activa=True, area_id=ensamble.id)
        session.add(celula)
        session.commit()
        session.refresh(celula)
        _seed_auditoria_ensamble_final(session)
        auditoria = session.exec(
            select(Auditoria).where(Auditoria.nombre.like("%Ensamble%"))
        ).first()
        auditor = _usuario(session, "Ana Auditora", "Auditor")
        session.add(UsuarioArea(usuario_id=auditor.id, area_id=ensamble.id))
        session.commit()

        service = EjecucionAuditoriaService(session)

        # Genera la pendiente al consultar (sin día fijado => Disponible hoy).
        items = service.mis_pendientes(auditor)
        assert len(items) == 1
        assert items[0]["estado"] == "disponible"
        assert items[0]["accion"] == "iniciar"
        ejec_id = items[0]["ejecucion_id"]
        assert ejec_id is not None

        iniciada = service.iniciar_pendiente(ejec_id, auditor)
        assert iniciada.estado == "en_proceso"

        # Iniciada pero no finalizada sigue apareciendo como "En progreso".
        items = service.mis_pendientes(auditor)
        assert len(items) == 1
        assert items[0]["estado"] == "en_progreso"
        assert items[0]["accion"] == "continuar"


    def _base_gerente(
        self, session: Session
    ) -> tuple[Usuario, Usuario, Auditoria]:
        _seed_capas(session)
        _seed_frecuencias(session)
        _seed_roles(session)
        _seed_areas(session)
        area = session.exec(
            select(Area).where(Area.nombre == "Ensamble Final")
        ).first()
        supervisor = _usuario(session, "Sergio Supervisor", "Supervisor")
        session.add(UsuarioArea(usuario_id=supervisor.id, area_id=area.id))
        gerente = _usuario(session, "Gina Gerente", "Gerente")
        session.add(
            UsuarioSupervisor(
                gerente_id=gerente.id, supervisor_id=supervisor.id
            )
        )
        capa = session.exec(select(Capa).where(Capa.nombre == "Gerente")).first()
        frecuencia = session.exec(
            select(Frecuencia).where(Frecuencia.nombre == "Semanal")
        ).first()
        auditoria = Auditoria(
            nombre="Auditoría de Verificación - Gerente",
            activa=True,
            tipo_respuesta="cumplimiento",
            capa_id=capa.id,
            frecuencia_id=frecuencia.id,
            area_id=area.id,
        )
        session.add(auditoria)
        session.commit()
        session.refresh(gerente)
        session.refresh(auditoria)
        return gerente, supervisor, auditoria

    def test_gerente_ejecuta_auditoria_disponible(self, session: Session):
        """El gerente ve y ejecuta su auditoría según las áreas de sus supervisores."""
        gerente, _, auditoria = self._base_gerente(session)
        service = EjecucionAuditoriaService(session)

        items = service.mis_pendientes(gerente)
        assert len(items) == 1
        item = items[0]
        assert item["auditoria_id"] == auditoria.id
        assert item["estado"] == "disponible"
        assert item["accion"] == "iniciar"
        assert item["ejecucion_id"] is not None

        iniciada = service.iniciar_pendiente(item["ejecucion_id"], gerente)
        assert iniciada.estado == "en_proceso"

    def test_generar_pendientes_incluye_gerente(self, session: Session):
        """La generación automática crea la pendiente también para el gerente."""
        gerente, supervisor, auditoria = self._base_gerente(session)

        generar_pendientes(session)

        pendientes = list(
            session.exec(
                select(EjecucionAuditoria).where(
                    EjecucionAuditoria.auditoria_id == auditoria.id,
                    EjecucionAuditoria.estado == "pendiente",
                )
            ).all()
        )
        assert {p.usuario_id for p in pendientes} == {
            gerente.id,
            supervisor.id,
        }


class TestAsignacionUsuario:
    def test_asignar_areas_y_celulas(self, session: Session):
        _seed_roles(session)
        _seed_areas(session)
        _seed_capas(session)
        area = session.exec(select(Area).where(Area.nombre == "Pulido")).first()
        celula = Celula(numero=5, activa=True, area_id=area.id)
        session.add(celula)
        session.commit()
        session.refresh(celula)

        auditor = _usuario(session, "Ana Auditora", "Auditor")
        service = UsuarioService(session)
        service.asignar(auditor.id, [area.id], [celula.id])

        asignacion = service.obtener_asignacion(auditor.id)
        assert asignacion["area_ids"] == [area.id]
        assert asignacion["celula_ids"] == [celula.id]

    def test_rechaza_celula_de_otra_area(self, session: Session):
        _seed_roles(session)
        _seed_areas(session)
        area1 = session.exec(select(Area).where(Area.nombre == "Pulido")).first()
        area2 = session.exec(select(Area).where(Area.nombre == "Ensamble Final")).first()
        celula1 = Celula(numero=1, activa=True, area_id=area1.id)
        celula2 = Celula(numero=1, activa=True, area_id=area2.id)
        session.add_all([celula1, celula2])
        session.commit()
        session.refresh(celula1)
        session.refresh(celula2)

        auditor = _usuario(session, "Ana Auditora", "Auditor")
        service = UsuarioService(session)
        with pytest.raises(ValueError):
            service.asignar(auditor.id, [area1.id], [celula2.id])

    def test_supervisor_no_puede_tener_celulas(self, session: Session):
        _seed_roles(session)
        _seed_areas(session)
        area = session.exec(select(Area).where(Area.nombre == "Pulido")).first()
        celula = Celula(numero=1, activa=True, area_id=area.id)
        session.add(celula)
        session.commit()
        session.refresh(celula)

        supervisor = _usuario(session, "Sergio Supervisor", "Supervisor")
        service = UsuarioService(session)
        with pytest.raises(ValueError):
            service.asignar(supervisor.id, [area.id], [celula.id])

        service.asignar(supervisor.id, [area.id], [])
        asignacion = service.obtener_asignacion(supervisor.id)
        assert asignacion["area_ids"] == [area.id]
        assert asignacion["celula_ids"] == []

    def test_gerente_asigna_supervisores(self, session: Session):
        _seed_roles(session)
        supervisor = _usuario(session, "Sergio Supervisor", "Supervisor")
        gerente = _usuario(session, "Gina Gerente", "Gerente")

        service = UsuarioService(session)
        service.asignar(gerente.id, [], [], [supervisor.id])

        asignacion = service.obtener_asignacion(gerente.id)
        assert asignacion["supervisor_ids"] == [supervisor.id]


class TestHallazgosPorArea:
    """El Supervisor/Gerente solo ve hallazgos de sus áreas asignadas."""

    def _plantar_hallazgo_ensamble(self, session: Session) -> Hallazgo:
        _seed_capas(session)
        _seed_frecuencias(session)
        _seed_roles(session)
        _seed_areas(session)
        _seed_auditoria_ensamble_final(session)
        auditoria = session.exec(
            select(Auditoria).where(Auditoria.nombre.like("%Ensamble%"))
        ).first()
        auditor = _usuario(session, "Ana Auditora", "Auditor")
        criterio = session.exec(
            select(Criterio).where(Criterio.auditoria_id == auditoria.id)
        ).first()
        ejecucion = EjecucionAuditoria(
            estado="finalizada",
            auditoria_id=auditoria.id,
            usuario_id=auditor.id,
            celula_id=None,
        )
        session.add(ejecucion)
        session.commit()
        session.refresh(ejecucion)
        respuesta = Respuesta(
            valor="R",
            ejecucion_auditoria_id=ejecucion.id,
            criterio_id=criterio.id,
        )
        session.add(respuesta)
        session.commit()
        session.refresh(respuesta)
        hallazgo = Hallazgo(
            descripcion="Desviación en Ensamble",
            respuesta_id=respuesta.id,
            estado="abierto",
        )
        session.add(hallazgo)
        session.commit()
        session.refresh(hallazgo)
        return hallazgo

    def test_supervisor_solo_ve_su_area(self, session: Session):
        hallazgo = self._plantar_hallazgo_ensamble(session)
        pulido = session.exec(select(Area).where(Area.nombre == "Pulido")).first()
        supervisor = _usuario(session, "Carlos", "Supervisor")
        session.add(UsuarioArea(usuario_id=supervisor.id, area_id=pulido.id))
        session.commit()

        service = HallazgoService(session)
        # Solo en Pulido → no ve el hallazgo de Ensamble.
        assert service.listar(supervisor) == []

        # Al asignarle Ensamble sí lo ve.
        ensamble = session.exec(select(Area).where(Area.nombre == "Ensamble Final")).first()
        session.add(UsuarioArea(usuario_id=supervisor.id, area_id=ensamble.id))
        session.commit()
        hallazgos = service.listar(supervisor)
        assert len(hallazgos) == 1
        assert hallazgos[0].id == hallazgo.id

    def test_administrador_ve_todo(self, session: Session):
        hallazgo = self._plantar_hallazgo_ensamble(session)
        admin = _usuario(session, "Admin", "Administrador")
        service = HallazgoService(session)
        assert [h.id for h in service.listar(admin)] == [hallazgo.id]


class TestProgramacionSemanal:
    """Auditorías semanales de Supervisor: solo se habilitan el jueves."""

    Z = 3  # jueves, configurado en la seed

    def _base(self, session: Session) -> tuple[Usuario, Auditoria]:
        _seed_capas(session)
        _seed_frecuencias(session)
        _seed_roles(session)
        _seed_areas(session)
        _seed_auditoria_verificacion_supervisor(session)
        ensamble = session.exec(
            select(Area).where(Area.nombre == "Ensamble Final")
        ).first()
        supervisor = _usuario(session, "Sergio", "Supervisor")
        session.add(UsuarioArea(usuario_id=supervisor.id, area_id=ensamble.id))
        session.commit()
        auditoria = session.exec(
            select(Auditoria).where(Auditoria.nombre.like("%Verificación%Ensamble%"))
        ).first()
        return supervisor, auditoria

    def _fijar_hoy(self, fecha: datetime) -> None:
        patch(
            "app.services.ejecucion_auditoria_service.ahora_business",
            return_value=fecha,
        ).start()
        patch(
            "app.services.programacion_service.ahora_business",
            return_value=fecha,
        ).start()

    def test_lunes_bloqueada_faltan_3_dias(self, session: Session):
        supervisor, _ = self._base(session)
        lunes = datetime(2026, 10, 5, 10, 0, tzinfo=timezone.utc)
        self._fijar_hoy(lunes)
        try:
            items = EjecucionAuditoriaService(session).mis_pendientes(supervisor)
        finally:
            patch.stopall()
        assert len(items) == 1
        item = items[0]
        assert item["estado"] == "bloqueada"
        assert item["contador"] == "Faltan 3 días"
        assert item["accion"] is None
        assert item["tooltip"] and "Jueves" in item["tooltip"]
        # No se generó ninguna ejecución.
        assert len(session.exec(select(EjecucionAuditoria)).all()) == 0

    def test_jueves_disponible(self, session: Session):
        supervisor, _ = self._base(session)
        jueves = datetime(2026, 10, 8, 10, 0, tzinfo=timezone.utc)
        self._fijar_hoy(jueves)
        try:
            items = EjecucionAuditoriaService(session).mis_pendientes(supervisor)
        finally:
            patch.stopall()
        assert items[0]["estado"] == "disponible"
        assert items[0]["contador"] == "Disponible hoy"
        assert items[0]["accion"] == "iniciar"
        assert items[0]["ejecucion_id"] is not None

    def test_iniciar_martes_rechazado(self, session: Session):
        supervisor, auditoria = self._base(session)
        martes = datetime(2026, 10, 6, 10, 0, tzinfo=timezone.utc)
        self._fijar_hoy(martes)
        try:
            service = EjecucionAuditoriaService(session)
            with pytest.raises(DiaNoHabilitadoError):
                service.iniciar(auditoria.id, supervisor, celula_id=None)
        finally:
            patch.stopall()

    def test_iniciar_jueves_ok_y_duplicada_rechazada(self, session: Session):
        supervisor, auditoria = self._base(session)
        jueves = datetime(2026, 10, 8, 10, 0, tzinfo=timezone.utc)
        self._fijar_hoy(jueves)
        try:
            service = EjecucionAuditoriaService(session)
            ejecucion = service.iniciar(auditoria.id, supervisor, celula_id=None)
            assert ejecucion.estado == "en_proceso"
            # Se intenta otra del mismo periodo -> duplicada (409).
            with pytest.raises(EjecucionAbiertaError):
                service.iniciar(auditoria.id, supervisor, celula_id=None)
        finally:
            patch.stopall()


class TestDiasSemanaRecurrentes:
    """Días hábiles elegidos al crear la auditoría (recurrencia semanal).

    Semana de referencia: lunes 2026-10-19 … viernes 2026-10-23.
    """

    LUNES = datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)
    MARTES = datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc)
    MIERCOLES = datetime(2026, 10, 21, 10, 0, tzinfo=timezone.utc)
    JUEVES = datetime(2026, 10, 22, 10, 0, tzinfo=timezone.utc)
    VIERNES = datetime(2026, 10, 23, 10, 0, tzinfo=timezone.utc)
    SABADO = datetime(2026, 10, 24, 10, 0, tzinfo=timezone.utc)

    @staticmethod
    def _auditoria_con_dias(dias: list[int]) -> Auditoria:
        auditoria = Auditoria(
            nombre="Control Martes Jueves",
            activa=True,
            capa_id=1,
            frecuencia_id=1,
        )
        object.__setattr__(auditoria, "dias_semana", dias)
        return auditoria

    @staticmethod
    def _frecuencia(dias: int = 7) -> Frecuencia:
        return Frecuencia(nombre="Semanal", descripcion="", dias=dias)

    def _fijar_hoy(self, fecha: datetime) -> None:
        patch(
            "app.services.ejecucion_auditoria_service.ahora_business",
            return_value=fecha,
        ).start()
        patch(
            "app.services.programacion_service.ahora_business",
            return_value=fecha,
        ).start()

    # ——— fecha_habilita / periodo / siguiente ———

    def test_fecha_habilita_hoy_es_un_dia_elegido(self):
        a = self._auditoria_con_dias([1, 3])
        medianoche = self.MARTES.replace(hour=0, minute=0, second=0, microsecond=0)
        assert fecha_habilita(a, self._frecuencia(), self.MARTES) == medianoche

    def test_fecha_habilita_proximo_dia_elegido(self):
        a = self._auditoria_con_dias([1, 3])
        medianoche = self.MARTES.replace(hour=0, minute=0, second=0, microsecond=0)
        # Lunes: sin días elegidos pasados → el próximo (martes de la semana).
        assert fecha_habilita(a, self._frecuencia(), self.LUNES) == medianoche

    def test_fecha_habilita_dia_elegido_pasado_queda_atrasada(self):
        a = self._auditoria_con_dias([1, 3])
        # Miércoles: el martes ya pasó → muestra el martes (atrasada); el
        # jueves se verá al completar el martes (siguiente_habilita).
        assert fecha_habilita(
            a, self._frecuencia(), self.MIERCOLES
        ) == datetime(2026, 10, 20, tzinfo=timezone.utc)
        # Viernes: el último día elegido pasó (jueves 22).
        assert fecha_habilita(
            a, self._frecuencia(), self.VIERNES
        ) == datetime(2026, 10, 22, tzinfo=timezone.utc)
        # Sábado también apunta al jueves pasado.
        assert fecha_habilita(
            a, self._frecuencia(), self.SABADO
        ) == datetime(2026, 10, 22, tzinfo=timezone.utc)

    def test_fecha_habilita_un_solo_dia_elegido(self):
        a = self._auditoria_con_dias([0])  # solo lunes
        # Viernes: el lunes de esta semana ya pasó → atrasada (lunes 19);
        # al completarlo, siguiente_habilita apunta al lunes 26.
        assert fecha_habilita(
            a, self._frecuencia(), self.VIERNES
        ) == datetime(2026, 10, 19, tzinfo=timezone.utc)
        assert siguiente_habilita(
            a, self._frecuencia(), datetime(2026, 10, 19, tzinfo=timezone.utc)
        ) == datetime(2026, 10, 26, tzinfo=timezone.utc)

    def test_periodo_es_la_fecha_del_dia_elegido(self):
        a = self._auditoria_con_dias([1, 3])
        # Cada día elegido tiene su propio periodo (una ejecución por día).
        assert periodo_auditoria(
            a, self._frecuencia(), self.MARTES
        ) == datetime(2026, 10, 20, tzinfo=timezone.utc)
        assert periodo_auditoria(
            a, self._frecuencia(), self.JUEVES
        ) == datetime(2026, 10, 22, tzinfo=timezone.utc)

    def test_siguiente_habilita_va_al_proximo_dia_elegido(self):
        a = self._auditoria_con_dias([1, 3])
        habilita = datetime(2026, 10, 20, tzinfo=timezone.utc)
        # Después del martes → jueves; después del jueves → martes siguiente.
        assert siguiente_habilita(
            a, self._frecuencia(), habilita
        ) == datetime(2026, 10, 22, tzinfo=timezone.utc)
        assert siguiente_habilita(
            a, self._frecuencia(), datetime(2026, 10, 22, tzinfo=timezone.utc)
        ) == datetime(2026, 10, 27, tzinfo=timezone.utc)

    # ——— generación de pendientes ———

    def _base_dias(
        self, session: Session, dias: list[int]
    ) -> tuple[Auditoria, Usuario, Celula]:
        _seed_capas(session)
        _seed_frecuencias(session)
        _seed_roles(session)
        _seed_areas(session)
        area = session.exec(
            select(Area).where(Area.nombre == "Ensamble Final")
        ).first()
        celula = Celula(numero=1, activa=True, area_id=area.id)
        session.add(celula)
        session.commit()
        session.refresh(celula)

        auditor = _usuario(session, "Ana Auditora", "Auditor")
        session.add(UsuarioArea(usuario_id=auditor.id, area_id=area.id))
        session.add(UsuarioCelula(usuario_id=auditor.id, celula_id=celula.id))
        session.commit()

        frecuencia = session.exec(
            select(Frecuencia).where(Frecuencia.nombre == "Semanal")
        ).first()
        capa = session.exec(select(Capa).where(Capa.nombre == "Auditor")).first()
        auditoria = Auditoria(
            nombre="Control por días",
            activa=True,
            capa_id=capa.id,
            frecuencia_id=frecuencia.id,
            area_id=area.id,
        )
        session.add(auditoria)
        session.commit()
        session.refresh(auditoria)
        for dia in dias:
            session.add(
                AuditoriaDia(auditoria_id=auditoria.id, dia_semana=dia)
            )
        session.commit()
        return auditoria, auditor, celula

    def test_genera_pendiente_en_cada_dia_elegido(self, session: Session):
        auditoria, auditor, _ = self._base_dias(session, [1, 3])

        # Martes: crea el pendiente del martes.
        generar_pendientes(session, ahora=self.MARTES)
        pendientes = list(session.exec(select(EjecucionAuditoria)).all())
        assert len(pendientes) == 1
        assert pendientes[0].fecha_programada.date() == self.MARTES.date()

        # Martes otra vez: idempotente.
        assert generar_pendientes(session, ahora=self.MARTES)["creadas"] == 0

        # Miércoles: no es un día elegido → no crea nada nuevo.
        assert generar_pendientes(session, ahora=self.MIERCOLES)["creadas"] == 0
        assert len(session.exec(select(EjecucionAuditoria)).all()) == 1

        # Jueves: crea la segunda ejecución de la semana (periodo propio).
        generar_pendientes(session, ahora=self.JUEVES)
        pendientes = list(session.exec(select(EjecucionAuditoria)).all())
        assert len(pendientes) == 2
        assert {p.fecha_programada.date() for p in pendientes} == {
            self.MARTES.date(),
            self.JUEVES.date(),
        }
        assert all(p.usuario_id == auditor.id for p in pendientes)

    def test_sin_dias_genera_segun_frecuencia(self, session: Session):
        """Sin días elegidos la frecuencia Semanal genera una vez por semana."""
        auditoria, _, _ = self._base_dias(session, [])
        generar_pendientes(session, ahora=self.LUNES)
        assert generar_pendientes(session, ahora=self.MIERCOLES)["creadas"] == 0
        assert len(session.exec(select(EjecucionAuditoria)).all()) == 1

    def test_dias_no_participan_en_el_sorteo(self, session: Session):
        """La auditoría con días elegidos no entra al sorteo semanal."""
        auditoria, _, _ = self._base_dias(session, [1, 3])
        assert auditoria.programacion_semanal is False
        admin = _usuario(session, "Admin Días", "Administrador")
        calendario = plan_semanal_usuario(session, admin, ahora=self.LUNES)
        nombres = [
            dia.auditoria_nombre
            for area in calendario.areas
            for dia in area.dias
            if dia.auditoria_nombre
        ]
        assert "Control por días" not in nombres

    # ——— estados en «Mis pendientes» ———

    def test_mis_pendientes_bloqueada_hasta_el_dia_elegido(self, session: Session):
        auditoria, auditor, _ = self._base_dias(session, [1])  # solo martes
        self._fijar_hoy(self.LUNES)
        try:
            items = EjecucionAuditoriaService(session).mis_pendientes(auditor)
        finally:
            patch.stopall()
        assert len(items) == 1
        item = items[0]
        assert item["estado"] == "bloqueada"
        assert item["contador"] == "Mañana"
        assert item["accion"] is None
        assert item["tooltip"] and "Martes" in item["tooltip"]
        assert len(session.exec(select(EjecucionAuditoria)).all()) == 0

    def test_mis_pendientes_disponible_el_dia_elegido(self, session: Session):
        auditoria, auditor, _ = self._base_dias(session, [1])
        self._fijar_hoy(self.MARTES)
        try:
            items = EjecucionAuditoriaService(session).mis_pendientes(auditor)
        finally:
            patch.stopall()
        assert items[0]["estado"] == "disponible"
        assert items[0]["accion"] == "iniciar"
        assert items[0]["ejecucion_id"] is not None

    def test_iniciar_fuera_del_dia_elegido_rechazado(self, session: Session):
        auditoria, auditor, celula = self._base_dias(session, [1])
        self._fijar_hoy(self.LUNES)
        try:
            service = EjecucionAuditoriaService(session)
            with pytest.raises(DiaNoHabilitadoError):
                service.iniciar(
                    auditoria.id, auditor, celula_id=celula.id
                )
        finally:
            patch.stopall()
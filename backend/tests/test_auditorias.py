"""Pruebas para el modulo de Auditorias."""

from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from app.models.area import Area
from app.models.auditoria import Auditoria
from app.models.capa import Capa
from app.models.frecuencia import Frecuencia
from app.schemas.auditoria import AuditoriaCreate, AuditoriaUpdate
from app.services.auditoria_service import AuditoriaService
from app.repositories.auditoria_repository import AuditoriaRepository
from app.services.capa_service import CapaService
from app.services.frecuencia_service import FrecuenciaService


def _usuario(rol: str, areas: list[Area] | None = None) -> MagicMock:
    """Usuario de prueba con rol y áreas asignadas."""
    usuario = MagicMock()
    usuario.rol.nombre = rol
    usuario.areas = areas or []
    return usuario


def _usuario_admin() -> MagicMock:
    return _usuario("Administrador")


def _usuario_supervisor(areas: list[Area] | None = None) -> MagicMock:
    return _usuario("Supervisor", areas)


def _usuario_gerente() -> MagicMock:
    return _usuario("Gerente")


def _capas_base() -> list[Capa]:
    return [
        Capa(id=1, nombre="Auditor", activa=True),
        Capa(id=2, nombre="Supervisor", activa=True),
        Capa(id=3, nombre="Gerente", activa=True),
    ]


class TestAuditoriaService:
    """Pruebas unitarias para AuditoriaService."""

    def setup_method(self):
        self.mock_session = MagicMock(spec=Session)
        self.service = AuditoriaService(self.mock_session)
        self.admin = _usuario_admin()

    def _mock_fk_get(self):
        """Mock de session.get para enriquecer_read."""
        self.mock_session.get.side_effect = lambda cls, id: MagicMock(
            spec=cls, nombre="Mock"
        )

    def test_crear_auditoria_exitoso(self):
        """Verifica que se pueda crear una auditoria con datos validos."""
        datos = AuditoriaCreate(
            nombre="Auditoria Proceso",
            descripcion="Descripcion de prueba",
            activa=True,
            capa_id=1,
            frecuencia_id=1,
            area_id=1,
        )

        self._mock_fk_get()

        with patch.object(
            CapaService, "obtener_por_id", return_value=MagicMock(spec=Capa)
        ):
            with patch.object(
                FrecuenciaService,
                "obtener_por_id",
                return_value=MagicMock(spec=Frecuencia),
            ):
                with patch.object(
                    AuditoriaRepository, "obtener_por_nombre", return_value=None
                ):
                    with patch.object(
                        AuditoriaRepository,
                        "crear",
                        return_value=Auditoria(id=1, **datos.model_dump()),
                    ):
                        resultado = self.service.crear(datos, self.admin)

        assert resultado.nombre == "Auditoria Proceso"
        assert resultado.capa_id == 1
        assert resultado.frecuencia_id == 1
        assert resultado.area_id == 1

    def test_crear_auditoria_nombre_duplicado(self):
        """Verifica que no se pueda crear con nombre duplicado."""
        datos = AuditoriaCreate(
            nombre="Duplicada", activa=True, capa_id=1, frecuencia_id=1
        )

        with patch.object(
            AuditoriaRepository,
            "obtener_por_nombre",
            return_value=Auditoria(
                id=1, nombre="Duplicada", capa_id=1, frecuencia_id=1
            ),
        ):
            with pytest.raises(ValueError, match="Ya existe una auditoria"):
                self.service.crear(datos, self.admin)

    def test_crear_auditoria_capa_inexistente(self):
        """Verifica que falle si la capa no existe."""
        datos = AuditoriaCreate(
            nombre="Test", activa=True, capa_id=999, frecuencia_id=1
        )

        with patch.object(AuditoriaRepository, "obtener_por_nombre", return_value=None):
            with patch.object(
                CapaService,
                "obtener_por_id",
                side_effect=ValueError("Capa no encontrada."),
            ):
                with pytest.raises(ValueError, match="La capa especificada no existe"):
                    self.service.crear(datos, self.admin)

    def test_obtener_por_id_existe(self):
        """Verifica que se obtenga una auditoria por ID."""
        auditoria = Auditoria(
            id=1,
            nombre="Test",
            activa=True,
            capa_id=1,
            frecuencia_id=1,
        )
        self._mock_fk_get()

        with patch.object(AuditoriaRepository, "obtener_por_id", return_value=auditoria):
            resultado = self.service.obtener_por_id(1)

        assert resultado.id == 1
        assert resultado.nombre == "Test"

    def test_obtener_por_id_no_existe(self):
        """Verifica que se lance error si no existe."""
        with patch.object(AuditoriaRepository, "obtener_por_id", return_value=None):
            with pytest.raises(ValueError, match="Auditoria no encontrada"):
                self.service.obtener_por_id(999)

    def test_actualizar_auditoria_exitoso(self):
        """Verifica que se actualice correctamente."""
        auditoria = Auditoria(
            id=1,
            nombre="Original",
            activa=True,
            capa_id=1,
            frecuencia_id=1,
        )
        datos = AuditoriaUpdate(nombre="Actualizada")

        self._mock_fk_get()

        with patch.object(AuditoriaRepository, "obtener_por_id", return_value=auditoria):
            with patch.object(
                AuditoriaRepository, "obtener_por_nombre", return_value=None
            ):
                with patch.object(
                    AuditoriaRepository, "actualizar", return_value=auditoria
                ) as mock_actualizar:
                    self.service.actualizar(1, datos, self.admin)
                    mock_actualizar.assert_called_once()

    def test_actualizar_nombre_duplicado(self):
        """Verifica que falle si el nombre ya esta en uso."""
        auditoria = Auditoria(
            id=1,
            nombre="Original",
            activa=True,
            capa_id=1,
            frecuencia_id=1,
        )
        duplicado = Auditoria(
            id=2,
            nombre="EnUso",
            activa=True,
            capa_id=1,
            frecuencia_id=1,
        )

        with patch.object(AuditoriaRepository, "obtener_por_id", return_value=auditoria):
            with patch.object(
                AuditoriaRepository,
                "obtener_por_nombre",
                return_value=duplicado,
            ):
                with pytest.raises(
                    ValueError, match="Ya existe una auditoria"
                ):
                    self.service.actualizar(
                        1, AuditoriaUpdate(nombre="EnUso"), self.admin
                    )

    def test_cambiar_estado(self):
        """Verifica que se cambie el estado correctamente."""
        auditoria = Auditoria(
            id=1,
            nombre="Test",
            activa=True,
            capa_id=1,
            frecuencia_id=1,
        )
        self._mock_fk_get()

        with patch.object(AuditoriaRepository, "obtener_por_id", return_value=auditoria):
            with patch.object(
                AuditoriaRepository, "actualizar", return_value=auditoria
            ) as mock_actualizar:
                self.service.cambiar_estado(1, False, self.admin)
                mock_actualizar.assert_called_once()

    def test_cambiar_estado_mismo_valor(self):
        """Verifica que no actualice si el estado es el mismo."""
        auditoria = Auditoria(
            id=1,
            nombre="Test",
            activa=True,
            capa_id=1,
            frecuencia_id=1,
        )
        self._mock_fk_get()

        with patch.object(AuditoriaRepository, "obtener_por_id", return_value=auditoria):
            with patch.object(AuditoriaRepository, "actualizar") as mock_actualizar:
                self.service.cambiar_estado(1, True, self.admin)
                mock_actualizar.assert_not_called()

    def test_listar_auditorias(self):
        """Verifica que se listen las auditorias (Administrador: todas)."""
        auditorias = [
            Auditoria(
                id=1,
                nombre="A1",
                activa=True,
                capa_id=1,
                frecuencia_id=1,
            ),
            Auditoria(
                id=2,
                nombre="A2",
                activa=False,
                capa_id=2,
                frecuencia_id=2,
            ),
        ]
        self._mock_fk_get()

        with patch.object(AuditoriaRepository, "listar", return_value=auditorias):
            resultado = self.service.listar(self.admin)

        assert len(resultado) == 2


class TestPermisosGestionAuditorias:
    """Pruebas de las reglas de capa/área por rol en la gestión."""

    def setup_method(self):
        self.mock_session = MagicMock(spec=Session)
        self.service = AuditoriaService(self.mock_session)
        self.area_ensamble = Area(id=10, nombre="Ensamble Final SB")
        self.area_otra = Area(id=20, nombre="Otra Area")
        self.supervisor = _usuario_supervisor([self.area_ensamble])
        self.gerente = _usuario_gerente()
        self.mock_session.get.side_effect = lambda cls, id: MagicMock(
            spec=cls, nombre="Mock", id=id
        )

    def _mock_capas(self):
        """Mock de session.exec: catálogos de Capa, Area y Frecuencia."""
        from app.models.frecuencia import Frecuencia

        catalogs = {
            "Capa": _capas_base(),
            "Area": [self.area_ensamble, self.area_otra],
            "Frecuencia": [Frecuencia(id=1, nombre="Mensual")],
        }

        def _exec(query, *args, **kwargs):
            nombre = query.column_descriptions[0]["entity"].__name__
            resultado = MagicMock()
            resultado.all.return_value = catalogs.get(nombre, [])
            return resultado

        self.mock_session.exec.side_effect = _exec

    def _datos(self, capa_id: int, area_id: int | None) -> AuditoriaCreate:
        return AuditoriaCreate(
            nombre=f"Aud-{capa_id}-{area_id}",
            activa=True,
            capa_id=capa_id,
            frecuencia_id=1,
            area_id=area_id,
        )

    def _crear_con_repo(self, datos: AuditoriaCreate) -> Auditoria:
        with patch.object(
            CapaService, "obtener_por_id", return_value=MagicMock(spec=Capa)
        ):
            with patch.object(
                FrecuenciaService,
                "obtener_por_id",
                return_value=MagicMock(spec=Frecuencia),
            ):
                with patch.object(
                    AuditoriaRepository, "obtener_por_nombre", return_value=None
                ):
                    with patch.object(
                        AuditoriaRepository,
                        "crear",
                        return_value=Auditoria(id=1, **datos.model_dump()),
                    ):
                        return self.service.crear(datos, self.supervisor)

    def test_supervisor_crea_auditoria_en_su_area(self):
        """Un Supervisor crea auditorías en sus áreas y capas permitidas."""
        self._mock_capas()
        resultado = self._crear_con_repo(self._datos(capa_id=1, area_id=10))
        assert resultado.area_id == 10

    def test_supervisor_no_puede_crear_fuera_de_sus_areas(self):
        """Un Supervisor no puede crear fuera de sus áreas asignadas."""
        self._mock_capas()
        with pytest.raises(ValueError, match="fuera de sus áreas"):
            self._crear_con_repo(self._datos(capa_id=1, area_id=20))

    def test_supervisor_no_puede_crear_sin_area(self):
        """Un Supervisor no puede crear una auditoría sin área."""
        self._mock_capas()
        with pytest.raises(ValueError, match="Debe seleccionar un área"):
            self._crear_con_repo(self._datos(capa_id=1, area_id=None))

    def test_supervisor_no_puede_crear_capa_superior(self):
        """Un Supervisor no puede crear auditorías de capa Gerente."""
        self._mock_capas()
        with pytest.raises(ValueError, match="esa capa"):
            self._crear_con_repo(self._datos(capa_id=3, area_id=10))

    def test_supervisor_crea_en_cualquier_area_asignada(self):
        """El Supervisor gestiona en todas sus áreas, no solo una."""
        self.mock_session.get.side_effect = lambda cls, id: MagicMock(
            spec=cls, nombre="Mock", id=id
        )
        datos = self._datos(capa_id=2, area_id=10)
        self._mock_capas()

        with patch.object(
            CapaService, "obtener_por_id", return_value=MagicMock(spec=Capa)
        ):
            with patch.object(
                FrecuenciaService,
                "obtener_por_id",
                return_value=MagicMock(spec=Frecuencia),
            ):
                with patch.object(
                    AuditoriaRepository, "obtener_por_nombre", return_value=None
                ):
                    with patch.object(
                        AuditoriaRepository,
                        "crear",
                        return_value=Auditoria(id=5, **datos.model_dump()),
                    ):
                        resultado = self.service.crear(datos, self.supervisor)
        assert resultado.capa_id == 2

    def test_gerente_crea_en_cualquier_area(self):
        """Un Gerente crea auditorías de su capa e inferiores en cualquier área."""
        self._mock_capas()
        datos = AuditoriaCreate(
            nombre="Gerente-Aud",
            activa=True,
            capa_id=1,
            frecuencia_id=1,
            area_id=20,
        )
        with patch.object(
            CapaService, "obtener_por_id", return_value=MagicMock(spec=Capa)
        ):
            with patch.object(
                FrecuenciaService,
                "obtener_por_id",
                return_value=MagicMock(spec=Frecuencia),
            ):
                with patch.object(
                    AuditoriaRepository, "obtener_por_nombre", return_value=None
                ):
                    with patch.object(
                        AuditoriaRepository,
                        "crear",
                        return_value=Auditoria(id=2, **datos.model_dump()),
                    ):
                        resultado = self.service.crear(datos, self.gerente)
        assert resultado.area_id == 20

    def test_supervisor_no_edita_auditoria_ajena(self):
        """Un Supervisor no puede editar una auditoría de otra área."""
        self._mock_capas()
        auditoria = Auditoria(
            id=1,
            nombre="Ajena",
            activa=True,
            capa_id=1,
            frecuencia_id=1,
            area_id=20,
        )
        with patch.object(
            AuditoriaRepository, "obtener_por_id", return_value=auditoria
        ):
            with pytest.raises(ValueError, match="No tiene permisos"):
                self.service.actualizar(
                    1, AuditoriaUpdate(nombre="X"), self.supervisor
                )

    def test_supervisor_edita_auditoria_de_su_area(self):
        """Un Supervisor sí puede editar una auditoría de su área."""
        self._mock_capas()
        auditoria = Auditoria(
            id=1,
            nombre="Propia",
            activa=True,
            capa_id=1,
            frecuencia_id=1,
            area_id=10,
        )
        with patch.object(
            AuditoriaRepository, "obtener_por_id", return_value=auditoria
        ):
            with patch.object(AuditoriaRepository, "actualizar", return_value=auditoria):
                with patch.object(AuditoriaRepository, "obtener_por_nombre", return_value=None):
                    resultado = self.service.actualizar(
                        1, AuditoriaUpdate(nombre="Nueva"), self.supervisor
                    )
        assert resultado.nombre == "Nueva"

    def test_listar_supervisor_filtra_por_capa_y_area(self):
        """El listado de Supervisor filtra por sus capas y áreas."""
        self._mock_capas()
        visibles = Auditoria(
            id=1, nombre="Propia", activa=True, capa_id=1, frecuencia_id=1,
            area_id=10,
        )
        ajena_area = Auditoria(
            id=2, nombre="OtraArea", activa=True, capa_id=1, frecuencia_id=1,
            area_id=20,
        )
        ajena_capa = Auditoria(
            id=3, nombre="Gerente", activa=True, capa_id=3, frecuencia_id=1,
            area_id=10,
        )
        with patch.object(
            AuditoriaRepository,
            "listar",
            return_value=[visibles, ajena_area, ajena_capa],
        ):
            resultado = self.service.listar(self.supervisor)
        assert [a.id for a in resultado] == [1]

    def test_listar_gerente_filtra_por_capa(self):
        """El Gerente ve las auditorías de su capa y las inferiores."""
        self._mock_capas()
        capa_auditor = Auditoria(
            id=1, nombre="A", activa=True, capa_id=1, frecuencia_id=1,
            area_id=10,
        )
        capa_supervisor = Auditoria(
            id=2, nombre="S", activa=True, capa_id=2, frecuencia_id=1,
            area_id=20,
        )
        with patch.object(
            AuditoriaRepository,
            "listar",
            return_value=[capa_auditor, capa_supervisor],
        ):
            resultado = self.service.listar(self.gerente)
        assert [a.id for a in resultado] == [1, 2]

    def test_permisos_gestion_devuelve_ids(self):
        """El endpoint de permisos refleja capas y áreas permitidas."""
        self._mock_capas()
        permisos = self.service.permisos(self.supervisor)
        assert permisos["puede_gestionar"] is True
        assert permisos["capa_ids"] == [1, 2]
        assert permisos["area_ids"] == [10]

    def test_permisos_gestion_gerente_sin_restriccion_area(self):
        self._mock_capas()
        permisos = self.service.permisos(self.gerente)
        assert permisos["capa_ids"] == [1, 2, 3]
        assert permisos["area_ids"] is None


class TestGestionSupervisorE2E:
    """E2E: Supervisor crea auditoría de capa Auditor en su área y el
    Auditor asignado la ve disponible para ejecutar («Mis pendientes»)."""

    @pytest.fixture
    def session(self):
        from sqlmodel import SQLModel, create_engine

        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}
        )
        SQLModel.metadata.create_all(engine)
        with Session(engine) as session:
            yield session

    def test_auditoria_creada_por_supervisor_es_visible_para_auditor(
        self, session: Session
    ):
        from sqlmodel import select

        from app.models.frecuencia import Frecuencia
        from app.models.rol import Rol
        from app.models.usuario import Usuario
        from app.models.usuario_area import UsuarioArea
        from app.seed import (
            _seed_areas,
            _seed_capas,
            _seed_frecuencias,
            _seed_roles,
        )
        from app.services.ejecucion_auditoria_service import (
            EjecucionAuditoriaService,
        )

        _seed_capas(session)
        _seed_frecuencias(session)
        _seed_roles(session)
        _seed_areas(session)
        area = session.exec(
            select(Area).where(Area.nombre == "Ensamble Final")
        ).first()
        frecuencia = session.exec(select(Frecuencia)).first()
        capa_auditor = session.exec(
            select(Capa).where(Capa.nombre == "Auditor")
        ).first()

        def _usuario_real(nombre: str, rol: str) -> Usuario:
            rol_id = session.exec(
                select(Rol).where(Rol.nombre == rol)
            ).first().id
            usuario = Usuario(
                nombre=nombre,
                correo=f"{nombre}@lpa.com",
                contrasena_hash="x",
                activo=True,
                rol_id=rol_id,
            )
            session.add(usuario)
            session.commit()
            session.refresh(usuario)
            return usuario

        supervisor = _usuario_real("Sup SB", "Supervisor")
        auditor = _usuario_real("Aud SB", "Auditor")
        session.add(UsuarioArea(usuario_id=supervisor.id, area_id=area.id))
        session.add(UsuarioArea(usuario_id=auditor.id, area_id=area.id))
        session.commit()

        datos = AuditoriaCreate(
            nombre="Control de proceso - Ensamble Final SB",
            activa=True,
            capa_id=capa_auditor.id,
            frecuencia_id=frecuencia.id,
            area_id=area.id,
        )
        creada = AuditoriaService(session).crear(datos, supervisor)

        # El auditor de esa área la ve en «Mis pendientes».
        disponibles = EjecucionAuditoriaService(session).listar_disponibles(
            auditor
        )
        assert any(a.id == creada.id for a in disponibles)

        # El supervisor solo ve su propia auditoría en la gestión.
        visibles = AuditoriaService(session).listar(supervisor)
        assert [a.id for a in visibles] == [creada.id]

        # Un auditor no puede gestionarla (solo ejecutarla).
        assert AuditoriaService(session).puede_gestionar(auditor, creada) is False
        with pytest.raises(ValueError, match="No tiene permisos"):
            AuditoriaService(session).actualizar(
                creada.id, AuditoriaUpdate(nombre="X"), auditor
            )


class TestAuditoriaDiasSemana:
    """CRUD de los días hábiles elegidos al crear/editar la auditoría."""

    @pytest.fixture
    def session(self):
        from sqlmodel import SQLModel, create_engine

        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}
        )
        SQLModel.metadata.create_all(engine)
        with Session(engine) as session:
            yield session

    def _preparar(self, session: Session):
        from sqlmodel import select

        from app.models.rol import Rol
        from app.models.usuario import Usuario
        from app.seed import (
            _seed_areas,
            _seed_capas,
            _seed_frecuencias,
            _seed_roles,
        )

        _seed_capas(session)
        _seed_frecuencias(session)
        _seed_roles(session)
        _seed_areas(session)
        area = session.exec(
            select(Area).where(Area.nombre == "Ensamble Final")
        ).first()
        frecuencia = session.exec(
            select(Frecuencia).where(Frecuencia.nombre == "Semanal")
        ).first()
        capa = session.exec(select(Capa).where(Capa.nombre == "Auditor")).first()
        rol_id = session.exec(
            select(Rol).where(Rol.nombre == "Administrador")
        ).first().id
        admin = Usuario(
            nombre="Admin Días",
            correo="admin.dias@lpa.com",
            contrasena_hash="x",
            activo=True,
            rol_id=rol_id,
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
        return area, frecuencia, capa, admin

    def test_crear_con_dias_persiste_y_se_listan(self, session: Session):
        from sqlmodel import select

        from app.models.auditoria_dia import AuditoriaDia

        area, frecuencia, capa, admin = self._preparar(session)
        service = AuditoriaService(session)
        creada = service.crear(
            AuditoriaCreate(
                nombre="Martes y Jueves",
                activa=True,
                capa_id=capa.id,
                frecuencia_id=frecuencia.id,
                area_id=area.id,
                dias_semana=[3, 1],
            ),
            admin,
        )

        filas = session.exec(
            select(AuditoriaDia)
            .where(AuditoriaDia.auditoria_id == creada.id)
            .order_by(AuditoriaDia.dia_semana)
        ).all()
        assert [f.dia_semana for f in filas] == [1, 3]

        visibles = service.listar(admin)
        assert visibles[0].dias_semana == [1, 3]

    def test_crear_sin_dias_no_crea_filas(self, session: Session):
        from sqlmodel import select

        from app.models.auditoria_dia import AuditoriaDia

        area, frecuencia, capa, admin = self._preparar(session)
        creada = AuditoriaService(session).crear(
            AuditoriaCreate(
                nombre="Según frecuencia",
                activa=True,
                capa_id=capa.id,
                frecuencia_id=frecuencia.id,
                area_id=area.id,
            ),
            admin,
        )
        filas = session.exec(
            select(AuditoriaDia).where(AuditoriaDia.auditoria_id == creada.id)
        ).all()
        assert filas == []
        visibles = AuditoriaService(session).listar(admin)
        assert visibles[0].dias_semana == []

    def test_actualizar_reemplaza_conserva_y_limpia_dias(self, session: Session):
        from sqlmodel import select

        from app.models.auditoria_dia import AuditoriaDia

        area, frecuencia, capa, admin = self._preparar(session)
        service = AuditoriaService(session)
        creada = service.crear(
            AuditoriaCreate(
                nombre="Días editables",
                activa=True,
                capa_id=capa.id,
                frecuencia_id=frecuencia.id,
                area_id=area.id,
                dias_semana=[1, 3],
            ),
            admin,
        )

        def _dias_bd() -> list[int]:
            return [
                f.dia_semana
                for f in session.exec(
                    select(AuditoriaDia)
                    .where(AuditoriaDia.auditoria_id == creada.id)
                    .order_by(AuditoriaDia.dia_semana)
                ).all()
            ]

        # Reemplaza por otros días.
        service.actualizar(creada.id, AuditoriaUpdate(dias_semana=[4]), admin)
        assert _dias_bd() == [4]
        assert service.listar(admin)[0].dias_semana == [4]

        # Sin el campo (None): los días no cambian.
        service.actualizar(creada.id, AuditoriaUpdate(nombre="Renombrada"), admin)
        assert _dias_bd() == [4]

        # Lista vacía: limpia los días y sus filas.
        service.actualizar(creada.id, AuditoriaUpdate(dias_semana=[]), admin)
        assert _dias_bd() == []
        assert service.listar(admin)[0].dias_semana == []

    def test_dias_invalidos_rechazados(self):
        with pytest.raises(ValueError, match="días"):
            AuditoriaCreate(
                nombre="Inválida",
                activa=True,
                capa_id=1,
                frecuencia_id=1,
                dias_semana=[0, 7],
            )

    def test_dias_duplicados_y_desordenados_normalizados(self):
        datos = AuditoriaCreate(
            nombre="Normalizada",
            activa=True,
            capa_id=1,
            frecuencia_id=1,
            dias_semana=[3, 1, 3, 0],
        )
        assert datos.dias_semana == [0, 1, 3]

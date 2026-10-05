"""Pruebas de RCS. Se ejecutan con:  python tests.py"""
import os
import tempfile
import unittest
from unittest.mock import patch

import eventos
import recursos
import reportes
import usuarios
import utilidades
from main import crear_mision


def todos(valor):
    """Diccionario con todos los recursos en el mismo valor."""
    return {n: valor for n in recursos.NOMBRES}


def mision_con(valores=None, **cambios):
    """Misión de prueba con los recursos y campos que se necesiten."""
    m = crear_mision("test")
    if valores:
        m["recursos"] = dict(valores)
    m.update(cambios)
    return m


class TestAlgoritmoRiesgo(unittest.TestCase):
    """Algoritmo propio: riesgo = suma de peso * (100 - valor)."""

    def test_ideal_es_cero(self):
        self.assertAlmostEqual(eventos.indice_riesgo(todos(100)), 0.0)

    def test_colapso_es_cien(self):
        self.assertAlmostEqual(eventos.indice_riesgo(todos(0)), 100.0)

    def test_ejemplo_documentado(self):
        r = {"Energía": 100, "Agua": 80, "Alimentos": 70, "Comunicación": 90}
        self.assertAlmostEqual(eventos.indice_riesgo(r), 13.0)

    def test_energia_pesa_mas(self):
        sin_energia = {**todos(100), "Energía": 0}
        sin_comunicacion = {**todos(100), "Comunicación": 0}
        self.assertAlmostEqual(eventos.indice_riesgo(sin_energia), 40.0)
        self.assertAlmostEqual(eventos.indice_riesgo(sin_comunicacion), 10.0)

    def test_niveles(self):
        casos = [(100, 0.0, "BAJO"), (76, 24.0, "BAJO"), (74, 26.0, "MEDIO"),
                 (55, 45.0, "MEDIO"), (45, 55.0, "ALTO"), (0, 100.0, "ALTO")]
        for valor, riesgo, nivel in casos:
            with self.subTest(valor=valor):
                self.assertEqual(eventos.algoritmo_propio(mision_con(todos(valor))), (riesgo, nivel))

    def test_pesos_suman_uno(self):
        self.assertAlmostEqual(sum(eventos.PESOS.values()), 1.0)


class TestRecursos(unittest.TestCase):
    def test_limites(self):
        r = todos(90)
        recursos.modificar_recurso(r, "Agua", +50)
        recursos.modificar_recurso(r, "Energía", -500)
        self.assertEqual(r["Agua"], 100)
        self.assertEqual(r["Energía"], 0)

    def test_inicio_aleatorio_en_rango(self):
        for dif, (bajo, alto) in recursos.RANGOS_INICIO.items():
            for _ in range(200):
                r = recursos.crear_recursos(dif)
                self.assertEqual(set(r), set(recursos.NOMBRES))
                self.assertTrue(all(bajo <= v <= alto for v in r.values()), (dif, r))

    def test_inicio_no_es_siempre_igual(self):
        self.assertGreater(len({tuple(recursos.crear_recursos("Normal").values()) for _ in range(50)}), 1)


class TestReglas(unittest.TestCase):
    def estado(self, valores, **extra):
        """Evalúa las reglas de una misión de prueba y devuelve su estado."""
        m = mision_con(valores, **extra)
        eventos.evaluar_reglas(m)
        return m["estado"]

    def test_fallida_si_un_recurso_llega_a_cero(self):
        self.assertEqual(self.estado({**todos(80), "Agua": 0}), "FALLIDA")

    def test_critica_energia_menor_a_20(self):
        self.assertEqual(self.estado({**todos(80), "Energía": 19}), "CRÍTICA")

    def test_energia_20_no_es_critica(self):
        self.assertEqual(self.estado({**todos(80), "Energía": 20}), "ALERTA")

    def test_alerta_por_agua_baja(self):
        self.assertEqual(self.estado({**todos(80), "Agua": 14}), "ALERTA")

    def test_alerta_por_recurso_bajo_30(self):
        self.assertEqual(self.estado({**todos(80), "Alimentos": 29}), "ALERTA")

    def test_operativa(self):
        self.assertEqual(self.estado(todos(80), eventos_procesados=3), "OPERATIVA")

    def test_resuelta_con_bonus(self):
        m = mision_con(todos(80), eventos_procesados=10, dificultad="Normal")
        eventos.evaluar_reglas(m)
        self.assertEqual(m["estado"], "RESUELTA")
        self.assertEqual(m["puntos"], eventos.DIFICULTADES["Normal"]["bonus"])

    def test_no_se_resuelve_en_alerta(self):
        self.assertEqual(self.estado({**todos(80), "Agua": 14}, eventos_procesados=10), "ALERTA")

    def test_meta_depende_de_dificultad(self):
        self.assertEqual(self.estado(todos(80), eventos_procesados=8, dificultad="Fácil"), "RESUELTA")
        self.assertEqual(self.estado(todos(80), eventos_procesados=8, dificultad="Difícil"), "OPERATIVA")

    def test_estado_final_no_cambia(self):
        self.assertEqual(self.estado(todos(0), estado="RESUELTA"), "RESUELTA")


class TestEventos(unittest.TestCase):
    def setUp(self):
        # Evita que las pruebas escriban archivos CSV
        p = patch("reportes.guardar_progreso")
        p.start()
        self.addCleanup(p.stop)

    def test_datos_de_eventos(self):
        self.assertGreaterEqual(len(eventos.EVENTOS), 5)
        for ev in eventos.EVENTOS:
            ops = ev["opciones"]
            self.assertGreaterEqual(len(ops), 3, ev["nombre"])
            self.assertTrue(any(o["puntos"] > 0 for o in ops), ev["nombre"])
            self.assertTrue(any(o["puntos"] < 0 for o in ops), ev["nombre"])
            self.assertIn(ev["recurso"], recursos.NOMBRES)
            for o in ops:
                self.assertTrue(set(o["efectos"]) <= set(recursos.NOMBRES), o["texto"])
                self.assertTrue(0 < o["prob"] <= 1, o["texto"])

    def test_orden_de_opciones_aleatorio(self):
        antes = [[o["texto"] for o in e["opciones"]] for e in eventos.EVENTOS]
        ordenes = {}
        for _ in range(400):
            ev = eventos.generar_evento()
            ordenes.setdefault(ev["nombre"], set()).add(tuple(o["texto"] for o in ev["opciones"]))
        self.assertTrue(any(len(v) > 1 for v in ordenes.values()))
        despues = [[o["texto"] for o in e["opciones"]] for e in eventos.EVENTOS]
        self.assertEqual(antes, despues)  # la lista original no se altera

    def test_azar_depende_del_estado(self):
        def cuenta(m):
            return sum(eventos.generar_evento(m)["recurso"] == "Energía" for _ in range(2000))
        baja = mision_con({**todos(100), "Energía": 5})
        alta = mision_con(todos(100))
        self.assertGreater(cuenta(baja), cuenta(alta))

    def test_puntos_y_contadores(self):
        m = mision_con(todos(80))
        ev = {"nombre": "X", "recurso": "Energía", "opciones": [eventos.op("bien", 10, Energía=+5)]}
        res = eventos.aplicar_opcion(m, ev, 0)
        self.assertTrue(res["exito"])
        self.assertEqual((m["puntos"], m["eventos_procesados"], m["decisiones_correctas"]), (10, 1, 1))
        self.assertIn("(+10 pts)", m["historial"][-1])

    def test_decision_mala_cuenta_como_incorrecta(self):
        m = mision_con(todos(80))
        ev = {"nombre": "X", "recurso": "Agua", "opciones": [eventos.op("mal", -10, Agua=-20)]}
        eventos.aplicar_opcion(m, ev, 0)
        self.assertEqual((m["puntos"], m["decisiones_incorrectas"]), (-10, 1))
        self.assertLess(m["recursos"]["Agua"], 80)

    def test_accion_riesgosa_puede_fallar(self):
        m = mision_con(todos(80), dificultad="Normal")
        ev = {"nombre": "X", "recurso": "Energía",
              "opciones": [eventos.op("riesgo", 12, 0.5, Energía=+20, Agua=-10)]}
        # random() = 0.99 fuerza el fallo
        with patch("eventos.random.random", return_value=0.99):
            res = eventos.aplicar_opcion(m, ev, 0)
        self.assertFalse(res["exito"])
        self.assertEqual(res["puntos"], eventos.FALLO_PUNTOS)
        self.assertLessEqual(m["recursos"]["Energía"], 80)  # no hubo mejora
        self.assertLess(m["recursos"]["Agua"], 80)          # el costo sí se pagó
        self.assertIn("FALLÓ", m["historial"][-1])

    def test_accion_riesgosa_puede_salir_bien(self):
        m = mision_con(todos(80), dificultad="Normal")
        ev = {"nombre": "X", "recurso": "Energía", "opciones": [eventos.op("riesgo", 12, 0.5, Energía=+20)]}
        # random() = 0.0 fuerza el éxito
        with patch("eventos.random.random", return_value=0.0):
            res = eventos.aplicar_opcion(m, ev, 0)
        self.assertTrue(res["exito"])
        self.assertGreater(m["recursos"]["Energía"], 80)

    def test_recursos_siempre_entre_0_y_100(self):
        for dif in eventos.DIFICULTADES:
            for _ in range(30):
                m = crear_mision("test", dif)
                eventos.simular(m, 20)
                self.assertTrue(all(0 <= v <= 100 for v in m["recursos"].values()), (dif, m["recursos"]))

    def test_simular_no_pasa_de_la_meta(self):
        # Fácil: meta 8. Con 5 procesados solo faltan 3, aunque se pidan 20.
        m = mision_con(todos(100), dificultad="Fácil", eventos_procesados=5)
        self.assertEqual(eventos.eventos_restantes(m), 3)
        self.assertEqual(eventos.simular(m, 20), 3)
        self.assertEqual(m["eventos_procesados"], 8)

    def test_simular_se_suma_a_los_eventos_actuales(self):
        m = mision_con(todos(100), dificultad="Fácil")
        eventos.simular(m, 3)
        self.assertEqual(m["eventos_procesados"], 3)
        self.assertEqual(eventos.eventos_restantes(m), 5)
        eventos.simular(m, 20)
        self.assertLessEqual(m["eventos_procesados"], 8)

    def test_simular_sin_eventos_restantes(self):
        m = mision_con(todos(80), dificultad="Normal", eventos_procesados=10, estado="ALERTA")
        self.assertEqual(eventos.eventos_restantes(m), 0)
        self.assertEqual(eventos.simular(m, 5), 0)
        self.assertEqual(m["eventos_procesados"], 10)

    def test_simular_se_detiene_en_estado_final(self):
        m = mision_con(todos(80), estado="FALLIDA")
        self.assertEqual(eventos.simular(m, 5), 0)

    def test_dificil_es_mas_dificil_que_facil(self):
        def exito(dif):
            ok = 0
            for _ in range(150):
                m = crear_mision("test", dif)
                eventos.simular(m, 20)
                ok += m["estado"] == "RESUELTA"
            return ok
        self.assertGreater(exito("Fácil"), exito("Difícil"))


class TestProgreso(unittest.TestCase):
    def setUp(self):
        # Trabaja en una carpeta temporal para no ensuciar el proyecto
        self.viejo = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)

    def tearDown(self):
        os.chdir(self.viejo)
        self.tmp.cleanup()

    def test_guardar_y_cargar(self):
        m = crear_mision("ana", "Difícil")
        m["puntos"] = 42
        reportes.registrar(m, "algo (+3 pts)")
        reportes.guardar_progreso(m)
        c = reportes.cargar_progreso("ana")
        for clave in ("recursos", "dificultad", "puntos", "historial", "estado", "id"):
            self.assertEqual(c[clave], m[clave], clave)

    def test_historial_por_usuario(self):
        ana, luis = crear_mision("ana"), crear_mision("luis")
        reportes.registrar(ana, "accion de ana (+5 pts)")
        reportes.guardar_progreso(ana)
        reportes.guardar_progreso(luis)
        self.assertTrue(os.path.exists(reportes.ruta_historial("ana")))
        self.assertTrue(os.path.exists(reportes.ruta_historial("luis")))
        acciones = reportes.cargar_historial("ana")[0]["acciones"]
        self.assertIn("accion de ana (+5 pts)", acciones)
        self.assertNotIn("accion de ana (+5 pts)", reportes.cargar_historial("luis")[0]["acciones"])

    def test_historial_acumula_misiones(self):
        m1 = crear_mision("ana")
        m1["id"] = "2026-01-01 10:00:00"
        reportes.guardar_progreso(m1)
        reportes.registrar(m1, "otra accion")
        reportes.guardar_progreso(m1)           # misma misión: se actualiza, no se duplica
        m2 = crear_mision("ana")
        m2["id"] = "2026-01-02 10:00:00"
        reportes.guardar_progreso(m2)           # misión nueva: se agrega
        misiones = reportes.cargar_historial("ana")
        self.assertEqual(len(misiones), 2)
        self.assertIn("otra accion", misiones[0]["acciones"])

    def test_historial_inexistente_o_danado(self):
        self.assertEqual(reportes.cargar_historial("nadie"), [])
        reportes.crear_carpeta()
        with open(reportes.ruta_historial("ana"), "w", encoding="utf-8") as f:
            f.write("{roto")
        self.assertEqual(reportes.cargar_historial("ana"), [])

    def test_no_existe(self):
        self.assertFalse(reportes.existe_progreso("nadie"))
        self.assertIsNone(reportes.cargar_progreso("nadie"))

    def test_archivo_danado(self):
        reportes.crear_carpeta()
        with open(reportes.ruta_progreso("ana"), "w", encoding="utf-8") as f:
            f.write("tipo,clave,valor\ncontador,puntos,abc\n")
        self.assertIsNone(reportes.cargar_progreso("ana"))

    def test_borrar_progreso(self):
        reportes.guardar_progreso(crear_mision("ana"))
        self.assertTrue(reportes.borrar_progreso("ana"))
        self.assertFalse(reportes.existe_progreso("ana"))
        self.assertFalse(reportes.borrar_progreso("ana"))

    def test_nombre_de_archivo_seguro(self):
        ruta = reportes.ruta_progreso("a/b..c")
        self.assertEqual(os.path.basename(ruta), "progreso_abc.csv")

    def test_archivos_van_en_la_carpeta_de_datos(self):
        reportes.guardar_progreso(crear_mision("ana"))
        self.assertTrue(os.path.isfile(os.path.join("datos", "progreso_ana.csv")))
        self.assertTrue(os.path.isfile(os.path.join("datos", "historial_ana.json")))
        self.assertEqual(os.listdir("."), ["datos"])  # nada suelto fuera de la carpeta

    def test_estadisticas(self):
        m = mision_con(todos(80), eventos_procesados=4, decisiones_correctas=3, decisiones_incorrectas=1)
        est = reportes.calcular_estadisticas(m)
        self.assertEqual(est["Eficiencia (%)"], 75.0)
        self.assertEqual(reportes.calcular_estadisticas(mision_con())["Eficiencia (%)"], 0.0)


class TestValidacionesYUsuarios(unittest.TestCase):
    def test_leer_entero_rechaza_vacio_texto_y_rango(self):
        with patch("builtins.input", side_effect=["", "abc", "99", "5"]):
            self.assertEqual(utilidades.leer_entero("n: ", 1, 10), 5)

    def test_leer_texto_exige_minimo(self):
        with patch("builtins.input", side_effect=["", "  ", "ab", "abc"]):
            self.assertEqual(utilidades.leer_texto("t: ", 3), "abc")

    def test_login_correcto(self):
        with patch("builtins.input", side_effect=["admin", "1234"]):
            self.assertEqual(usuarios.iniciar_sesion(), "admin")

    def test_login_bloqueado_tras_tres_intentos(self):
        with patch("builtins.input", side_effect=["admin", "mal"] * 3):
            self.assertIsNone(usuarios.iniciar_sesion())

    def test_crear_operador(self):
        self.addCleanup(usuarios.operadores.pop, "nuevo_t", None)
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(usuarios, "ARCHIVO", os.path.join(tmp, "u.json")):
                with patch("builtins.input", side_effect=["nuevo_t", "abcd"]):
                    self.assertTrue(usuarios.crear_operador())
        self.assertEqual(usuarios.operadores["nuevo_t"], "abcd")

    def test_operadores_se_guardan_en_json(self):
        self.addCleanup(usuarios.operadores.pop, "persistente", None)
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(usuarios, "ARCHIVO", os.path.join(tmp, "u.json")):
                usuarios.registrar("persistente", "clave1")
                cargados = usuarios.cargar_operadores()
        self.assertEqual(cargados["persistente"], "clave1")
        self.assertEqual(cargados["admin"], "1234")

    def test_json_inexistente_o_danado(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = os.path.join(tmp, "u.json")
            with patch.object(usuarios, "ARCHIVO", ruta):
                self.assertEqual(usuarios.cargar_operadores(), {"admin": "1234"})
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write("esto no es json")
                self.assertEqual(usuarios.cargar_operadores(), {"admin": "1234"})

    def test_operador_duplicado(self):
        with patch("builtins.input", side_effect=["admin"]):
            self.assertFalse(usuarios.crear_operador())

    def test_roles(self):
        self.assertTrue(usuarios.es_admin("admin"))
        self.assertFalse(usuarios.es_admin("cualquiera"))
        self.assertEqual(usuarios.rol("cualquiera"), "operador")


if __name__ == "__main__":
    unittest.main(buffer=True)
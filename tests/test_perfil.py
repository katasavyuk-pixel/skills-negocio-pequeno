"""The profile validator: it has to accept the example and name exactly what is wrong in a bad one."""
import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
EMPEZAR = RAIZ / "skills" / "empezar"
sys.path.insert(0, str(EMPEZAR / "scripts"))

import validar_perfil  # noqa: E402

EJEMPLO = (EMPEZAR / "ejemplos" / "perfil-negocio.md").read_text(encoding="utf-8")


def ejecutar(texto, *opciones):
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fichero:
        fichero.write(texto)
    salida, errores = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(salida), contextlib.redirect_stderr(errores):
        codigo = validar_perfil.main([fichero.name, *opciones])
    return codigo, salida.getvalue(), errores.getvalue()


def cambiar(clave, valor):
    lineas = []
    for linea in EJEMPLO.splitlines():
        lineas.append("- %s: %s" % (clave, valor) if linea.startswith("- %s:" % clave) else linea)
    return "\n".join(lineas) + "\n"


class PerfilDeEjemplo(unittest.TestCase):
    def test_el_ejemplo_es_valido_y_dice_que_queda_pendiente(self):
        codigo, salida, _ = ejecutar(EJEMPLO)
        self.assertEqual(codigo, 0, salida)
        self.assertIn("PERFIL VÁLIDO", salida)
        self.assertIn("web", salida.split("pendiente de respuesta:")[1])

    def test_la_salida_json_trae_los_valores(self):
        codigo, salida, _ = ejecutar(EJEMPLO, "--json")
        datos = json.loads(salida)
        self.assertEqual(codigo, 0)
        self.assertTrue(datos["valido"])
        self.assertEqual(datos["valores"]["plazo_cobro_dias"], "30")
        self.assertEqual(datos["pendientes"], ["web"])

    def test_la_plantilla_tiene_las_mismas_claves_que_el_validador(self):
        plantilla = (EMPEZAR / "assets" / "perfil-negocio.plantilla.md").read_text(encoding="utf-8")
        claves = [linea[2:].split(":")[0] for linea in plantilla.splitlines() if linea.startswith("- ")]
        self.assertEqual(claves, list(validar_perfil.CLAVES))

    def test_la_guia_del_perfil_documenta_cada_clave(self):
        guia = (RAIZ / "comun" / "perfil.md").read_text(encoding="utf-8")
        for clave, (_, dominio, _) in validar_perfil.CLAVES.items():
            self.assertIn("| `%s` |" % clave, guia, "comun/perfil.md no documenta %s" % clave)
            if isinstance(dominio, tuple):
                fila = next(linea for linea in guia.splitlines() if linea.startswith("| `%s` |" % clave))
                for valor in dominio:
                    self.assertIn("`%s`" % valor, fila, "%s: la guía no nombra el valor %s" % (clave, valor))


class PerfilConErrores(unittest.TestCase):
    CASOS = [
        ("un plazo escrito con letras", "plazo_cobro_dias", "treinta", "número entero"),
        ("un plazo imposible", "plazo_cobro_dias", "0", "entre 1 y 365"),
        ("un valor que no existe", "clientes", "todos", "Valores válidos: empresas, particulares, ambos"),
        ("un trato pendiente", "trato", "pendiente", "no puede quedar pendiente"),
        ("una fecha que no lo es", "actualizado", "13/10/2026", "AAAA-MM-DD"),
        ("una web sin https", "web", "tresrobles.example", "https://"),
        ("un importe con símbolo", "caja_minima_eur", "8.000 €", "solo la cifra"),
    ]

    def test_cada_error_dice_la_linea_y_como_arreglarlo(self):
        for nombre, clave, valor, mensaje in self.CASOS:
            with self.subTest(nombre):
                codigo, salida, _ = ejecutar(cambiar(clave, valor))
                self.assertEqual(codigo, 1, salida)
                self.assertIn("PERFIL NO VÁLIDO", salida)
                self.assertRegex(salida, r"línea \d+, `%s`" % clave)
                self.assertIn(mensaje, salida)

    def test_falta_una_clave_obligatoria(self):
        texto = "\n".join(linea for linea in EJEMPLO.splitlines() if not linea.startswith("- forma:"))
        codigo, salida, _ = ejecutar(texto)
        self.assertEqual(codigo, 1)
        self.assertIn("`forma`: falta", salida)

    def test_una_clave_repetida_no_pasa(self):
        codigo, salida, _ = ejecutar(EJEMPLO + "- trato: tu\n")
        self.assertEqual(codigo, 1)
        self.assertIn("está dos veces", salida)

    def test_cobrar_a_plazo_sin_plazo_no_pasa(self):
        texto = "\n".join(linea for linea in EJEMPLO.splitlines() if not linea.startswith("- plazo_cobro_dias:"))
        codigo, salida, _ = ejecutar(texto)
        self.assertEqual(codigo, 1)
        self.assertIn("hace falta el plazo", salida)

    def test_un_fichero_que_no_es_un_perfil_se_dice_sin_traza(self):
        codigo, salida, errores = ejecutar("# Lista de la compra\n\nPan y leche.\n")
        self.assertEqual(codigo, 2)
        self.assertEqual(salida, "")
        self.assertIn("plantilla", errores)


class Avisos(unittest.TestCase):
    def test_mas_de_sesenta_dias_entre_empresas_avisa_pero_vale(self):
        codigo, salida, _ = ejecutar(cambiar("plazo_cobro_dias", "90"))
        self.assertEqual(codigo, 0, salida)
        self.assertIn("art. 4.3", salida)

    def test_sesenta_dias_a_particulares_no_avisa(self):
        texto = cambiar("plazo_cobro_dias", "90").replace("- clientes: ambos", "- clientes: particulares")
        _, salida, _ = ejecutar(texto)
        self.assertNotIn("art. 4.3", salida)

    def test_retencion_en_una_sociedad_avisa(self):
        _, salida, _ = ejecutar(cambiar("retencion_irpf", "15"))
        self.assertIn("una sociedad no lleva retención", salida)

    def test_territorio_foral_avisa(self):
        _, salida, _ = ejecutar(cambiar("territorio", "pais_vasco"))
        self.assertIn("no son los del territorio común", salida)

    def test_cobrar_en_el_momento_no_deja_el_plazo_como_pendiente(self):
        for plazo in ("no_aplica", "pendiente"):
            texto = cambiar("plazo_cobro_dias", plazo).replace("- cobro: mixto", "- cobro: al_momento")
            codigo, salida, _ = ejecutar(texto, "--json")
            self.assertEqual(codigo, 0, salida)
            self.assertNotIn("plazo_cobro_dias", json.loads(salida)["pendientes"])

    def test_no_aplica_no_vale_si_se_cobra_a_plazo(self):
        codigo, salida, _ = ejecutar(cambiar("plazo_cobro_dias", "no_aplica"))
        self.assertEqual(codigo, 1)
        self.assertIn("solo vale si `cobro` es al_momento", salida)

    def test_una_clave_desconocida_avisa_por_si_es_una_errata(self):
        codigo, salida, _ = ejecutar(EJEMPLO + "- tratto: tu\n")
        self.assertEqual(codigo, 0)
        self.assertIn("`tratto` no es una clave", salida)


if __name__ == "__main__":
    unittest.main()

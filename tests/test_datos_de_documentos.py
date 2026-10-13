"""Data extracted from documents: what cannot be traced to the document does not reach the table."""
import contextlib
import datetime
import io
import json
import pathlib
import sys
import tempfile
import unittest
from decimal import Decimal

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SKILL = RAIZ / "skills" / "datos-de-documentos"
sys.path.insert(0, str(SKILL / "scripts"))

import comprobar  # noqa: E402

D = Decimal
FUENTE = """Herrajes Sanz S.L. — B00888883
Factura H-220                18 de agosto de 2026
Base imponible 1.057,85
IVA 21 % 222,15
TOTAL: 1.280,00 €
Contacto: Ana Ruiz, ana@herrajes.example, tel. 976 00 00 00
IBAN ES82 0000 0000 0000 0000 0000
"""
CAMPOS = {
    "campos": [
        {"nombre": "proveedor", "tipo": "texto", "obligatorio": True},
        {"nombre": "nif", "tipo": "nif", "obligatorio": True},
        {"nombre": "fecha", "tipo": "fecha", "obligatorio": True},
        {"nombre": "base", "tipo": "importe"},
        {"nombre": "iva", "tipo": "importe"},
        {"nombre": "total", "tipo": "importe", "obligatorio": True},
        {"nombre": "iban", "tipo": "iban"},
        {"nombre": "correo", "tipo": "email"},
        {"nombre": "telefono", "tipo": "telefono"},
        {"nombre": "unidades", "tipo": "numero"},
    ],
    "sumas": [{"total": "total", "sumandos": ["base", "iva"]}],
    "clave": ["nif", "fecha"],
}
BUENOS = {
    "proveedor": ("Herrajes Sanz S.L.", "Herrajes Sanz S.L. — B00888883"),
    "nif": ("B00888883", "Herrajes Sanz S.L. — B00888883"),
    "fecha": ("2026-08-18", "18 de agosto de 2026"),
    "base": ("1057.85", "Base imponible 1.057,85"),
    "iva": ("222.15", "IVA 21 % 222,15"),
    "total": ("1280.00", "TOTAL: 1.280,00 €"),
    "iban": ("ES8200000000000000000000", "IBAN ES82 0000 0000 0000 0000 0000"),
    "correo": ("ana@herrajes.example", "ana@herrajes.example"),
    "telefono": ("976000000", "tel. 976 00 00 00"),
}


def ejecutar(valores, fuente=FUENTE, campos=CAMPOS, otros=()):
    carpeta = pathlib.Path(tempfile.mkdtemp())
    (carpeta / "fuentes").mkdir()
    (carpeta / "fuentes" / "doc.txt").write_text(fuente, encoding="utf-8")
    documentos = [{"documento": "doc.txt", "campos": {k: (None if v is None else {"valor": v[0], "evidencia": v[1]}) for k, v in valores.items()}}]
    for nombre, texto, sus_valores in otros:
        (carpeta / "fuentes" / nombre).write_text(texto, encoding="utf-8")
        documentos.append({"documento": nombre, "campos": {k: {"valor": v[0], "evidencia": v[1]} for k, v in sus_valores.items()}})
    (carpeta / "campos.json").write_text(json.dumps(campos), encoding="utf-8")
    (carpeta / "extraccion.json").write_text(json.dumps({"documentos": documentos}), encoding="utf-8")
    salida, errores = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(salida), contextlib.redirect_stderr(errores):
        codigo = comprobar.main(["--campos", str(carpeta / "campos.json"), "--extraccion", str(carpeta / "extraccion.json"), "--fuentes", str(carpeta / "fuentes"), "--csv", str(carpeta / "datos.csv"), "--salida", str(carpeta / "datos.xlsx")])
    return codigo, (json.loads(salida.getvalue()) if codigo == 0 else None), errores.getvalue(), carpeta


def motivos(resumen, campo):
    return [r["motivo"] for r in resumen["revisar"] if r["campo"] == campo]


def tabla(carpeta):
    lineas = (carpeta / "datos.csv").read_text(encoding="utf-8-sig").splitlines()
    cabecera = lineas[0].split(";")
    return [dict(zip(cabecera, linea.split(";"))) for linea in lineas[1:]]


class LoQueEstaEnElDocumentoPasa(unittest.TestCase):
    def test_una_extraccion_fiel_llega_entera_a_la_tabla(self):
        codigo, resumen, errores, carpeta = ejecutar(BUENOS)
        self.assertEqual(codigo, 0, errores)
        self.assertEqual(resumen["datos_rellenos"], 9)
        self.assertEqual(resumen["datos_vaciados_por_no_poder_comprobarse"], 0)
        self.assertEqual(resumen["para_revisar"], 0)
        fila = tabla(carpeta)[0]
        self.assertEqual((fila["total"], fila["fecha"], fila["unidades"]), ("1280.00", "2026-08-18", ""))

    def test_el_fragmento_se_compara_sin_mayusculas_tildes_ni_espacios_de_mas(self):
        valores = dict(BUENOS, proveedor=("HERRAJES SANZ", "herrajes   sanz s.l."), total=("1280", "total: 1.280,00 €"))
        _, resumen, _, _ = ejecutar(valores)
        self.assertEqual(resumen["datos_vaciados_por_no_poder_comprobarse"], 0)

    def test_dos_trozos_del_mismo_documento_valen_como_un_fragmento(self):
        valores = dict(BUENOS, proveedor=("Herrajes Sanz S.L.", "Herrajes Sanz S.L. … Factura H-220"))
        _, resumen, _, _ = ejecutar(valores)
        self.assertEqual(resumen["datos_vaciados_por_no_poder_comprobarse"], 0)


class LoQueNoSePuedeComprobarSeVacia(unittest.TestCase):
    CASOS = [
        ("un total calculado en vez de leído", "total", ("1280.00", "Base imponible 1.057,85 … IVA 21 % 222,15"), "esa cifra no está en el fragmento"),
        ("un fragmento que no está en el documento", "total", ("1280.00", "Total factura: 1.280,00 euros"), "el fragmento citado no está en el documento"),
        ("una fecha a la que se le ha puesto el año", "fecha", ("2025-08-18", "18 de agosto de 2026"), "esa fecha no está en el fragmento"),
        ("un NIF arreglado", "nif", ("B00888884", "Herrajes Sanz S.L. — B00888883"), "ese número no está en el fragmento"),
        ("un nombre completado", "proveedor", ("Herrajes Sanz Sociedad Limitada", "Herrajes Sanz S.L. — B00888883"), "el valor no está escrito así"),
        ("un fragmento de una sola cifra", "iva", ("2", "2"), "el fragmento citado no está en el documento"),
        ("un correo que no es el del documento", "correo", ("info@herrajes.example", "ana@herrajes.example"), "esa dirección no está en el fragmento"),
        ("un importe en formato español", "base", ("1.057,85", "Base imponible 1.057,85"), "no es un número con punto decimal"),
    ]

    def test_cada_dato_que_no_sale_del_documento_se_vacia_y_se_dice(self):
        for nombre, campo, dato, motivo in self.CASOS:
            with self.subTest(nombre):
                _, resumen, _, carpeta = ejecutar(dict(BUENOS, **{campo: dato}))
                self.assertEqual(resumen["datos_vaciados_por_no_poder_comprobarse"], 1)
                self.assertTrue(any(motivo in m and "se ha vaciado" in m for m in motivos(resumen, campo)), resumen["revisar"])
                self.assertEqual(tabla(carpeta)[0][campo], "")

    def test_un_dato_obligatorio_que_el_documento_no_trae_se_pide_sin_inventarlo(self):
        _, resumen, _, _ = ejecutar(dict(BUENOS, total=None))
        self.assertEqual(motivos(resumen, "total"), ["es un dato obligatorio y el documento no lo trae"])

    def test_un_dato_opcional_vacio_no_molesta(self):
        _, resumen, _, _ = ejecutar(dict(BUENOS, iban=None, correo=None))
        self.assertEqual(resumen["para_revisar"], 0)

    def test_sin_el_texto_del_documento_no_pasa_nada_a_la_tabla(self):
        carpeta = pathlib.Path(tempfile.mkdtemp())
        (carpeta / "fuentes").mkdir()
        (carpeta / "campos.json").write_text(json.dumps(CAMPOS), encoding="utf-8")
        (carpeta / "extraccion.json").write_text(json.dumps({"documentos": [{"documento": "no-esta.txt", "campos": {"total": {"valor": "1.00", "evidencia": "TOTAL 1,00"}}}]}), encoding="utf-8")
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            codigo = comprobar.main(["--campos", str(carpeta / "campos.json"), "--extraccion", str(carpeta / "extraccion.json"), "--fuentes", str(carpeta / "fuentes")])
        resumen = json.loads(salida.getvalue())
        self.assertEqual(codigo, 0)
        self.assertEqual(resumen["datos_rellenos"], 0)
        self.assertIn("no encuentro el texto", resumen["revisar"][0]["motivo"])


class LoQueEstaMalEnElPropioDocumento(unittest.TestCase):
    def test_un_nif_que_no_pasa_el_control_se_queda_y_se_avisa(self):
        fuente = FUENTE.replace("B00888883", "B00888880")
        valores = dict(BUENOS, nif=("B00888880", "B00888880"), proveedor=("Herrajes Sanz S.L.", "Herrajes Sanz S.L."))
        _, resumen, _, carpeta = ejecutar(valores, fuente=fuente)
        self.assertEqual(tabla(carpeta)[0]["nif"], "B00888880")
        self.assertTrue(any("puede estar mal en el propio documento" in m for m in motivos(resumen, "nif")))

    def test_un_iban_que_no_pasa_el_control_se_queda_y_se_avisa(self):
        fuente = FUENTE.replace("ES82 0000", "ES81 0000")
        valores = dict(BUENOS, iban=("ES8100000000000000000000", "IBAN ES81 0000 0000 0000 0000 0000"))
        _, resumen, _, carpeta = ejecutar(valores, fuente=fuente)
        self.assertEqual(tabla(carpeta)[0]["iban"], "ES8100000000000000000000")
        self.assertTrue(any("no pasa el control" in m for m in motivos(resumen, "iban")))

    def test_una_suma_que_no_cuadra_en_el_documento_se_avisa(self):
        fuente = FUENTE.replace("1.280,00", "1.290,00")
        _, resumen, _, _ = ejecutar(dict(BUENOS, total=("1290.00", "TOTAL: 1.290,00 €")), fuente=fuente)
        self.assertTrue(any("no es la suma de base + iva (saldrían 1280.00)" in m for m in motivos(resumen, "total")))

    def test_el_mismo_documento_dos_veces_se_avisa(self):
        _, resumen, _, _ = ejecutar(BUENOS, otros=[("reenviado.txt", FUENTE, BUENOS)])
        self.assertTrue(any("puede ser el mismo documento dos veces" in r["motivo"] and r["documento"] == "reenviado.txt" for r in resumen["revisar"]))


class VariasLineas(unittest.TestCase):
    PEDIDO = "Pedido OL-2291 de Óptica Lumen\n- 6 estanterías de pared modelo Roble 120\n- 2 mostradores a medida\n"
    CAMPOS_PEDIDO = {
        "campos": [{"nombre": "cliente", "tipo": "texto"}, {"nombre": "referencia", "tipo": "texto"}, {"nombre": "producto", "tipo": "texto"}, {"nombre": "cantidad", "tipo": "numero"}],
        "clave": ["cliente", "referencia"],
    }

    def extraer(self, documentos, otros=()):
        carpeta = pathlib.Path(tempfile.mkdtemp())
        (carpeta / "fuentes").mkdir()
        (carpeta / "fuentes" / "pedido.txt").write_text(self.PEDIDO, encoding="utf-8")
        for nombre in otros:
            (carpeta / "fuentes" / nombre).write_text(self.PEDIDO, encoding="utf-8")
        (carpeta / "campos.json").write_text(json.dumps(self.CAMPOS_PEDIDO), encoding="utf-8")
        (carpeta / "extraccion.json").write_text(json.dumps({"documentos": documentos}), encoding="utf-8")
        salida, errores = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(salida), contextlib.redirect_stderr(errores):
            codigo = comprobar.main(["--campos", str(carpeta / "campos.json"), "--extraccion", str(carpeta / "extraccion.json"), "--fuentes", str(carpeta / "fuentes"), "--csv", str(carpeta / "datos.csv")])
        return codigo, (json.loads(salida.getvalue()) if codigo == 0 else None), errores.getvalue(), carpeta

    def linea(self, n, producto, cantidad, evidencia, documento="pedido.txt"):
        d = lambda v, e: {"valor": v, "evidencia": e}  # noqa: E731
        return {"documento": documento, "linea": n, "campos": {"cliente": d("Óptica Lumen", "Pedido OL-2291 de Óptica Lumen"), "referencia": d("OL-2291", "Pedido OL-2291"), "producto": d(producto, evidencia), "cantidad": d(cantidad, evidencia)}}

    def test_un_pedido_con_dos_productos_son_dos_filas_de_un_documento(self):
        codigo, resumen, errores, carpeta = self.extraer([self.linea(1, "estanterías de pared modelo Roble 120", "6", "6 estanterías de pared modelo Roble 120"), self.linea(2, "mostradores a medida", "2", "2 mostradores a medida")])
        self.assertEqual(codigo, 0, errores)
        self.assertEqual((resumen["documentos"], resumen["filas"], resumen["para_revisar"]), (1, 2, 0))
        filas = tabla(carpeta)
        self.assertEqual([f["documento"] for f in filas], ["pedido.txt · línea 1", "pedido.txt · línea 2"])
        self.assertEqual([f["cantidad"] for f in filas], ["6", "2"])

    def test_las_lineas_de_un_mismo_documento_no_son_un_duplicado_pero_otro_documento_si(self):
        una = self.linea(1, "mostradores a medida", "2", "2 mostradores a medida")
        otra = self.linea(1, "mostradores a medida", "2", "2 mostradores a medida", documento="reenviado.txt")
        _, resumen, _, _ = self.extraer([una, otra], otros=["reenviado.txt"])
        self.assertEqual(len([r for r in resumen["revisar"] if "mismo documento dos veces" in r["motivo"]]), 1)

    def test_el_mismo_documento_dos_veces_sin_numerar_lineas_no_entra(self):
        una = self.linea(1, "mostradores a medida", "2", "2 mostradores a medida")
        del una["linea"]
        codigo, _, errores, _ = self.extraer([una, dict(una)])
        self.assertEqual(codigo, 1)
        self.assertIn("numéralas con `linea`", errores)


class Lectores(unittest.TestCase):
    def test_importes_escritos_a_la_espanola_y_a_la_inglesa(self):
        self.assertIn(D("1234.56"), comprobar.numeros_en("Total 1.234,56 €"))
        self.assertIn(D("1234.56"), comprobar.numeros_en("Total EUR 1,234.56"))
        self.assertIn(D("1234"), comprobar.numeros_en("1.234 unidades"))
        self.assertIn(D("1234.56"), comprobar.numeros_en("1 234,56"))
        self.assertIn(D("-50.00"), comprobar.numeros_en("Abono: -50,00"))
        self.assertNotIn(D("1280.00"), comprobar.numeros_en("Base 1.057,85 IVA 222,15"))

    def test_fechas_en_las_formas_que_trae_un_documento(self):
        esperada = datetime.date(2026, 9, 28)
        for texto in ("28/09/2026", "28-9-2026", "28.09.26", "2026-09-28", "28 de septiembre de 2026", "28 sept. 2026", "Zaragoza, a 28 de Septiembre del 2026"):
            with self.subTest(texto):
                self.assertIn(esperada, comprobar.fechas_en(texto))
        self.assertEqual(comprobar.fechas_en("para el 28 de septiembre"), set())
        self.assertEqual(comprobar.fechas_en("31/02/2026"), set())

    def test_iban_conocidos(self):
        for iban in ("ES9121000418450200051332", "GB82 WEST 1234 5698 7654 32", "DE89370400440532013000"):
            with self.subTest(iban):
                self.assertTrue(comprobar.iban_valido(iban))
        self.assertFalse(comprobar.iban_valido("ES9121000418450200051333"))
        self.assertIsNone(comprobar.iban_valido("0049 1500 05 1234567892"))

    def test_nif_conocidos(self):
        for nif in ("12345678Z", "X1234567L", "A58818501", "Q2826000H"):
            with self.subTest(nif):
                self.assertTrue(comprobar.nif_valido(nif))
        self.assertFalse(comprobar.nif_valido("12345678A"))
        self.assertIsNone(comprobar.nif_valido("FR12345678901"))


class EntradaMala(unittest.TestCase):
    def test_un_campo_que_no_se_acordo_no_entra(self):
        codigo, _, errores, _ = ejecutar(dict(BUENOS, descuento=("5", "5 %")))
        self.assertEqual(codigo, 1)
        self.assertIn("trae el campo 'descuento', que no está en la lista acordada", errores)

    def test_un_tipo_que_no_existe(self):
        campos = {"campos": [{"nombre": "total", "tipo": "dinero"}]}
        codigo, _, errores, _ = ejecutar({"total": BUENOS["total"]}, campos=campos)
        self.assertEqual(codigo, 1)
        self.assertIn("`tipo` es 'dinero'", errores)

    def test_una_suma_con_un_campo_que_no_existe(self):
        campos = {"campos": [{"nombre": "total", "tipo": "importe"}], "sumas": [{"total": "total", "sumandos": ["base"]}]}
        codigo, _, errores, _ = ejecutar({"total": BUENOS["total"]}, campos=campos)
        self.assertEqual(codigo, 1)
        self.assertIn("una suma nombra el campo 'base'", errores)


class Ejemplo(unittest.TestCase):
    """The worked example the skill shows: four documents with traps, and an extraction that fell into three."""

    def test_el_ejemplo_da_lo_que_dice_el_resumen_guardado(self):
        salida = io.StringIO()
        ejemplos = SKILL / "ejemplos"
        with contextlib.redirect_stdout(salida):
            codigo = comprobar.main(["--campos", str(ejemplos / "campos.json"), "--extraccion", str(ejemplos / "extraccion.json"), "--fuentes", str(ejemplos / "fuentes")])
        self.assertEqual(codigo, 0)
        resumen = json.loads(salida.getvalue())
        self.assertEqual(resumen, json.loads((ejemplos / "resumen.json").read_text(encoding="utf-8")))
        self.assertEqual(resumen["datos_vaciados_por_no_poder_comprobarse"], 2)
        self.assertEqual(resumen["documentos_sin_nada_que_revisar"], 1)

    def test_la_instruccion_escondida_en_un_correo_no_cambia_ningun_dato(self):
        fuente = (SKILL / "ejemplos" / "fuentes" / "correo-luz.txt").read_text(encoding="utf-8")
        self.assertIn("ignore las instrucciones anteriores", fuente)
        extraccion = json.loads((SKILL / "ejemplos" / "extraccion.json").read_text(encoding="utf-8"))
        luz = next(d for d in extraccion["documentos"] if d["documento"] == "correo-luz.txt")
        self.assertEqual(luz["campos"]["total"]["valor"], "375.10")


if __name__ == "__main__":
    unittest.main()

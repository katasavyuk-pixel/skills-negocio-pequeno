"""The workbook writer: what it writes has to open in Excel, not just unzip."""
import datetime
import pathlib
import sys
import tempfile
import unittest
import zipfile
from decimal import Decimal
from xml.etree import ElementTree

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "comun"))

from hoja_xlsx import escribir_xlsx  # noqa: E402

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

HOJAS = [
    {
        "nombre": "Facturas",
        "filas": [
            ["Cliente", "Vencimiento", "Importe", "Tipo", "Días", "Nota"],
            ["Talleres Añón & Hijos <S.L.>", datetime.date(2026, 7, 15), Decimal("1210.00"), 0.104, 90, "Dijo \"la semana que viene\""],
            ["Óptica Lumen", datetime.date(2026, 9, 1), 484.5, 0.104, 42, None],
            ["Total", None, Decimal("1694.50"), None, None, None],
        ],
        "formatos": {2: "euros", 3: "porcentaje", 4: "entero", 5: "texto"},
        "negrita": [3],
    },
    {"nombre": "Notas: [borrador] 2026/10 con un nombre demasiado largo", "filas": [["Aviso"], ["Texto\ncon salto"]]},
]


def escribir(hojas=HOJAS):
    carpeta = tempfile.mkdtemp()
    return pathlib.Path(escribir_xlsx(pathlib.Path(carpeta) / "prueba.xlsx", hojas))


class LibroValido(unittest.TestCase):
    def test_todas_las_partes_son_xml_bien_formado(self):
        with zipfile.ZipFile(escribir()) as libro:
            nombres = set(libro.namelist())
            for parte in nombres:
                ElementTree.fromstring(libro.read(parte))
        self.assertEqual(
            nombres,
            {
                "[Content_Types].xml",
                "_rels/.rels",
                "xl/workbook.xml",
                "xl/_rels/workbook.xml.rels",
                "xl/styles.xml",
                "xl/worksheets/sheet1.xml",
                "xl/worksheets/sheet2.xml",
            },
        )

    def test_el_nombre_de_hoja_respeta_las_reglas_de_excel(self):
        with zipfile.ZipFile(escribir()) as libro:
            hojas = ElementTree.fromstring(libro.read("xl/workbook.xml")).findall("m:sheets/m:sheet", NS)
        self.assertEqual(hojas[0].get("name"), "Facturas")
        self.assertLessEqual(len(hojas[1].get("name")), 31)
        self.assertNotRegex(hojas[1].get("name"), r"[\[\]:*?/\\]")

    def test_cada_estilo_que_usa_una_celda_existe(self):
        with zipfile.ZipFile(escribir()) as libro:
            estilos = ElementTree.fromstring(libro.read("xl/styles.xml"))
            hoja = ElementTree.fromstring(libro.read("xl/worksheets/sheet1.xml"))
        disponibles = len(estilos.findall("m:cellXfs/m:xf", NS))
        usados = {int(celda.get("s")) for celda in hoja.iter("{%s}c" % NS["m"])}
        self.assertTrue(usados)
        self.assertLess(max(usados), disponibles)

    def test_texto_numeros_y_fechas_se_escriben_como_lo_que_son(self):
        with zipfile.ZipFile(escribir()) as libro:
            hoja = ElementTree.fromstring(libro.read("xl/worksheets/sheet1.xml"))
        celdas = {celda.get("r"): celda for celda in hoja.iter("{%s}c" % NS["m"])}
        self.assertEqual(celdas["A2"].find("m:is/m:t", NS).text, "Talleres Añón & Hijos <S.L.>")
        self.assertEqual(celdas["C2"].find("m:v", NS).text, "1210.00")
        self.assertIsNone(celdas["C2"].get("t"))
        # 15-Jul-2026 as an Excel serial number.
        self.assertEqual(celdas["B2"].find("m:v", NS).text, str((datetime.date(2026, 7, 15) - datetime.date(1899, 12, 30)).days))
        self.assertEqual(celdas["F2"].find("m:is/m:t", NS).text, 'Dijo "la semana que viene"')
        self.assertIsNone(celdas["F3"].find("m:v", NS))

    def test_la_misma_entrada_da_el_mismo_fichero(self):
        self.assertEqual(escribir().read_bytes(), escribir().read_bytes())

    def test_un_caracter_de_control_no_rompe_el_fichero(self):
        ruta = escribir([{"nombre": "x", "filas": [["a"], ["antes\x07después"]]}])
        with zipfile.ZipFile(ruta) as libro:
            hoja = ElementTree.fromstring(libro.read("xl/worksheets/sheet1.xml"))
        textos = [nodo.text for nodo in hoja.findall(".//m:is/m:t", NS)]
        self.assertEqual(textos, ["a", "antesdespués"])

    def test_avisa_en_vez_de_escribir_algo_que_excel_no_abre(self):
        with self.assertRaises(ValueError):
            escribir([])
        with self.assertRaises(ValueError):
            escribir([{"nombre": "Igual", "filas": [["a"]]}, {"nombre": "igual", "filas": [["a"]]}])
        with self.assertRaises(ValueError):
            escribir([{"nombre": "x", "filas": [["a"], [1]], "formatos": {0: "dolares"}}])


class LeidoPorOtraLibreria(unittest.TestCase):
    """The real check: a spreadsheet library reads back what was written."""

    def setUp(self):
        try:
            import openpyxl
        except ImportError:
            self.skipTest("openpyxl no está instalado (en CI sí lo está).")
        self.openpyxl = openpyxl

    def test_openpyxl_lee_valores_formatos_y_negritas(self):
        libro = self.openpyxl.load_workbook(escribir())
        hoja = libro["Facturas"]
        self.assertEqual(hoja["A2"].value, "Talleres Añón & Hijos <S.L.>")
        self.assertEqual(hoja["B2"].value.date(), datetime.date(2026, 7, 15))
        self.assertAlmostEqual(hoja["C2"].value, 1210.00)
        self.assertIn("€", hoja["C2"].number_format)
        self.assertEqual(hoja["D2"].number_format, "0.00%")
        self.assertTrue(hoja["A1"].font.bold)
        self.assertTrue(hoja["C4"].font.bold)
        self.assertFalse(hoja["C3"].font.bold)
        self.assertEqual(hoja.freeze_panes, "A2")
        self.assertEqual(hoja.auto_filter.ref, "A1:F4")
        self.assertEqual(len(libro.sheetnames), 2)


if __name__ == "__main__":
    unittest.main()

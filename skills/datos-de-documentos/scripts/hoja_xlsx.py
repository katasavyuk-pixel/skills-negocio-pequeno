"""Writes a real .xlsx workbook with the Python standard library only.

A skill of this catalogue has to leave a file the owner of a business can open,
and it has to run wherever the skill is installed: a laptop with a bare Python,
or the sandbox of the Claude apps. So there is no openpyxl here, on purpose.
This writes the handful of XML parts a workbook needs and nothing else: text,
numbers, dates, a bold header that stays in view, euro and percentage formats,
bold total rows and column widths.

Use it from another script of the same skill:

    from hoja_xlsx import escribir_xlsx

    escribir_xlsx("salida.xlsx", [{
        "nombre": "Resumen",
        "filas": [["Cliente", "Importe"], ["Acme", Decimal("1210.00")]],
        "formatos": {1: "euros"},      # by column index, 0-based
        "negrita": [5],                # row indexes (0-based) to set in bold
    }])

The first row of every sheet is the header.
"""
import datetime
import re
import zipfile
from decimal import Decimal
from xml.sax.saxutils import escape

__all__ = ["escribir_xlsx"]

# Excel refuses these characters in a sheet name and cuts names at 31.
_NOMBRE_PROHIBIDO = re.compile(r"[\[\]:*?/\\]")
_NOMBRE_MAX = 31
# Characters XML 1.0 does not allow; a stray one makes Excel report the file as damaged.
_XML_ILEGAL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f]")
# Excel counts days from this date (the 1900 system with its leap-year bug absorbed).
_EPOCA = datetime.date(1899, 12, 30)
# A fixed timestamp makes the same input produce the same file, byte for byte.
_FECHA_ZIP = (1980, 1, 1, 0, 0, 0)

# Index into <cellXfs> of styles.xml, below.
_ESTILO = {
    "normal": 0,
    "cabecera": 1,
    "euros": 2,
    "fecha": 3,
    "porcentaje": 4,
    "entero": 5,
    "texto": 6,
}
# The bold variant of each style sits this many positions after the plain one.
_NEGRITA = 7

_FORMATOS_NUMERO = (
    (164, '#,##0.00\\ "€"'),
    (165, "dd/mm/yyyy"),
    (166, "0.00%"),
    (167, "#,##0"),
)


def _estilos_xml():
    def xf(fuente, formato, relleno=0, ajustar=False):
        alineacion = '<alignment vertical="top" wrapText="1"/>' if ajustar else '<alignment vertical="top"/>'
        return (
            '<xf numFmtId="%d" fontId="%d" fillId="%d" borderId="0" xfId="0" '
            'applyNumberFormat="1" applyFont="1" applyFill="1" applyAlignment="1">%s</xf>'
            % (formato, fuente, relleno, alineacion)
        )

    def serie(fuente):
        return [
            xf(fuente, 0),  # normal
            xf(1, 0, relleno=2, ajustar=True),  # cabecera (always bold)
            xf(fuente, 164),  # euros
            xf(fuente, 165),  # fecha
            xf(fuente, 166),  # porcentaje
            xf(fuente, 167),  # entero
            xf(fuente, 49, ajustar=True),  # texto, wrapped
        ]

    celdas = serie(0) + serie(1)
    formatos = "".join('<numFmt numFmtId="%d" formatCode="%s"/>' % (n, escape(c, {'"': "&quot;"})) for n, c in _FORMATOS_NUMERO)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<numFmts count="%d">%s</numFmts>'
        '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
        '<font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="3"><fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFE7E6E6"/><bgColor indexed="64"/></patternFill></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="%d">%s</cellXfs>'
        "</styleSheet>" % (len(_FORMATOS_NUMERO), formatos, len(celdas), "".join(celdas))
    )


def _columna(indice):
    """0 -> A, 25 -> Z, 26 -> AA."""
    letras = ""
    indice += 1
    while indice:
        indice, resto = divmod(indice - 1, 26)
        letras = chr(65 + resto) + letras
    return letras


def _texto(valor):
    return escape(_XML_ILEGAL.sub("", str(valor)))


def _celda(referencia, valor, estilo):
    if valor is None or valor == "":
        return '<c r="%s" s="%d"/>' % (referencia, estilo)
    if isinstance(valor, bool):
        valor = "Sí" if valor else "No"
    if isinstance(valor, (datetime.datetime, datetime.date)):
        dia = valor.date() if isinstance(valor, datetime.datetime) else valor
        return '<c r="%s" s="%d"><v>%d</v></c>' % (referencia, estilo, (dia - _EPOCA).days)
    if isinstance(valor, (int, float, Decimal)):
        return '<c r="%s" s="%d"><v>%s</v></c>' % (referencia, estilo, valor)
    return '<c r="%s" s="%d" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (
        referencia,
        estilo,
        _texto(valor),
    )


def _ancho(valor, formato):
    if isinstance(valor, (datetime.date, datetime.datetime)):
        return 11
    if isinstance(valor, (int, float, Decimal)) and not isinstance(valor, bool):
        return len("%.2f" % valor) + (4 if formato == "euros" else 2)
    return max((len(linea) for linea in str(valor).split("\n")), default=0)


def _hoja_xml(hoja):
    filas = hoja.get("filas") or [[]]
    formatos = hoja.get("formatos") or {}
    negrita = set(hoja.get("negrita") or [])
    columnas = max(len(fila) for fila in filas)

    anchos = [0] * columnas
    cuerpo = []
    for f, fila in enumerate(filas):
        celdas = []
        for c, valor in enumerate(fila):
            if f == 0:
                estilo = _ESTILO["cabecera"]
            else:
                nombre = formatos.get(c)
                if nombre is None:
                    nombre = "fecha" if isinstance(valor, (datetime.date, datetime.datetime)) else "normal"
                if nombre not in _ESTILO:
                    raise ValueError("Formato desconocido %r. Válidos: %s" % (nombre, ", ".join(sorted(_ESTILO))))
                estilo = _ESTILO[nombre] + (_NEGRITA if f in negrita else 0)
            if valor is not None:
                anchos[c] = max(anchos[c], _ancho(valor, formatos.get(c)))
            celdas.append(_celda("%s%d" % (_columna(c), f + 1), valor, estilo))
        cuerpo.append('<row r="%d">%s</row>' % (f + 1, "".join(celdas)))

    # A width is "characters of the default font"; cap it so one long note does not push the rest off screen.
    pedidos = hoja.get("anchos") or []
    cols = "".join(
        '<col min="%d" max="%d" width="%s" customWidth="1"/>'
        % (c + 1, c + 1, pedidos[c] if c < len(pedidos) and pedidos[c] else min(max(anchos[c] + 2, 8), 60))
        for c in range(columnas)
    )
    filtro = ""
    if columnas and len(filas) > 1:
        filtro = '<autoFilter ref="A1:%s%d"/>' % (_columna(columnas - 1), len(filas))
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetViews><sheetView workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        "</sheetView></sheetViews>"
        '<sheetFormatPr defaultRowHeight="15"/>'
        "%s<sheetData>%s</sheetData>%s</worksheet>"
        % ("<cols>%s</cols>" % cols if cols else "", "".join(cuerpo), filtro)
    )


def _nombres(hojas):
    vistos = set()
    for i, hoja in enumerate(hojas):
        nombre = _NOMBRE_PROHIBIDO.sub(" ", str(hoja.get("nombre") or "Hoja %d" % (i + 1))).strip()[:_NOMBRE_MAX]
        nombre = nombre or "Hoja %d" % (i + 1)
        if nombre.lower() in vistos:
            raise ValueError("Dos hojas se llaman %r: Excel no lo admite." % nombre)
        vistos.add(nombre.lower())
        yield nombre


def escribir_xlsx(ruta, hojas):
    """Writes `hojas` to `ruta`. Each sheet is a dict:

    nombre    sheet name (cut at 31 characters)
    filas     list of rows; the first one is the header
    formatos  {column index: "euros" | "fecha" | "porcentaje" | "entero" | "texto"}
    negrita   row indexes (0-based) to set in bold, for totals
    anchos    optional column widths, in characters; missing ones are estimated

    Cell values: str, int, float, Decimal, date, datetime, bool or None.
    A percentage is a fraction: 0.104 shows as 10,40 %.
    """
    if not hojas:
        raise ValueError("Hace falta al menos una hoja.")
    nombres = list(_nombres(hojas))
    partes = {
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            "%s</Types>"
            % "".join(
                '<Override PartName="/xl/worksheets/sheet%d.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                % (i + 1)
                for i in range(len(hojas))
            )
        ),
        "_rels/.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>"
        ),
        "xl/workbook.xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            "<sheets>%s</sheets></workbook>"
            % "".join(
                '<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (escape(nombre, {'"': "&quot;"}), i + 1, i + 1)
                for i, nombre in enumerate(nombres)
            )
        ),
        "xl/_rels/workbook.xml.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            "%s"
            '<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            "</Relationships>"
            % (
                "".join(
                    '<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet%d.xml"/>'
                    % (i + 1, i + 1)
                    for i in range(len(hojas))
                ),
                len(hojas) + 1,
            )
        ),
        "xl/styles.xml": _estilos_xml(),
    }
    for i, hoja in enumerate(hojas):
        partes["xl/worksheets/sheet%d.xml" % (i + 1)] = _hoja_xml(hoja)

    with zipfile.ZipFile(str(ruta), "w", zipfile.ZIP_DEFLATED) as libro:
        for nombre, contenido in partes.items():
            info = zipfile.ZipInfo(nombre, date_time=_FECHA_ZIP)
            info.compress_type = zipfile.ZIP_DEFLATED
            libro.writestr(info, contenido.encode("utf-8"))
    return str(ruta)

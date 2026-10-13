#!/usr/bin/env python3
"""Checks data pulled out of documents against the documents themselves, and builds the table.

A model that reads an invoice or an email and fills in a table is right most of the
time, and when it is wrong it is wrong silently: a total it worked out instead of
reading, a date it completed, a tax number it tidied up. One invented cell is
enough to stop trusting the other two hundred. So here the model has to hand over,
with every value, the literal fragment of the document it took it from, and this
script checks two things nobody should take on trust: that the fragment really is
in the document, and that the value really comes out of the fragment. What fails is
emptied and sent to a person. What is left in the table can be traced.

Inputs:
    campos.json      the fields agreed with the person
    extraccion.json  what the model extracted, with its evidence
    fuentes/         one .txt per document: the text the model read

campos.json:
    {"campos": [{"nombre": "total", "tipo": "importe", "obligatorio": true}, ...],
     "sumas": [{"total": "total", "sumandos": ["base", "iva"]}],
     "clave": ["nif_emisor", "numero"]}
    Types: texto | numero | importe | fecha | nif | iban | email | telefono

extraccion.json:
    {"documentos": [{"documento": "factura-031.txt",
                     "campos": {"total": {"valor": "3630.00", "evidencia": "TOTAL 3.630,00 €"},
                                "pedido": null}}]}
    Values: numbers with a dot for decimals, dates as YYYY-MM-DD, everything else as written.
    A document with several lines (an order with three products) takes one entry per line,
    with the same "documento" and "linea": 1, 2, 3.

Usage:
    python3 scripts/comprobar.py --campos campos.json --extraccion extraccion.json \
        --fuentes fuentes --salida datos.xlsx --csv datos.csv

Prints a JSON summary, writes the workbook and, with --csv, the table alone.
Exit code 0 when the check ran (whatever it found), 1 when the fields or the
extraction are not written as described (each problem named), 2 when a file cannot
be read or written.
Standard library only. Reads the three inputs, writes the outputs, opens no connection.
"""
import argparse
import csv
import datetime
import json
import pathlib
import re
import sys
import unicodedata
from decimal import Decimal, InvalidOperation

from hoja_xlsx import escribir_xlsx

TIPOS = ("texto", "numero", "importe", "fecha", "nif", "iban", "email", "telefono")
# One cent: a total read as 3630.00 and one read as 3630 are the same amount.
TOLERANCIA = Decimal("0.01")
# Two cents on a sum: documents that round each line can be off by one cent per addend.
TOLERANCIA_SUMA = Decimal("0.02")
LETRAS_NIF = "TRWAGMYFPDXBNJZSQVHLCKE"
LETRAS_ENTIDAD = "JABCDEFGHI"
MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dic": 12,
}
# The model may join two fragments of the same document with one of these.
SEPARADOR_DE_TROZOS = re.compile(r"\s*(?:…|\.\.\.|\s\|\s)\s*")
# A fragment shorter than this proves nothing: "21" is in every invoice.
EVIDENCIA_MIN = 2


class EntradaInvalida(Exception):
    def __init__(self, problemas):
        super().__init__("\n".join(problemas))
        self.problemas = problemas


# ---------------------------------------------------------------- normalising


def plano(texto):
    """Case, accents, typographic quotes and dashes, and runs of spaces, aside."""
    texto = unicodedata.normalize("NFKC", str(texto))
    for raro, normal in (("−", "-"), ("–", "-"), ("—", "-"), ("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), (" ", " "), (" ", " ")):
        texto = texto.replace(raro, normal)
    texto = "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).strip().lower()


def compacto(texto):
    """Only letters and digits: for tax numbers, account numbers and phones written with dots, spaces or dashes."""
    return re.sub(r"[^a-z0-9]", "", plano(texto))


def evidencia_en_fuente(evidencia, fuente):
    """True when the fragment (or each piece of it) is literally in the document."""
    trozos = [t for t in SEPARADOR_DE_TROZOS.split(str(evidencia)) if t.strip()]
    if not trozos:
        return False
    donde = plano(fuente)
    return all(len(plano(t)) >= EVIDENCIA_MIN and plano(t) in donde for t in trozos)


# ---------------------------------------------------------------- reading values out of a fragment


def numeros_en(texto):
    """Every amount a fragment may be stating, read both the Spanish way (1.234,56) and the English way (1,234.56)."""
    encontrados = set()
    for trozo in re.findall(r"[-+−]?\d(?:[\d.,\s ']*\d)?", str(texto)):
        limpio = re.sub(r"[\s ']", "", trozo).replace("−", "-")
        candidatos = {limpio}
        if "," in limpio and "." in limpio:
            ultimo = max(limpio.rfind(","), limpio.rfind("."))
            decimal = limpio[ultimo]
            miles = "." if decimal == "," else ","
            candidatos = {limpio.replace(miles, "").replace(decimal, ".")}
        elif "," in limpio:
            candidatos = {limpio.replace(",", "."), limpio.replace(",", "")}
        elif "." in limpio:
            candidatos = {limpio, limpio.replace(".", "")}
        for candidato in candidatos:
            try:
                encontrados.add(Decimal(candidato))
            except InvalidOperation:
                pass
    return encontrados


def fechas_en(texto):
    """Every date a fragment may be stating: 28/09/2026, 28-9-26, 2026-09-28, 28 de septiembre de 2026."""
    encontradas = set()

    def apuntar(anio, mes, dia):
        anio = int(anio)
        if anio < 100:
            anio += 2000
        try:
            encontradas.add(datetime.date(anio, int(mes), int(dia)))
        except ValueError:
            pass

    for dia, mes, anio in re.findall(r"\b(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4}|\d{2})\b", str(texto)):
        apuntar(anio, mes, dia)
    for anio, mes, dia in re.findall(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", str(texto)):
        apuntar(anio, mes, dia)
    for dia, mes, anio in re.findall(r"\b(\d{1,2})\s+(?:de\s+)?([a-z]+)\.?\s+(?:de\s+|del\s+)?(\d{4})\b", plano(texto)):
        if mes in MESES:
            apuntar(anio, MESES[mes], dia)
    return encontradas


def nif_valido(nif):
    """None when the number does not look like a Spanish tax number; True or False when it does."""
    limpio = compacto(nif).upper()
    if limpio.startswith("ES") and len(limpio) == 11:
        limpio = limpio[2:]
    if re.fullmatch(r"\d{8}[A-Z]", limpio):
        return LETRAS_NIF[int(limpio[:8]) % 23] == limpio[8]
    if re.fullmatch(r"[XYZ]\d{7}[A-Z]", limpio):
        return LETRAS_NIF[("XYZ".index(limpio[0]) * 10 ** 7 + int(limpio[1:8])) % 23] == limpio[8]
    if re.fullmatch(r"[ABCDEFGHJKLMNPQRSUVW]\d{7}[0-9A-J]", limpio):
        digitos = [int(d) for d in limpio[1:8]]
        suma = sum(digitos[1::2]) + sum(sum(divmod(2 * d, 10)) for d in digitos[0::2])
        control = (10 - suma % 10) % 10
        validos = set()
        if limpio[0] not in "ABEH":
            validos.add(LETRAS_ENTIDAD[control])
        if limpio[0] not in "KPQRSNW":
            validos.add(str(control))
        return limpio[8] in validos
    return None


def iban_valido(iban):
    """ISO 13616: move the first four characters to the end, turn letters into numbers, and the rest of dividing by 97 is 1."""
    limpio = compacto(iban).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", limpio):
        return None
    girado = limpio[4:] + limpio[:4]
    return int("".join(str(int(c, 36)) for c in girado)) % 97 == 1


def comprobar_valor(tipo, valor, evidencia):
    """Returns (ok, motivo, aviso). `ok` False empties the field; `aviso` keeps it and sends it to review."""
    valor = str(valor).strip()
    if tipo == "texto":
        return (plano(valor) in plano(evidencia), "el valor no está escrito así en el fragmento citado", None)
    if tipo in ("numero", "importe"):
        try:
            numero = Decimal(valor)
        except InvalidOperation:
            return False, "el valor %r no es un número con punto decimal" % valor, None
        return (any(abs(numero - candidato) <= (TOLERANCIA if tipo == "importe" else 0) for candidato in numeros_en(evidencia)), "esa cifra no está en el fragmento citado", None)
    if tipo == "fecha":
        try:
            dia = datetime.date.fromisoformat(valor)
        except ValueError:
            return False, "el valor %r no es una fecha AAAA-MM-DD" % valor, None
        return dia in fechas_en(evidencia), "esa fecha no está en el fragmento citado", None
    if tipo in ("nif", "iban", "telefono"):
        if tipo == "telefono":
            propio, ajeno = re.sub(r"\D", "", valor), re.sub(r"\D", "", str(evidencia))
        else:
            propio, ajeno = compacto(valor), compacto(evidencia)
        if not propio or propio not in ajeno:
            return False, "ese número no está en el fragmento citado", None
        if tipo == "nif" and nif_valido(valor) is False:
            return True, "", "el NIF está en el documento, pero su letra o dígito de control no corresponde: puede estar mal en el propio documento"
        if tipo == "iban" and iban_valido(valor) is False:
            return True, "", "el IBAN está en el documento, pero no pasa el control: puede estar mal en el propio documento"
        return True, "", None
    if tipo == "email":
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", valor):
            return False, "el valor %r no tiene forma de dirección de correo" % valor, None
        return valor.lower() in str(evidencia).lower(), "esa dirección no está en el fragmento citado", None
    raise ValueError(tipo)


# ---------------------------------------------------------------- reading the inputs


def leer_json(ruta, que):
    try:
        with open(ruta, encoding="utf-8") as fichero:
            return json.load(fichero)
    except ValueError as fallo:
        raise EntradaInvalida(["%s (%s) no es JSON válido: %s" % (que, ruta, fallo)])


def leer_campos(ruta):
    datos = leer_json(ruta, "La lista de campos")
    problemas, campos = [], []
    lista = datos.get("campos") if isinstance(datos, dict) else None
    if not isinstance(lista, list) or not lista:
        raise EntradaInvalida(["campos.json tiene que ser {\"campos\": [...]} con al menos un campo."])
    for i, campo in enumerate(lista, 1):
        if not isinstance(campo, dict) or not str(campo.get("nombre", "")).strip():
            problemas.append("campo %d: le falta `nombre`." % i)
            continue
        if campo.get("tipo") not in TIPOS:
            problemas.append("campo `%s`: `tipo` es %r y tiene que ser uno de %s." % (campo["nombre"], campo.get("tipo"), ", ".join(TIPOS)))
        campos.append({"nombre": str(campo["nombre"]).strip(), "tipo": campo.get("tipo"), "obligatorio": bool(campo.get("obligatorio", False))})
    nombres = [c["nombre"] for c in campos]
    if len(set(nombres)) != len(nombres):
        problemas.append("hay dos campos con el mismo nombre.")
    sumas = datos.get("sumas", [])
    for suma in sumas:
        for nombre in [suma.get("total")] + list(suma.get("sumandos", [])):
            if nombre not in nombres:
                problemas.append("una suma nombra el campo %r, que no está en la lista." % nombre)
    clave = datos.get("clave", [])
    for nombre in clave:
        if nombre not in nombres:
            problemas.append("`clave` nombra el campo %r, que no está en la lista." % nombre)
    if problemas:
        raise EntradaInvalida(problemas)
    return campos, sumas, clave


def leer_extraccion(ruta, campos):
    datos = leer_json(ruta, "La extracción")
    documentos = datos.get("documentos") if isinstance(datos, dict) else None
    if not isinstance(documentos, list) or not documentos:
        raise EntradaInvalida(["extraccion.json tiene que ser {\"documentos\": [...]} con al menos un documento."])
    nombres = {c["nombre"] for c in campos}
    problemas, vistos = [], set()
    for i, documento in enumerate(documentos, 1):
        nombre = documento.get("documento") if isinstance(documento, dict) else None
        if not nombre:
            problemas.append("documento %d: le falta `documento` (el nombre de su fichero en fuentes/)." % i)
            continue
        linea = documento.get("linea")
        if linea is not None and not (isinstance(linea, int) and linea >= 1):
            problemas.append("%s: `linea` es %r y tiene que ser 1, 2, 3…" % (nombre, linea))
        if (nombre, linea) in vistos:
            problemas.append("%s: está dos veces en la extracción. Si trae varias líneas, numéralas con `linea`." % nombre)
        if any(visto == nombre and (otra is None) != (linea is None) for visto, otra in vistos):
            problemas.append("%s: unas entradas llevan `linea` y otras no. O todas o ninguna." % nombre)
        vistos.add((nombre, linea))
        valores = documento.get("campos")
        if not isinstance(valores, dict):
            problemas.append("%s: le falta `campos`." % nombre)
            continue
        for campo, dato in valores.items():
            if campo not in nombres:
                problemas.append("%s: trae el campo %r, que no está en la lista acordada." % (nombre, campo))
            elif dato is not None and not (isinstance(dato, dict) and "valor" in dato and "evidencia" in dato):
                problemas.append("%s, campo `%s`: tiene que ser null o {\"valor\": ..., \"evidencia\": ...}." % (nombre, campo))
    if problemas:
        raise EntradaInvalida(problemas)
    return documentos


# ---------------------------------------------------------------- the check


def comprobar(campos, sumas, clave, documentos, carpeta):
    filas, revisar, trazas = [], [], []
    cuenta = {"rellenos": 0, "vacios": 0, "vaciados_sin_evidencia": 0}

    def a_revisar(documento, campo, valor, motivo):
        revisar.append({"documento": documento, "campo": campo, "valor": "" if valor is None else str(valor), "motivo": motivo})

    for documento in documentos:
        fichero = documento["documento"]
        # A document with several lines gives several rows; each one says which line it is.
        nombre = fichero if documento.get("linea") is None else "%s · línea %d" % (fichero, documento["linea"])
        ruta = pathlib.Path(carpeta) / fichero
        try:
            fuente = ruta.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            fuente = None
            a_revisar(nombre, "", None, "no encuentro el texto de este documento en %s: no se ha podido comprobar nada y la fila queda vacía" % ruta)
        fila = {"documento": nombre, "_fichero": fichero}
        for campo in campos:
            dato = documento["campos"].get(campo["nombre"])
            valor = None
            if dato is not None and str(dato["valor"]).strip() != "" and fuente is not None:
                evidencia = str(dato.get("evidencia") or "")
                if not evidencia_en_fuente(evidencia, fuente):
                    cuenta["vaciados_sin_evidencia"] += 1
                    a_revisar(nombre, campo["nombre"], dato["valor"], "el fragmento citado no está en el documento: el dato se ha vaciado")
                else:
                    ok, motivo, aviso = comprobar_valor(campo["tipo"], dato["valor"], evidencia)
                    if not ok:
                        cuenta["vaciados_sin_evidencia"] += 1
                        a_revisar(nombre, campo["nombre"], dato["valor"], motivo + ": el dato se ha vaciado")
                    else:
                        valor = str(dato["valor"]).strip()
                        trazas.append({"documento": nombre, "campo": campo["nombre"], "valor": valor, "evidencia": evidencia})
                        if aviso:
                            a_revisar(nombre, campo["nombre"], valor, aviso)
            if valor is None:
                cuenta["vacios"] += 1
                if campo["obligatorio"] and fuente is not None and not any(r["documento"] == nombre and r["campo"] == campo["nombre"] for r in revisar):
                    a_revisar(nombre, campo["nombre"], None, "es un dato obligatorio y el documento no lo trae")
            else:
                cuenta["rellenos"] += 1
            fila[campo["nombre"]] = valor
        for suma in sumas:
            partes = [fila.get(n) for n in suma["sumandos"]]
            if fila.get(suma["total"]) is not None and all(p is not None for p in partes):
                esperado = sum((Decimal(p) for p in partes), Decimal("0"))
                if abs(esperado - Decimal(fila[suma["total"]])) > TOLERANCIA_SUMA:
                    a_revisar(nombre, suma["total"], fila[suma["total"]], "%s no es la suma de %s (saldrían %s): está así en el documento, o se ha leído mal" % (suma["total"], " + ".join(suma["sumandos"]), esperado))
        filas.append(fila)

    if clave:
        vistas = {}
        for fila in filas:
            identidad = tuple(compacto(fila.get(n) or "") for n in clave)
            if all(identidad):
                # Lines of the same document share its key on purpose: only another document counts.
                if identidad in vistas and vistas[identidad] != fila["_fichero"]:
                    a_revisar(fila["documento"], clave[0], fila.get(clave[0]), "coincide en %s con %s: puede ser el mismo documento dos veces" % (" y ".join(clave), vistas[identidad]))
                vistas.setdefault(identidad, fila["_fichero"])

    resumen = {
        "documentos": len({fila["_fichero"] for fila in filas}),
        "filas": len(filas),
        "campos_por_documento": len(campos),
        "datos_rellenos": cuenta["rellenos"],
        "datos_vacios": cuenta["vacios"],
        "datos_vaciados_por_no_poder_comprobarse": cuenta["vaciados_sin_evidencia"],
        "para_revisar": len(revisar),
        "documentos_sin_nada_que_revisar": sum(1 for fila in filas if not any(r["documento"] == fila["documento"] for r in revisar)),
        "revisar": revisar,
    }
    return filas, trazas, resumen


# ---------------------------------------------------------------- output


def celda(campo, valor):
    if valor is None:
        return None
    if campo["tipo"] in ("numero", "importe"):
        return Decimal(valor)
    if campo["tipo"] == "fecha":
        return datetime.date.fromisoformat(valor)
    return valor


def hojas(campos, filas, trazas, resumen):
    datos = [["Documento"] + [c["nombre"] for c in campos]]
    for fila in filas:
        datos.append([fila["documento"]] + [celda(c, fila[c["nombre"]]) for c in campos])
    formatos = {i + 1: {"importe": "euros", "fecha": "fecha"}.get(c["tipo"], "normal") for i, c in enumerate(campos)}
    revisar = [["Documento", "Dato", "Lo que se leyó", "Por qué hay que mirarlo"]]
    for r in resumen["revisar"]:
        revisar.append([r["documento"], r["campo"], r["valor"], r["motivo"]])
    origen = [["Documento", "Dato", "Valor", "Fragmento del documento del que sale"]]
    for t in trazas:
        origen.append([t["documento"], t["campo"], t["valor"], t["evidencia"]])
    return [
        {"nombre": "Datos", "filas": datos, "formatos": formatos},
        {"nombre": "Para revisar", "filas": revisar, "formatos": {2: "texto", 3: "texto"}, "anchos": [30, 22, 26, 90]},
        {"nombre": "De dónde sale cada dato", "filas": origen, "formatos": {2: "texto", 3: "texto"}, "anchos": [30, 22, 26, 90]},
    ]


def main(argumentos=None):
    analizador = argparse.ArgumentParser(description="Comprueba contra los documentos los datos que se han sacado de ellos, y monta la tabla.")
    analizador.add_argument("--campos", required=True, help="campos.json: los datos acordados")
    analizador.add_argument("--extraccion", required=True, help="extraccion.json: lo extraído, con su evidencia")
    analizador.add_argument("--fuentes", required=True, help="carpeta con el texto de cada documento")
    analizador.add_argument("--salida", help="ruta del .xlsx")
    analizador.add_argument("--csv", help="ruta de un .csv con la tabla sola, para importarla en otro programa")
    opciones = analizador.parse_args(argumentos)

    try:
        campos, sumas, clave = leer_campos(opciones.campos)
        documentos = leer_extraccion(opciones.extraccion, campos)
    except EntradaInvalida as fallo:
        print("HAY %d PROBLEMA(S) EN LA ENTRADA. Corrígelos y vuelve a ejecutar:" % len(fallo.problemas), file=sys.stderr)
        for linea in fallo.problemas:
            print("  ✗ " + linea, file=sys.stderr)
        return 1
    except OSError as fallo:
        print("No puedo leer la entrada: %s" % fallo, file=sys.stderr)
        return 2

    filas, trazas, resumen = comprobar(campos, sumas, clave, documentos, opciones.fuentes)
    try:
        if opciones.salida:
            escribir_xlsx(opciones.salida, hojas(campos, filas, trazas, resumen))
            resumen["fichero"] = opciones.salida
        if opciones.csv:
            with open(opciones.csv, "w", encoding="utf-8-sig", newline="") as fichero:
                escritor = csv.writer(fichero, delimiter=";")
                escritor.writerow(["documento"] + [c["nombre"] for c in campos])
                for fila in filas:
                    escritor.writerow([fila["documento"]] + ["" if fila[c["nombre"]] is None else fila[c["nombre"]] for c in campos])
            resumen["csv"] = opciones.csv
    except OSError as fallo:
        print("No puedo escribir la salida: %s" % fallo, file=sys.stderr)
        return 2
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

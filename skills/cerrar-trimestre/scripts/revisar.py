#!/usr/bin/env python3
"""Checks the invoices of a quarter before they go to whoever files the taxes.

The quarter costs a small business hours for one reason: the errors are found by the
accountant, days later, one email at a time. A total that does not add up, a tax
number with a wrong letter, a gap in the numbering, the March invoice of a supplier
that is there in January and February. Every one of these can be found by a machine
the same afternoon. This script finds them, adds up the VAT by rate, and says when
each return is due. It does not file anything and it does not decide what is
deductible: it leaves the books ready for the person who does.

Input: one CSV for issued invoices and one for received invoices, same header:
    numero,fecha,nif,nombre,base,tipo_iva,cuota_iva,retencion,total
and, optionally, the columns `serie`, `recargo` and `simplificada`.

    numero        invoice number as printed
    fecha         YYYY-MM-DD, the date of the invoice
    nif           tax number of the other party (customer on issued, supplier on received)
    nombre        name of the other party
    base          taxable base at this VAT rate: 1000.00 (negative on a corrective invoice)
    tipo_iva      VAT rate as a number: 21, 10, 4 or 0
    cuota_iva     VAT amount at this rate
    retencion     income-tax withholding of the whole invoice, as a positive amount, or 0
    total         total of the whole invoice
    serie         (optional) numbering series
    recargo       (optional) equivalence surcharge amount at this rate
    simplificada  (optional) si | no; a simplified invoice (a till receipt)

An invoice with two VAT rates takes two lines with the same `numero`, repeating
`retencion` and `total`.

Usage:
    python3 scripts/revisar.py --trimestre 2026-3 --emitidas emitidas.csv \
        --recibidas recibidas.csv --salida trimestre-2026-3.xlsx

Prints a JSON summary and writes the workbook. Exit code 0 when the review was done
(whatever it found), 1 when a CSV cannot be read as such (each problem with its
line), 2 when a file cannot be read or written.
Standard library only. Reads the two CSVs, writes the workbook, opens no connection.
"""
import argparse
import csv
import datetime
import json
import re
import sys
import unicodedata
from decimal import ROUND_HALF_UP, Decimal

from hoja_xlsx import escribir_xlsx

OBLIGATORIAS = ["numero", "fecha", "nif", "nombre", "base", "tipo_iva", "cuota_iva", "retencion", "total"]
OPCIONALES = ["serie", "recargo", "simplificada"]
IMPORTE = re.compile(r"^-?\d+(\.\d{1,2})?$")
TIPO = re.compile(r"^\d{1,2}(\.\d{1,2})?$")
CENTIMO = Decimal("0.01")
# Two cents: an invoice that rounds line by line can differ by one cent per rate from base x rate.
TOLERANCIA = Decimal("0.02")
ERROR, AVISO = "error", "aviso"

# Ley 37/1992 del IVA, arts. 90 and 91: general, reduced and super-reduced rates. 0 covers exempt and not-subject lines.
TIPOS_HABITUALES = (Decimal("21"), Decimal("10"), Decimal("4"), Decimal("0"))
# Ley 37/1992, art. 161: the equivalence surcharge that goes with each VAT rate.
RECARGO = {Decimal("21"): Decimal("5.2"), Decimal("10"): Decimal("1.4"), Decimal("4"): Decimal("0.5")}
# Real Decreto 1619/2012, art. 4: a simplified invoice is allowed up to 400 euros VAT included,
# and up to 3,000 euros in the activities its second paragraph lists (retail, transport of people, hospitality...).
SIMPLIFICADA_MAX = Decimal("400")
SIMPLIFICADA_MAX_ACTIVIDADES = Decimal("3000")
# The control letter of a DNI or NIE: the number modulo 23 indexes this string.
LETRAS_NIF = "TRWAGMYFPDXBNJZSQVHLCKE"
# The control character of the tax number of an entity, when it is a letter.
LETRAS_ENTIDAD = "JABCDEFGHI"
# Entities whose control character is always a letter, and those where it is always a digit.
ENTIDAD_CON_LETRA = "KPQRSNW"
ENTIDAD_CON_DIGITO = "ABEH"

# Quarterly filing deadlines in the common tax territory: quarter -> (month, day, of the following year?).
# Agencia Tributaria, calendario del contribuyente 2026: modelos 303 and 130 from the 1st to the 20th of April,
# July and October, and until 30 January for the fourth quarter; modelos 111 and 115 until the 20th.
VENCE_IVA = {1: (4, 20, False), 2: (7, 20, False), 3: (10, 20, False), 4: (1, 30, True)}
VENCE_RETENCIONES = {1: (4, 20, False), 2: (7, 20, False), 3: (10, 20, False), 4: (1, 20, True)}


class EntradaInvalida(Exception):
    def __init__(self, problemas):
        super().__init__("\n".join(problemas))
        self.problemas = problemas


def centimos(valor):
    return Decimal(valor).quantize(CENTIMO, rounding=ROUND_HALF_UP)


def clave(texto):
    plano = unicodedata.normalize("NFD", str(texto).lower())
    return " ".join("".join(c for c in plano if unicodedata.category(c) != "Mn").split())


# ---------------------------------------------------------------- tax numbers


def comprobar_nif(nif):
    """Returns (estado, limpio). Estado: valido | control | formato | extranjero | vacio.

    `control` means the shape is right and the control character is not: a typo, almost always.
    """
    limpio = re.sub(r"[\s.\-/]", "", str(nif or "")).upper()
    if not limpio:
        return "vacio", ""
    if limpio.startswith("ES") and len(limpio) == 11:
        limpio = limpio[2:]
    if re.fullmatch(r"\d{8}[A-Z]", limpio):
        return ("valido" if LETRAS_NIF[int(limpio[:8]) % 23] == limpio[8] else "control"), limpio
    if re.fullmatch(r"[XYZ]\d{7}[A-Z]", limpio):
        numero = int("XYZ".index(limpio[0]) * 10 ** 7 + int(limpio[1:8]))
        return ("valido" if LETRAS_NIF[numero % 23] == limpio[8] else "control"), limpio
    if re.fullmatch(r"[ABCDEFGHJKLMNPQRSUVW]\d{7}[0-9A-J]", limpio):
        digitos = [int(d) for d in limpio[1:8]]
        # Digits in odd positions are doubled and their own digits added; the ones in even positions are added as they are.
        suma = sum(digitos[1::2]) + sum(sum(divmod(2 * d, 10)) for d in digitos[0::2])
        control = (10 - suma % 10) % 10
        esperados = set()
        if limpio[0] not in ENTIDAD_CON_DIGITO:
            esperados.add(LETRAS_ENTIDAD[control])
        if limpio[0] not in ENTIDAD_CON_LETRA:
            esperados.add(str(control))
        return ("valido" if limpio[8] in esperados else "control"), limpio
    if re.fullmatch(r"[A-Z]{2}[A-Z0-9]{2,13}", limpio) and limpio[:2] not in ("ES",):
        return "extranjero", limpio
    return "formato", limpio


# ---------------------------------------------------------------- reading


def leer_libro(ruta, libro):
    with open(ruta, encoding="utf-8-sig", newline="") as fichero:
        filas = [fila for fila in csv.reader(fichero) if any(celda.strip() for celda in fila)]
    if not filas:
        raise EntradaInvalida(["%s: el fichero está vacío. Hace falta la cabecera %s." % (libro, ",".join(OBLIGATORIAS))])
    cabecera = [celda.strip().lower() for celda in filas[0]]
    faltan = [c for c in OBLIGATORIAS if c not in cabecera]
    sobran = [c for c in cabecera if c not in OBLIGATORIAS + OPCIONALES]
    if faltan or sobran or len(set(cabecera)) != len(cabecera):
        raise EntradaInvalida(["%s: la primera línea tiene que llevar estas columnas: %s (y, si hacen falta, %s). Recibido: %s" % (libro, ",".join(OBLIGATORIAS), ", ".join(OPCIONALES), ",".join(filas[0]))])

    problemas, lineas = [], []
    for numero, fila in enumerate(filas[1:], 2):
        donde = "%s, línea %d" % (libro, numero)
        if len(fila) != len(cabecera):
            problemas.append("%s: tiene %d columnas y la cabecera tiene %d. Si un nombre lleva una coma, ponlo entre comillas." % (donde, len(fila), len(cabecera)))
            continue
        dato = {columna: celda.strip() for columna, celda in zip(cabecera, fila)}
        antes = len(problemas)
        if not dato["numero"]:
            problemas.append("%s: falta el número de factura." % donde)
        try:
            fecha = datetime.date.fromisoformat(dato["fecha"])
        except ValueError:
            fecha = None
            problemas.append("%s: la fecha %r tiene que ser AAAA-MM-DD." % (donde, dato["fecha"]))
        for columna in ("base", "cuota_iva", "total"):
            if not IMPORTE.match(dato[columna]):
                problemas.append("%s: `%s` es %r y tiene que ser un número con punto decimal, sin símbolo (1000.00)." % (donde, columna, dato[columna]))
        for columna in ("retencion", "recargo"):
            if dato.get(columna, "") and not IMPORTE.match(dato[columna]):
                problemas.append("%s: `%s` es %r y tiene que ser un importe, o ir vacío." % (donde, columna, dato[columna]))
        if not TIPO.match(dato["tipo_iva"]):
            problemas.append("%s: `tipo_iva` es %r y tiene que ser el tipo como número: 21, 10, 4 o 0." % (donde, dato["tipo_iva"]))
        simplificada = dato.get("simplificada", "").lower()
        if simplificada not in ("", "si", "sí", "no"):
            problemas.append("%s: `simplificada` es %r y tiene que ser si o no." % (donde, dato["simplificada"]))
        if len(problemas) == antes:
            lineas.append(
                {
                    "libro": libro,
                    "linea": numero,
                    "numero": dato["numero"],
                    "serie": dato.get("serie", ""),
                    "fecha": fecha,
                    "nif": dato["nif"],
                    "nombre": dato["nombre"],
                    "base": Decimal(dato["base"]),
                    "tipo_iva": Decimal(dato["tipo_iva"]),
                    "cuota_iva": Decimal(dato["cuota_iva"]),
                    "retencion": Decimal(dato["retencion"] or "0"),
                    "recargo": Decimal(dato.get("recargo") or "0"),
                    "total": Decimal(dato["total"]),
                    "simplificada": simplificada in ("si", "sí"),
                }
            )
    if problemas:
        raise EntradaInvalida(problemas)
    return lineas


def agrupar(lineas):
    """One entry per invoice: the lines of a multi-rate invoice share serie, numero and counterparty.

    A second line at a rate the invoice already has is not a second rate: it is the same
    invoice entered twice, and it is kept apart so the duplicate check can say so.
    """
    facturas = {}
    for linea in lineas:
        identidad = (linea["serie"], linea["numero"].upper(), comprobar_nif(linea["nif"])[1] or clave(linea["nombre"]))
        copia = 0
        while any(otra["tipo_iva"] == linea["tipo_iva"] for otra in facturas.get(identidad + (copia,), [])):
            copia += 1
        facturas.setdefault(identidad + (copia,), []).append(linea)
    return list(facturas.values())


def tipo_texto(tipo):
    """Decimal('21') -> '21', Decimal('5.20') -> '5.2'. (normalize() alone turns 10 into 1E+1.)"""
    return ("%f" % tipo).rstrip("0").rstrip(".")


# ---------------------------------------------------------------- checks


def trimestre_de(texto):
    encontrado = re.fullmatch(r"(\d{4})-([1-4])", texto)
    if not encontrado:
        raise ValueError("%r no es un trimestre: AAAA-N, por ejemplo 2026-3." % texto)
    anio, numero = int(encontrado.group(1)), int(encontrado.group(2))
    desde = datetime.date(anio, 3 * numero - 2, 1)
    hasta = datetime.date(anio + (numero == 4), 3 * numero % 12 + 1, 1) - datetime.timedelta(days=1)
    return anio, numero, desde, hasta


def revisar_factura(lineas, libro, desde, hasta):
    """The findings of one invoice: [(gravedad, que, arreglo)]."""
    hallazgos = []
    primera = lineas[0]
    emitida = libro == "emitidas"
    otro = "destinatario" if emitida else "emisor"

    if not desde <= primera["fecha"] <= hasta:
        if primera["fecha"] > hasta:
            hallazgos.append((AVISO, "Tiene fecha %s, posterior al trimestre." % primera["fecha"].strftime("%d/%m/%Y"), "Va en el trimestre siguiente: sácala de este."))
        elif emitida:
            hallazgos.append((ERROR, "Tiene fecha %s, anterior al trimestre." % primera["fecha"].strftime("%d/%m/%Y"), "Una factura emitida se declara en su trimestre. Si quedó sin declarar, díselo a quien presenta los impuestos."))
        else:
            hallazgos.append((AVISO, "Tiene fecha %s, de un trimestre anterior." % primera["fecha"].strftime("%d/%m/%Y"), "Avisa a quien presenta los impuestos de que llega con retraso: es quien decide en qué declaración entra."))

    estado, _ = comprobar_nif(primera["nif"])
    if estado == "vacio":
        if emitida and primera["simplificada"]:
            pass  # a simplified invoice does not need the customer's tax number (art. 7.1)
        else:
            hallazgos.append((ERROR, "Falta el NIF del %s." % otro, "Es un dato obligatorio de la factura (Real Decreto 1619/2012, art. 6.1.d). Pídelo y corrige la factura."))
    elif estado == "control":
        hallazgos.append((ERROR, "El NIF %s no es correcto: la letra o el dígito de control no corresponde al número." % primera["nif"], "Casi siempre es una errata. Compáralo con el de otra factura del mismo %s." % otro))
    elif estado == "formato":
        hallazgos.append((AVISO, "El NIF %s no tiene la forma de un NIF español." % primera["nif"], "Compruébalo. Si es de fuera de España, escríbelo con el código del país delante."))
    elif estado == "extranjero":
        hallazgos.append((AVISO, "El %s es de fuera de España (%s)." % (otro, primera["nif"]), "Las operaciones con el extranjero tienen sus propias reglas de IVA: sepáralas para quien presenta los impuestos."))

    if not primera["nombre"]:
        hallazgos.append((ERROR, "Falta el nombre del %s." % otro, "Es un dato obligatorio de la factura (art. 6.1.c)."))

    for linea in lineas:
        esperada = centimos(linea["base"] * linea["tipo_iva"] / Decimal(100))
        if abs(esperada - linea["cuota_iva"]) > TOLERANCIA:
            hallazgos.append(
                (ERROR, "La cuota de IVA (%s) no corresponde a la base (%s) al %s %%: saldrían %s." % (linea["cuota_iva"], linea["base"], tipo_texto(linea["tipo_iva"]), esperada), "Revisa la base, el tipo o la cuota en la factura original.")
            )
        if linea["recargo"]:
            tipo_recargo = RECARGO.get(linea["tipo_iva"])
            if tipo_recargo is None:
                hallazgos.append((AVISO, "Lleva recargo de equivalencia con un IVA del %s %%, que no tiene recargo previsto." % tipo_texto(linea["tipo_iva"]), "Revisa la factura original."))
            elif abs(centimos(linea["base"] * tipo_recargo / Decimal(100)) - linea["recargo"]) > TOLERANCIA:
                hallazgos.append((ERROR, "El recargo de equivalencia (%s) no corresponde a la base (%s) al %s %%: saldrían %s." % (linea["recargo"], linea["base"], tipo_texto(tipo_recargo), centimos(linea["base"] * tipo_recargo / Decimal(100))), "Con IVA del %s %%, el recargo es el %s %% (Ley del IVA, art. 161)." % (tipo_texto(linea["tipo_iva"]), tipo_texto(tipo_recargo))))
        if linea["tipo_iva"] not in TIPOS_HABITUALES:
            hallazgos.append((AVISO, "El tipo de IVA es el %s %%, que no es ninguno de los habituales (21, 10, 4)." % tipo_texto(linea["tipo_iva"]), "Confirma que es el que corresponde."))

    retenciones = {linea["retencion"] for linea in lineas}
    totales = {linea["total"] for linea in lineas}
    if len(retenciones) > 1 or len(totales) > 1:
        hallazgos.append((ERROR, "Las líneas de esta factura no repiten el mismo total o la misma retención.", "En una factura con varios tipos de IVA, `total` y `retencion` son los de la factura entera, iguales en todas sus líneas."))
    else:
        suma = sum((l["base"] + l["cuota_iva"] + l["recargo"] for l in lineas), Decimal("0")) - primera["retencion"]
        if abs(suma - primera["total"]) > TOLERANCIA:
            hallazgos.append((ERROR, "El total (%s) no es la suma de bases, IVA y recargo menos la retención: saldrían %s." % (primera["total"], centimos(suma)), "Revisa la factura original: falta una línea, sobra una, o el total está mal copiado."))

    if emitida and primera["simplificada"]:
        if abs(primera["total"]) > SIMPLIFICADA_MAX_ACTIVIDADES:
            hallazgos.append((ERROR, "Es una factura simplificada de %s €: pasa de los %s € que admite la norma en cualquier caso." % (primera["total"], SIMPLIFICADA_MAX_ACTIVIDADES), "Tiene que ser una factura completa (Real Decreto 1619/2012, art. 4)."))
        elif abs(primera["total"]) > SIMPLIFICADA_MAX:
            hallazgos.append((AVISO, "Es una factura simplificada de %s €: por encima de %s € solo vale en las actividades que lista la norma (comercio al por menor, hostelería, transporte de personas y otras)." % (primera["total"], SIMPLIFICADA_MAX), "Confirma que tu actividad está entre ellas (art. 4.2). Si no, tiene que ser una factura completa."))
    return hallazgos


def numeracion(facturas):
    """Gaps, repeats and out-of-order dates in the numbering of issued invoices, per series."""
    hallazgos, series = [], {}
    for lineas in facturas:
        primera = lineas[0]
        encontrado = re.fullmatch(r"(.*?)(\d+)", primera["numero"])
        if not encontrado:
            hallazgos.append((primera, AVISO, "El número %r no acaba en cifras: no se puede comprobar que la numeración sea correlativa." % primera["numero"], "Compruébalo a mano."))
            continue
        series.setdefault((primera["serie"], encontrado.group(1)), []).append((int(encontrado.group(2)), primera))
    for (serie, prefijo), numeros in series.items():
        numeros.sort(key=lambda par: par[0])
        vistos = {}
        for numero, primera in numeros:
            if numero in vistos:
                hallazgos.append((primera, ERROR, "El número %s está repetido: lo llevan dos facturas a destinatarios distintos." % primera["numero"], "Dos facturas no pueden llevar el mismo número en la misma serie (art. 6.1.a). Una de las dos está mal numerada."))
            vistos[numero] = primera
        ordenados = sorted(vistos)
        for anterior, siguiente in zip(ordenados, ordenados[1:]):
            if siguiente - anterior > 1:
                faltan = siguiente - anterior - 1
                ancho = len(re.fullmatch(r"(.*?)(\d+)", vistos[siguiente]["numero"]).group(2))
                ejemplo = "%s%s" % (prefijo, str(anterior + 1).zfill(ancho))
                hallazgos.append(
                    (vistos[siguiente], AVISO, "Entre la %s y la %s %s: %s." % (vistos[anterior]["numero"], vistos[siguiente]["numero"], "falta una factura" if faltan == 1 else "faltan %d facturas" % faltan, ejemplo if faltan == 1 else "de la %s en adelante" % ejemplo), "La numeración de cada serie tiene que ser correlativa (art. 6.1.a). Si esa factura existe, falta en el listado; si se anuló, tiene que constar.")
                )
            if vistos[siguiente]["fecha"] < vistos[anterior]["fecha"]:
                hallazgos.append((vistos[siguiente], AVISO, "La %s tiene fecha anterior a la %s, que va antes en la numeración." % (vistos[siguiente]["numero"], vistos[anterior]["numero"]), "Los números tienen que seguir el orden de las fechas. Revisa cuál de las dos fechas está mal."))
    return hallazgos


def proveedores_con_hueco(facturas, desde, hasta):
    """A supplier invoiced in two months of the quarter and not in the third: the missing invoice, usually."""
    meses = sorted({(desde.year, desde.month + i) for i in range(3)})
    por_proveedor = {}
    for lineas in facturas:
        primera = lineas[0]
        if desde <= primera["fecha"] <= hasta:
            identidad = comprobar_nif(primera["nif"])[1] or clave(primera["nombre"])
            por_proveedor.setdefault(identidad, {"nombre": primera["nombre"], "meses": set()})["meses"].add((primera["fecha"].year, primera["fecha"].month))
    nombres = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    avisos = []
    for proveedor in por_proveedor.values():
        if len(proveedor["meses"]) == 2:
            falta = next(mes for mes in meses if mes not in proveedor["meses"])
            if falta == meses[0]:
                continue  # billed from the second month on: a new supplier, most likely
            avisos.append("%s tiene factura dos meses del trimestre y no en %s. ¿Falta esa factura?" % (proveedor["nombre"], nombres[falta[1] - 1]))
    return sorted(avisos)


def totales(facturas, desde, hasta):
    """Base, VAT and surcharge by rate, for the invoices dated in the quarter."""
    por_tipo, retenciones = {}, Decimal("0")
    for lineas in facturas:
        if not desde <= lineas[0]["fecha"] <= hasta:
            continue
        retenciones += lineas[0]["retencion"]
        for linea in lineas:
            fila = por_tipo.setdefault(linea["tipo_iva"], {"base": Decimal("0"), "cuota": Decimal("0"), "recargo": Decimal("0")})
            fila["base"] += linea["base"]
            fila["cuota"] += linea["cuota_iva"]
            fila["recargo"] += linea["recargo"]
    return por_tipo, retenciones


def dia_habil(dia):
    """Saturday or Sunday moves to Monday. Local holidays are not known here: the note says so."""
    while dia.weekday() >= 5:
        dia += datetime.timedelta(days=1)
    return dia


def calendario(anio, numero):
    def fecha(tabla):
        mes, dia, siguiente = tabla[numero]
        return dia_habil(datetime.date(anio + siguiente, mes, dia))

    return [
        {"que": "IVA del trimestre (modelo 303)", "hasta": fecha(VENCE_IVA).isoformat()},
        {"que": "Pago fraccionado del IRPF de autónomos (modelo 130)", "hasta": fecha(VENCE_IVA).isoformat()},
        {"que": "Retenciones de nóminas y profesionales (modelo 111)", "hasta": fecha(VENCE_RETENCIONES).isoformat()},
        {"que": "Retenciones de alquileres (modelo 115)", "hasta": fecha(VENCE_RETENCIONES).isoformat()},
    ]


def revisar(trimestre, emitidas, recibidas, territorio_comun=True):
    anio, numero, desde, hasta = trimestre_de(trimestre)
    hallazgos = []

    def apuntar(lineas, gravedad, que, arreglo):
        primera = lineas[0] if isinstance(lineas, list) else lineas
        hallazgos.append({"libro": primera["libro"], "linea": primera["linea"], "factura": primera["numero"], "con": primera["nombre"], "gravedad": gravedad, "que": que, "arreglo": arreglo})

    facturas_emitidas, facturas_recibidas = agrupar(emitidas), agrupar(recibidas)

    # First, the same invoice entered twice: its VAT would be declared or deducted twice.
    # A copy is reported once and left out of every other check and of the totals.
    def sin_copias(facturas, consecuencia):
        vistas, unicas = {}, []
        for lineas in facturas:
            primera = lineas[0]
            identidad = (primera["serie"], comprobar_nif(primera["nif"])[1] or clave(primera["nombre"]), primera["numero"].upper())
            if identidad in vistas:
                apuntar(lineas, ERROR, "Esta factura ya está apuntada en la línea %d." % vistas[identidad], "Quita una de las dos: apuntada dos veces, %s." % consecuencia)
            else:
                vistas[identidad] = primera["linea"]
                unicas.append(lineas)
        return unicas

    facturas_emitidas = sin_copias(facturas_emitidas, "su IVA se declararía dos veces")
    facturas_recibidas = sin_copias(facturas_recibidas, "su IVA se deduciría dos veces")

    for libro, facturas in (("emitidas", facturas_emitidas), ("recibidas", facturas_recibidas)):
        for lineas in facturas:
            for gravedad, que, arreglo in revisar_factura(lineas, libro, desde, hasta):
                apuntar(lineas, gravedad, que, arreglo)
    for primera, gravedad, que, arreglo in numeracion(facturas_emitidas):
        apuntar(primera, gravedad, que, arreglo)

    devengado, retenido = totales(facturas_emitidas, desde, hasta)
    soportado, practicado = totales(facturas_recibidas, desde, hasta)

    def tabla(por_tipo):
        return [{"tipo": tipo_texto(tipo), "base": str(centimos(fila["base"])), "cuota": str(centimos(fila["cuota"])), "recargo": str(centimos(fila["recargo"]))} for tipo, fila in sorted(por_tipo.items(), reverse=True)]

    iva_devengado = sum((f["cuota"] + f["recargo"] for f in devengado.values()), Decimal("0"))
    iva_soportado = sum((f["cuota"] for f in soportado.values()), Decimal("0"))
    hallazgos.sort(key=lambda h: (h["gravedad"] != ERROR, h["libro"], h["linea"]))
    return {
        "trimestre": trimestre,
        "desde": desde.isoformat(),
        "hasta": hasta.isoformat(),
        "facturas_emitidas": len(facturas_emitidas),
        "facturas_recibidas": len(facturas_recibidas),
        "errores": sum(1 for h in hallazgos if h["gravedad"] == ERROR),
        "avisos": sum(1 for h in hallazgos if h["gravedad"] == AVISO),
        "hallazgos": hallazgos,
        "posibles_facturas_que_faltan": proveedores_con_hueco(facturas_recibidas, desde, hasta),
        "iva_de_las_ventas": {"por_tipo": tabla(devengado), "total": str(centimos(iva_devengado))},
        "iva_de_las_compras": {"por_tipo": tabla(soportado), "total": str(centimos(iva_soportado))},
        "diferencia": str(centimos(iva_devengado - iva_soportado)),
        "retenciones_que_te_han_practicado": str(centimos(retenido)),
        "retenciones_que_has_practicado": str(centimos(practicado)),
        "plazos": calendario(anio, numero) if territorio_comun else [],
        "que_es_la_diferencia": "IVA de las ventas menos IVA de las compras del trimestre, tal como están apuntadas. No es la liquidación: quien presenta el modelo decide qué es deducible y aplica lo que aquí no se mira (prorrata, bienes de inversión, regímenes especiales, cuotas a compensar de otros trimestres).",
    }


# ---------------------------------------------------------------- output


def hojas(informe, emitidas, recibidas):
    resumen = [["Qué", "Dato"]]
    resumen.append(["Trimestre", "%s (del %s al %s)" % (informe["trimestre"], datetime.date.fromisoformat(informe["desde"]).strftime("%d/%m/%Y"), datetime.date.fromisoformat(informe["hasta"]).strftime("%d/%m/%Y"))])
    resumen.append(["Facturas emitidas y recibidas", "%d y %d" % (informe["facturas_emitidas"], informe["facturas_recibidas"])])
    resumen.append(["Errores que corregir antes de entregar", informe["errores"]])
    resumen.append(["Avisos que confirmar", informe["avisos"]])
    for aviso in informe["posibles_facturas_que_faltan"]:
        resumen.append(["Posible factura que falta", aviso])
    for fila in informe["plazos"]:
        resumen.append(["Plazo: " + fila["que"], "hasta el %s (si es festivo, el siguiente día hábil)" % datetime.date.fromisoformat(fila["hasta"]).strftime("%d/%m/%Y")])
    resumen.append(["Qué es esto", "Una revisión de lo apuntado, para entregarlo sin errores a quien presenta los impuestos. No es una declaración ni la sustituye."])

    iva = [["Libro", "Tipo de IVA", "Base", "Cuota de IVA", "Recargo de equivalencia"]]
    for nombre, bloque in (("Ventas (emitidas)", informe["iva_de_las_ventas"]), ("Compras (recibidas)", informe["iva_de_las_compras"])):
        for fila in bloque["por_tipo"]:
            iva.append([nombre, Decimal(fila["tipo"]) / Decimal(100), Decimal(fila["base"]), Decimal(fila["cuota"]), Decimal(fila["recargo"])])
    negritas = [len(iva)]
    iva.append(["IVA de las ventas menos IVA de las compras", None, None, Decimal(informe["diferencia"]), None])
    iva.append(["No es la liquidación", None, None, None, None])

    hallazgos = [["Libro", "Factura", "Con", "Gravedad", "Qué pasa", "Qué hacer", "Línea del listado"]]
    for h in informe["hallazgos"]:
        hallazgos.append([h["libro"], h["factura"], h["con"], h["gravedad"].upper(), h["que"], h["arreglo"], h["linea"]])

    def libro(lineas):
        filas = [["Serie", "Número", "Fecha", "NIF", "Nombre", "Base", "Tipo de IVA", "Cuota de IVA", "Recargo", "Retención", "Total"]]
        for l in lineas:
            filas.append([l["serie"], l["numero"], l["fecha"], l["nif"], l["nombre"], l["base"], l["tipo_iva"] / Decimal(100), l["cuota_iva"], l["recargo"], l["retencion"], l["total"]])
        return filas

    formato_libro = {5: "euros", 6: "porcentaje", 7: "euros", 8: "euros", 9: "euros", 10: "euros"}
    return [
        {"nombre": "Resumen", "filas": resumen, "formatos": {0: "texto", 1: "texto"}, "anchos": [44, 90]},
        {"nombre": "Qué corregir", "filas": hallazgos, "formatos": {4: "texto", 5: "texto", 6: "entero"}, "anchos": [12, 14, 26, 10, 60, 60, 10]},
        {"nombre": "IVA por tipo", "filas": iva, "formatos": {1: "porcentaje", 2: "euros", 3: "euros", 4: "euros"}, "negrita": negritas, "anchos": [44, 12, 14, 14, 16]},
        {"nombre": "Emitidas", "filas": libro(emitidas), "formatos": formato_libro},
        {"nombre": "Recibidas", "filas": libro(recibidas), "formatos": formato_libro},
    ]


def main(argumentos=None):
    analizador = argparse.ArgumentParser(description="Revisa las facturas de un trimestre antes de entregarlas a quien presenta los impuestos.")
    analizador.add_argument("--trimestre", required=True, help="AAAA-N, por ejemplo 2026-3")
    analizador.add_argument("--emitidas", help="CSV de facturas emitidas")
    analizador.add_argument("--recibidas", help="CSV de facturas recibidas")
    analizador.add_argument("--sin-calendario-fiscal", action="store_true", help="no dar los plazos: úsalo si `territorio` no es `comun`")
    analizador.add_argument("--salida", help="ruta del .xlsx; sin ella solo se imprime el resumen")
    opciones = analizador.parse_args(argumentos)
    if not opciones.emitidas and not opciones.recibidas:
        analizador.error("hace falta --emitidas, --recibidas o los dos")

    try:
        trimestre_de(opciones.trimestre)
        emitidas = leer_libro(opciones.emitidas, "emitidas") if opciones.emitidas else []
        recibidas = leer_libro(opciones.recibidas, "recibidas") if opciones.recibidas else []
    except EntradaInvalida as fallo:
        print("HAY %d PROBLEMA(S) EN LOS LISTADOS. Corrígelos y vuelve a ejecutar:" % len(fallo.problemas), file=sys.stderr)
        for linea in fallo.problemas:
            print("  ✗ " + linea, file=sys.stderr)
        return 1
    except ValueError as fallo:
        print(str(fallo), file=sys.stderr)
        return 1
    except (OSError, UnicodeDecodeError) as fallo:
        print("No puedo leer los listados: %s" % fallo, file=sys.stderr)
        return 2

    informe = revisar(opciones.trimestre, emitidas, recibidas, territorio_comun=not opciones.sin_calendario_fiscal)
    if opciones.salida:
        try:
            escribir_xlsx(opciones.salida, hojas(informe, emitidas, recibidas))
        except OSError as fallo:
            print("No puedo escribir %s: %s" % (opciones.salida, fallo), file=sys.stderr)
            return 2
        informe["fichero"] = opciones.salida
    print(json.dumps(informe, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

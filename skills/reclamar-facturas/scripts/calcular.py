#!/usr/bin/env python3
"""Works out what a business is owed for late invoices: the principal, the late-payment
interest the law grants, and the fixed compensation for recovery costs.

Spanish law (Ley 3/2004) gives a business that is paid late by another business two
things on top of the invoice: interest at a legal rate that changes every semester,
and 40 euros per invoice. Most suppliers never claim either, because nobody wants to
do this arithmetic: days late counted from the legal due date, split by semester,
each stretch at its own rate. A language model gets it nearly right, which in a
letter that quotes an amount is worse than not quoting one. So the model prepares the
list of invoices and this script does the sums, shows every step, and refuses to
guess a rate that is not in its table.

Input: a CSV with the header
    cliente,numero,fecha_factura,vencimiento,importe,tipo_cliente,avisos
and, optionally, the columns `entrega` and `base`.

    cliente        who owes the money
    numero         invoice number
    fecha_factura  YYYY-MM-DD
    vencimiento    YYYY-MM-DD, or empty when no due date was agreed
    importe        what is still unpaid of that invoice, VAT included: 4840.00
    tipo_cliente   empresa | particular | administracion
    avisos         reminders already sent for this invoice: 0, 1, 2...
    entrega        (optional) YYYY-MM-DD the goods or services were received, when it is not the invoice date
    base           (optional) the unpaid amount without VAT, to show the interest on that base too

Usage:
    python3 scripts/calcular.py facturas.csv --hasta 2026-10-13 --plazo-dias 30 \
        --salida reclamacion.xlsx

Prints a JSON summary and writes the workbook. Exit code 0 when the calculation was
done, 1 when the CSV or a missing rate has to be fixed first (each problem with its
line), 2 when a file cannot be read or written.
Standard library only. Reads the CSV and the rates table, writes the workbook, opens no connection.
"""
import argparse
import csv
import datetime
import json
import pathlib
import re
import sys
import unicodedata
from decimal import ROUND_HALF_UP, Decimal

from hoja_xlsx import escribir_xlsx

OBLIGATORIAS = ["cliente", "numero", "fecha_factura", "vencimiento", "importe", "tipo_cliente", "avisos"]
OPCIONALES = ["entrega", "base"]
TIPOS_DE_CLIENTE = ("empresa", "particular", "administracion")
IMPORTE = re.compile(r"^\d+(\.\d{1,2})?$")
CENTIMO = Decimal("0.01")

# Ley 3/2004, art. 4.1: with no agreed term, thirty calendar days after the goods or services are received.
PLAZO_SIN_PACTO = 30
# Ley 3/2004, art. 4.3: no agreement can set a term above sixty calendar days.
PLAZO_MAXIMO = 60
# Ley 3/2004, art. 8.1: a fixed amount added to the principal once the debtor is late.
COMPENSACION = Decimal("40.00")
# Simple interest on a 365-day year: the law fixes the rate and its semester, not the day count. This is the usual practice.
DIAS_DEL_ANIO = 365
# Código Civil, art. 1964.2 (general, five years) and art. 1967 (three years for some professional and trade debts).
PRESCRIPCION_GENERAL_ANIOS = 5
PRESCRIPCION_CORTA_ANIOS = 3
# How the claim escalates. The third step is the one that has to work as a documented attempt to negotiate
# before a court claim (Ley Orgánica 1/2025, art. 5 and 10), so it is reached by reminders sent or by time alone.
DIAS_PARA_RECLAMAR_CON_CIFRAS = 30
DIAS_PARA_REQUERIMIENTO = 60
FASES = {
    1: "recordatorio",
    2: "reclamación con intereses",
    3: "requerimiento formal con propuesta de acuerdo",
}

TIPOS_POR_DEFECTO = pathlib.Path(__file__).resolve().parent.parent / "assets" / "tipos-demora.json"


class EntradaInvalida(Exception):
    def __init__(self, problemas):
        super().__init__("\n".join(problemas))
        self.problemas = problemas


def centimos(valor):
    return Decimal(valor).quantize(CENTIMO, rounding=ROUND_HALF_UP)


def euros(importe):
    """1234.5 -> '1.234,50 €', the way an amount is written in Spain."""
    texto = "{:,.2f}".format(abs(Decimal(importe)))
    texto = texto.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    return ("-" if Decimal(importe) < 0 else "") + texto + " €"


def dia_mes(dia):
    return dia.strftime("%d/%m/%Y")


def clave(texto):
    """Groups 'Hotel Mirador', 'hotel mirador ' and 'HOTEL MIRADOR' as one customer."""
    plano = unicodedata.normalize("NFD", texto.lower())
    return " ".join("".join(c for c in plano if unicodedata.category(c) != "Mn").split())


def semestre_de(dia):
    return "%d-%d" % (dia.year, 1 if dia.month <= 6 else 2)


def limites_del_semestre(semestre):
    anio, mitad = (int(parte) for parte in semestre.split("-"))
    if mitad == 1:
        return datetime.date(anio, 1, 1), datetime.date(anio, 6, 30)
    return datetime.date(anio, 7, 1), datetime.date(anio, 12, 31)


def leer_tipos(ruta, aportados=()):
    """{semester: {"tipo": Decimal, "boe": str}} from the table, plus any rate given on the command line."""
    with open(ruta, encoding="utf-8") as fichero:
        tabla = json.load(fichero)
    tipos = {fila["semestre"]: {"tipo": Decimal(fila["tipo"]), "boe": fila["boe"]} for fila in tabla["tipos"]}
    for semestre, tipo in aportados:
        tipos[semestre] = {"tipo": tipo, "boe": "aportado al ejecutar, sin referencia en la tabla"}
    return tipos, tabla.get("comprobado", "")


def leer_facturas(ruta):
    with open(ruta, encoding="utf-8-sig", newline="") as fichero:
        filas = [fila for fila in csv.reader(fichero) if any(celda.strip() for celda in fila)]
    if not filas:
        raise EntradaInvalida(["El fichero está vacío. Hace falta la cabecera %s y al menos una factura." % ",".join(OBLIGATORIAS)])
    cabecera = [celda.strip().lower() for celda in filas[0]]
    faltan = [columna for columna in OBLIGATORIAS if columna not in cabecera]
    sobran = [columna for columna in cabecera if columna not in OBLIGATORIAS + OPCIONALES]
    if faltan or sobran or len(set(cabecera)) != len(cabecera):
        raise EntradaInvalida(
            ["La primera línea tiene que llevar estas columnas: %s (y, si hacen falta, %s). Recibido: %s" % (",".join(OBLIGATORIAS), ", ".join(OPCIONALES), ",".join(filas[0]))]
        )

    def fecha(valor, numero, nombre, problemas, obligatoria=True):
        if not valor:
            if obligatoria:
                problemas.append("línea %d: falta `%s`." % (numero, nombre))
            return None
        try:
            return datetime.date.fromisoformat(valor)
        except ValueError:
            problemas.append("línea %d: `%s` es %r y tiene que ser AAAA-MM-DD." % (numero, nombre, valor))
            return None

    problemas, facturas, vistas = [], [], {}
    for numero, fila in enumerate(filas[1:], 2):
        if len(fila) != len(cabecera):
            problemas.append("línea %d: tiene %d columnas y la cabecera tiene %d. Si un nombre lleva una coma, ponlo entre comillas." % (numero, len(fila), len(cabecera)))
            continue
        dato = {columna: celda.strip() for columna, celda in zip(cabecera, fila)}
        antes = len(problemas)
        if not dato["cliente"]:
            problemas.append("línea %d: falta el cliente." % numero)
        if not dato["numero"]:
            problemas.append("línea %d: falta el número de factura." % numero)
        emitida = fecha(dato["fecha_factura"], numero, "fecha_factura", problemas)
        vence = fecha(dato["vencimiento"], numero, "vencimiento", problemas, obligatoria=False)
        entrega = fecha(dato.get("entrega", ""), numero, "entrega", problemas, obligatoria=False)
        if not IMPORTE.match(dato["importe"]) or Decimal(dato["importe"]) == 0:
            problemas.append("línea %d: el importe %r tiene que ser lo que queda por cobrar, mayor que cero, con punto decimal y sin símbolo (4840.00)." % (numero, dato["importe"]))
        base = dato.get("base", "")
        if base and not IMPORTE.match(base):
            problemas.append("línea %d: la base %r tiene que ser un número con punto decimal, o ir vacía." % (numero, base))
        elif base and IMPORTE.match(dato["importe"]) and Decimal(base) > Decimal(dato["importe"]):
            problemas.append("línea %d: la base (%s) es mayor que el importe con IVA (%s). ¿Están cambiadas?" % (numero, base, dato["importe"]))
        if dato["tipo_cliente"].lower() not in TIPOS_DE_CLIENTE:
            problemas.append("línea %d: `tipo_cliente` es %r y tiene que ser %s." % (numero, dato["tipo_cliente"], ", ".join(TIPOS_DE_CLIENTE)))
        if not dato["avisos"].isdigit():
            problemas.append("línea %d: `avisos` es %r y tiene que ser cuántos avisos se han enviado ya: 0, 1, 2…" % (numero, dato["avisos"]))
        if emitida and vence and vence < emitida:
            problemas.append("línea %d: el vencimiento (%s) es anterior a la factura (%s)." % (numero, vence, emitida))
        repetida = (clave(dato["cliente"]), dato["numero"].lower())
        if repetida in vistas:
            problemas.append("línea %d: la factura %s de %s ya está en la línea %d. Una factura, una línea." % (numero, dato["numero"], dato["cliente"], vistas[repetida]))
        vistas.setdefault(repetida, numero)
        if len(problemas) == antes:
            facturas.append(
                {
                    "linea": numero,
                    "cliente": dato["cliente"],
                    "numero": dato["numero"],
                    "fecha_factura": emitida,
                    "vencimiento": vence,
                    "entrega": entrega or emitida,
                    "importe": Decimal(dato["importe"]),
                    "base": Decimal(base) if base else None,
                    "tipo_cliente": dato["tipo_cliente"].lower(),
                    "avisos": int(dato["avisos"]),
                }
            )
    if problemas:
        raise EntradaInvalida(problemas)
    if not facturas:
        raise EntradaInvalida(["No hay ninguna factura debajo de la cabecera."])
    return facturas


def vencimiento_legal(factura, plazo_pactado):
    """The day from which the debtor is late, and a note when the law moves it."""
    tope = factura["entrega"] + datetime.timedelta(days=PLAZO_MAXIMO)
    if factura["vencimiento"]:
        if factura["vencimiento"] > tope:
            return tope, "El vencimiento pactado (%s) pasa de los %d días que admite la ley: el retraso se cuenta desde el %s (art. 4.3)." % (dia_mes(factura["vencimiento"]), PLAZO_MAXIMO, dia_mes(tope))
        return factura["vencimiento"], ""
    if plazo_pactado:
        dias = min(plazo_pactado, PLAZO_MAXIMO)
        nota = "Sin vencimiento en la factura: se usa el plazo habitual de %d días." % dias
        if plazo_pactado > PLAZO_MAXIMO:
            nota = "Sin vencimiento en la factura y plazo habitual de %d días, que pasa del máximo legal: se usan %d (art. 4.3)." % (plazo_pactado, PLAZO_MAXIMO)
        return factura["entrega"] + datetime.timedelta(days=dias), nota
    return factura["entrega"] + datetime.timedelta(days=PLAZO_SIN_PACTO), "Sin plazo pactado: la ley da %d días desde la entrega (art. 4.1)." % PLAZO_SIN_PACTO


def tramos_de_interes(desde, hasta, principal, tipos):
    """Interest from the day after `desde` up to `hasta`, one stretch per semester.

    Returns (stretches, semesters with no published rate in the table).
    """
    tramos, sin_tipo = [], []
    dia = desde + datetime.timedelta(days=1)
    while dia <= hasta:
        semestre = semestre_de(dia)
        _, fin = limites_del_semestre(semestre)
        ultimo = min(fin, hasta)
        dias = (ultimo - dia).days + 1
        if semestre in tipos:
            tipo = tipos[semestre]["tipo"]
            tramos.append(
                {
                    "semestre": semestre,
                    "desde": dia,
                    "hasta": ultimo,
                    "dias": dias,
                    "tipo": tipo,
                    "boe": tipos[semestre]["boe"],
                    # Not rounded here: the cents are settled once, on the invoice total.
                    "interes": principal * tipo / Decimal(100) * Decimal(dias) / Decimal(DIAS_DEL_ANIO),
                }
            )
        else:
            sin_tipo.append(semestre)
        dia = ultimo + datetime.timedelta(days=1)
    return tramos, sin_tipo


def fase_de(dias, avisos):
    if avisos >= 2 or dias > DIAS_PARA_REQUERIMIENTO:
        return 3
    if avisos == 1 or dias > DIAS_PARA_RECLAMAR_CON_CIFRAS:
        return 2
    return 1


def anios_despues(dia, anios):
    try:
        return dia.replace(year=dia.year + anios)
    except ValueError:  # 29 February
        return dia.replace(year=dia.year + anios, day=28)


def calcular(facturas, hasta, tipos, plazo_pactado=None):
    """Returns (rows, missing semesters). Raises nothing: a missing rate is reported, not guessed."""
    filas, faltan = [], set()
    for factura in facturas:
        vence, nota_plazo = vencimiento_legal(factura, plazo_pactado)
        dias = (hasta - vence).days
        fila = dict(factura, vencimiento_legal=vence, dias_de_retraso=max(dias, 0), notas=[], tramos=[], intereses=Decimal("0.00"), compensacion=Decimal("0.00"), intereses_sobre_base=None, fase=None)
        if nota_plazo:
            fila["notas"].append(nota_plazo)
        if dias <= 0:
            fila["estado"] = "no vencida"
            fila["notas"].append("Vence el %s: todavía no hay retraso." % dia_mes(vence))
        elif factura["tipo_cliente"] == "particular":
            fila["estado"] = "vencida, sin intereses de esta ley"
            fila["fase"] = fase_de(dias, factura["avisos"])
            fila["notas"].append("El cliente es un particular: la Ley 3/2004 no se aplica (art. 3.2.a). Se reclama el importe, sin estos intereses ni los 40 €.")
        elif factura["tipo_cliente"] == "administracion":
            fila["estado"] = "vencida, caso aparte"
            fila["notas"].append("El cliente es una Administración: tiene plazos y trámite propios. Aquí no se calcula; se reclama por su procedimiento.")
        else:
            fila["estado"] = "vencida"
            fila["fase"] = fase_de(dias, factura["avisos"])
            tramos, sin_tipo = tramos_de_interes(vence, hasta, factura["importe"], tipos)
            faltan.update(sin_tipo)
            fila["tramos"] = tramos
            fila["intereses"] = centimos(sum((t["interes"] for t in tramos), Decimal("0")))
            fila["compensacion"] = COMPENSACION
            if factura["base"] is not None:
                sobre_base, _ = tramos_de_interes(vence, hasta, factura["base"], tipos)
                fila["intereses_sobre_base"] = centimos(sum((t["interes"] for t in sobre_base), Decimal("0")))
        if dias > 0 and factura["tipo_cliente"] != "administracion":
            if hasta > anios_despues(vence, PRESCRIPCION_GENERAL_ANIOS):
                fila["notas"].append("Venció hace más de %d años: puede haber prescrito (art. 1964.2 del Código Civil). Que lo vea un abogado antes de reclamar." % PRESCRIPCION_GENERAL_ANIOS)
            elif hasta > anios_despues(vence, PRESCRIPCION_CORTA_ANIOS):
                fila["notas"].append("Venció hace más de %d años: algunas deudas prescriben a ese plazo (art. 1967 del Código Civil). Compruébalo antes de reclamar." % PRESCRIPCION_CORTA_ANIOS)
        fila["total"] = factura["importe"] + fila["intereses"] + fila["compensacion"] if dias > 0 and factura["tipo_cliente"] != "administracion" else Decimal("0.00")
        filas.append(fila)
    # What can be claimed first, oldest first; then what is not due yet or follows another procedure.
    filas.sort(key=lambda f: (f["total"] == 0, -f["dias_de_retraso"], clave(f["cliente"]), f["numero"]))
    return filas, sorted(faltan)


def resumir(filas, hasta, comprobado):
    reclamables = [f for f in filas if f["dias_de_retraso"] > 0 and f["tipo_cliente"] != "administracion"]
    con_ley = [f for f in reclamables if f["tipo_cliente"] == "empresa"]
    clientes = {}
    for fila in reclamables:
        grupo = clientes.setdefault(clave(fila["cliente"]), {"cliente": fila["cliente"], "facturas": 0, "pendiente": Decimal("0"), "intereses": Decimal("0"), "compensacion": Decimal("0"), "mayor_retraso_dias": 0, "fase": 0})
        grupo["facturas"] += 1
        grupo["pendiente"] += fila["importe"]
        grupo["intereses"] += fila["intereses"]
        grupo["compensacion"] += fila["compensacion"]
        grupo["mayor_retraso_dias"] = max(grupo["mayor_retraso_dias"], fila["dias_de_retraso"])
        grupo["fase"] = max(grupo["fase"], fila["fase"] or 0)
        if fila["intereses_sobre_base"] is not None:
            grupo["sin_iva"] = grupo.get("sin_iva", Decimal("0")) + fila["intereses_sobre_base"]
        elif fila["tipo_cliente"] == "empresa":
            grupo["sin_iva_incompleto"] = True
    por_cliente = sorted(clientes.values(), key=lambda g: -(g["pendiente"] + g["intereses"] + g["compensacion"]))
    pendiente = sum((f["importe"] for f in reclamables), Decimal("0"))
    intereses = sum((f["intereses"] for f in con_ley), Decimal("0"))
    compensacion = sum((f["compensacion"] for f in con_ley), Decimal("0"))
    con_base = [f for f in con_ley if f["intereses_sobre_base"] is not None]

    avisos = []
    if any(f["tipo_cliente"] == "particular" for f in reclamables):
        avisos.append("Hay facturas de particulares: se reclama su importe, pero la ley de morosidad entre empresas no les añade intereses ni compensación.")
    if any(f["tipo_cliente"] == "administracion" and f["dias_de_retraso"] > 0 for f in filas):
        avisos.append("Hay facturas a una Administración vencidas: no se han calculado. Tienen su propio procedimiento.")
    if any("prescri" in nota for f in filas for nota in f["notas"]):
        avisos.append("Hay facturas antiguas que pueden haber prescrito: están marcadas en la hoja. Que las vea un abogado antes de reclamarlas.")
    if con_ley:
        avisos.append("Los intereses están calculados sobre el importe con IVA. Hay tribunales que los calculan sobre la base sin IVA: es la cifra prudente si se va a juicio.")

    def cifra(valor):
        return str(centimos(valor))

    return {
        "calculado_a": hasta.isoformat(),
        "tipos_comprobados_el": comprobado,
        "facturas_vencidas": len(reclamables),
        "facturas_no_vencidas": sum(1 for f in filas if f["dias_de_retraso"] == 0),
        "pendiente": cifra(pendiente),
        "intereses_de_demora": cifra(intereses),
        "compensacion_por_costes_de_cobro": cifra(compensacion),
        "total_a_reclamar": cifra(pendiente + intereses + compensacion),
        "lo_que_la_ley_anade_al_importe": cifra(intereses + compensacion),
        "intereses_si_se_calculan_sin_iva": cifra(sum((f["intereses_sobre_base"] for f in con_base), Decimal("0"))) if con_base and len(con_base) == len(con_ley) else None,
        "por_cliente": [
            {
                "cliente": g["cliente"],
                "facturas": g["facturas"],
                "pendiente": cifra(g["pendiente"]),
                "intereses": cifra(g["intereses"]),
                "compensacion": cifra(g["compensacion"]),
                "total": cifra(g["pendiente"] + g["intereses"] + g["compensacion"]),
                "intereses_si_se_calculan_sin_iva": cifra(g["sin_iva"]) if "sin_iva" in g and not g.get("sin_iva_incompleto") else None,
                # For a proposal in two instalments: the halves, with the odd cent on the first.
                "pendiente_en_dos_pagos": [cifra(g["pendiente"] - centimos(g["pendiente"] / 2)), cifra(centimos(g["pendiente"] / 2))],
                "mayor_retraso_dias": g["mayor_retraso_dias"],
                "fase": g["fase"],
                "que_toca": FASES.get(g["fase"], ""),
            }
            for g in por_cliente
        ],
        "facturas": [
            {
                "cliente": f["cliente"],
                "numero": f["numero"],
                "estado": f["estado"],
                "vencimiento_legal": f["vencimiento_legal"].isoformat(),
                "dias_de_retraso": f["dias_de_retraso"],
                "pendiente": cifra(f["importe"]),
                "intereses": cifra(f["intereses"]),
                "compensacion": cifra(f["compensacion"]),
                "total": cifra(f["total"]),
                "fase": f["fase"],
                "notas": f["notas"],
            }
            for f in filas
        ],
        "avisos": avisos,
    }


def hojas(filas, resumen):
    reclamaciones = [["Cliente", "Factura", "Vence (según la ley)", "Días de retraso", "Pendiente", "Intereses de demora", "Compensación (art. 8)", "Total a reclamar", "Qué toca", "Notas"]]
    for f in filas:
        reclamaciones.append([f["cliente"], f["numero"], f["vencimiento_legal"], f["dias_de_retraso"], f["importe"], f["intereses"], f["compensacion"], f["total"], FASES.get(f["fase"], f["estado"]), " ".join(f["notas"])])
    reclamaciones.append(["Total", None, None, None, Decimal(resumen["pendiente"]), Decimal(resumen["intereses_de_demora"]), Decimal(resumen["compensacion_por_costes_de_cobro"]), Decimal(resumen["total_a_reclamar"]), None, None])

    clientes = [["Cliente", "Facturas vencidas", "Pendiente", "Intereses", "Compensación", "Total a reclamar", "Mayor retraso (días)", "Qué toca"]]
    for g in resumen["por_cliente"]:
        clientes.append([g["cliente"], g["facturas"], Decimal(g["pendiente"]), Decimal(g["intereses"]), Decimal(g["compensacion"]), Decimal(g["total"]), g["mayor_retraso_dias"], g["que_toca"]])

    calculo = [["Cliente", "Factura", "Desde", "Hasta", "Días", "Tipo anual", "Sobre", "Interés del tramo", "Tipo publicado en"]]
    for f in filas:
        for t in f["tramos"]:
            calculo.append([f["cliente"], f["numero"], t["desde"], t["hasta"], t["dias"], t["tipo"] / Decimal(100), f["importe"], centimos(t["interes"]), t["boe"]])

    base_legal = [
        ["Qué", "Dónde está", "Qué dice"],
        ["A quién se aplica", "Ley 3/2004, art. 3", "A los pagos entre empresas (un autónomo lo es) y con la Administración. No a los consumidores."],
        ["Plazo de pago", "Ley 3/2004, art. 4", "Treinta días naturales desde la entrega si no se pactó otro. El pactado no puede pasar de sesenta."],
        ["Cuándo empieza el retraso", "Ley 3/2004, art. 5", "Automáticamente al pasar el plazo, sin necesidad de aviso ni reclamación."],
        ["Interés de demora", "Ley 3/2004, art. 7", "El pactado en el contrato; si no hay, el tipo legal: el del Banco Central Europeo más ocho puntos, fijado para cada semestre."],
        ["Compensación por costes de cobro", "Ley 3/2004, art. 8", "Cuarenta euros que se añaden a la deuda en todo caso, y los costes acreditados que los superen."],
        ["No se puede renunciar por contrato", "Ley 3/2004, art. 9", "Son nulas las cláusulas que excluyen el interés de demora o la compensación."],
        ["Cómo se ha calculado", "Hoja «Cálculo»", "Interés simple: importe × tipo × días ÷ %d, tramo a tramo por semestre. Los tipos se comprobaron en el BOE el %s." % (DIAS_DEL_ANIO, resumen["tipos_comprobados_el"])],
        ["Qué es esto", "", "Un cálculo con las normas citadas, para reclamar lo que se debe. No es asesoramiento jurídico: antes de ir a un juzgado, que lo revise un abogado."],
    ]
    return [
        {"nombre": "Reclamaciones", "filas": reclamaciones, "formatos": {3: "entero", 4: "euros", 5: "euros", 6: "euros", 7: "euros", 9: "texto"}, "negrita": [len(reclamaciones) - 1], "anchos": [28, 14, 14, 10, 14, 14, 14, 16, 30, 70]},
        {"nombre": "Por cliente", "filas": clientes, "formatos": {1: "entero", 2: "euros", 3: "euros", 4: "euros", 5: "euros", 6: "entero"}},
        {"nombre": "Cálculo", "filas": calculo, "formatos": {4: "entero", 5: "porcentaje", 6: "euros", 7: "euros"}},
        {"nombre": "Base legal", "filas": base_legal, "formatos": {0: "texto", 1: "texto", 2: "texto"}, "anchos": [34, 24, 100]},
    ]


def fecha_arg(texto):
    try:
        return datetime.date.fromisoformat(texto)
    except ValueError:
        raise argparse.ArgumentTypeError("%r no es una fecha AAAA-MM-DD" % texto)


def tipo_arg(texto):
    encontrado = re.fullmatch(r"(\d{4}-[12])=(\d{1,2}(\.\d{1,2})?)", texto)
    if not encontrado:
        raise argparse.ArgumentTypeError("%r no tiene la forma AAAA-S=tipo, por ejemplo 2027-1=10.40" % texto)
    return encontrado.group(1), Decimal(encontrado.group(2))


def main(argumentos=None):
    analizador = argparse.ArgumentParser(description="Lo que se debe por facturas pagadas tarde: importe, intereses de demora y compensación.")
    analizador.add_argument("facturas", help="CSV con la cabecera %s" % ",".join(OBLIGATORIAS))
    analizador.add_argument("--hasta", type=fecha_arg, required=True, help="día al que se calcula, AAAA-MM-DD (normalmente hoy)")
    analizador.add_argument("--plazo-dias", type=int, help="plazo de pago habitual, para las facturas sin vencimiento (plazo_cobro_dias del perfil)")
    analizador.add_argument("--tipo", type=tipo_arg, action="append", default=[], metavar="AAAA-S=TIPO", help="tipo de un semestre que no esté en la tabla, leído en el BOE; se puede repetir")
    analizador.add_argument("--tipos", default=str(TIPOS_POR_DEFECTO), help="tabla de tipos (por defecto, la de la skill)")
    analizador.add_argument("--salida", help="ruta del .xlsx; sin ella solo se imprime el resumen")
    opciones = analizador.parse_args(argumentos)
    if opciones.plazo_dias is not None and not 1 <= opciones.plazo_dias <= 365:
        analizador.error("--plazo-dias tiene que estar entre 1 y 365")

    try:
        tipos, comprobado = leer_tipos(opciones.tipos, opciones.tipo)
        facturas = leer_facturas(opciones.facturas)
    except EntradaInvalida as fallo:
        print("EL CSV TIENE %d PROBLEMA(S). Corrígelos y vuelve a ejecutar:" % len(fallo.problemas), file=sys.stderr)
        for linea in fallo.problemas:
            print("  ✗ " + linea, file=sys.stderr)
        return 1
    except (OSError, UnicodeDecodeError, ValueError, KeyError) as fallo:
        print("No puedo leer los datos: %s" % fallo, file=sys.stderr)
        return 2

    filas, faltan = calcular(facturas, opciones.hasta, tipos, opciones.plazo_dias)
    if faltan:
        print(
            "FALTA EL TIPO DE DEMORA DE %d SEMESTRE(S): %s.\n"
            "  ✗ No se calcula con un tipo supuesto. Búscalo en boe.es («tipo legal de interés de demora» y el semestre),\n"
            "    y vuelve a ejecutar añadiendo, por cada uno, --tipo AAAA-S=TIPO (por ejemplo --tipo %s=10.40)." % (len(faltan), ", ".join(faltan), faltan[0]),
            file=sys.stderr,
        )
        return 1

    resumen = resumir(filas, opciones.hasta, comprobado)
    if opciones.salida:
        try:
            escribir_xlsx(opciones.salida, hojas(filas, resumen))
        except OSError as fallo:
            print("No puedo escribir %s: %s" % (opciones.salida, fallo), file=sys.stderr)
            return 2
        resumen["fichero"] = opciones.salida
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

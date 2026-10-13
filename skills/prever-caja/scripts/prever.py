#!/usr/bin/env python3
"""Projects the cash of a small business week by week and says when it runs short.

The arithmetic of a cash forecast is where a language model slips: one payment
counted twice or a monthly cost missing from week nine and the answer is wrong
without looking wrong. So the model only prepares the list of expected
movements; this script validates it, repeats the recurring ones, places every
movement in its week, runs three scenarios and writes the workbook.

Input: a CSV with the header `fecha,concepto,importe,tercero,repite`

    fecha     YYYY-MM-DD, the day the money is expected to move
    concepto  what it is ("Factura 2026-041", "Nóminas", "IVA 3T modelo 303")
    importe   positive = money coming in, negative = money going out.
              Plain number with a dot for decimals: 4840.00, -1450.00
    tercero   who pays or is paid (may be empty)
    repite    no | mensual | trimestral

Usage:
    python3 scripts/prever.py movimientos.csv --saldo 12350.40 --fecha 2026-10-13 \
        --minimo 8000 --salida prevision-caja.xlsx

Scenarios:
    previsto           every movement on its date
    con_retraso        every incoming payment arrives --retraso-dias later
    sin_cliente_mayor  nothing arrives from the customer the period depends on most

Prints a JSON summary and writes the workbook. Exit code 0 when the forecast was
produced, 1 when the CSV has to be fixed (each problem with its line), 2 when a
file cannot be read or written.
Standard library only. Reads the CSV, writes the workbook, opens no connection.
"""
import argparse
import calendar
import csv
import datetime
import json
import re
import sys
import unicodedata
from decimal import Decimal, InvalidOperation

from hoja_xlsx import escribir_xlsx

COLUMNAS = ["fecha", "concepto", "importe", "tercero", "repite"]
REPITE = ("no", "mensual", "trimestral")
# Thirteen weeks is one quarter: long enough to see the next tax payment, short enough to be believable.
SEMANAS = 13
SEMANAS_MAX = 52
# Average delay in paying invoices in Spain, in days (Informa D&B, second quarter of 2026: 14.36).
# https://www.informa.es/notas-de-prensa/las-empresas-espanolas-pagan-con-un-retraso-medio-de-1436-dias-en-el-segundo-trimestre-del-ano
RETRASO_DIAS = 14
IMPORTE = re.compile(r"^-?\d+(\.\d{1,2})?$")
# Quarterly filing deadlines in the common tax territory (modelos 303 and 130): (month, day).
# https://sede.agenciatributaria.gob.es/Sede/ayuda/calendario-contribuyente/calendario-contribuyente-2026.html
VENCIMIENTOS_TRIMESTRALES = ((1, 30), (4, 20), (7, 20), (10, 20))
PALABRAS_DE_IMPUESTO = ("iva", "303", "130", "irpf", "hacienda", "aeat", "impuesto", "111", "115", "trimestre")
# How far from a filing deadline a payment still counts as "the tax payment of that quarter".
MARGEN_IMPUESTO_DIAS = 12
# Enough payments per key week to explain it; the full list is in the workbook.
PAGOS_POR_SEMANA = 3
# From this share of the period's income on, one customer is reported as a risk of its own.
CONCENTRACION = Decimal("0.33")


class EntradaInvalida(Exception):
    def __init__(self, problemas):
        super().__init__("\n".join(problemas))
        self.problemas = problemas


def euros(importe):
    """1234.5 -> '1.234,50 €', the way an amount is written in Spain."""
    texto = "{:,.2f}".format(abs(Decimal(importe)))
    texto = texto.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    return ("-" if Decimal(importe) < 0 else "") + texto + " €"


def dia_mes(dia):
    return dia.strftime("%d/%m/%Y")


def sin_tildes(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


def leer_movimientos(ruta):
    """Returns the rows as dicts; raises EntradaInvalida naming every bad line."""
    with open(ruta, encoding="utf-8-sig", newline="") as fichero:
        lector = csv.reader(fichero)
        filas = [fila for fila in lector if any(celda.strip() for celda in fila)]
    if not filas:
        raise EntradaInvalida(["El fichero está vacío. Hace falta la cabecera %s y al menos un movimiento." % ",".join(COLUMNAS)])
    cabecera = [celda.strip().lower() for celda in filas[0]]
    if cabecera != COLUMNAS:
        raise EntradaInvalida(["La primera línea tiene que ser exactamente: %s (recibido: %s)" % (",".join(COLUMNAS), ",".join(filas[0]))])

    problemas, movimientos = [], []
    for numero, fila in enumerate(filas[1:], 2):
        if len(fila) != len(COLUMNAS):
            problemas.append("línea %d: tiene %d columnas y hacen falta %d. Si el concepto lleva una coma, ponlo entre comillas." % (numero, len(fila), len(COLUMNAS)))
            continue
        fecha, concepto, importe, tercero, repite = (celda.strip() for celda in fila)
        correcto = True
        try:
            dia = datetime.date.fromisoformat(fecha)
        except ValueError:
            problemas.append("línea %d: la fecha %r no es AAAA-MM-DD." % (numero, fecha))
            correcto = False
        if not concepto:
            problemas.append("línea %d: falta el concepto." % numero)
            correcto = False
        if not IMPORTE.match(importe):
            problemas.append("línea %d: el importe %r tiene que ser un número con punto decimal, sin símbolo ni separador de miles (4840.00, -1450.00)." % (numero, importe))
            correcto = False
        elif Decimal(importe) == 0:
            problemas.append("línea %d: el importe es cero. Si no se sabe el importe, no se apunta el movimiento: se avisa de que falta." % numero)
            correcto = False
        if repite.lower() not in REPITE:
            problemas.append("línea %d: `repite` es %r y tiene que ser %s." % (numero, repite, ", ".join(REPITE)))
            correcto = False
        if correcto:
            movimientos.append({"linea": numero, "fecha": dia, "concepto": concepto, "importe": Decimal(importe), "tercero": tercero, "repite": repite.lower()})
    if problemas:
        raise EntradaInvalida(problemas)
    if not movimientos:
        raise EntradaInvalida(["No hay ningún movimiento debajo de la cabecera."])
    return movimientos


def sumar_meses(dia, meses):
    """Same day `meses` months later; the 31st of a short month becomes its last day."""
    total = dia.month - 1 + meses
    anio, mes = dia.year + total // 12, total % 12 + 1
    return datetime.date(anio, mes, min(dia.day, calendar.monthrange(anio, mes)[1]))


def desplegar(movimientos, inicio, fin):
    """Expands recurring movements and moves overdue ones to the start date.

    Returns the dated movements inside [inicio, fin] and the list of overdue ones.
    """
    desplegados, vencidos = [], []
    for movimiento in movimientos:
        paso = {"no": 0, "mensual": 1, "trimestral": 3}[movimiento["repite"]]
        if paso == 0:
            fechas = [movimiento["fecha"]]
        else:
            fechas, n = [], 0
            while True:
                dia = sumar_meses(movimiento["fecha"], n * paso)
                if dia > fin:
                    break
                fechas.append(dia)
                n += 1
            # A recurring movement that started in the past: only what is still to come counts.
            fechas = [dia for dia in fechas if dia >= inicio]
        for dia in fechas:
            copia = dict(movimiento, fecha=dia, vencido=False)
            if dia < inicio:
                # A one-off dated before today has not happened yet (it would already be in the balance):
                # it is an overdue invoice or an unpaid bill. It is assumed to move now, and it is reported.
                copia.update(fecha=inicio, vencido=True, fecha_original=dia)
                vencidos.append(copia)
            if copia["fecha"] <= fin:
                desplegados.append(copia)
    desplegados.sort(key=lambda m: (m["fecha"], -m["importe"]))
    return desplegados, vencidos


def lunes(dia):
    return dia - datetime.timedelta(days=dia.weekday())


def semanas(inicio, cuantas):
    """Week 1 runs from the balance date to that Sunday; the rest are Monday to Sunday."""
    tramos, desde = [], inicio
    for _ in range(cuantas):
        hasta = lunes(desde) + datetime.timedelta(days=6)
        tramos.append((desde, hasta))
        desde = hasta + datetime.timedelta(days=1)
    return tramos


def proyectar(movimientos, tramos, saldo, retraso=0, excluir=()):
    """Weekly inflows, outflows and closing balance. `excluir` are the movements that never arrive."""
    fin = tramos[-1][1]
    entradas = [Decimal("0")] * len(tramos)
    salidas = [Decimal("0")] * len(tramos)
    fuera = Decimal("0")
    for movimiento in movimientos:
        if any(movimiento is excluido for excluido in excluir):
            continue
        dia = movimiento["fecha"]
        if movimiento["importe"] > 0 and retraso:
            dia = dia + datetime.timedelta(days=retraso)
        if dia > fin:
            fuera += movimiento["importe"]
            continue
        indice = next(i for i, (desde, hasta) in enumerate(tramos) if dia <= hasta)
        if movimiento["importe"] > 0:
            entradas[indice] += movimiento["importe"]
        else:
            salidas[indice] += movimiento["importe"]
    saldos, actual = [], saldo
    for i in range(len(tramos)):
        actual += entradas[i] + salidas[i]
        saldos.append(actual)
    return {"entradas": entradas, "salidas": salidas, "saldos": saldos, "fuera_del_periodo": fuera}


def primera(saldos, tramos, umbral):
    for (desde, _), saldo in zip(tramos, saldos):
        if saldo < umbral:
            return desde
    return None


def resumir(nombre, proyeccion, tramos, minimo):
    saldos = proyeccion["saldos"]
    peor = min(range(len(saldos)), key=lambda i: saldos[i])
    bajo_minimo = primera(saldos, tramos, minimo) if minimo is not None else None
    en_negativo = primera(saldos, tramos, Decimal("0"))
    return {
        "escenario": nombre,
        "saldo_final": str(saldos[-1]),
        "saldo_mas_bajo": str(saldos[peor]),
        "semana_del_saldo_mas_bajo": tramos[peor][0].isoformat(),
        "primera_semana_bajo_el_minimo": bajo_minimo.isoformat() if bajo_minimo else None,
        "primera_semana_en_negativo": en_negativo.isoformat() if en_negativo else None,
        # Closing balance of every week, so two scenarios can be compared on the same week and a date can be answered.
        "saldo_al_cierre_de_cada_semana": {desde.isoformat(): str(saldo) for (desde, _), saldo in zip(tramos, saldos)},
    }


def avisos_de_impuestos(movimientos, inicio, fin):
    """A filing deadline inside the period with no payment near it is a question to ask, not a zero."""
    avisos = []
    for anio in range(inicio.year, fin.year + 1):
        for mes, dia in VENCIMIENTOS_TRIMESTRALES:
            limite = datetime.date(anio, mes, dia)
            if not inicio <= limite <= fin:
                continue
            cubierto = any(
                m["importe"] < 0
                and abs((m["fecha"] - limite).days) <= MARGEN_IMPUESTO_DIAS
                and any(palabra in sin_tildes(m["concepto"] + " " + m["tercero"]) for palabra in PALABRAS_DE_IMPUESTO)
                for m in movimientos
            )
            if not cubierto:
                avisos.append(
                    "El %s vence la declaración trimestral (IVA y pago a cuenta) y no hay ningún pago de impuestos apuntado cerca de esa fecha. "
                    "Si toca pagar, la previsión es demasiado optimista: pregunta el importe." % dia_mes(limite)
                )
    return avisos


def cliente_mayor(cobros):
    """The customer whose payments weigh most in the period, or the largest single payment without a name.

    One invoice not arriving is a bad week; a customer not paying is what closes businesses, and
    a customer usually owes more than one invoice.
    """
    if not cobros:
        return None
    grupos = {}
    for indice, cobro in enumerate(cobros):
        # A payment without a name cannot be grouped with another: it stands alone.
        clave = sin_tildes(cobro["tercero"]).strip() or "\x00%d" % indice
        grupos.setdefault(clave, []).append(cobro)
    grupo = max(grupos.values(), key=lambda lista: sum(c["importe"] for c in lista))
    total = sum(c["importe"] for c in cobros)
    importe = sum(c["importe"] for c in grupo)
    return {
        "nombre": grupo[0]["tercero"] or grupo[0]["concepto"],
        "cobros": grupo,
        "importe": importe,
        "parte": importe / total,
    }


def construir(movimientos, saldo, inicio, cuantas, minimo, retraso, calendario_fiscal=True):
    tramos = semanas(inicio, cuantas)
    fin = tramos[-1][1]
    desplegados, vencidos = desplegar(movimientos, inicio, fin)
    cobros = [m for m in desplegados if m["importe"] > 0]
    mayor = cliente_mayor(cobros)

    escenarios = {
        "previsto": proyectar(desplegados, tramos, saldo),
        "con_retraso": proyectar(desplegados, tramos, saldo, retraso=retraso),
        "sin_cliente_mayor": proyectar(desplegados, tramos, saldo, excluir=mayor["cobros"] if mayor else ()),
    }

    avisos = []
    cobros_vencidos = [m for m in vencidos if m["importe"] > 0]
    pagos_vencidos = [m for m in vencidos if m["importe"] < 0]
    if cobros_vencidos:
        uno = len(cobros_vencidos) == 1
        avisos.append(
            "Hay %d %s por %s. La previsión supone que %s esta semana; si no es seguro, es dinero que hay que reclamar, no contar."
            % (len(cobros_vencidos), "cobro ya vencido" if uno else "cobros ya vencidos", euros(sum(m["importe"] for m in cobros_vencidos)), "entra" if uno else "entran")
        )
    if pagos_vencidos:
        uno = len(pagos_vencidos) == 1
        avisos.append(
            "Hay %d %s por %s. Se %s esta semana."
            % (len(pagos_vencidos), "pago con fecha pasada" if uno else "pagos con fecha pasada", euros(-sum(m["importe"] for m in pagos_vencidos)), "cuenta como si se pagara" if uno else "cuentan como si se pagaran")
        )
    # A third of the period's income riding on one customer is the classic way a forecast fails.
    if mayor is not None and mayor["parte"] >= CONCENTRACION:
        avisos.append(
            "%s es el %d %% de todo lo que se espera cobrar en el periodo (%s en %d %s)."
            % (mayor["nombre"], int(mayor["parte"] * 100), euros(mayor["importe"]), len(mayor["cobros"]), "cobro" if len(mayor["cobros"]) == 1 else "cobros")
        )
    if not cobros:
        avisos.append("No hay ningún cobro apuntado en el periodo. ¿Falta la lista de lo que está pendiente de cobrar?")
    if not any(m["importe"] < 0 for m in desplegados):
        avisos.append("No hay ningún pago apuntado en el periodo. Una previsión sin pagos no dice nada: faltan los gastos.")
    if calendario_fiscal:
        avisos.extend(avisos_de_impuestos(desplegados, inicio, fin))

    resumidos = [resumir(nombre, proyeccion, tramos, minimo) for nombre, proyeccion in escenarios.items()]
    # Why a week is bad is a fact of the list, not something to guess afterwards: its largest payments.
    claves = sorted({e[campo] for e in resumidos for campo in ("semana_del_saldo_mas_bajo", "primera_semana_bajo_el_minimo", "primera_semana_en_negativo") if e[campo]})
    pagos_clave = {}
    for clave in claves:
        desde, hasta = next(tramo for tramo in tramos if tramo[0].isoformat() == clave)
        pagos = sorted((m for m in desplegados if m["importe"] < 0 and desde <= m["fecha"] <= hasta), key=lambda m: m["importe"])
        pagos_clave[clave] = [{"concepto": m["concepto"], "importe": str(-m["importe"]), "fecha": m["fecha"].isoformat()} for m in pagos[:PAGOS_POR_SEMANA]]

    resumen = {
        "fecha_del_saldo": inicio.isoformat(),
        "saldo_inicial": str(saldo),
        "hasta": fin.isoformat(),
        "semanas": cuantas,
        "minimo": str(minimo) if minimo is not None else None,
        "retraso_dias": retraso,
        "escenarios": resumidos,
        "mayores_pagos_de_las_semanas_clave": pagos_clave,
        "cliente_mayor": {"nombre": mayor["nombre"], "importe": str(mayor["importe"]), "cobros": len(mayor["cobros"]), "parte_de_los_cobros": "%d %%" % int(mayor["parte"] * 100)} if mayor else None,
        "cobros_vencidos": str(sum(m["importe"] for m in cobros_vencidos)),
        "avisos": avisos,
    }
    return tramos, desplegados, escenarios, resumen


def hojas(tramos, desplegados, escenarios, resumen, minimo):
    previsto, retraso, sin_mayor = escenarios["previsto"], escenarios["con_retraso"], escenarios["sin_cliente_mayor"]
    cliente = resumen["cliente_mayor"]["nombre"] if resumen["cliente_mayor"] else "el cliente mayor"
    filas = [["Semana", "Hasta", "Cobros", "Pagos", "Saldo previsto", "Saldo si cobras con %d días de retraso" % resumen["retraso_dias"], "Saldo si no paga %s" % cliente, "Por debajo del mínimo"]]
    for i, (desde, hasta) in enumerate(tramos):
        bajo = ""
        if minimo is not None:
            marcas = [nombre for nombre, serie in (("previsto", previsto), ("con retraso", retraso), ("sin %s" % cliente, sin_mayor)) if serie["saldos"][i] < minimo]
            bajo = ", ".join(marcas)
        filas.append([desde, hasta, previsto["entradas"][i], previsto["salidas"][i], previsto["saldos"][i], retraso["saldos"][i], sin_mayor["saldos"][i], bajo])

    detalle = [["Fecha", "Semana que empieza", "Concepto", "Tercero", "Importe", "Se repite", "Nota"]]
    for movimiento in desplegados:
        semana = next(desde for desde, hasta in tramos if movimiento["fecha"] <= hasta)
        nota = ""
        if movimiento["vencido"]:
            nota = "Vencido el %s: se supone que se mueve esta semana" % dia_mes(movimiento["fecha_original"])
        detalle.append([movimiento["fecha"], semana, movimiento["concepto"], movimiento["tercero"], movimiento["importe"], movimiento["repite"], nota])

    notas = [["Qué mirar", "Dato"]]
    def fecha(iso):
        return dia_mes(datetime.date.fromisoformat(iso))

    notas.append(["Saldo de partida (%s)" % fecha(resumen["fecha_del_saldo"]), euros(resumen["saldo_inicial"])])
    if minimo is not None:
        notas.append(["Mínimo con el que el negocio está tranquilo", euros(minimo)])
    for escenario in resumen["escenarios"]:
        nombre = {"previsto": "Si todo va según lo previsto", "con_retraso": "Si los cobros llegan con %d días de retraso" % resumen["retraso_dias"], "sin_cliente_mayor": "Si no paga %s" % cliente}[escenario["escenario"]]
        frase = "El saldo más bajo es %s, la semana del %s." % (euros(escenario["saldo_mas_bajo"]), fecha(escenario["semana_del_saldo_mas_bajo"]))
        if escenario["primera_semana_en_negativo"]:
            frase += " La cuenta entra en negativo la semana del %s." % fecha(escenario["primera_semana_en_negativo"])
        if escenario["primera_semana_bajo_el_minimo"]:
            frase += " Baja del mínimo la semana del %s." % fecha(escenario["primera_semana_bajo_el_minimo"])
        elif minimo is not None:
            frase += " No baja del mínimo."
        notas.append([nombre, frase])
    for aviso in resumen["avisos"]:
        notas.append(["Aviso", aviso])
    notas.append(["Qué es esto", "Una previsión hecha con los movimientos de la hoja «Movimientos». Lo que no está ahí no está contado."])

    return [
        {"nombre": "Semanas", "filas": filas, "formatos": {2: "euros", 3: "euros", 4: "euros", 5: "euros", 6: "euros", 7: "texto"}, "anchos": [12, 12, 14, 14, 16, 22, 22, 28]},
        {"nombre": "Movimientos", "filas": detalle, "formatos": {4: "euros", 6: "texto"}},
        {"nombre": "Avisos", "filas": notas, "formatos": {0: "texto", 1: "texto"}, "anchos": [44, 90]},
    ]


def importe_arg(texto):
    if not IMPORTE.match(texto):
        raise argparse.ArgumentTypeError("%r no es un importe: número con punto decimal, sin símbolo (12350.40)" % texto)
    return Decimal(texto)


def fecha_arg(texto):
    try:
        return datetime.date.fromisoformat(texto)
    except ValueError:
        raise argparse.ArgumentTypeError("%r no es una fecha AAAA-MM-DD" % texto)


def main(argumentos=None):
    analizador = argparse.ArgumentParser(description="Previsión de caja semana a semana, con tres escenarios.")
    analizador.add_argument("movimientos", help="CSV con la cabecera %s" % ",".join(COLUMNAS))
    analizador.add_argument("--saldo", type=importe_arg, required=True, help="saldo en cuenta el día --fecha")
    analizador.add_argument("--fecha", type=fecha_arg, required=True, help="día del saldo, AAAA-MM-DD")
    analizador.add_argument("--minimo", type=importe_arg, help="saldo por debajo del cual hay que avisar (caja_minima_eur del perfil)")
    analizador.add_argument("--semanas", type=int, default=SEMANAS, help="semanas a proyectar (por defecto %d)" % SEMANAS)
    analizador.add_argument("--retraso-dias", type=int, default=RETRASO_DIAS, help="retraso de los cobros en el segundo escenario (por defecto %d)" % RETRASO_DIAS)
    analizador.add_argument("--salida", help="ruta del .xlsx; sin ella solo se imprime el resumen")
    analizador.add_argument(
        "--sin-calendario-fiscal",
        action="store_true",
        help="no avisar de los vencimientos trimestrales: úsalo si `territorio` no es `comun`, porque esas fechas son las del territorio común",
    )
    opciones = analizador.parse_args(argumentos)

    if not 1 <= opciones.semanas <= SEMANAS_MAX:
        analizador.error("--semanas tiene que estar entre 1 y %d" % SEMANAS_MAX)
    if not 0 <= opciones.retraso_dias <= 180:
        analizador.error("--retraso-dias tiene que estar entre 0 y 180")

    try:
        movimientos = leer_movimientos(opciones.movimientos)
    except (OSError, UnicodeDecodeError) as fallo:
        print("No puedo leer %s: %s" % (opciones.movimientos, fallo), file=sys.stderr)
        return 2
    except EntradaInvalida as fallo:
        print("EL CSV TIENE %d PROBLEMA(S). Corrígelos y vuelve a ejecutar:" % len(fallo.problemas), file=sys.stderr)
        for linea in fallo.problemas:
            print("  ✗ " + linea, file=sys.stderr)
        return 1

    tramos, desplegados, escenarios, resumen = construir(
        movimientos, opciones.saldo, opciones.fecha, opciones.semanas, opciones.minimo, opciones.retraso_dias, calendario_fiscal=not opciones.sin_calendario_fiscal
    )
    if opciones.salida:
        try:
            escribir_xlsx(opciones.salida, hojas(tramos, desplegados, escenarios, resumen, opciones.minimo))
        except OSError as fallo:
            print("No puedo escribir %s: %s" % (opciones.salida, fallo), file=sys.stderr)
            return 2
        resumen["fichero"] = opciones.salida
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

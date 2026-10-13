#!/usr/bin/env python3
"""Checks a business profile (`perfil-negocio.md`) before the other skills rely on it.

The profile is what makes a generic skill behave like one written for this
business, so a typo in it ("plazo: treinta") would quietly change every letter
and every calculation that comes after. This reads the file, says exactly which
line is wrong and what the valid values are, and lists what is still pending.

Usage:
    python3 scripts/validar_perfil.py perfil-negocio.md
    python3 scripts/validar_perfil.py perfil-negocio.md --json

Exit code 0 when the profile can be used (pending answers are allowed), 1 when
something has to be fixed, 2 when the file cannot be read.
Standard library only. Reads one file, writes nothing, opens no connection.
"""
import argparse
import datetime
import json
import re
import sys

PENDIENTE = "pendiente"
# A business that is paid on the spot has no payment term. That is an answer, not a gap.
NO_APLICA = "no_aplica"

# The Spanish VAT rates a business invoices with, plus the cases where it does not charge VAT.
# IGIC (Canarias) and IPSI (Ceuta, Melilla) replace VAT there; the skills say what they do not cover.
IVA = ("21", "10", "4", "exento", "recargo_equivalencia", "varios", "igic", "ipsi")
# Withholding a professional states on an invoice: none, the general rate, or the reduced one for new professionals.
RETENCION = ("no", "15", "7")

# clave -> (obligatoria, valores válidos o None si es texto libre, puede quedar pendiente)
CLAVES = {
    "quien_configura": (True, ("dueno", "equipo", "asesor"), False),
    "nombre": (False, None, True),
    "actividad": (True, None, False),
    "clientes": (True, ("empresas", "particulares", "ambos"), False),
    "forma": (True, ("autonomo", "sociedad"), False),
    "personas": (False, "entero", True),
    "territorio": (True, ("comun", "pais_vasco", "navarra", "canarias", "ceuta_melilla", "fuera_de_espana"), True),
    "cobro": (True, ("al_momento", "a_plazo", "mixto"), False),
    "plazo_cobro_dias": (False, "entero", True),
    "iva": (True, IVA, True),
    "retencion_irpf": (True, RETENCION, True),
    "caja_minima_eur": (False, "importe", True),
    "facturas_en": (False, None, True),
    "banco_exporta": (False, None, True),
    "clientes_en": (False, None, True),
    "gestoria": (True, ("si", "no"), True),
    "trato": (True, ("tu", "usted"), False),
    "firma": (False, None, True),
    "idioma": (False, None, True),
    "prioridad": (True, ("cobrar", "caja", "trimestre", "visibilidad", "datos", "no_lo_se"), False),
    "web": (False, None, True),
    "actualizado": (True, "fecha", False),
    "formato": (True, ("1",), False),
}

LINEA = re.compile(r"^-\s+([a-z_]+)\s*:\s*(.*?)\s*$")
# Longer than this and a payment term stops being a term (and the law caps most at 60, see `avisos`).
PLAZO_MAX = 365
# Ley 3/2004, art. 4.3: the agreed term between businesses cannot go beyond 60 calendar days.
PLAZO_LEGAL_MAX = 60


def leer(ruta):
    with open(ruta, encoding="utf-8") as fichero:
        lineas = fichero.read().splitlines()
    valores, donde, repetidas = {}, {}, []
    for numero, linea in enumerate(lineas, 1):
        encontrada = LINEA.match(linea)
        if not encontrada:
            continue
        clave, valor = encontrada.group(1), encontrada.group(2)
        if clave in valores:
            repetidas.append((clave, numero))
        valores[clave] = valor
        donde[clave] = numero
    return valores, donde, repetidas


def _entero(valor):
    return valor.isdigit()


def _importe(valor):
    return re.fullmatch(r"\d+([.,]\d{1,2})?", valor) is not None


def _fecha(valor):
    try:
        datetime.date.fromisoformat(valor)
    except ValueError:
        return False
    return True


def revisar(valores, donde, repetidas):
    errores, avisos, pendientes = [], [], []

    def error(clave, mensaje):
        linea = donde.get(clave)
        errores.append(("línea %d, " % linea if linea else "") + "`%s`: %s" % (clave, mensaje))

    for clave, linea in repetidas:
        errores.append("línea %d, `%s`: está dos veces en el fichero. Deja una sola." % (linea, clave))

    for clave in valores:
        if clave not in CLAVES:
            avisos.append("`%s` no es una clave del perfil: las skills no la leen. ¿Es un error al escribir?" % clave)

    for clave, (obligatoria, dominio, admite_pendiente) in CLAVES.items():
        valor = valores.get(clave)
        if valor is None or valor == "":
            if obligatoria:
                error(clave, "falta. " + _ayuda(dominio, admite_pendiente))
            continue
        if valor.lower() == PENDIENTE:
            if admite_pendiente:
                pendientes.append(clave)
            else:
                error(clave, "no puede quedar pendiente: las skills la necesitan. " + _ayuda(dominio, False))
            continue
        if dominio is None:
            continue
        if clave == "plazo_cobro_dias" and valor == NO_APLICA:
            continue  # checked against `cobro` below
        if dominio == "entero":
            if not _entero(valor):
                error(clave, "tiene que ser un número entero, sin texto (recibido: %r)." % valor)
        elif dominio == "importe":
            if not _importe(valor):
                error(clave, "tiene que ser un importe en euros, solo la cifra (recibido: %r)." % valor)
        elif dominio == "fecha":
            if not _fecha(valor):
                error(clave, "tiene que ser una fecha AAAA-MM-DD (recibido: %r)." % valor)
        elif valor not in dominio:
            error(clave, "%r no es un valor válido. %s" % (valor, _ayuda(dominio, admite_pendiente)))

    cobro, plazo = valores.get("cobro"), valores.get("plazo_cobro_dias")
    if cobro == "al_momento":
        if plazo not in (None, "", NO_APLICA, PENDIENTE):
            avisos.append("`plazo_cobro_dias` es %s pero `cobro` es al_momento: si se cobra en el momento no hay plazo. Confírmalo." % plazo)
        if "plazo_cobro_dias" in pendientes:
            pendientes.remove("plazo_cobro_dias")
    elif cobro in ("a_plazo", "mixto"):
        if plazo is None or plazo == "":
            error("plazo_cobro_dias", "cobras a plazo, así que hace falta el plazo en días (o `pendiente`).")
        elif plazo == NO_APLICA:
            error("plazo_cobro_dias", "`no_aplica` solo vale si `cobro` es al_momento. Pon los días, o `pendiente`.")
        elif _entero(plazo):
            dias = int(plazo)
            if not 1 <= dias <= PLAZO_MAX:
                error("plazo_cobro_dias", "tiene que estar entre 1 y %d días (recibido: %d)." % (PLAZO_MAX, dias))
            elif dias > PLAZO_LEGAL_MAX and valores.get("clientes") in ("empresas", "ambos"):
                avisos.append(
                    "`plazo_cobro_dias` es %d: entre empresas la ley no admite pactar más de %d días "
                    "(Ley 3/2004, art. 4.3). Las skills de cobros calcularán con %d."
                    % (dias, PLAZO_LEGAL_MAX, PLAZO_LEGAL_MAX)
                )
    if valores.get("retencion_irpf") in ("15", "7") and valores.get("forma") == "sociedad":
        avisos.append("`retencion_irpf` es %s pero `forma` es sociedad: una sociedad no lleva retención de IRPF en sus facturas. Confírmalo." % valores["retencion_irpf"])
    web = valores.get("web")
    if web and web.lower() not in (PENDIENTE, "no") and not re.match(r"https?://\S+\.\S+", web):
        error("web", "escribe la dirección completa, con https://, o `no` si no hay web (recibido: %r)." % web)
    if valores.get("territorio") in ("pais_vasco", "navarra", "canarias", "ceuta_melilla", "fuera_de_espana"):
        avisos.append(
            "`territorio` es %s: los impuestos y sus plazos no son los del territorio común. "
            "Las skills fiscales avisan de lo que no cubren ahí." % valores["territorio"]
        )
    return errores, avisos, pendientes


def _ayuda(dominio, admite_pendiente):
    cola = " También vale `pendiente`." if admite_pendiente else ""
    if dominio is None:
        return "Escribe el dato en texto." + cola
    if dominio == "entero":
        return "Tiene que ser un número entero." + cola
    if dominio == "importe":
        return "Tiene que ser un importe, solo la cifra." + cola
    if dominio == "fecha":
        return "Tiene que ser una fecha AAAA-MM-DD."
    return "Valores válidos: %s.%s" % (", ".join(dominio), cola)


def main(argumentos=None):
    analizador = argparse.ArgumentParser(description="Comprueba un perfil de negocio.")
    analizador.add_argument("perfil", help="ruta de perfil-negocio.md")
    analizador.add_argument("--json", action="store_true", help="salida en JSON")
    opciones = analizador.parse_args(argumentos)

    try:
        valores, donde, repetidas = leer(opciones.perfil)
    except (OSError, UnicodeDecodeError) as fallo:
        print("No puedo leer %s: %s" % (opciones.perfil, fallo), file=sys.stderr)
        return 2
    if not valores:
        print(
            "%s no tiene ninguna línea con el formato `- clave: valor`. "
            "Parte de la plantilla assets/perfil-negocio.plantilla.md." % opciones.perfil,
            file=sys.stderr,
        )
        return 2

    errores, avisos, pendientes = revisar(valores, donde, repetidas)
    if opciones.json:
        print(json.dumps({"valido": not errores, "errores": errores, "avisos": avisos, "pendientes": pendientes, "valores": valores}, ensure_ascii=False, indent=2))
    else:
        if errores:
            print("PERFIL NO VÁLIDO: %d cosa(s) que corregir" % len(errores))
            for linea in errores:
                print("  ✗ " + linea)
        else:
            print("PERFIL VÁLIDO")
        for linea in avisos:
            print("  ! " + linea)
        if pendientes:
            print("  … pendiente de respuesta: " + ", ".join(pendientes))
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Checks whether an AI assistant can find and read a business website.

Nine checks, the same ones a person would run by hand with `curl`, done the same
way every time: does every public page answer, does each one say which address
is its own, are AI crawlers let in without opening what was closed, is the brand
written one way, is there structured data and does it tell the truth, is the
text in the HTML without running JavaScript, does each page have its own
heading, and do all the ways into the domain end in the same place.

It reads the site as a crawler does: plain GET requests, no JavaScript, no
browser. It never submits a form, never sends anything but the request, and only
asks for pages of the site it was given.

Usage:
    python3 scripts/auditar.py https://ejemplo.es --salida visibilidad-en-ia.xlsx
    python3 scripts/auditar.py https://ejemplo.es --nombre "Clínica Ejemplo" --max-paginas 40

Prints a JSON summary and writes the workbook. Exit code 0 when the audit ran
(whatever it found), 2 when the site could not be reached at all or a file
could not be written.
Standard library only. Opens connections to the audited site and to nothing else.
"""
import argparse
import hashlib
import json
import re
import ssl
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from xml.etree import ElementTree

from hoja_xlsx import escribir_xlsx

BIEN, AVISO, FALLO, SIN_COMPROBAR, NO_APLICA = "bien", "aviso", "fallo", "sin comprobar", "no aplica"

# Says who is asking and why, so the owner of the site can recognise the visit in the logs.
AGENTE = "auditoria-visibilidad/2.0 (comprobacion de la propia web; skill negocio-pequeno)"
# A page that takes longer than this is a problem of its own; the audit does not wait for it.
ESPERA_SEGUNDOS = 15
# Enough to see a pattern in a small business site without hammering it. The rest is reported as not visited.
MAX_PAGINAS = 30
# Pause between requests: an audit must not look like an attack to a shared hosting or trip its bot protection.
PAUSA_SEGUNDOS = 0.5
# Nothing useful for these checks lies beyond the first megabytes of a page.
MAX_BYTES = 3_000_000
MAX_SALTOS = 6
# A page with less visible text than this has nothing an assistant could quote; usually the text arrives with JavaScript.
PALABRAS_MIN = 50

# The crawlers of the assistants and AI search engines that announce themselves with these names.
RASTREADORES_IA = (
    "GPTBot",
    "OAI-SearchBot",
    "ChatGPT-User",
    "PerplexityBot",
    "ClaudeBot",
    "Claude-Web",
    "Google-Extended",
    "Applebot-Extended",
    "meta-externalagent",
    "CCBot",
)
TIPOS_DE_ORGANIZACION = ("Organization", "LocalBusiness", "Corporation", "Store", "Restaurant", "MedicalBusiness", "ProfessionalService")
ETIQUETAS_SIN_TEXTO = ("script", "style", "noscript", "template", "svg", "head")


# ---------------------------------------------------------------- fetching


class _SinRedirigir(urllib.request.HTTPRedirectHandler):
    """Redirects are a finding, not something to follow silently."""

    def redirect_request(self, *argumentos, **opciones):
        return None


def pedir(url):
    """One GET, without following redirects. Returns a dict that never raises:

    {"url", "codigo" (int or None), "destino" (Location or None), "cuerpo" (str), "error" (str or None)}
    """
    respuesta = {"url": url, "codigo": None, "destino": None, "cuerpo": "", "error": None}
    abridor = urllib.request.build_opener(_SinRedirigir)
    peticion = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
    try:
        with abridor.open(peticion, timeout=ESPERA_SEGUNDOS) as contestacion:
            respuesta["codigo"] = contestacion.status
            crudo = contestacion.read(MAX_BYTES)
            juego = contestacion.headers.get_content_charset() or "utf-8"
            respuesta["cuerpo"] = crudo.decode(juego, errors="replace")
    except urllib.error.HTTPError as fallo:
        respuesta["codigo"] = fallo.code
        respuesta["destino"] = fallo.headers.get("Location")
    except urllib.error.URLError as fallo:
        motivo = fallo.reason
        if isinstance(motivo, ssl.SSLError):
            respuesta["error"] = "certificado no válido (%s)" % (getattr(motivo, "verify_message", None) or motivo.reason or motivo)
        elif type(motivo).__name__ == "gaierror":
            respuesta["error"] = "ese nombre no existe en internet (no está dado de alta en el DNS)"
        else:
            respuesta["error"] = "no responde (%s)" % motivo
    except (ssl.SSLError, OSError, ValueError) as fallo:
        respuesta["error"] = "no responde (%s)" % fallo
    return respuesta


# ---------------------------------------------------------------- reading a page


class _Pagina(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.canonical = None
        self.titulo = ""
        self.h1 = []
        self.jsonld = []
        self.texto = []
        self.noindex = False
        self._oculto = 0
        self._en = None
        self._buffer = []

    def handle_starttag(self, etiqueta, atributos):
        atributos = dict(atributos)
        if etiqueta == "link" and "canonical" in (atributos.get("rel") or "").lower().split():
            self.canonical = self.canonical or atributos.get("href")
        if etiqueta == "meta" and (atributos.get("name") or "").lower() == "robots" and "noindex" in (atributos.get("content") or "").lower():
            self.noindex = True
        if etiqueta == "script" and (atributos.get("type") or "").lower() == "application/ld+json":
            self._en, self._buffer = "jsonld", []
        elif etiqueta == "title" and self._en is None:
            self._en, self._buffer = "title", []
        elif etiqueta == "h1" and self._en is None:
            self._en, self._buffer = "h1", []
        if etiqueta in ETIQUETAS_SIN_TEXTO and etiqueta != "head":
            self._oculto += 1

    def handle_endtag(self, etiqueta):
        if etiqueta in ETIQUETAS_SIN_TEXTO and etiqueta != "head" and self._oculto:
            self._oculto -= 1
        if self._en == "jsonld" and etiqueta == "script":
            self.jsonld.append("".join(self._buffer))
            self._en = None
        elif self._en == "title" and etiqueta == "title":
            self.titulo = " ".join("".join(self._buffer).split())
            self._en = None
        elif self._en == "h1" and etiqueta == "h1":
            self.h1.append(" ".join("".join(self._buffer).split()))
            self._en = None

    def handle_data(self, datos):
        if self._en in ("jsonld", "title"):
            self._buffer.append(datos)
            return
        if self._en == "h1":
            self._buffer.append(datos)
        if not self._oculto:
            self.texto.append(datos)


def leer_pagina(html):
    """What a crawler that does not run JavaScript gets from a page."""
    pagina = _Pagina()
    try:
        pagina.feed(html)
        pagina.close()
    except Exception:  # a page so broken the parser gives up still yields what was read so far
        pass
    nodos, json_roto = [], 0
    for bloque in pagina.jsonld:
        try:
            nodos.extend(_aplanar(json.loads(bloque)))
        except ValueError:
            json_roto += 1
    texto = " ".join(" ".join(pagina.texto).split())
    return {
        "canonical": pagina.canonical,
        "titulo": pagina.titulo,
        "h1": [h for h in pagina.h1 if h],
        "nodos": nodos,
        "json_roto": json_roto,
        "bloques_jsonld": len(pagina.jsonld),
        "texto": texto,
        "palabras": len(texto.split()),
        "noindex": pagina.noindex,
    }


def _aplanar(dato):
    """Every object with an @type inside a JSON-LD block, however it is nested."""
    encontrados = []
    if isinstance(dato, list):
        for elemento in dato:
            encontrados.extend(_aplanar(elemento))
    elif isinstance(dato, dict):
        if "@type" in dato:
            encontrados.append(dato)
        for valor in dato.values():
            if isinstance(valor, (dict, list)):
                encontrados.extend(_aplanar(valor))
    return encontrados


def tipos(nodo):
    tipo = nodo.get("@type")
    return [str(t) for t in tipo] if isinstance(tipo, list) else [str(tipo)]


def normalizar(texto):
    """For comparing what the markup declares with what the page shows: case, accents and spacing aside."""
    texto = unicodedata.normalize("NFKD", str(texto)).lower()
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^\w\s]", " ", texto).split())


def misma_direccion(a, b):
    """Two URLs that a crawler treats as the same page: scheme and host case, and a trailing slash, aside."""

    def limpia(url):
        partes = urllib.parse.urlsplit(url.strip())
        ruta = partes.path.rstrip("/") or "/"
        return (partes.scheme.lower(), partes.netloc.lower(), ruta, partes.query)

    return limpia(a) == limpia(b)


def sin_www(servidor):
    servidor = servidor.lower()
    return servidor[4:] if servidor.startswith("www.") else servidor


# Second-level labels that are part of the suffix, not of the name: ejemplo.com.es is a domain, not a subdomain.
SUFIJOS_DE_DOS_NIVELES = ("com", "co", "org", "net", "gob", "edu", "nom")


def es_dominio_principal(servidor):
    """True for ejemplo.es or ejemplo.com.es; False for tienda.ejemplo.es.

    People type «www.» in front of a domain, not in front of a subdomain, so only the
    first has a «www» entrance worth checking.
    """
    etiquetas = sin_www(servidor.split(":")[0]).split(".")
    if len(etiquetas) <= 2:
        return True
    return len(etiquetas) == 3 and etiquetas[1] in SUFIJOS_DE_DOS_NIVELES


# ---------------------------------------------------------------- robots.txt and sitemap


def leer_robots(texto):
    """Groups of robots.txt: [{"agentes": [...], "reglas": [("disallow"|"allow", path)]}] and the sitemaps."""
    grupos, mapas, actual, en_agentes = [], [], None, False
    for linea in texto.splitlines():
        linea = linea.split("#", 1)[0].strip()
        if ":" not in linea:
            continue
        clave, valor = (parte.strip() for parte in linea.split(":", 1))
        clave = clave.lower()
        if clave == "user-agent":
            if not en_agentes:
                actual = {"agentes": [], "reglas": []}
                grupos.append(actual)
            actual["agentes"].append(valor.lower())
            en_agentes = True
        elif clave in ("disallow", "allow"):
            en_agentes = False
            if actual is not None and (valor or clave == "disallow"):
                actual["reglas"].append((clave, valor))
        elif clave == "sitemap":
            mapas.append(valor)
        else:
            en_agentes = False
    return grupos, mapas


def grupo_de(grupos, agente):
    """The group a crawler obeys: the one with its name, or the general one. Never both."""
    agente = agente.lower()
    for grupo in grupos:
        if agente in grupo["agentes"]:
            return grupo, True
    for grupo in grupos:
        if "*" in grupo["agentes"]:
            return grupo, False
    return None, False


def cerrado_del_todo(grupo):
    if grupo is None:
        return False
    prohibidas = [ruta for regla, ruta in grupo["reglas"] if regla == "disallow"]
    permitidas = [ruta for regla, ruta in grupo["reglas"] if regla == "allow"]
    return "/" in prohibidas and "/" not in permitidas


def prohibida(grupo, ruta):
    """Longest matching rule wins, as crawlers apply it (wildcards are not expanded: prefixes only)."""
    if grupo is None:
        return False
    mejor, veredicto = -1, False
    for regla, patron in grupo["reglas"]:
        patron = patron.split("*", 1)[0].rstrip("$")
        if patron and ruta.startswith(patron) and len(patron) > mejor:
            mejor, veredicto = len(patron), regla == "disallow"
    return veredicto


def direcciones_del_mapa(xml):
    """(urls, child sitemaps) of a sitemap or a sitemap index."""
    try:
        raiz = ElementTree.fromstring(xml.encode("utf-8"))
    except ElementTree.ParseError:
        return [], []
    direcciones = [nodo.text.strip() for nodo in raiz.iter() if nodo.tag.endswith("}loc") or nodo.tag == "loc" if nodo.text]
    if raiz.tag.endswith("sitemapindex"):
        return [], direcciones
    return direcciones, []


# ---------------------------------------------------------------- the audit


def auditar(web, pedir=pedir, nombre=None, max_paginas=MAX_PAGINAS, pausa=PAUSA_SEGUNDOS):
    """Runs the nine checks. `pedir` is the function that fetches a URL; tests pass their own."""
    partes = urllib.parse.urlsplit(web if "://" in web else "https://" + web)
    if not partes.netloc:
        raise ValueError("%r no es una dirección web." % web)
    origen = "%s://%s" % (partes.scheme, partes.netloc)
    servidor = sin_www(partes.netloc)

    def ir(url):
        if pausa:
            time.sleep(pausa)
        return pedir(url)

    # The ways in: http and https, with and without www, followed by hand so every hop is seen.
    anfitriones = [servidor]
    if es_dominio_principal(servidor) or partes.netloc.lower().startswith("www."):
        anfitriones.append("www." + servidor)
    entradas = []
    for esquema in ("https", "http"):
        for anfitrion in anfitriones:
            entradas.append(_seguir("%s://%s/" % (esquema, anfitrion), ir))
    portada = next((e for e in entradas if e["url"].startswith(origen) and e["final"]), None) or next((e for e in entradas if e["final"]), None)
    if portada is None:
        return None
    canonico = "%s://%s" % urllib.parse.urlsplit(portada["final"])[:2]

    robots = ir(canonico + "/robots.txt")
    grupos, mapas = leer_robots(robots["cuerpo"]) if robots["codigo"] == 200 else ([], [])
    general, _ = grupo_de(grupos, "*")

    # Pages to visit: the sitemap, or just the home page when there is none.
    pendientes, visitados, declaradas, ajenas = list(mapas) or [canonico + "/sitemap.xml"], set(), [], []
    hay_mapa = False
    while pendientes and len(visitados) < 10:
        mapa = pendientes.pop(0)
        if mapa in visitados:
            continue
        visitados.add(mapa)
        contestacion = ir(mapa)
        if contestacion["codigo"] != 200:
            continue
        direcciones, hijos = direcciones_del_mapa(contestacion["cuerpo"])
        hay_mapa = hay_mapa or bool(direcciones or hijos)
        pendientes.extend(hijos)
        for direccion in direcciones:
            if sin_www(urllib.parse.urlsplit(direccion).netloc) == servidor:
                declaradas.append(direccion)
            else:
                ajenas.append(direccion)
    declaradas = list(dict.fromkeys(declaradas))
    if not any(misma_direccion(d, canonico + "/") for d in declaradas):
        declaradas.insert(0, canonico + "/")

    paginas, cerradas = [], []
    for direccion in declaradas[:max_paginas]:
        ruta = urllib.parse.urlsplit(direccion).path or "/"
        if prohibida(general, ruta):
            cerradas.append(direccion)
            continue
        contestacion = ir(direccion)
        pagina = {"url": direccion, "codigo": contestacion["codigo"], "destino": contestacion["destino"], "error": contestacion["error"]}
        if contestacion["codigo"] == 200:
            pagina.update(leer_pagina(contestacion["cuerpo"]))
        paginas.append(pagina)
    leidas = [p for p in paginas if p["codigo"] == 200]

    comprobaciones = [
        _direcciones(paginas, hay_mapa, len(declaradas), max_paginas, cerradas, ajenas),
        _canonicas(leidas),
        _robots(robots, grupos),
        _marca(leidas, nombre),
        _datos_estructurados(leidas, canonico),
        _marcado_veraz(leidas),
        _texto_en_html(leidas),
        _encabezados(leidas),
        _entradas(entradas),
    ]
    llms = ir(canonico + "/llms.txt")
    return {
        "web": canonico,
        "paginas_en_el_mapa": len(declaradas) if hay_mapa else 0,
        "paginas_visitadas": len(paginas),
        "resultado": {estado: sum(1 for c in comprobaciones if c["resultado"] == estado) for estado in (BIEN, AVISO, FALLO, SIN_COMPROBAR, NO_APLICA)},
        "comprobaciones": comprobaciones,
        "llms_txt": llms["codigo"] == 200,
        "paginas": paginas,
        "rastreadores": _tabla_rastreadores(grupos),
    }


def _seguir(url, ir):
    """Follows redirects by hand. Returns {"url", "saltos": [...], "final" (None on failure), "error"}."""
    saltos, actual = [], url
    for _ in range(MAX_SALTOS):
        contestacion = ir(actual)
        if contestacion["error"]:
            return {"url": url, "saltos": saltos, "final": None, "error": contestacion["error"]}
        codigo = contestacion["codigo"]
        if codigo in (301, 302, 303, 307, 308) and contestacion["destino"]:
            siguiente = urllib.parse.urljoin(actual, contestacion["destino"])
            saltos.append("%d → %s" % (codigo, siguiente))
            actual = siguiente
            continue
        if codigo == 200:
            return {"url": url, "saltos": saltos, "final": actual, "error": None}
        return {"url": url, "saltos": saltos, "final": None, "error": "responde %s" % codigo}
    return {"url": url, "saltos": saltos, "final": None, "error": "más de %d redirecciones seguidas" % MAX_SALTOS}


def _comprobacion(numero, nombre, resultado, visto, arreglo="", ejemplos=()):
    return {"numero": numero, "nombre": nombre, "resultado": resultado, "visto": visto, "arreglo": arreglo, "ejemplos": list(ejemplos)[:8]}


def _direcciones(paginas, hay_mapa, declaradas, max_paginas, cerradas, ajenas):
    nombre = "Cada página pública responde y no redirige"
    if not hay_mapa:
        return _comprobacion(1, nombre, SIN_COMPROBAR, "No hay sitemap.xml legible, así que solo se ha podido mirar la portada.", "Publica un sitemap con las páginas que quieres que se lean y decláralo en robots.txt.")
    frenadas = [p for p in paginas if p["codigo"] in (403, 429)]
    # A site that starts refusing the audit is not a site with broken pages: say so instead of reporting them as missing.
    if frenadas and len(frenadas) >= max(2, len(paginas) // 3):
        return _comprobacion(1, nombre, SIN_COMPROBAR, "La web ha rechazado %d de %d peticiones (códigos 403 o 429): su protección contra robots ha frenado la auditoría." % (len(frenadas), len(paginas)), "Repite la auditoría con una pausa mayor entre peticiones (--pausa 2). Si sigue igual, esa misma protección puede estar frenando a los rastreadores de IA: pregúntalo a quien lleva el alojamiento.", [p["url"] for p in frenadas])
    rotas = [p for p in paginas if p["error"] or (p["codigo"] or 0) >= 400]
    redirigen = [p for p in paginas if p["codigo"] in (301, 302, 303, 307, 308)]
    notas = []
    if declaradas > max_paginas:
        notas.append("Se han visitado %d de las %d páginas del sitemap." % (len(paginas) + len(cerradas), declaradas))
    if cerradas:
        notas.append("%d página(s) del sitemap están cerradas en robots.txt: se anuncia lo que se prohíbe leer." % len(cerradas))
    if ajenas:
        notas.append("%d dirección(es) del sitemap son de otro dominio." % len(ajenas))
    cola = (" " + " ".join(notas)) if notas else ""
    if rotas:
        return _comprobacion(1, nombre, FALLO, "%d de %d páginas del sitemap no responden bien.%s" % (len(rotas), len(paginas), cola), "Quita del sitemap las páginas que ya no existen o arregla las que fallan.", ["%s → %s" % (p["url"], p["error"] or p["codigo"]) for p in rotas])
    if redirigen or cerradas or ajenas:
        visto = "%d de %d páginas del sitemap redirigen a otra dirección.%s" % (len(redirigen), len(paginas), cola) if redirigen else "Todas responden.%s" % cola
        return _comprobacion(1, nombre, AVISO, visto, "El sitemap tiene que anunciar la dirección final de cada página, y solo páginas que se puedan leer.", ["%s → %s" % (p["url"], p["destino"]) for p in redirigen] + cerradas + ajenas)
    return _comprobacion(1, nombre, BIEN, "Las %d páginas visitadas responden 200 sin redirigir.%s" % (len(paginas), cola))


def _canonicas(leidas):
    nombre = "Cada página declara su propia dirección"
    if not leidas:
        return _comprobacion(2, nombre, SIN_COMPROBAR, "No se ha podido leer ninguna página.")
    sin = [p for p in leidas if not p["canonical"]]
    ajena = [p for p in leidas if p["canonical"] and not misma_direccion(urllib.parse.urljoin(p["url"], p["canonical"]), p["url"])]
    if ajena:
        return _comprobacion(2, nombre, FALLO, "%d de %d páginas dicen que su versión buena es otra página." % (len(ajena), len(leidas)), "Cada página tiene que llevar en su «canonical» su propia dirección. Una página que apunta a otra le está diciendo al buscador que no existe.", ["%s declara %s" % (p["url"], p["canonical"]) for p in ajena])
    if sin:
        return _comprobacion(2, nombre, AVISO, "%d de %d páginas no declaran ninguna dirección canónica." % (len(sin), len(leidas)), "Añade a cada página un «link rel=canonical» con su propia dirección.", [p["url"] for p in sin])
    return _comprobacion(2, nombre, BIEN, "Las %d páginas leídas declaran su propia dirección." % len(leidas))


def _tabla_rastreadores(grupos):
    general, _ = grupo_de(grupos, "*")
    protegidas = [ruta for regla, ruta in (general["reglas"] if general else []) if regla == "disallow" and ruta and ruta != "/"]
    tabla = []
    for agente in RASTREADORES_IA:
        grupo, propio = grupo_de(grupos, agente)
        faltan = []
        if propio:
            suyas = {ruta for regla, ruta in grupo["reglas"] if regla == "disallow"}
            faltan = [ruta for ruta in protegidas if ruta not in suyas and "/" not in suyas]
        tabla.append({"rastreador": agente, "puede_entrar": not cerrado_del_todo(grupo), "tiene_apartado_propio": propio, "protecciones_que_le_faltan": faltan})
    return tabla


def _robots(robots, grupos):
    nombre = "Los rastreadores de IA pueden entrar, y lo privado sigue cerrado"
    if robots["error"]:
        return _comprobacion(3, nombre, SIN_COMPROBAR, "No se ha podido leer robots.txt: %s." % robots["error"])
    if robots["codigo"] != 200:
        return _comprobacion(3, nombre, AVISO, "No hay robots.txt (responde %s). Nadie está bloqueado, pero tampoco hay nada protegido ni se anuncia el sitemap." % robots["codigo"], "Publica un robots.txt que declare el sitemap y cierre las rutas privadas.")
    tabla = _tabla_rastreadores(grupos)
    bloqueados = [fila["rastreador"] for fila in tabla if not fila["puede_entrar"]]
    abiertos = [fila for fila in tabla if fila["protecciones_que_le_faltan"]]
    if bloqueados:
        todos = len(bloqueados) == len(tabla)
        return _comprobacion(3, nombre, FALLO, ("robots.txt cierra la web entera a todos los rastreadores de IA." if todos else "robots.txt cierra la web entera a %d rastreador(es) de IA." % len(bloqueados)), "Quita el «Disallow: /» de esos apartados si quieres que esos asistentes puedan leer la web.", bloqueados)
    if abiertos:
        return _comprobacion(
            3,
            nombre,
            FALLO,
            "%d rastreador(es) tienen un apartado con su nombre que no repite las protecciones del apartado general. Un rastreador con apartado propio ignora el general: tiene abiertas rutas que creías cerradas." % len(abiertos),
            "Repite en cada apartado con nombre las mismas líneas «Disallow» del apartado general.",
            ["%s puede entrar en %s" % (fila["rastreador"], ", ".join(fila["protecciones_que_le_faltan"])) for fila in abiertos],
        )
    return _comprobacion(3, nombre, BIEN, "Ningún rastreador de IA está bloqueado y ninguno tiene menos protecciones que el resto.")


def _organizaciones(pagina):
    return [nodo for nodo in pagina["nodos"] if any(tipo in TIPOS_DE_ORGANIZACION or tipo.endswith("Business") for tipo in tipos(nodo)) and nodo.get("name")]


def _personas(pagina):
    """People declared with an identifier of their own: the entity of a personal brand, not every author mentioned."""
    return [nodo for nodo in pagina["nodos"] if "Person" in tipos(nodo) and nodo.get("name") and nodo.get("@id")]


def _marca(leidas, nombre_del_negocio):
    nombre = "El negocio se llama igual en todas partes"
    apariciones = {}
    for buscar in (_organizaciones, _personas):
        for pagina in leidas:
            for nodo in buscar(pagina):
                clave = str(nodo.get("@id") or "sin identificador")
                apariciones.setdefault(clave, {}).setdefault(str(nodo["name"]).strip(), []).append(pagina["url"])
        if apariciones:
            break
    if not apariciones:
        return _comprobacion(4, nombre, AVISO, "Ninguna página dice en sus datos estructurados quién es el negocio.", "Añade a la portada un bloque de datos estructurados de tipo Organization o LocalBusiness con el nombre, la dirección y el teléfono.")
    distintos = sorted({n for nombres in apariciones.values() for n in nombres})
    if len(distintos) > 1:
        mismos = [nombres for nombres in apariciones.values() if len(nombres) > 1]
        if not mismos and buscar is _personas:
            # Several people, each under an identifier of their own, is a site with several authors, not a brand with several names.
            return _comprobacion(4, nombre, BIEN, "La web declara %d personas, cada una con su identificador y un solo nombre." % len(distintos))
        return _comprobacion(4, nombre, FALLO, "El negocio aparece con %d nombres distintos en los datos estructurados." % len(distintos), "Elige una sola forma de escribir el nombre y úsala en todas las páginas.", distintos)
    if nombre_del_negocio and normalizar(nombre_del_negocio) != normalizar(distintos[0]):
        return _comprobacion(4, nombre, AVISO, "La web dice que el negocio se llama «%s» y el perfil dice «%s»." % (distintos[0], nombre_del_negocio), "Confirma cuál es el nombre con el que quieres que te encuentren y usa ese en la web.")
    return _comprobacion(4, nombre, BIEN, "Un solo nombre, «%s», en todas las páginas que lo declaran." % distintos[0])


def _datos_estructurados(leidas, canonico):
    nombre = "Las páginas llevan datos estructurados"
    if not leidas:
        return _comprobacion(5, nombre, SIN_COMPROBAR, "No se ha podido leer ninguna página.")
    rotos = [p for p in leidas if p["json_roto"]]
    sin = [p for p in leidas if not p["bloques_jsonld"]]
    if rotos:
        return _comprobacion(5, nombre, FALLO, "%d página(s) llevan un bloque de datos estructurados que no se puede leer (JSON mal formado)." % len(rotos), "Corrige el bloque: un dato estructurado que no se puede leer es como si no estuviera.", [p["url"] for p in rotos])
    if any(misma_direccion(p["url"], canonico + "/") for p in sin):
        return _comprobacion(5, nombre, FALLO, "La portada no lleva datos estructurados%s." % (" y otras %d páginas tampoco" % (len(sin) - 1) if len(sin) > 1 else ""), "Empieza por la portada: quién es el negocio, qué hace, dónde está y cómo contactar.", [p["url"] for p in sin])
    if sin:
        return _comprobacion(5, nombre, AVISO, "%d de %d páginas no llevan datos estructurados." % (len(sin), len(leidas)), "Añádelos al menos a las páginas de servicios, precios y contacto.", [p["url"] for p in sin])
    return _comprobacion(5, nombre, BIEN, "Las %d páginas leídas llevan datos estructurados." % len(leidas))


def _marcado_veraz(leidas):
    nombre = "Los datos estructurados no dicen nada que no se vea"
    declaradas, ocultas = 0, []
    for pagina in leidas:
        visible = normalizar(pagina["texto"])
        for nodo in pagina["nodos"]:
            if "Question" not in tipos(nodo) or not nodo.get("name"):
                continue
            declaradas += 1
            if normalizar(nodo["name"]) not in visible:
                ocultas.append("%s: «%s»" % (pagina["url"], str(nodo["name"])[:90]))
    if not declaradas:
        return _comprobacion(6, nombre, NO_APLICA, "Ninguna página declara preguntas frecuentes en sus datos estructurados.")
    if ocultas:
        return _comprobacion(6, nombre, FALLO, "%d de %d preguntas declaradas en los datos estructurados no están en el texto de su página." % (len(ocultas), declaradas), "Quita del marcado lo que no se pueda leer en la página, o enséñalo en la página. Declarar lo que no se ve es lo que los buscadores tratan como engaño.", ocultas)
    return _comprobacion(6, nombre, BIEN, "Las %d preguntas declaradas se leen en su página." % declaradas)


def _texto_en_html(leidas):
    nombre = "El texto está en la página sin ejecutar JavaScript"
    if not leidas:
        return _comprobacion(7, nombre, SIN_COMPROBAR, "No se ha podido leer ninguna página.")
    vacias = [p for p in leidas if p["palabras"] < PALABRAS_MIN]
    huellas = {}
    for pagina in leidas:
        if pagina["palabras"] >= PALABRAS_MIN:
            huellas.setdefault(hashlib.sha256(normalizar(pagina["texto"]).encode("utf-8")).hexdigest(), []).append(pagina["url"])
    repetidas = [urls for urls in huellas.values() if len(urls) > 1]
    if vacias:
        return _comprobacion(7, nombre, FALLO, "%d de %d páginas llegan casi vacías (menos de %d palabras) a quien no ejecuta JavaScript." % (len(vacias), len(leidas), PALABRAS_MIN), "El texto tiene que venir en el HTML que sirve el servidor. Pídeselo a quien hizo la web con estas palabras: «renderizado en servidor» o «HTML estático».", ["%s (%d palabras)" % (p["url"], p["palabras"]) for p in vacias])
    if repetidas:
        return _comprobacion(7, nombre, FALLO, "%d grupo(s) de páginas distintas sirven exactamente el mismo texto: lo que las diferencia llega solo con JavaScript." % len(repetidas), "Cada página tiene que traer su propio texto en el HTML.", [" = ".join(urls[:3]) for urls in repetidas])
    media = sum(p["palabras"] for p in leidas) // len(leidas)
    return _comprobacion(7, nombre, BIEN, "Las %d páginas traen su texto en el HTML (%d palabras de media)." % (len(leidas), media))


def _encabezados(leidas):
    nombre = "Cada página tiene un titular propio"
    if not leidas:
        return _comprobacion(8, nombre, SIN_COMPROBAR, "No se ha podido leer ninguna página.")
    sin = [p for p in leidas if not p["h1"]]
    varios = [p for p in leidas if len(p["h1"]) > 1]
    usados = {}
    for pagina in leidas:
        if len(pagina["h1"]) == 1:
            usados.setdefault(normalizar(pagina["h1"][0]), []).append(pagina["url"])
    repetidos = [urls for urls in usados.values() if len(urls) > 1]
    if sin:
        return _comprobacion(8, nombre, FALLO, "%d de %d páginas no tienen titular principal (H1)." % (len(sin), len(leidas)), "Cada página necesita un H1 que diga en una frase de qué va.", [p["url"] for p in sin])
    if repetidos:
        return _comprobacion(8, nombre, AVISO, "%d titular(es) se repiten en varias páginas: para una máquina son copias de la misma." % len(repetidos), "Dale a cada página un H1 distinto, con lo que esa página tiene de propio.", [" = ".join(urls[:3]) for urls in repetidos])
    if varios:
        return _comprobacion(8, nombre, AVISO, "%d página(s) tienen más de un titular principal." % len(varios), "Deja un solo H1 por página; el resto, como H2.", [p["url"] for p in varios])
    return _comprobacion(8, nombre, BIEN, "Las %d páginas tienen un titular principal, y todos son distintos." % len(leidas))


def _entradas(entradas):
    nombre = "Todas las entradas al dominio acaban en el mismo sitio"
    finales = {entrada["final"].rstrip("/") for entrada in entradas if entrada["final"]}
    rotas = [entrada for entrada in entradas if not entrada["final"]]
    ejemplos = ["%s → %s" % (e["url"], e["final"] or e["error"]) for e in entradas]
    if rotas:
        return _comprobacion(9, nombre, FALLO, "%d de las %d formas de escribir la dirección no llegan a la web." % (len(rotas), len(entradas)), "Todas (con «http» y con «https», y con y sin «www» si es un dominio principal) tienen que acabar en la misma dirección, con un certificado válido. Suele ser un dominio sin asignar o un certificado caducado: es cosa de quien lleva el alojamiento.", ejemplos)
    if len(finales) > 1:
        return _comprobacion(9, nombre, FALLO, "Las entradas acaban en %d direcciones distintas: la web existe duplicada." % len(finales), "Elige una dirección y redirige las demás a ella.", ejemplos)
    final = next(iter(finales))
    if not final.startswith("https://"):
        return _comprobacion(9, nombre, FALLO, "La web acaba en una dirección sin «https».", "Activa el certificado y redirige «http» a «https».", ejemplos)
    return _comprobacion(9, nombre, BIEN, "Las %d entradas acaban en %s." % (len(entradas), final))


# ---------------------------------------------------------------- output


def hojas(informe):
    resumen = [["Nº", "Comprobación", "Resultado", "Qué se ha visto", "Qué hacer", "Dónde"]]
    for c in informe["comprobaciones"]:
        resumen.append([c["numero"], c["nombre"], c["resultado"].upper(), c["visto"], c["arreglo"], "\n".join(c["ejemplos"])])
    paginas = [["Página", "Código", "Titular (H1)", "Palabras sin JavaScript", "Declara como dirección propia", "Datos estructurados", "Nota"]]
    for p in informe["paginas"]:
        tipos_vistos = sorted({t for nodo in p.get("nodos", []) for t in tipos(nodo)})
        nota = p["error"] or (("redirige a %s" % p["destino"]) if p["destino"] else "") or ("pide no indexarse (noindex)" if p.get("noindex") else "")
        paginas.append([p["url"], p["codigo"], " | ".join(p.get("h1", [])), p.get("palabras"), p.get("canonical") or "", ", ".join(tipos_vistos), nota])
    robots = [["Rastreador", "Puede entrar", "Tiene apartado propio", "Rutas protegidas que tiene abiertas"]]
    for fila in informe["rastreadores"]:
        robots.append([fila["rastreador"], fila["puede_entrar"], fila["tiene_apartado_propio"], ", ".join(fila["protecciones_que_le_faltan"])])
    return [
        {"nombre": "Resumen", "filas": resumen, "formatos": {0: "entero", 1: "texto", 3: "texto", 4: "texto", 5: "texto"}, "anchos": [5, 40, 16, 60, 60, 60]},
        {"nombre": "Páginas", "filas": paginas, "formatos": {1: "entero", 2: "texto", 3: "entero", 5: "texto", 6: "texto"}, "anchos": [50, 9, 40, 12, 50, 30, 36]},
        {"nombre": "Rastreadores", "filas": robots, "anchos": [24, 14, 22, 50]},
    ]


def main(argumentos=None):
    analizador = argparse.ArgumentParser(description="Nueve comprobaciones de si un asistente de IA puede encontrar y leer una web.")
    analizador.add_argument("web", help="dirección de la web, con o sin https://")
    analizador.add_argument("--nombre", help="nombre del negocio, para compararlo con el que declara la web (clave `nombre` del perfil)")
    analizador.add_argument("--max-paginas", type=int, default=MAX_PAGINAS, help="páginas del sitemap que se visitan (por defecto %d)" % MAX_PAGINAS)
    analizador.add_argument("--salida", help="ruta del .xlsx; sin ella solo se imprime el resumen")
    analizador.add_argument("--pausa", type=float, default=PAUSA_SEGUNDOS, help="segundos entre peticiones (por defecto %s); súbela si la web empieza a responder 429 o 403" % PAUSA_SEGUNDOS)
    opciones = analizador.parse_args(argumentos)
    if not 1 <= opciones.max_paginas <= 200:
        analizador.error("--max-paginas tiene que estar entre 1 y 200")
    if not 0 <= opciones.pausa <= 10:
        analizador.error("--pausa tiene que estar entre 0 y 10 segundos")

    try:
        informe = auditar(opciones.web, nombre=opciones.nombre, max_paginas=opciones.max_paginas, pausa=opciones.pausa)
    except ValueError as fallo:
        print(str(fallo), file=sys.stderr)
        return 2
    if informe is None:
        print(
            "No se ha podido llegar a %s por ninguna de sus direcciones. Si la dirección es correcta, este entorno no tiene salida a internet: "
            "ejecuta la auditoría donde sí la haya." % opciones.web,
            file=sys.stderr,
        )
        return 2
    if opciones.salida:
        try:
            escribir_xlsx(opciones.salida, hojas(informe))
        except OSError as fallo:
            print("No puedo escribir %s: %s" % (opciones.salida, fallo), file=sys.stderr)
            return 2
        informe["fichero"] = opciones.salida
    # The page-by-page detail is in the workbook; the summary stays short enough to read.
    resumen = {clave: valor for clave, valor in informe.items() if clave not in ("paginas", "rastreadores")}
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

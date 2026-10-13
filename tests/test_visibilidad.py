"""The AI-visibility audit, run against two made-up sites served from memory: one sound, one with every defect."""
import json
import pathlib
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SKILL = RAIZ / "skills" / "visibilidad-en-ia"
sys.path.insert(0, str(SKILL / "scripts"))

import auditar  # noqa: E402

RELLENO = " ".join(["Hacemos muebles a medida para tiendas, hoteles y cocinas de particulares en Zaragoza."] * 8)


def pagina(h1, canonical, cuerpo=RELLENO, jsonld=None, extra=""):
    bloque = '<script type="application/ld+json">%s</script>' % json.dumps(jsonld) if jsonld is not None else ""
    enlace = '<link rel="canonical" href="%s">' % canonical if canonical else ""
    return (
        "<!doctype html><html><head><title>%s</title>%s%s"
        "<style>.x{color:red}</style></head><body><h1>%s</h1><p>%s</p>%s"
        "<script>window.__DATOS__ = 'esto no es texto visible';</script></body></html>" % (h1, enlace, bloque, h1, cuerpo, extra)
    )


def ok(cuerpo):
    return {"codigo": 200, "destino": None, "cuerpo": cuerpo, "error": None}


def a(destino, codigo=301):
    return {"codigo": codigo, "destino": destino, "cuerpo": "", "error": None}


def servidor(sitio):
    """A `pedir` that answers from a dict and records what was asked for."""
    pedidas = []

    def pedir(url):
        pedidas.append(url)
        respuesta = sitio.get(url, {"codigo": 404, "destino": None, "cuerpo": "", "error": None})
        return dict(respuesta, url=url)

    pedir.pedidas = pedidas
    return pedir


ORG = {"@context": "https://schema.org", "@type": "LocalBusiness", "@id": "https://sano.test/#negocio", "name": "Tres Robles Carpintería"}

SANO = {
    "https://sano.test/": ok(pagina("Muebles a medida en Zaragoza", "https://sano.test/", jsonld=ORG)),
    "http://sano.test/": a("https://sano.test/"),
    "https://www.sano.test/": a("https://sano.test/"),
    "http://www.sano.test/": a("https://www.sano.test/"),
    "https://sano.test/robots.txt": ok("User-agent: *\nDisallow: /panel\nDisallow: /api\n\nUser-agent: GPTBot\nDisallow: /panel\nDisallow: /api\n\nSitemap: https://sano.test/sitemap.xml\n"),
    "https://sano.test/sitemap.xml": ok(
        '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<url><loc>https://sano.test/</loc></url><url><loc>https://sano.test/cocinas</loc></url><url><loc>https://sano.test/preguntas</loc></url></urlset>"
    ),
    "https://sano.test/cocinas": ok(pagina("Cocinas a medida", "https://sano.test/cocinas", jsonld={"@graph": [ORG, {"@type": "Service", "name": "Cocinas"}]})),
    "https://sano.test/preguntas": ok(
        pagina(
            "Preguntas frecuentes",
            "https://sano.test/preguntas/",
            cuerpo=RELLENO + " ¿Cuánto tarda una cocina? Unas seis semanas desde que se toma medida.",
            jsonld={"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": "¿Cuánto tarda una cocina?", "acceptedAnswer": {"@type": "Answer", "text": "Unas seis semanas."}}]},
        )
    ),
}

ROTO = {
    "https://roto.test/": ok(pagina("Bienvenidos", "https://roto.test/", jsonld={"@type": "Organization", "@id": "#org", "name": "Roto S.L."})),
    "http://roto.test/": a("https://roto.test/"),
    "https://www.roto.test/": {"codigo": None, "destino": None, "cuerpo": "", "error": "certificado no válido (certificate has expired)"},
    "http://www.roto.test/": a("https://www.roto.test/"),
    "https://roto.test/robots.txt": ok("User-agent: *\nDisallow: /panel\nDisallow: /api\n\nUser-agent: GPTBot\nAllow: /\n\nUser-agent: CCBot\nDisallow: /\n"),
    "https://roto.test/sitemap.xml": ok(
        "<urlset><url><loc>https://roto.test/</loc></url><url><loc>https://roto.test/servicios</loc></url><url><loc>https://roto.test/precios</loc></url>"
        "<url><loc>https://roto.test/vieja</loc></url><url><loc>https://roto.test/movida</loc></url><url><loc>https://roto.test/app</loc></url>"
        "<url><loc>https://roto.test/panel/entrar</loc></url><url><loc>https://otro.test/</loc></url></urlset>"
    ),
    # Says the home page is its good version, repeats the home page heading, and names the business differently.
    "https://roto.test/servicios": ok(pagina("Bienvenidos", "https://roto.test/", jsonld={"@type": "Organization", "@id": "#org", "name": "ROTO"})),
    # No structured data, and a question declared nowhere... the FAQ lives on /precios below.
    "https://roto.test/precios": ok(
        pagina(
            "Precios",
            None,
            jsonld={"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": "¿Hay permanencia?", "acceptedAnswer": {"@type": "Answer", "text": "No."}}]},
        )
    ),
    "https://roto.test/movida": a("https://roto.test/servicios"),
    # The text arrives with JavaScript: the server sends a shell.
    "https://roto.test/app": ok('<html><head><link rel="canonical" href="https://roto.test/app"></head><body><div id="root">Cargando…</div><script>render()</script></body></html>'),
}


def comprobacion(informe, numero):
    return next(c for c in informe["comprobaciones"] if c["numero"] == numero)


class SitioSano(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pedir = servidor(SANO)
        cls.informe = auditar.auditar("https://sano.test", pedir=cls.pedir, nombre="Tres Robles Carpintería", pausa=0)

    def test_las_nueve_salen_bien(self):
        resultados = {c["numero"]: c["resultado"] for c in self.informe["comprobaciones"]}
        self.assertEqual(resultados, {n: auditar.BIEN for n in range(1, 10)}, json.dumps(self.informe["comprobaciones"], ensure_ascii=False, indent=1))

    def test_la_barra_final_no_cuenta_como_otra_direccion(self):
        self.assertEqual(comprobacion(self.informe, 2)["resultado"], auditar.BIEN)

    def test_no_pide_nada_fuera_del_sitio(self):
        self.assertTrue(all("sano.test" in url for url in self.pedir.pedidas), self.pedir.pedidas)

    def test_el_texto_de_los_scripts_no_cuenta_como_texto(self):
        portada = next(p for p in self.informe["paginas"] if p["url"] == "https://sano.test/")
        self.assertNotIn("__DATOS__", portada["texto"])
        self.assertNotIn("color:red", portada["texto"])
        self.assertEqual(portada["h1"], ["Muebles a medida en Zaragoza"])

    def test_el_libro_se_escribe(self):
        ruta = pathlib.Path(tempfile.mkdtemp()) / "informe.xlsx"
        auditar.escribir_xlsx(ruta, auditar.hojas(self.informe))
        self.assertGreater(ruta.stat().st_size, 1000)


class SitioRoto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pedir = servidor(ROTO)
        cls.informe = auditar.auditar("roto.test", pedir=cls.pedir, pausa=0)

    def test_1_el_sitemap_anuncia_paginas_que_no_estan(self):
        c = comprobacion(self.informe, 1)
        self.assertEqual(c["resultado"], auditar.FALLO)
        self.assertTrue(any("/vieja" in e for e in c["ejemplos"]))
        self.assertIn("cerradas en robots.txt", c["visto"])
        self.assertIn("otro dominio", c["visto"])

    def test_no_visita_lo_que_robots_cierra_ni_otros_dominios(self):
        self.assertNotIn("https://roto.test/panel/entrar", self.pedir.pedidas)
        self.assertFalse(any("otro.test" in url for url in self.pedir.pedidas))

    def test_2_una_pagina_dice_ser_la_portada(self):
        c = comprobacion(self.informe, 2)
        self.assertEqual(c["resultado"], auditar.FALLO)
        self.assertTrue(any("/servicios declara https://roto.test/" in e for e in c["ejemplos"]))

    def test_3_el_apartado_con_nombre_abre_lo_que_el_general_cierra(self):
        c = comprobacion(self.informe, 3)
        self.assertEqual(c["resultado"], auditar.FALLO)
        fila = {f["rastreador"]: f for f in self.informe["rastreadores"]}
        self.assertEqual(fila["GPTBot"]["protecciones_que_le_faltan"], ["/panel", "/api"])
        self.assertFalse(fila["CCBot"]["puede_entrar"])
        self.assertTrue(fila["ClaudeBot"]["puede_entrar"])
        self.assertEqual(fila["ClaudeBot"]["protecciones_que_le_faltan"], [])

    def test_4_el_negocio_tiene_dos_nombres(self):
        c = comprobacion(self.informe, 4)
        self.assertEqual(c["resultado"], auditar.FALLO)
        self.assertEqual(c["ejemplos"], ["ROTO", "Roto S.L."])

    def test_5_hay_paginas_sin_datos_estructurados(self):
        self.assertEqual(comprobacion(self.informe, 5)["resultado"], auditar.AVISO)

    def test_6_el_marcado_declara_una_pregunta_que_no_se_ve(self):
        c = comprobacion(self.informe, 6)
        self.assertEqual(c["resultado"], auditar.FALLO)
        self.assertIn("¿Hay permanencia?", c["ejemplos"][0])

    def test_7_una_pagina_llega_vacia_sin_javascript(self):
        c = comprobacion(self.informe, 7)
        self.assertEqual(c["resultado"], auditar.FALLO)
        self.assertTrue(any("/app" in e for e in c["ejemplos"]))

    def test_8_falta_un_titular(self):
        c = comprobacion(self.informe, 8)
        self.assertEqual(c["resultado"], auditar.FALLO)
        self.assertEqual(c["ejemplos"], ["https://roto.test/app"])

    def test_9_la_entrada_con_www_no_llega(self):
        c = comprobacion(self.informe, 9)
        self.assertEqual(c["resultado"], auditar.FALLO)
        self.assertTrue(any("certificado no válido" in e for e in c["ejemplos"]))

    def test_el_resumen_cuenta_los_resultados(self):
        self.assertEqual(sum(self.informe["resultado"].values()), 9)
        self.assertEqual(self.informe["resultado"][auditar.BIEN], 0)


class Piezas(unittest.TestCase):
    def test_un_rastreador_con_apartado_propio_ignora_el_general(self):
        grupos, mapas = auditar.leer_robots("User-agent: *\nDisallow: /privado\n\nUser-agent: GPTBot\nUser-agent: ClaudeBot\nAllow: /\n\nSitemap: https://x.test/s.xml\n")
        grupo, propio = auditar.grupo_de(grupos, "claudebot")
        self.assertTrue(propio)
        self.assertEqual(grupo["reglas"], [("allow", "/")])
        self.assertEqual(auditar.grupo_de(grupos, "PerplexityBot")[1], False)
        self.assertEqual(mapas, ["https://x.test/s.xml"])

    def test_disallow_vacio_no_cierra_nada(self):
        grupos, _ = auditar.leer_robots("User-agent: *\nDisallow:\n")
        self.assertFalse(auditar.cerrado_del_todo(auditar.grupo_de(grupos, "GPTBot")[0]))
        self.assertFalse(auditar.prohibida(grupos[0], "/lo-que-sea"))

    def test_gana_la_regla_mas_larga(self):
        grupos, _ = auditar.leer_robots("User-agent: *\nDisallow: /blog\nAllow: /blog/publico\n")
        self.assertTrue(auditar.prohibida(grupos[0], "/blog/borrador"))
        self.assertFalse(auditar.prohibida(grupos[0], "/blog/publico/uno"))

    def test_sin_robots_solo_avisa(self):
        sitio = dict(SANO)
        del sitio["https://sano.test/robots.txt"]
        informe = auditar.auditar("https://sano.test", pedir=servidor(sitio), pausa=0)
        self.assertEqual(comprobacion(informe, 3)["resultado"], auditar.AVISO)

    def test_sin_sitemap_se_dice_que_solo_se_miro_la_portada(self):
        sitio = {k: v for k, v in SANO.items() if not k.endswith("sitemap.xml")}
        informe = auditar.auditar("https://sano.test", pedir=servidor(sitio), pausa=0)
        self.assertEqual(comprobacion(informe, 1)["resultado"], auditar.SIN_COMPROBAR)
        self.assertEqual(informe["paginas_visitadas"], 1)

    def test_indice_de_sitemaps(self):
        sitio = dict(SANO)
        sitio["https://sano.test/sitemap.xml"] = ok('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>https://sano.test/paginas.xml</loc></sitemap></sitemapindex>')
        sitio["https://sano.test/paginas.xml"] = SANO["https://sano.test/sitemap.xml"]
        informe = auditar.auditar("https://sano.test", pedir=servidor(sitio), pausa=0)
        self.assertEqual(informe["paginas_visitadas"], 3)

    def test_el_nombre_del_perfil_que_no_coincide_avisa(self):
        informe = auditar.auditar("https://sano.test", pedir=servidor(SANO), nombre="Carpintería Olmo", pausa=0)
        self.assertEqual(comprobacion(informe, 4)["resultado"], auditar.AVISO)

    def test_una_web_inalcanzable_devuelve_none(self):
        self.assertIsNone(auditar.auditar("https://nadie.test", pedir=lambda url: {"url": url, "codigo": None, "destino": None, "cuerpo": "", "error": "no responde"}, pausa=0))

    def test_el_limite_de_paginas_se_respeta_y_se_dice(self):
        informe = auditar.auditar("https://sano.test", pedir=servidor(SANO), max_paginas=2, pausa=0)
        self.assertEqual(informe["paginas_visitadas"], 2)
        self.assertIn("2 de las 3", comprobacion(informe, 1)["visto"])

    def test_json_ld_mal_formado_es_un_fallo(self):
        sitio = dict(SANO)
        sitio["https://sano.test/cocinas"] = ok(pagina("Cocinas a medida", "https://sano.test/cocinas").replace("</head>", '<script type="application/ld+json">{"@type": "Service",}</script></head>'))
        informe = auditar.auditar("https://sano.test", pedir=servidor(sitio), pausa=0)
        self.assertEqual(comprobacion(informe, 5)["resultado"], auditar.FALLO)


class ConexionReal(unittest.TestCase):
    """`pedir` against a server on this machine: the only part the in-memory sites cannot exercise."""

    @classmethod
    def setUpClass(cls):
        import http.server
        import threading

        class Manejador(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/movida":
                    self.send_response(301)
                    self.send_header("Location", "/nueva")
                    self.end_headers()
                elif self.path == "/latin":
                    cuerpo = "<h1>Año de fundación</h1>".encode("latin-1")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=iso-8859-1")
                    self.end_headers()
                    self.wfile.write(cuerpo)
                elif self.path == "/agente":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(self.headers.get("User-Agent", "").encode("utf-8"))
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, *argumentos):
                pass

        cls.servidor = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Manejador)
        cls.base = "http://127.0.0.1:%d" % cls.servidor.server_address[1]
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()

    def test_una_redireccion_no_se_sigue_y_se_ve_a_donde_va(self):
        respuesta = auditar.pedir(self.base + "/movida")
        self.assertEqual((respuesta["codigo"], respuesta["destino"], respuesta["error"]), (301, "/nueva", None))

    def test_un_404_es_un_codigo_no_un_error(self):
        respuesta = auditar.pedir(self.base + "/no-existe")
        self.assertEqual((respuesta["codigo"], respuesta["error"]), (404, None))

    def test_se_respeta_la_codificacion_que_declara_el_servidor(self):
        self.assertEqual(auditar.leer_pagina(auditar.pedir(self.base + "/latin")["cuerpo"])["h1"], ["Año de fundación"])

    def test_la_peticion_dice_quien_es(self):
        self.assertIn("auditoria-visibilidad", auditar.pedir(self.base + "/agente")["cuerpo"])

    def test_un_servidor_que_no_existe_no_lanza_una_excepcion(self):
        respuesta = auditar.pedir("http://127.0.0.1:1/")
        self.assertIsNone(respuesta["codigo"])
        self.assertIn("no responde", respuesta["error"])


class Subdominios(unittest.TestCase):
    def test_solo_un_dominio_principal_tiene_entrada_con_www(self):
        for servidor, principal in (
            ("ejemplo.es", True),
            ("www.ejemplo.es", True),
            ("ejemplo.com.es", True),
            ("tienda.ejemplo.es", False),
            ("blog.ejemplo.com.es", False),
            ("localhost:3000", True),
        ):
            with self.subTest(servidor):
                self.assertEqual(auditar.es_dominio_principal(servidor), principal)

    def test_a_un_subdominio_no_se_le_exige_www(self):
        sitio = {
            "https://blog.sano.test/": ok(pagina("El cuaderno", "https://blog.sano.test/", jsonld={"@type": "Person", "@id": "https://blog.sano.test/#persona", "name": "Marta Olmo"})),
            "http://blog.sano.test/": a("https://blog.sano.test/"),
        }
        pedir = servidor(sitio)
        informe = auditar.auditar("https://blog.sano.test", pedir=pedir, nombre="Marta Olmo", pausa=0)
        self.assertEqual(comprobacion(informe, 9)["resultado"], auditar.BIEN)
        self.assertFalse(any("www.blog" in url for url in pedir.pedidas))

    def test_una_marca_personal_se_identifica_como_persona(self):
        sitio = {
            "https://blog.sano.test/": ok(pagina("El cuaderno", "https://blog.sano.test/", jsonld={"@type": "Person", "@id": "https://blog.sano.test/#persona", "name": "Marta Olmo"})),
            "http://blog.sano.test/": a("https://blog.sano.test/"),
        }
        informe = auditar.auditar("https://blog.sano.test", pedir=servidor(sitio), nombre="Marta Olmo", pausa=0)
        c = comprobacion(informe, 4)
        self.assertEqual(c["resultado"], auditar.BIEN)
        self.assertIn("Marta Olmo", c["visto"])

    def test_la_misma_persona_con_dos_nombres_es_un_fallo(self):
        sitio = {
            "https://blog.sano.test/": ok(pagina("El cuaderno", "https://blog.sano.test/", jsonld={"@type": "Person", "@id": "#yo", "name": "Marta Olmo"})),
            "http://blog.sano.test/": a("https://blog.sano.test/"),
            "https://blog.sano.test/sitemap.xml": ok("<urlset><url><loc>https://blog.sano.test/</loc></url><url><loc>https://blog.sano.test/sobre-mi</loc></url></urlset>"),
            "https://blog.sano.test/sobre-mi": ok(pagina("Sobre mí", "https://blog.sano.test/sobre-mi", jsonld={"@type": "Person", "@id": "#yo", "name": "M. Olmo"})),
        }
        informe = auditar.auditar("https://blog.sano.test", pedir=servidor(sitio), pausa=0)
        self.assertEqual(comprobacion(informe, 4)["resultado"], auditar.FALLO)


class ProteccionContraRobots(unittest.TestCase):
    def test_si_la_web_frena_la_auditoria_no_se_dice_que_las_paginas_no_existen(self):
        sitio = dict(SANO)
        for ruta in ("cocinas", "preguntas"):
            sitio["https://sano.test/" + ruta] = {"codigo": 429, "destino": None, "cuerpo": "", "error": None}
        informe = auditar.auditar("https://sano.test", pedir=servidor(sitio), pausa=0)
        c = comprobacion(informe, 1)
        self.assertEqual(c["resultado"], auditar.SIN_COMPROBAR)
        self.assertIn("--pausa", c["arreglo"])


if __name__ == "__main__":
    unittest.main()

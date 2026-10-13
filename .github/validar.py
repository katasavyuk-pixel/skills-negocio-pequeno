"""Checks every skill the way a strict installer reads it, and holds the README to its word.

What this guards, and why each rule exists:

- The frontmatter is valid YAML. Claude Code tolerates one that is not; `npx
  skills add` skips the skill. Version 1.0.0 shipped five like that.
- A skill folder is self-contained: SKILL.md, and only `references/`, `scripts/`,
  `assets/` and `ejemplos/` beside it. Installers copy one folder at a time.
- Every file a skill ships is reachable from its SKILL.md, and every link in
  SKILL.md points at a file that exists. A reference nobody links is never read.
- References do not link to other references: an agent that follows a chain of
  files tends to read the second one only in part.
- Scripts use the standard library only, run on Python 3.9, and do not open the
  network or start other programs unless the skill is listed in `RED` with the
  reason. The README promises exactly that, so it is checked here.
- The files several skills share are byte-identical to `comun/`.

Usage: python3 .github/validar.py
"""
import ast
import json
import pathlib
import re
import subprocess
import sys

import yaml

REPO = pathlib.Path(__file__).resolve().parent.parent
# https://agentskills.io/specification
CLAVES_PERMITIDAS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
CARPETAS_PERMITIDAS = {"references", "scripts", "assets", "ejemplos"}
# Body of SKILL.md: past this an agent stops reading it whole (Anthropic's authoring guide).
LINEAS_MAX = 500
DESCRIPCION_MAX = 1024
# The Claude apps' help centre quotes 200 characters for a description; the specification, 1,024.
# The first sentence has to say what the skill does within the stricter of the two.
PRIMERA_FRASE_MAX = 200
# A reference this long needs a table of contents, so a partial read still shows what is in it.
REFERENCIA_SIN_INDICE_MAX = 100

# Skills whose scripts may open a connection, and why. Everything else may not.
RED = {
    "visibilidad-en-ia": "descarga las páginas públicas de la web que se audita",
}
MODULOS_DE_RED = {"socket", "ssl", "urllib", "http", "ftplib", "smtplib", "poplib", "imaplib", "telnetlib", "xmlrpc", "asyncio", "webbrowser"}
MODULOS_QUE_LANZAN_PROGRAMAS = {"subprocess", "multiprocessing", "pty", "ctypes"}
# What the scripts may import: the standard library modules they actually need. A new one is added here on purpose.
STDLIB_PERMITIDA = {
    "argparse", "calendar", "collections", "csv", "dataclasses", "datetime", "decimal", "difflib", "fractions",
    "functools", "hashlib", "html", "io", "itertools", "json", "math", "operator", "os", "pathlib", "re",
    "statistics", "string", "sys", "textwrap", "time", "typing", "unicodedata", "xml", "zipfile",
}
LLAMADAS_PROHIBIDAS = {"eval", "exec", "compile", "__import__"}
ENLACE = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")

errores = []


def error(donde, mensaje):
    errores.append("%s: %s" % (donde, mensaje))


def revisar_cabecera(nombre, texto, version):
    encontrada = re.match(r"^---\n(.*?)\n---\n", texto, re.S)
    if not encontrada:
        error(nombre, "SKILL.md no tiene cabecera")
        return ""
    try:
        datos = yaml.safe_load(encontrada.group(1))
    except yaml.YAMLError as fallo:
        error(nombre, "la cabecera no es YAML válido (%s)" % str(fallo).splitlines()[0])
        return texto[encontrada.end():]
    if not isinstance(datos, dict):
        error(nombre, "la cabecera no es un mapa de claves")
        return texto[encontrada.end():]
    if set(datos) - CLAVES_PERMITIDAS:
        error(nombre, "claves fuera de la especificación: %s" % sorted(set(datos) - CLAVES_PERMITIDAS))
    if datos.get("name") != nombre:
        error(nombre, "`name` es %r y tiene que ser el nombre de la carpeta" % datos.get("name"))
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", nombre) or len(nombre) > 64:
        error(nombre, "no es un nombre de skill válido")
    if re.search(r"claude|anthropic", nombre):
        error(nombre, "el nombre no puede llevar una marca reservada")
    descripcion = datos.get("description")
    if not isinstance(descripcion, str) or not 1 <= len(descripcion) <= DESCRIPCION_MAX:
        error(nombre, "`description` tiene que ser texto de 1 a %d caracteres" % DESCRIPCION_MAX)
    else:
        primera = re.split(r"(?<=[.:])\s", descripcion, maxsplit=1)[0]
        if len(primera) > PRIMERA_FRASE_MAX:
            error(nombre, "la primera frase de `description` tiene %d caracteres; máximo %d" % (len(primera), PRIMERA_FRASE_MAX))
        if "Úsala" not in descripcion:
            error(nombre, "`description` tiene que decir cuándo se usa («Úsala cuando…»)")
    if str((datos.get("metadata") or {}).get("version")) != version:
        error(nombre, "`metadata.version` no es la versión del plugin (%s)" % version)
    return texto[encontrada.end():]


def revisar_enlaces(nombre, carpeta, cuerpo):
    enlazados = set()
    for destino in ENLACE.findall(cuerpo):
        if re.match(r"[a-z]+:", destino):
            continue
        if "\\" in destino:
            error(nombre, "ruta con barra invertida en SKILL.md: %s" % destino)
        if not (carpeta / destino).is_file():
            error(nombre, "SKILL.md enlaza %s, que no existe" % destino)
        enlazados.add(destino)
    mencionados = set(re.findall(r"(?:references|scripts|assets|ejemplos)/[\w./-]+", cuerpo))
    for fichero in sorted(path for path in carpeta.rglob("*") if path.is_file() and path.name != "SKILL.md"):
        relativo = fichero.relative_to(carpeta).as_posix()
        if "__pycache__" in relativo:
            continue
        if relativo == "scripts/hoja_xlsx.py":
            continue  # imported by the skill's own scripts, checked by sincronizar.py
        # A folder of sample documents is named once, as a folder: ejemplos/fuentes/.
        carpetas = {str(padre.as_posix()) + "/" for padre in pathlib.PurePosixPath(relativo).parents if str(padre) != "."}
        if relativo not in enlazados and relativo not in mencionados and not carpetas & mencionados:
            error(nombre, "%s no se nombra en SKILL.md: un fichero que nadie enlaza no se lee" % relativo)
    for referencia in sorted((carpeta / "references").glob("*.md")) if (carpeta / "references").is_dir() else []:
        texto = referencia.read_text(encoding="utf-8")
        for destino in ENLACE.findall(texto):
            if not re.match(r"[a-z]+:", destino):
                error(nombre, "%s enlaza %s: las referencias no enlazan otros ficheros" % (referencia.name, destino))
        if texto.count("\n") > REFERENCIA_SIN_INDICE_MAX and "## Contenido" not in texto:
            error(nombre, "%s pasa de %d líneas y no tiene «## Contenido»" % (referencia.name, REFERENCIA_SIN_INDICE_MAX))


def revisar_script(nombre, script):
    donde = "%s/scripts/%s" % (nombre, script.name)
    fuente = script.read_text(encoding="utf-8")
    try:
        # feature_version: a script that parses here also parses on the Python 3.9 of a stock macOS.
        arbol = ast.parse(fuente, feature_version=(3, 9))
    except SyntaxError as fallo:
        error(donde, "no es Python 3.9 válido (%s)" % fallo)
        return
    if not ast.get_docstring(arbol):
        error(donde, "le falta la cabecera que dice qué hace y cómo se usa")
    locales = {hermano.stem for hermano in script.parent.glob("*.py")}
    for nodo in ast.walk(arbol):
        modulos = []
        if isinstance(nodo, ast.Import):
            modulos = [alias.name for alias in nodo.names]
        elif isinstance(nodo, ast.ImportFrom):
            modulos = [nodo.module or ""]
        for modulo in modulos:
            raiz = modulo.split(".")[0]
            if raiz in locales:
                continue
            if raiz in MODULOS_DE_RED:
                if nombre not in RED:
                    error(donde, "importa `%s`: esta skill no está entre las que pueden abrir conexiones" % modulo)
                continue
            if raiz in MODULOS_QUE_LANZAN_PROGRAMAS:
                error(donde, "importa `%s`: los scripts no lanzan otros programas" % modulo)
            elif raiz not in STDLIB_PERMITIDA:
                error(donde, "importa `%s`, que no está en la lista de módulos estándar permitidos" % modulo)
        if isinstance(nodo, ast.Call):
            funcion = nodo.func
            if isinstance(funcion, ast.Name) and funcion.id in LLAMADAS_PROHIBIDAS:
                error(donde, "llama a `%s`" % funcion.id)
            if isinstance(funcion, ast.Attribute) and isinstance(funcion.value, ast.Name) and funcion.value.id == "os":
                if funcion.attr in {"system", "popen", "remove", "unlink", "rmdir", "removedirs"} or funcion.attr.startswith(("exec", "spawn")):
                    error(donde, "llama a `os.%s`" % funcion.attr)


def main():
    plugin = json.loads((REPO / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    mercado = json.loads((REPO / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    version = plugin["version"]
    if plugin["name"] not in [entrada["name"] for entrada in mercado["plugins"]]:
        error("marketplace.json", "no lista el plugin %r" % plugin["name"])
    # The Claude app only takes a path inside the repository when it starts with
    # "./". With "." (which Claude Code and the skills CLI accept) it answers
    # "External plugin sources must be objects with a 'source' field" and the
    # marketplace cannot be added. Seen on 13 Oct 2026, with version 2.0.0.
    for entrada in mercado["plugins"]:
        origen = entrada.get("source")
        if isinstance(origen, str) and not origen.startswith("./"):
            error(
                "marketplace.json",
                "el `source` de %r es %r: tiene que empezar por \"./\" o la aplicación de Claude no sincroniza el repositorio"
                % (entrada["name"], origen),
            )
    # A top-level bin/ makes the Claude apps refuse the plugin.
    if (REPO / "bin").exists():
        error("repositorio", "una carpeta bin/ en la raíz impide instalar el plugin en las aplicaciones de Claude")

    carpetas = sorted(path for path in (REPO / "skills").iterdir() if path.is_dir())
    if not carpetas:
        error("skills", "no hay ninguna skill")
    for carpeta in carpetas:
        nombre = carpeta.name
        if not (carpeta / "SKILL.md").is_file():
            error(nombre, "falta SKILL.md")
            continue
        for hijo in carpeta.iterdir():
            if hijo.name == "SKILL.md" or hijo.name == "__pycache__":
                continue
            if not hijo.is_dir() or hijo.name not in CARPETAS_PERMITIDAS:
                error(nombre, "%s: junto a SKILL.md solo van %s" % (hijo.name, ", ".join(sorted(CARPETAS_PERMITIDAS))))
        texto = (carpeta / "SKILL.md").read_text(encoding="utf-8")
        cuerpo = revisar_cabecera(nombre, texto, version)
        if cuerpo.count("\n") > LINEAS_MAX:
            error(nombre, "SKILL.md tiene %d líneas; máximo %d" % (cuerpo.count("\n"), LINEAS_MAX))
        revisar_enlaces(nombre, carpeta, cuerpo)
        for script in sorted((carpeta / "scripts").glob("*.py")) if (carpeta / "scripts").is_dir() else []:
            revisar_script(nombre, script)
    for skill in RED:
        if not (REPO / "skills" / skill).is_dir():
            # Not an error while the skill is being written, but a stale entry would be a standing permission.
            print("aviso: RED nombra %s, que no existe" % skill)

    copias = subprocess.run([sys.executable, str(REPO / ".github" / "sincronizar.py"), "--comprobar"], capture_output=True, text=True)
    for linea in copias.stdout.splitlines():
        error("copias", linea.strip(" -"))

    print("%d skills, versión %s, %d errores" % (len(carpetas), version, len(errores)))
    for linea in errores:
        print(" - " + linea)
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())

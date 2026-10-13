"""Copies the shared files in `comun/` into every skill that carries them.

A skill is installed on its own: `npx skills add` copies one folder and nothing
outside it. So what several skills share (how to read the business profile, the
workbook writer) cannot live in one place; each skill carries its own copy.
`comun/` is where those files are edited, this script is how the copies are
made, and `.github/validar.py` fails when a copy has drifted.

Usage: python3 .github/sincronizar.py            (copy)
       python3 .github/sincronizar.py --comprobar (report drift, change nothing)
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent

# file in comun/ -> where it goes inside a skill folder
DESTINO = {
    "perfil.md": "references/perfil.md",
    "hoja_xlsx.py": "scripts/hoja_xlsx.py",
}


def copias():
    """Yields (source, copy) for every skill that already carries the file, plus the profile guide for all."""
    for carpeta in sorted(path for path in (REPO / "skills").iterdir() if path.is_dir()):
        for nombre, destino in DESTINO.items():
            copia = carpeta / destino
            # Every skill reads the profile. The workbook writer goes only where a script imports it.
            necesaria = nombre == "perfil.md" or any(
                "hoja_xlsx" in script.read_text(encoding="utf-8")
                for script in (carpeta / "scripts").glob("*.py")
                if script.name != "hoja_xlsx.py"
            )
            if necesaria or copia.exists():
                yield REPO / "comun" / nombre, copia, necesaria


def main():
    comprobar = "--comprobar" in sys.argv[1:]
    desviadas = []
    for origen, copia, necesaria in copias():
        if not necesaria:
            desviadas.append("%s: sobra, ningún script de la skill lo usa" % copia.relative_to(REPO))
            continue
        contenido = origen.read_bytes()
        if copia.exists() and copia.read_bytes() == contenido:
            continue
        if comprobar:
            desviadas.append("%s: no coincide con comun/%s" % (copia.relative_to(REPO), origen.name))
        else:
            copia.parent.mkdir(parents=True, exist_ok=True)
            copia.write_bytes(contenido)
            print("copiado", copia.relative_to(REPO))
    for linea in desviadas:
        print(" -", linea)
    return 1 if desviadas else 0


if __name__ == "__main__":
    sys.exit(main())

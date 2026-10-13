---
name: visibilidad-en-ia
description: 'Audita si los asistentes de IA y sus buscadores pueden encontrar y leer la web de un negocio: nueve comprobaciones con resultado y arreglo, en una hoja de Excel. Úsala cuando pidan "que ChatGPT me recomiende", "no aparezco en la IA", "auditoría GEO", "revisa mi web para la IA", "robots.txt para IA" o "por qué no me encuentran", y antes y después de rehacer una web.'
license: MIT
metadata:
  author: Kata Ivanovych
  version: "2.0.0"
---

# Visibilidad en IA

Entrega dos cosas: `visibilidad-en-ia.xlsx`, con nueve comprobaciones, cada una con lo que se ha visto y qué hacer, y un resumen corto, en seis partes, ordenado por lo que más daño hace.

Las comprobaciones las hace `scripts/auditar.py`, leyendo la web como la lee un rastreador: peticiones sueltas, sin ejecutar JavaScript, sin navegador. Tu trabajo es ejecutarlo, explicar el resultado en el idioma de quien lleva el negocio y decir a quién hay que pedirle cada arreglo.

**Esto comprueba que una IA pueda leer la web. No hace que la recomiende, y nada de lo que entregues puede prometerlo.**

## Flujo

1. Leer el perfil del negocio
2. Ejecutar la auditoría
3. Leer el resultado con la guía
4. Entregar la hoja y el resumen

### 1. Leer el perfil del negocio

Como indica [references/perfil.md](references/perfil.md). Esta skill usa:

| Dato | Para qué |
| --- | --- |
| `web` | La dirección que se audita. Si está pendiente, pregúntala. Si es `no`, no hay nada que auditar: dilo y para. |
| `nombre` | Se compara con el nombre que declara la web (`--nombre`). |
| `quien_configura` | Si es `asesor`, los arreglos se explican para quien los va a hacer; si no, para quien tiene que encargarlos. |

Audita solo la web del negocio. Si piden auditar la de un competidor, se puede: son páginas públicas y la auditoría solo las lee. Dilo en el resumen.

### 2. Ejecutar la auditoría

Desde la carpeta de esta skill:

```bash
python3 scripts/auditar.py https://DOMINIO --nombre "NOMBRE DEL NEGOCIO" --salida RUTA/visibilidad-en-ia.xlsx
```

- Visita hasta 30 páginas del sitemap, con medio segundo entre peticiones. Si el sitemap tiene más, el resumen lo dice: ofrece repetirla con `--max-paginas` y el número que haga falta.
- Termina con código 2 si no llega a la web por ninguna dirección. Si la dirección es correcta, este entorno no tiene salida a internet: dilo y propón ejecutarla en un entorno que la tenga. No hagas la auditoría a mano con otra herramienta y la presentes como equivalente.
- Si la comprobación 1 sale «sin comprobar» porque la web ha rechazado peticiones, repite con `--pausa 2`.
- El script imprime un resumen en JSON. Lo que cuentes sale de ahí y de la hoja.

### 3. Leer el resultado con la guía

Qué significa cada comprobación, por qué importa, cómo se arregla y a quién se le pide está en [references/las-nueve-comprobaciones.md](references/las-nueve-comprobaciones.md). Léelo antes de escribir el resumen.

Cada comprobación sale con uno de estos resultados:

| Resultado | Qué significa |
| --- | --- |
| `fallo` | Hay un problema concreto que impide o estropea la lectura. |
| `aviso` | Funciona, pero se pierde algo. |
| `bien` | Comprobado y correcto. |
| `sin comprobar` | No se ha podido mirar. Se dice, no se da por bueno. |
| `no aplica` | La web no usa eso. |

### 4. Entregar

La hoja y un resumen con la estructura de [references/como-contarlo.md](references/como-contarlo.md).

## Lo que no hace

- No cambia nada en la web. Lee y dice qué cambiar.
- No promete que el negocio vaya a aparecer ni a ser recomendado. Quien lo promete miente.
- No entra en zonas privadas, no rellena formularios y no visita lo que `robots.txt` cierra.
- No mide si un asistente recomienda ya el negocio. Eso se comprueba preguntándoselo, y la guía dice cómo.

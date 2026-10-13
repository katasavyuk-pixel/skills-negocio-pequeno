---
name: cerrar-trimestre
description: 'Revisa las facturas emitidas y recibidas de un trimestre antes de entregarlas a quien presenta los impuestos: encuentra los errores, suma el IVA por tipo y da los plazos, en una hoja de Excel. Úsala cuando pidan "cierra el trimestre", "prepara el IVA", "revisa las facturas del trimestre", "qué le mando a la gestoría", "modelo 303" o "se acerca el día 20", y al acabar marzo, junio, septiembre y diciembre.'
license: MIT
metadata:
  author: Kata Ivanovych
  version: "2.0.1"
---

# Cerrar el trimestre

Entrega dos cosas: `trimestre.xlsx`, con lo que hay que corregir, el IVA por tipo, los plazos y los dos libros; y un resumen de cinco bloques que dice qué arreglar antes de entregar nada.

El trimestre cuesta horas porque los errores los encuentra la gestoría, días después y de uno en uno: un total que no suma, un NIF con la letra cambiada, un hueco en la numeración, la factura de marzo de un proveedor que sí está en enero y en febrero. Todo eso lo encuentra una máquina la misma tarde.

Las comprobaciones y las sumas las hace `scripts/revisar.py`. **Esta skill no presenta ningún impuesto ni decide qué es deducible**: deja los libros limpios para quien lo hace.

## Flujo

Copia esta lista y márcala según avances:

```
- [ ] 1. Leer el perfil del negocio
- [ ] 2. Reunir las facturas emitidas y recibidas del trimestre
- [ ] 3. Escribir emitidas.csv y recibidas.csv
- [ ] 4. Ejecutar el script hasta que no dé errores de lectura
- [ ] 5. Repasar con la persona lo que hay que corregir
- [ ] 6. Entregar la hoja y el resumen
```

### 1. Leer el perfil del negocio

Como indica [references/perfil.md](references/perfil.md). Esta skill usa:

| Dato | Para qué |
| --- | --- |
| `territorio` | Si no es `comun`, ejecuta con `--sin-calendario-fiscal` y dilo: los plazos y los modelos son otros. En `canarias` y `ceuta_melilla` no hay IVA: las comprobaciones de facturas valen, las sumas de IVA no. |
| `forma` | Un autónomo tiene además el pago fraccionado del IRPF; una sociedad, no. Se nombra el plazo que le toca. |
| `iva` | Si es `exento`, no hay IVA que sumar: la revisión de facturas sigue sirviendo. Si es `recargo_equivalencia`, dilo: en ese régimen el IVA no se liquida como en el general, y las sumas quedan solo como información. |
| `gestoria` | Si es `si`, el resumen se escribe para reenviarlo. Si es `no`, se dice dos veces que esto no es la declaración. |

### 2. Reunir las facturas

Las emitidas y las recibidas del trimestre, como salgan de su programa o de su carpeta: una exportación, una hoja, los PDF. Si faltan las recibidas, se puede revisar solo las emitidas, y se dice.

Si tienes las facturas delante (PDF o imágenes) y no solo un listado, comprueba además lo que un listado no enseña, con [references/lo-que-se-comprueba.md](references/lo-que-se-comprueba.md): que cada factura lleve todos sus datos obligatorios.

### 3. Escribir los dos CSV

El formato y cómo convertir lo que te den están en [references/formato-csv.md](references/formato-csv.md). Copia los importes como están en la factura: **no corrijas ni recalcules nada al pasarlos**. Si corriges un error al copiar, el script no lo ve y la factura sigue mal.

### 4. Ejecutar el script

Desde la carpeta de esta skill:

```bash
python3 scripts/revisar.py --trimestre 2026-3 --emitidas RUTA/emitidas.csv \
    --recibidas RUTA/recibidas.csv --salida RUTA/trimestre-2026-3.xlsx
```

- `--trimestre` es el año y el número: `2026-3` es de julio a septiembre.
- Si lista problemas de los listados, cada uno trae su libro y su línea: son errores de copia tuyos. Corrige el CSV y vuelve a ejecutar.
- Termina bien aunque encuentre cien errores en las facturas: encontrarlos es su trabajo.
- Si no puedes ejecutar Python, dilo. No entregues sumas de IVA hechas a mano.

### 5. Repasar lo que hay que corregir

Qué significa cada hallazgo y cómo se arregla está en [references/lo-que-se-comprueba.md](references/lo-que-se-comprueba.md). Léelo antes de contar nada.

- Los **errores** se corrigen antes de entregar: una factura con un error se rectifica, no se retoca.
- Los **avisos** se confirman con la persona: casi todos tienen una explicación, y hay que tenerla.
- Las **posibles facturas que faltan** se preguntan una a una.

El resumen del paso 6 es ese repaso: se entrega con la hoja, que es provisional mientras queden errores. Cuando la persona corrija o conteste, cambia el CSV y vuelve al paso 4.

Los listados originales no se tocan: los CSV son una copia para la revisión.

### 6. Entregar

La hoja y un resumen con la estructura de [references/como-contarlo.md](references/como-contarlo.md).

## Un ejemplo resuelto

[ejemplos/emitidas.csv](ejemplos/emitidas.csv) y [ejemplos/recibidas.csv](ejemplos/recibidas.csv) son el tercer trimestre de 2026 de una carpintería, con defectos puestos a propósito. El script devuelve [ejemplos/resumen.json](ejemplos/resumen.json): cinco errores (un NIF con el dígito de control mal, una cuota que no corresponde a su base, una factura sin NIF del cliente, una factura de proveedor apuntada dos veces y un total que no suma), cuatro avisos (un hueco en la numeración, dos fechas desordenadas, una factura de octubre y un proveedor extranjero) y dos facturas que probablemente faltan.

## Lo que no hace

- No presenta nada ni rellena ningún modelo.
- No decide qué gasto es deducible ni en qué porcentaje.
- No aplica prorrata, bienes de inversión, criterio de caja ni regímenes especiales.
- No da asesoramiento fiscal. Encuentra errores de forma y de suma, y lo dice.
- No corrige una factura: dice cuál hay que rectificar.

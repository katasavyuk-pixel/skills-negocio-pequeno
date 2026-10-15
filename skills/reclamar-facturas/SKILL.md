---
name: reclamar-facturas
description: 'Calcula lo que le deben a un negocio por facturas pagadas tarde, con los intereses de demora y los 40 euros por factura que la ley añade, y redacta la reclamación que toca a cada cliente. Úsala cuando pidan "qué facturas tengo sin cobrar", "reclama esta factura", "me pagan tarde", "intereses de demora", "carta de reclamación", "burofax" o "cuánto me deben", y en el repaso semanal de cobros.'
license: MIT
metadata:
  author: Kata Ivanovych
  version: "2.1.0"
---

# Reclamar facturas

Entrega tres cosas: `reclamacion.xlsx`, con cada factura vencida, sus intereses y su total; un resumen en cinco bloques con lo que se debe y lo que la ley añade; y el borrador de la reclamación que toca a cada cliente, listo para que la persona lo revise y lo mande.

Entre empresas, la ley añade a una factura pagada tarde un interés (el 10,40 % anual en el segundo semestre de 2026) y 40 euros por factura, sin necesidad de haberlo pactado ni de haber avisado. Casi nadie lo reclama. Esta skill lo calcula al céntimo y lo pone en la carta, con su artículo.

Las cuentas las hace `scripts/calcular.py`. No calcules un interés a mano ni redondees una cifra del script. Nada sale de aquí sin que la persona lo mande: esta skill no envía.

## Flujo

Copia esta lista y márcala según avances:

```
- [ ] 1. Leer el perfil del negocio
- [ ] 2. Reunir las facturas sin cobrar
- [ ] 3. Escribir facturas.csv
- [ ] 4. Ejecutar el script hasta que no dé errores
- [ ] 5. Contar el resultado
- [ ] 6. Decidir con la persona qué se reclama a cada cliente
- [ ] 7. Redactar las reclamaciones
```

### 1. Leer el perfil del negocio

Como indica [references/perfil.md](references/perfil.md). Esta skill usa:

| Dato | Para qué |
| --- | --- |
| `clientes` | Si es `particulares`, la ley de morosidad no se aplica a ninguna factura: dilo antes de empezar. Se pueden hacer recordatorios, sin intereses. |
| `plazo_cobro_dias` | El vencimiento de las facturas que no lo dicen (`--plazo-dias`). |
| `trato`, `firma`, `nombre` | El tono y la firma de cada carta. |
| `cobro` | Si es `al_momento`, pregunta qué facturas hay: lo normal es que no haya ninguna. |

### 2. Reunir las facturas sin cobrar

Pide el listado tal como lo saque su programa o su hoja. De cada factura hacen falta: cliente, número, fecha, vencimiento si lo tiene, lo que queda por cobrar y cuántos avisos se han mandado ya. Si no sabe los avisos de alguna, pregunta por las más antiguas; a las demás, cero.

Pregunta también, una sola vez y en el mismo mensaje:

- Si cada cliente es una empresa o autónomo, un particular o una Administración. De eso depende todo lo demás, y no se deduce del nombre.
- Si alguna factura está discutida (el cliente se queja del trabajo, del precio o de la entrega) o corresponde a un trabajo sin entregar. Esas no se reclaman aquí.
- Si ha entrado algún pago desde que se sacó el listado.

### 3. Escribir facturas.csv

El formato y cómo convertir lo que te den están en [references/formato-csv.md](references/formato-csv.md).

### 4. Ejecutar el script

Desde la carpeta de esta skill:

```bash
python3 scripts/calcular.py RUTA/facturas.csv --hasta 2026-10-13 --plazo-dias 30 \
    --salida RUTA/reclamacion.xlsx
```

- `--hasta` es hoy. `--plazo-dias` es el `plazo_cobro_dias` del perfil; si está pendiente, no lo pongas.
- Los tipos de interés de cada semestre están en `assets/tipos-demora.json`, cada uno con la resolución del BOE de la que sale. El script los lee solo.
- Si lista problemas del CSV, cada uno trae su línea: corrige y vuelve a ejecutar.
- **Si dice que falta el tipo de demora de un semestre, no lo supongas.** Búscalo en el BOE como explica [references/la-ley.md](references/la-ley.md), y vuelve a ejecutar con `--tipo AAAA-S=TIPO`. Si no puedes consultarlo, dilo y para.
- Si no puedes ejecutar Python, dilo y no des cifras de intereses: un interés aproximado en una carta es peor que no ponerlo.

### 5. Contar el resultado

Con la estructura de [references/como-contarlo.md](references/como-contarlo.md). Antes de escribirlo, lee [references/la-ley.md](references/la-ley.md): dice qué da la ley, a quién, y qué puntos no están cerrados.

### 6. Decidir con la persona

Los intereses y los 40 euros son suyos, y reclamarlos o no es decisión suya, cliente a cliente. Pregúntalo para los clientes cuya reclamación vayas a redactar, con estas tres opciones:

1. Reclamar todo: importe, intereses y compensación.
2. Reclamar el importe y ofrecer renunciar a lo demás si paga en un plazo corto. Es lo que más cobra sin romper la relación.
3. Reclamar solo el importe.

Si no contesta, redacta la opción 2.

### 7. Redactar las reclamaciones

Una por cliente, con todas sus facturas vencidas, en la fase que el script indica en `que_toca`. Las tres fases, qué tiene que llevar cada una y cómo se envía están en [references/las-tres-cartas.md](references/las-tres-cartas.md).

La tercera fase no es una carta más dura: es el documento que hará falta enseñar en el juzgado si el cliente no paga. Léela entera antes de redactarla.

Si la persona pregunta qué pasa si aun así no pagan, la respuesta está en [references/si-no-pagan.md](references/si-no-pagan.md).

## Un ejemplo resuelto

[ejemplos/facturas.csv](ejemplos/facturas.csv) son seis facturas de una carpintería, calculadas al 13 de octubre de 2026. El script devuelve [ejemplos/resumen.json](ejemplos/resumen.json): 15.605,00 € pendientes en cuatro facturas vencidas, y 417,86 € que la ley añade (297,86 € de intereses y 120,00 € de compensación). Una factura vence a 90 días y la ley solo admite 60: el retraso se cuenta desde el día 60. Otra es de un particular y no lleva intereses. Otra es de un ayuntamiento y no se calcula.

## Lo que no hace

- No envía nada. Deja borradores.
- No da asesoramiento jurídico ni sustituye a un abogado. Calcula con las normas que cita y lo dice.
- No amenaza con nada que la persona no haya decidido hacer.
- No calcula deudas de una Administración ni de un cliente en concurso de acreedores.
- No da por buena una deuda discutida: si el cliente dice que el trabajo está mal, eso se resuelve antes de reclamar intereses.

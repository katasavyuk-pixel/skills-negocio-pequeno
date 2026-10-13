# El formato de emitidas.csv y recibidas.csv

Los dos listados tienen las mismas columnas. El script los rechaza con el libro y la línea exactos si algo no encaja.

**Regla que manda sobre todas: se copia lo que dice la factura, aunque esté mal.** Si una cuota no cuadra y la arreglas al copiarla, el error sigue en la factura y nadie se entera.

## Las columnas

Primera línea:

```
numero,fecha,nif,nombre,base,tipo_iva,cuota_iva,retencion,total
```

Se pueden añadir, al final y en cualquier orden, `serie`, `recargo` y `simplificada`.

| Columna | Qué va | Ejemplo |
| --- | --- | --- |
| `numero` | El número tal como está impreso. | `2026-031` |
| `fecha` | La fecha de la factura, `AAAA-MM-DD`. | `2026-08-29` |
| `nif` | El del otro: el cliente en las emitidas, el proveedor en las recibidas. Tal como está escrito, con sus erratas. Vacío si no lo lleva. | `B00000018` |
| `nombre` | El del otro. Si lleva coma, entre comillas dobles. | `Hotel Mirador` |
| `base` | La base imponible a ese tipo. Negativa en una rectificativa. | `3000.00` |
| `tipo_iva` | El tipo como número, sin el signo de porcentaje. | `21` |
| `cuota_iva` | La cuota de IVA a ese tipo. | `630.00` |
| `retencion` | La retención de IRPF de la factura entera, en positivo. `0` si no lleva. | `0` |
| `total` | El total de la factura entera. | `3630.00` |
| `serie` | Opcional. La serie, si el negocio usa varias. | `R` |
| `recargo` | Opcional. La cuota de recargo de equivalencia a ese tipo. | `52.00` |
| `simplificada` | Opcional. `si` en un tique o factura simplificada. | `si` |

Importes con punto decimal, sin separador de miles ni símbolo.

## Una factura con varios tipos de IVA

Una línea por tipo, con el mismo `numero`, el mismo `nif`, y `retencion` y `total` repetidos:

```
2026-032,2026-09-15,B00111112,Zapatería Paso,800.00,21,168.00,0,1188.00
2026-032,2026-09-15,B00111112,Zapatería Paso,200.00,10,20.00,0,1188.00
```

Dos líneas con el mismo número, el mismo NIF **y el mismo tipo** no son dos tipos: el script las toma por la misma factura apuntada dos veces.

## Cómo convertir lo que te den

| Lo que te dan | Cómo se apunta |
| --- | --- |
| Fecha `29/08/2026` | `2026-08-29` |
| Importe `3.630,00 €` | `3630.00` |
| Tipo `21 %` | `21` |
| Factura exenta o sin IVA | `tipo_iva` `0`, `cuota_iva` `0.00` |
| Factura con retención del 15 % | En `retencion`, el importe retenido, no el porcentaje. |
| Tique sin datos del cliente | `nif` vacío, `simplificada` `si` |
| Rectificativa | Importes en negativo, en su serie. |
| Factura de un proveedor de otro país | El NIF con el código del país delante (`IE1234567X`), `tipo_iva` `0` si no trae IVA. |
| Suplidos, tasas o conceptos sin IVA dentro de una factura con IVA | Una línea aparte con `tipo_iva` `0`. |
| Listado que solo trae el total | No se inventa el desglose. Se pide el listado con base y cuota, o las facturas. |

## Qué va en cada libro

- **Emitidas**: todas las facturas y tiques que el negocio ha emitido con fecha del trimestre, anuladas y rectificativas incluidas. Si falta una, el script verá el hueco.
- **Recibidas**: las facturas de gastos y compras con fecha del trimestre, y las de trimestres anteriores que hayan llegado tarde. No van nóminas, seguros sociales, recibos del banco ni nada que no sea una factura.

## Lo que el script no puede ver

- **Un importe mal leído de un PDF o una foto.** Si un número no se lee con seguridad, se pregunta.
- **Una factura que no está en el listado** y cuyo número no deja hueco: la última del trimestre, o cualquier recibida.
- **Lo que la factura dice además de las cifras**: el domicilio, la descripción, la mención de exención. Eso se comprueba con la factura delante.

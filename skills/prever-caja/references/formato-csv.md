# El formato de movimientos.csv

El script solo entiende este formato, y lo rechaza con la línea exacta si algo no encaja. Es estricto a propósito: un importe mal leído no da error, da una previsión equivocada.

## Contenido

- Las columnas
- Cómo convertir cada cosa
- Lo que se repite
- Errores que el script no puede ver

## Las columnas

Primera línea, tal cual:

```
fecha,concepto,importe,tercero,repite
```

| Columna | Qué va | Ejemplo |
| --- | --- | --- |
| `fecha` | El día en que el dinero se mueve, `AAAA-MM-DD` | `2026-11-10` |
| `concepto` | Qué es. Si lleva una coma, entre comillas dobles | `Factura 2026-038` |
| `importe` | Positivo si entra, negativo si sale. Punto decimal, sin separador de miles ni símbolo | `14520.00`, `-1450.00` |
| `tercero` | Quién paga o cobra. Puede ir vacío | `Hotel Mirador` |
| `repite` | `no`, `mensual` o `trimestral` | `mensual` |

Escribe el nombre de cada cliente siempre igual: el script agrupa por `tercero` para saber cuánto depende la caja de cada uno.

## Cómo convertir cada cosa

| Lo que te dan | Cómo se apunta |
| --- | --- |
| Factura emitida con vencimiento | `fecha` = el vencimiento. Importe con IVA, menos la retención si la lleva. |
| Factura emitida sin vencimiento | `fecha` = fecha de la factura + `plazo_cobro_dias` del perfil. Si el perfil no lo tiene, se pregunta. |
| Factura ya vencida y sin cobrar | Se apunta con su vencimiento real, aunque sea pasado. El script la detecta, la cuenta esta semana y avisa. |
| Factura con fecha posterior al día del saldo | Es un trabajo sin entregar o un error de fecha: pregunta cuál. Si es un trabajo comprometido, se apunta en su vencimiento. |
| Venta acordada pero sin facturar (una señal, un presupuesto aceptado) | Se apunta en la fecha que dé la persona, con «previsión» en el concepto, y se nombra en el resumen. |
| Venta a particulares que se cobra en el momento | No se apunta factura a factura. Una línea por semana o por mes con la venta esperada, y se dice en el resumen de dónde sale esa cifra. |
| Factura de proveedor | `fecha` = el día en que se va a pagar. Importe negativo, con IVA. |
| Nómina, alquiler, cuota de préstamo | Una sola línea con el próximo cargo y `repite: mensual`. |
| Impuesto del trimestre con importe conocido | Una línea en su fecha de vencimiento, con el modelo en el concepto (`IVA 3T modelo 303`). |
| Importe en formato español (`1.234,56 €`) | `1234.56` |

## Lo que se repite

- `mensual` repite el mismo día cada mes hasta el final del periodo. El día 31 se ajusta al último día de los meses cortos.
- `trimestral` repite cada tres meses.
- La `fecha` de una línea que se repite es **el próximo cargo**, no el primero que hubo. Si pones una fecha pasada, el script cuenta solo los cargos que quedan por venir.
- Un gasto que se repite pero cambia de importe (una paga extra, un seguro anual) va en líneas sueltas con `repite: no`.

## Errores que el script no puede ver

Compruébalos tú antes de ejecutar:

- **El mismo dinero dos veces.** Una factura que está en la lista de pendientes y también, ya cobrada, dentro del saldo. O un gasto fijo apuntado como `mensual` y además como factura de proveedor.
- **Importes sin IVA.** La lista de facturas de un programa suele traer base e importe total: se usa el total.
- **Signo cambiado.** Un pago en positivo sube la caja. Repasa que todo lo que sale lleva el signo menos.
- **Cobros que no son seguros.** Un presupuesto sin aceptar no es un cobro y no se apunta.

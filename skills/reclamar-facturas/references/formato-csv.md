# El formato de facturas.csv

El script solo entiende este formato y rechaza con la línea exacta lo que no encaja. Es estricto a propósito: un importe mal leído acaba en una carta.

## Las columnas

Primera línea:

```
cliente,numero,fecha_factura,vencimiento,importe,tipo_cliente,avisos
```

Se pueden añadir, al final y en cualquier orden, `entrega` y `base`.

| Columna | Qué va | Ejemplo |
| --- | --- | --- |
| `cliente` | Quién debe. Siempre escrito igual: el script agrupa por cliente. Si lleva coma, entre comillas dobles. | `Hotel Mirador` |
| `numero` | El número de la factura. | `2026-031` |
| `fecha_factura` | `AAAA-MM-DD` | `2026-08-29` |
| `vencimiento` | `AAAA-MM-DD`, o vacío si la factura no dice cuándo vence. | `2026-09-28` |
| `importe` | Lo que queda por cobrar de esa factura, con IVA. Punto decimal, sin separador de miles ni símbolo. | `3630.00` |
| `tipo_cliente` | `empresa` (también un autónomo), `particular` o `administracion`. | `empresa` |
| `avisos` | Cuántas veces se ha reclamado ya esa factura por escrito: `0`, `1`, `2`… | `1` |
| `entrega` | Opcional. El día en que se entregó el trabajo, si no es el de la factura. | `2026-08-20` |
| `base` | Opcional. Lo que queda por cobrar sin IVA, para ver también el interés sobre esa base. | `3000.00` |

## Cómo convertir lo que te den

| Lo que te dan | Cómo se apunta |
| --- | --- |
| Fecha `28/09/2026` | `2026-09-28` |
| Importe `3.630,00 €` | `3630.00` |
| Factura cobrada en parte | En `importe`, solo lo que falta. En `base`, la parte proporcional sin IVA, o vacío. |
| Factura con retención de IRPF | `importe` es lo que el cliente tiene que pagar: el total menos la retención. |
| «A 30 días» sin fecha | `vencimiento` vacío; el script usa `--plazo-dias`. |
| «A 90 días» | Se apunta el vencimiento que dice la factura. El script lo recorta a 60 y lo explica. |
| Un cliente que es autónomo | `empresa`. |
| Una comunidad de propietarios, una asociación, una fundación | Pregunta. Si actúa en una actividad económica o profesional, `empresa`; si no está claro, dilo en el resumen. |
| Factura que aún no ha vencido | Se incluye: el script la aparta y dice cuándo vence. |
| Factura que el cliente discute | No se incluye. Se nombra aparte en el resumen. |
| Abono o factura rectificativa | Se resta de la factura que corrige; no va en una línea propia. |

## Lo que el script no puede ver

Compruébalo antes de ejecutar:

- **Una factura ya cobrada que sigue como pendiente** en el listado. Si el listado es de hace días, pregunta si ha entrado algún pago.
- **El mismo cliente con dos nombres** («Hotel Mirador» y «Mirador Hoteles, S.L.»). Unifícalos.
- **El tipo de cliente supuesto.** No lo deduzcas por el nombre: pregúntalo.
- **Los avisos.** Si no se sabe, cero. Poner de más adelanta la fase y endurece una carta sin motivo.

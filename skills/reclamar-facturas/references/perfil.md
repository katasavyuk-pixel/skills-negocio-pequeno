# El perfil del negocio

Las skills de este paquete se adaptan a cada negocio leyendo un fichero, `perfil-negocio.md`, que crea la skill `empezar`. Aquí está cómo encontrarlo, qué significa cada dato y qué hacer cuando falta.

## Dónde buscarlo

Por este orden, y para en cuanto aparezca:

1. En la raíz de la carpeta de trabajo, si tienes acceso a ficheros.
2. Entre los ficheros adjuntos o el conocimiento del proyecto de esta conversación.
3. En lo que la persona ya haya dicho en esta conversación.

## Si no hay perfil

No pares el trabajo ni exijas pasar por `empezar`.

1. Pregunta solo los datos que esta skill necesita (su SKILL.md los nombra), en una sola tanda y con opciones.
2. Haz el trabajo.
3. Al terminar, ofrece guardarlos: «¿Te lo guardo en un perfil para no volver a preguntártelo?». Si acepta, escribe `perfil-negocio.md` con el formato de abajo, con `pendiente` en lo que no se haya hablado.

## Si hay perfil pero falta un dato

Un dato en `pendiente`, vacío o ausente se pregunta en el momento, solo ese, y se apunta en el fichero junto con la fecha en `actualizado`.

## Qué manda sobre qué

- Lo que la persona dice ahora manda sobre el perfil. Si lo contradice, úsalo y ofrece actualizar el fichero.
- El perfil manda sobre tus suposiciones. No deduzcas el IVA, el plazo ni el trato por el tipo de negocio.
- `pendiente` es una respuesta válida. Un dato inventado no lo es.

## Los datos

Cada dato es una línea `- clave: valor`.

| Clave | Valores | Para qué se usa |
| --- | --- | --- |
| `quien_configura` | `dueno`, `equipo`, `asesor` | A quién le hablas: a quien lleva el negocio, a alguien de su equipo, o a quien lo monta para un cliente («el negocio de tu cliente», no «tu negocio»). |
| `nombre` | texto | Nombre comercial, para firmas y encabezados. |
| `actividad` | texto | Qué vende, en una frase. Da el vocabulario de cartas y resúmenes. |
| `clientes` | `empresas`, `particulares`, `ambos` | Decide qué leyes de pago se aplican: las de morosidad entre empresas no cubren a un particular. |
| `forma` | `autonomo`, `sociedad` | Qué impuestos y qué modelos le tocan. |
| `personas` | número | Cuántas personas trabajan, contando a quien lo lleva. |
| `territorio` | `comun`, `pais_vasco`, `navarra`, `canarias`, `ceuta_melilla`, `fuera_de_espana` | Qué hacienda y qué impuesto indirecto: fuera de `comun` cambian modelos, plazos y sistemas de facturación. |
| `cobro` | `al_momento`, `a_plazo`, `mixto` | Si tiene sentido hablar de facturas vencidas. |
| `plazo_cobro_dias` | número, o `no_aplica` si cobra en el momento | El plazo pactado habitual, para calcular vencimientos cuando la factura no lo dice. |
| `iva` | `21`, `10`, `4`, `exento`, `recargo_equivalencia`, `varios`, `igic`, `ipsi` | El tipo habitual, para comprobar facturas y previsiones. |
| `retencion_irpf` | `no`, `15`, `7` | Si sus facturas llevan retención y cuánta. |
| `caja_minima_eur` | importe | El saldo por debajo del cual hay que avisar. |
| `facturas_en` | texto | De dónde salen las facturas y en qué formato se pueden exportar. |
| `banco_exporta` | texto | Cómo se sacan los movimientos del banco. |
| `clientes_en` | texto | Dónde están clientes y oportunidades. |
| `gestoria` | `si`, `no` | Si hay alguien que presenta los impuestos: cambia lo que se prepara y para quién. |
| `trato` | `tu`, `usted` | Cómo se escribe a sus clientes. |
| `firma` | texto | Cómo se firma un correo. |
| `idioma` | texto | Idioma de lo que se entrega (`es` por defecto). |
| `prioridad` | `cobrar`, `caja`, `trimestre`, `visibilidad`, `datos`, `no_lo_se` | Lo que quiere resolver primero. |
| `web` | dirección con `https://`, o `no` | La web del negocio, si la hay. |
| `actualizado` | fecha `AAAA-MM-DD` | Cuándo se tocó el perfil por última vez. |
| `formato` | `1` | Versión de este formato. |

## Lo que no se hace con el perfil

- No se copia en lo que va a terceros. Una carta a un cliente lleva la firma y el trato, no el perfil.
- No se le añaden contraseñas, números de cuenta ni datos de clientes: no es el sitio.

# Las preguntas de la bienvenida

Nueve preguntas en tres tandas, más una de seguimiento. Cada una dice qué se pregunta, qué opciones se enseñan y en qué clave del perfil se guarda la respuesta.

Regla para añadir o quitar preguntas: si la respuesta no cambia lo que hará ninguna skill, no se pregunta.

## Contenido

- Cómo leer este fichero
- Tanda 1: el negocio
- Tanda 2: el dinero y los papeles
- Tanda 3: para qué lo quiere
- La pregunta de seguimiento
- De la provincia al territorio
- Cómo leer respuestas imprecisas

## Cómo leer este fichero

- **Opciones a la vista**: lo que se le enseña a la persona, cuatro como mucho. Si una pregunta no las trae, se hace abierta, con el ejemplo que da.
- **Cómo se guarda**: la tabla para convertir lo que conteste en el valor del perfil. No se lee en voz alta.
- **Admite «no lo sé»**: solo donde lo dice. En esas se ofrece como última opción y se guarda `pendiente`. En las demás no se ofrece: son cosas que cualquiera sabe de su negocio.
- La redacción se adapta al trato y a si lo configura un asesor («¿a quién le vende tu cliente?»). Las opciones y las claves, no.

## Tanda 1: el negocio

Va en el mismo mensaje que la bienvenida.

**1. ¿Para quién es?** No admite «no lo sé».
«¿Esto es para tu negocio o lo estás preparando para el de otra persona?»
Opciones a la vista: es mi negocio · trabajo en él · lo preparo para un cliente.

| Respuesta | `quien_configura` |
| --- | --- |
| Es mi negocio | `dueno` |
| Trabajo en él | `equipo` |
| Lo preparo para un cliente | `asesor` |

**2. ¿Qué negocio es?** Abierta. El nombre admite «no lo sé».
«¿Cómo se llama y a qué se dedica? Con una frase vale: "carpintería a medida para tiendas", "clínica dental", "asesoría laboral". ¿Y cuántas personas trabajáis, contándote a ti?»
Guarda `nombre`, `actividad` (su frase, sin adornar) y `personas` (todas las que trabajan, incluido quien lo lleva).

**3. ¿A quién le vende?** No admite «no lo sé».
«¿A quién le vende sobre todo?»
Opciones a la vista: a empresas y autónomos · a particulares · a los dos.

| Respuesta | `clientes` |
| --- | --- |
| A empresas y autónomos | `empresas` |
| A particulares | `particulares` |
| A los dos | `ambos` |

## Tanda 2: el dinero y los papeles

**4. ¿Autónomo o sociedad, y dónde?** No admite «no lo sé».
«¿Es autónomo o una sociedad (S.L., S.A., cooperativa)? ¿En qué provincia está?»
Guarda `forma` (`autonomo` o `sociedad`) y `territorio` según la tabla de más abajo.

**5. ¿Cómo cobra?** No admite «no lo sé»; el número de días, sí.
«¿Cobra en el momento, o emite factura y le pagan después? Si es después, ¿a cuántos días?»
Opciones a la vista: en el momento · con factura, a un plazo · depende del cliente.

| Respuesta | `cobro` | `plazo_cobro_dias` |
| --- | --- | --- |
| En el momento (tienda, bar, consulta) | `al_momento` | `no_aplica` |
| Con factura, a un plazo | `a_plazo` | los días que diga |
| Depende del cliente | `mixto` | el plazo más habitual |

Si dice «a 30 días fin de mes» o «a 60 días», guarda el número. Si factura pero no tiene plazo pactado, guarda `pendiente`: no pongas 30 por tu cuenta.

**6. ¿Qué impuestos van en sus facturas, y quién los presenta?** Admite «no lo sé» en las tres partes.
«¿Tienes una gestoría que te presenta los impuestos? ¿Y sabes qué IVA y qué retención llevan tus facturas? Por ejemplo: "21 % y sin retención". Si no lo sabes es normal: lo dejo pendiente y que lo confirme la gestoría.»
Abierta, sin lista de opciones. Si la provincia resulta ser de Canarias, Ceuta o Melilla, guarda `igic` o `ipsi` diga lo que diga del IVA, y díselo en una frase.

| Lo que diga sobre el IVA | `iva` |
| --- | --- |
| El normal, el 21 | `21` |
| El 10 (por ejemplo, hostelería o transporte de viajeros) | `10` |
| El 4 | `4` |
| No cobra IVA (por ejemplo, sanidad, enseñanza o seguros) | `exento` |
| Paga recargo de equivalencia (una tienda) | `recargo_equivalencia` |
| Varios tipos según lo que venda | `varios` |

`retencion_irpf`: `no`, `15` o `7`. `gestoria`: `si` o `no`.

No corrijas lo que diga aunque te parezca raro para su actividad: apúntalo y, si el validador avisa, se lo cuentas.

## Tanda 3: para qué lo quiere

**7. ¿Qué quiere resolver primero?**
«¿Qué te gustaría quitarte de encima primero?»
Esta es la única pregunta que enseña más de cuatro opciones, porque elegir entre ellas es la respuesta.

| Opción a la vista | `prioridad` |
| --- | --- |
| Me pagan tarde o tengo facturas sin cobrar | `cobrar` |
| No sé si llego a fin de mes | `caja` |
| El trimestre y los papeles me comen | `trimestre` |
| No me encuentran en internet ni me recomienda ChatGPT | `visibilidad` |
| Paso horas copiando datos de correos y facturas | `datos` |
| No lo sé todavía | `no_lo_se` |

**8. ¿Dónde está cada cosa?** Abierta. Admite «no lo sé» en cada parte.
«¿Dónde tienes las facturas, dónde apuntas a los clientes y cómo sacas los movimientos del banco? Un programa, un Excel, papel: lo que sea.»
Guarda `facturas_en`, `clientes_en` y `banco_exporta` con sus palabras, añadiendo el formato en que puede exportar si lo dice («Holded, exporta a Excel»).

**9. ¿Cómo escribe a sus clientes?** El trato no admite «no lo sé»; la firma, sí.
«A tus clientes, ¿les hablas de tú o de usted? ¿Y cómo firmas un correo?»
Guarda `trato` (`tu` o `usted`) y `firma` tal cual la diga.

## La pregunta de seguimiento

Depende de lo que haya contestado a la pregunta 7, así que va **después** de la tanda 3, en un mensaje aparte, y solo en estos dos casos:

| Si `prioridad` es | Pregunta | Clave |
| --- | --- | --- |
| `caja` | «¿Con cuánto dinero en la cuenta estás tranquilo? El saldo por debajo del cual quieres que te avise.» | `caja_minima_eur` |
| `visibilidad` | «¿Cuál es la dirección de la web? Si no hay web, dime que no.» | `web` (con `https://`, o `no`) |

En los demás casos no hay pregunta de seguimiento, y `caja_minima_eur` y `web` se quedan en `pendiente`.

## De la provincia al territorio

| Provincia | `territorio` |
| --- | --- |
| Álava, Bizkaia, Gipuzkoa | `pais_vasco` |
| Navarra | `navarra` |
| Las Palmas, Santa Cruz de Tenerife | `canarias` |
| Ceuta, Melilla | `ceuta_melilla` |
| Cualquier otra de España | `comun` |
| Fuera de España | `fuera_de_espana` |

Si da una ciudad, usa su provincia (Donostia → Gipuzkoa). Si no sabes a qué provincia pertenece, pregúntalo.

## Cómo leer respuestas imprecisas

- «Somos mi socio y yo» → `personas: 2`. «Yo solo» → `personas: 1`. «Yo y cinco empleados» → `personas: 6`.
- «Una S.L.» o «una limitada» → `forma: sociedad`. «Estoy de alta de autónomo» → `forma: autonomo`.
- «Cobro por transferencia cuando termino» → `cobro: a_plazo`, `plazo_cobro_dias: pendiente`.
- «Creo que no llevo retención, pero no estoy segura» → `retencion_irpf: pendiente`, y se le dice que queda por confirmar.
- «No tengo ni idea de lo del IVA» → `iva: pendiente`, `retencion_irpf: pendiente`. No expliques los tipos.
- Una web sin `https://` («mitienda.es») → guárdala con `https://` delante y díselo.
- «Todo en papel» → el mismo texto en `facturas_en` y `clientes_en`.
- Si da dos respuestas a la prioridad, guarda la primera que dijo y nombra la otra en el paso 7.

# Las tres fases de una reclamación

Una por cliente, con todas sus facturas vencidas. El script dice en `que_toca` la fase de cada cliente: la de su factura más avanzada. La persona puede pedir otra.

## Contenido

- Cómo decide el script la fase
- Lo que llevan las tres
- Fase 1: recordatorio
- Fase 2: reclamación con intereses
- Fase 3: requerimiento formal con propuesta de acuerdo
- Cómo se envía cada una
- Lo que ninguna dice

## Cómo decide el script la fase

| Fase | Cuándo |
| --- | --- |
| 1. Recordatorio | No se ha mandado ningún aviso y el retraso no pasa de 30 días. |
| 2. Reclamación con intereses | Ya se mandó un aviso, o el retraso pasa de 30 días. |
| 3. Requerimiento formal con propuesta de acuerdo | Ya se mandaron dos avisos, o el retraso pasa de 60 días. |

Son valores de partida, no una norma. Un cliente de muchos años que se retrasa por primera vez puede merecer una llamada antes que una carta: dilo si el perfil o la conversación lo sugieren.

## Lo que llevan las tres

- El trato del perfil (`tu` o `usted`) y la firma del perfil, sin cambiarlos.
- Cada factura con su número, su fecha, su vencimiento y su importe. Nunca «las facturas pendientes» a secas.
- Los datos para pagar. El número de cuenta no está en el perfil: pídeselo a la persona en el momento y no lo guardes.
- Una fecha concreta para el siguiente paso, no «a la mayor brevedad».
- Ninguna cifra que no venga del script.

## Fase 1: recordatorio

Para qué: que paguen sin que nadie se incomode. La mayoría de los retrasos cortos son un despiste o una factura traspapelada.

- Corta: cinco o seis líneas.
- Da por hecho que es un olvido. Pregunta si falta algo para poder pagarla (un pedido, una conformidad, otro destinatario).
- **No menciona intereses ni la ley.**
- Pide una fecha de pago, no el pago inmediato.

Modelo, de usted:

> Asunto: Factura 2026-031, vencida el 28 de septiembre
>
> Buenos días:
>
> Le escribo por la factura 2026-031, de 29 de agosto, por 3.630,00 €, que venció el 28 de septiembre y que no nos consta como cobrada.
>
> ¿Puede confirmarme en qué fecha tienen previsto el pago? Si falta algo por nuestra parte para tramitarla, dígamelo y se lo envío hoy.
>
> Los datos para la transferencia son: [cuenta].
>
> Un saludo,
> [firma]

## Fase 2: reclamación con intereses

Para qué: dejar por escrito lo que se debe, con las cifras de la ley, y dar una salida.

- Enumera las facturas en una lista.
- Da el total pendiente, y aparte lo que la ley añade: intereses calculados a la fecha y 40 euros por factura, con su artículo.
- Según lo que haya decidido la persona:
  - **Reclama todo**: pide el total con intereses y compensación.
  - **Ofrece renunciar** (la opción por defecto): pide el importe, dice que los intereses y la compensación ya se deben, y ofrece no reclamarlos si el pago llega antes de una fecha. Siete días naturales es lo habitual.
  - **Solo el importe**: no menciona la ley, pero sí que es la segunda vez que se reclama.
- Dice qué pasa después, sin amenazar: «si no recibo el pago ni noticias suyas, le enviaré un requerimiento formal».

Modelo, de usted, ofreciendo renunciar:

> Asunto: Reclamación de las facturas 2026-019 y 2026-031
>
> Buenos días:
>
> Le escribo de nuevo por dos facturas que siguen sin pagar:
>
> - Factura 2026-019, de 10 de abril, vencida el 9 de junio: 7.260,00 €
> - Factura 2026-031, de 29 de agosto, vencida el 28 de septiembre: 3.630,00 €
>
> El total pendiente es de 10.890,00 €.
>
> Desde su vencimiento, estas facturas devengan el interés de demora de la Ley 3/2004 (artículo 7), que a fecha de hoy asciende a 275,11 €, y dan derecho a una compensación de 40 € por factura por costes de cobro (artículo 8): 80,00 €.
>
> Mi intención es cerrar esto sin llegar ahí. Si recibo los 10.890,00 € antes del 20 de octubre, renuncio a los intereses y a la compensación.
>
> Si hay algún problema con las facturas o necesita proponer otro calendario, respóndame a este correo y lo vemos.
>
> Un saludo,
> [firma]

## Fase 3: requerimiento formal con propuesta de acuerdo

Para qué: es la última reclamación amistosa y, a la vez, **la prueba que exige la ley antes de ir al juzgado**.

Desde el 3 de abril de 2025, para que un juzgado admita una reclamación civil hay que haber intentado antes negociar (Ley Orgánica 1/2025, art. 5). El proceso monitorio, que es la vía normal para cobrar una factura, no está entre las excepciones. La negociación directa entre las partes vale (art. 5.1), y se prueba con «cualquier documento que pruebe que la otra parte ha recibido la solicitud o invitación para negociar o, en su caso, la propuesta, en qué fecha, y que ha podido acceder a su contenido íntegro» (art. 10.2).

Por eso esta carta no puede ser solo una exigencia de pago. Tiene que llevar, las seis cosas:

1. **Quién reclama y a quién**, con nombre completo o razón social, NIF y domicilio de los dos.
2. **Qué se reclama**: cada factura con número, fecha, vencimiento e importe; los intereses a la fecha, con su artículo; la compensación, con su artículo; y el total.
3. **Una invitación expresa a negociar**: la frase tiene que estar. Por ejemplo: «Le invito a negociar una solución antes de acudir a los tribunales».
4. **Una propuesta concreta**: un calendario de pagos, una fecha para hablar, o el pago del importe a cambio de renunciar a intereses. Si son dos pagos, sus importes están en `pendiente_en_dos_pagos` del resumen. Una propuesta concreta sin respuesta por escrito en treinta días naturales cierra el intento (art. 10.4).
5. **El plazo y lo que viene después**: treinta días naturales desde la recepción, y que pasado ese plazo sin acuerdo ni respuesta se reclamará judicialmente el total.
6. **La fecha y la firma.**

Además, la solicitud de negociación interrumpe la prescripción desde que consta el intento de comunicarla (art. 7.1).

Modelo, de usted:

> [Nombre o razón social de quien reclama], con NIF [NIF] y domicilio en [dirección]
>
> A [nombre o razón social del cliente], con NIF [NIF] y domicilio en [dirección]
>
> [Lugar], 13 de octubre de 2026
>
> Asunto: Requerimiento de pago e invitación a negociar. Facturas 2026-019 y 2026-031
>
> Muy señores míos:
>
> Les reclamo el pago de las siguientes facturas, emitidas por trabajos entregados y sobre los que no han formulado ninguna objeción:
>
> - Factura 2026-019, de 10 de abril de 2026, vencida el 9 de junio de 2026: 7.260,00 €
> - Factura 2026-031, de 29 de agosto de 2026, vencida el 28 de septiembre de 2026: 3.630,00 €
>
> A estas cantidades se añaden, conforme a la Ley 3/2004, de 29 de diciembre:
>
> - Intereses de demora al tipo legal (artículo 7), calculados a 13 de octubre de 2026: 275,11 €. Siguen devengándose hasta el pago.
> - Compensación por costes de cobro (artículo 8), 40 € por factura: 80,00 €.
>
> Total reclamado a esta fecha: 11.245,11 €.
>
> Antes de acudir a los tribunales, y a los efectos del artículo 5 de la Ley Orgánica 1/2025, les invito a negociar una solución. Les propongo lo siguiente: si abonan el principal, 10.890,00 €, en dos pagos de 5.445,00 € los días 30 de octubre y 30 de noviembre de 2026, renuncio a los intereses y a la compensación. Estoy también a su disposición para tratar otra propuesta por escrito o en una reunión.
>
> Los pagos pueden hacerse por transferencia a la cuenta [cuenta], indicando los números de factura.
>
> Si en el plazo de treinta días naturales desde la recepción de este escrito no hay acuerdo ni respuesta por escrito, daré por terminado el intento de negociación y reclamaré judicialmente la cantidad total, con los intereses que se devenguen hasta el pago y las costas.
>
> Pueden responder por escrito a la dirección indicada arriba o a [correo].
>
> Atentamente,
> [firma]

Los datos entre corchetes se piden a la persona. El NIF y el domicilio del cliente están en sus propias facturas.

La frase sobre los trabajos entregados solo se escribe si la persona lo ha confirmado. Y díselo al entregar el borrador: la carta lo afirma, y tiene que ser verdad.

## Cómo se envía cada una

| Fase | Medio | Por qué |
| --- | --- | --- |
| 1 | Correo electrónico, a quien paga las facturas | Basta. |
| 2 | Correo electrónico, a quien paga y a quien encargó el trabajo | Que lo vea quien decide. |
| 3 | Un medio que pruebe la recepción, la fecha y el contenido íntegro: burofax con certificación de texto y acuse de recibo, o un servicio de correo electrónico certificado | Es lo que pide el art. 10.2. Un correo normal no prueba que se recibió ni lo que decía. |

Guarda con la persona el justificante del envío de la fase 3: es lo que se presenta en el juzgado.

## Lo que ninguna dice

- No amenaza con listas de morosos, con contarlo a terceros ni con nada que la persona no haya decidido hacer.
- No califica al cliente («moroso», «incumplidor»). Describe facturas y fechas.
- No inventa conversaciones previas («como hablamos») si no constan.
- No da por cierto algo que el cliente discute. Si hay una queja abierta sobre el trabajo, la carta lo reconoce y la deja aparte.
- No cita artículos en la fase 1.

# Cómo contar el resultado

Quien lee esto quiere saber una cosa: si le va a faltar dinero y cuándo. Lo demás está en la hoja.

## La estructura

Cinco líneas, en este orden. Las cifras salen del resumen del script, tal cual, escritas a la española (`7.004,25 €`) y con fechas en palabras («la semana del 26 de octubre»).

1. **La respuesta.** La primera semana en que la cuenta baja del mínimo en el escenario previsto, o que no baja.
2. **El peor momento.** El saldo más bajo y su semana. Si entra en negativo, se dice aquí con esas palabras. El motivo se toma de `mayores_pagos_de_las_semanas_clave` del resumen: los pagos de esa semana, no los que recuerdes de otra.
3. **Si cobras tarde.** Qué cambia con el retraso. Compara la misma semana en los dos escenarios con `saldo_al_cierre_de_cada_semana`: «esa semana te quedas en -7.969,25 € en vez de -229,25 €». Si no cambia nada, se dice en media frase y se sigue.
4. **De quién depende.** El cliente que más pesa y su porcentaje, y qué pasa si no paga.
5. **Qué falta o qué hacer.** Lo que no está en la previsión (un impuesto sin importe), o las palancas evidentes para esa semana: adelantar un cobro concreto, aplazar un pago concreto.

Después, una línea con el nombre del fichero y dónde está.

## Ejemplo

Con el ejemplo de la skill (una carpintería con 9.420,75 € en cuenta y un mínimo de 8.000 €):

> Con lo que hay apuntado, la cuenta baja de tus 8.000 € la semana del 26 de octubre, cuando se juntan nóminas, Seguridad Social y alquiler.
>
> El peor momento es la semana del 28 de diciembre: te quedas en -7.004,25 €, en negativo, al juntarse nóminas, Seguridad Social y alquiler.
>
> Si tus clientes pagan con dos semanas de retraso, entras en negativo ya la semana del 26 de octubre: -4.339,25 € en vez de los 3.400,75 € previstos.
>
> El 60 % de lo que esperas cobrar (18.150,00 €) viene de Hotel Mirador. Si no paga, acabas el trimestre en -25.154,25 €.
>
> Hay una factura de ese cliente vencida desde el 28 de septiembre (3.630,00 €) que la previsión da por cobrada esta semana. Es lo primero que mover: reclamarla, y hablar con el hotel de la fecha de la grande.
>
> La hoja está en `prevision-caja.xlsx`.

## Reglas

- Empieza por la respuesta, no por cómo se ha hecho.
- Una cifra por frase. Quien quiera las trece semanas las tiene en la hoja.
- Di «en negativo», no «saldo deudor» ni «tensión de tesorería».
- Si falta un dato importante, va en la primera línea: «Falta el IVA de octubre, así que esto es optimista».
- Nombra cobros y pagos concretos al proponer algo. «Mejorar la gestión de cobros» no es una propuesta.
- No recomiendes financiación. Si la persona pregunta, di que eso es una conversación con su banco o su gestoría, con esta hoja delante.
- Si el escenario previsto no baja del mínimo en trece semanas, dilo en la primera línea y pasa a los otros dos: la tranquilidad también es un resultado.
- La previsión va por semanas. Si preguntan por un día concreto («¿llego a fin de año?»), responde con la semana que lo contiene y di que es el saldo al acabar esa semana.

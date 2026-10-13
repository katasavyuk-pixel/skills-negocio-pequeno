# Cómo contar el resultado del trimestre

Quien lee esto quiere saber qué tiene que arreglar antes de mandarlo, cuánto tiempo tiene y más o menos cuánto IVA sale.

## La estructura

Cinco bloques, en este orden. Las cifras salen del resumen del script, escritas a la española.

1. **El marcador y el plazo.** Cuántas facturas se han revisado, cuántos errores y cuántos avisos, y hasta qué día hay para presentar.
2. **Lo que hay que corregir**, uno por línea: la factura, con quién es, qué le pasa y qué se hace. Primero las emitidas.
3. **Lo que hay que confirmar**: los avisos y las posibles facturas que faltan, como preguntas que se contestan con un sí o un no.
4. **El IVA**, en una frase: el de las ventas, el de las compras y la diferencia, **diciendo en la misma frase que no es la liquidación**.
5. **Qué sigue**: corregir, volver a pasar la revisión y entregar.

Después, el nombre del fichero y dónde está.

## Ejemplo

Con el ejemplo de la skill, tercer trimestre de 2026:

> He revisado 9 facturas emitidas y 10 recibidas del tercer trimestre. Hay 5 errores que corregir y 4 cosas que confirmar. El plazo para presentar acaba el 20 de octubre.
>
> Para corregir:
>
> - **2026-025, Hotel Mirador**: el NIF está mal escrito (B00000011; en la 2026-031 es B00000018). Hay que rectificar la factura.
> - **2026-029, Óptica Lumen**: la cuota de IVA dice 300,00 € y a una base de 1.500,00 € al 21 % le corresponden 315,00 €. Mira la factura original.
> - **2026-030, Bar Central**: falta el NIF del cliente.
> - **H-220, Herrajes Sanz** (recibida): está apuntada dos veces. He contado una.
> - **H-231, Herrajes Sanz** (recibida): el total dice 112,00 € y la suma da 121,00 €.
>
> Para confirmar:
>
> - ¿Existe la factura 2026-026? Falta entre la 025 y la 027.
> - La 2026-027 tiene fecha de 1 de julio y la 2026-025, de 10 de julio: los números no siguen el orden de las fechas. ¿Cuál está mal?
> - La 2026-033 es de 2 de octubre: la saco de este trimestre.
> - La de «Software de diseño» es de un proveedor de fuera de España: la señalo aparte para la gestoría.
> - ¿Falta la factura de agosto de Luz del Ebro? ¿Y la de septiembre de Maderas Aragón?
>
> Tal como está apuntado, el IVA de las ventas es de 3.381,00 € y el de las compras de 2.180,01 €: 1.200,99 € de diferencia. No es lo que saldrá a pagar: eso lo calcula la gestoría, y cambiará cuando se corrija lo de arriba.
>
> Además, has retenido 683,07 € en las facturas de alquiler: se ingresan con el modelo 115, también hasta el 20 de octubre.
>
> Cuando lo corrijas, vuelvo a pasar la revisión y te dejo la hoja lista para enviar. Está en `trimestre-2026-3.xlsx`.

## Reglas

- Empieza por el marcador y el plazo.
- Un hallazgo, una línea, con el número de factura y el nombre. Nunca «hay varias facturas con errores».
- Los avisos se escriben como preguntas.
- La diferencia de IVA nunca va sola: siempre con «no es la liquidación» o «no es lo que saldrá a pagar» en la misma frase.
- No digas qué es deducible, ni si una operación está exenta, ni qué modelo le toca más allá de lo que dice el perfil.
- No digas «todo correcto» si no hay errores: di que no has encontrado errores de forma ni de suma, y qué es lo que esta revisión no mira.
- Si hay gestoría, ofrece al final el mensaje para mandarle la hoja, con los puntos abiertos en una lista.
- Si no hay gestoría, repite una vez más que esto no es la declaración.

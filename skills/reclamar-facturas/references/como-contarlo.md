# Cómo contar el resultado

Quien lee esto quiere saber cuánto le deben, cuánto más puede pedir y qué hacer con cada cliente.

## La estructura

Cinco bloques, en este orden. Las cifras salen del resumen del script, escritas a la española (`15.605,00 €`).

1. **Cuánto le deben.** `pendiente`, en cuántas facturas y de cuántos clientes.
2. **Lo que la ley añade.** `lo_que_la_ley_anade_al_importe`, separado en intereses y compensación, y de dónde sale en una frase: «entre empresas, la ley añade intereses y 40 € por factura a lo que se paga tarde».
3. **Cliente a cliente**, de más a menos dinero: cuánto debe, desde cuándo, y qué toca.
4. **Lo que se ha apartado y por qué.** Facturas de particulares, de una Administración, no vencidas, discutidas, o que pueden haber prescrito.
5. **La pregunta.** Qué quiere reclamar a cada cliente: todo, el importe con oferta de renunciar a lo demás, o solo el importe.

Después, el nombre del fichero y dónde está.

## Ejemplo

Con el ejemplo de la skill, calculado al 13 de octubre de 2026:

> Te deben 15.605,00 € en cuatro facturas vencidas, de tres clientes.
>
> A eso la ley añade 417,86 €: 297,86 € de intereses de demora y 120,00 € de compensación (40 € por cada una de las tres facturas de empresas). No hace falta haberlo pactado ni haber avisado antes.
>
> - **Hotel Mirador** debe 10.890,00 € en dos facturas; la más antigua lleva 126 días de retraso y ya se le han mandado dos avisos. Con intereses y compensación son 11.245,11 €. Toca el requerimiento formal.
> - **Familia Aranda** debe 2.900,00 €, con 14 días de retraso. Es un particular: se reclama el importe, sin intereses de esta ley.
> - **Zapatería Paso** debe 1.815,00 €. La factura dice «a 90 días», pero la ley no admite más de 60, así que lleva 44 días de retraso y no los 14 que parece. Con lo que añade la ley son 1.877,75 €.
>
> Aparte: la de Óptica Lumen vence el 20 de octubre y todavía no hay retraso; la del Ayuntamiento de Villaejemplo está vencida, pero las Administraciones tienen su propio procedimiento y no la he calculado.
>
> ¿Qué quieres reclamar a cada uno: todo, el importe ofreciendo renunciar a los intereses si pagan pronto, o solo el importe?
>
> La hoja está en `reclamacion.xlsx`; en la pestaña «Cálculo» está cada tramo de intereses con su tipo y la resolución del BOE.

## Reglas

- Empieza por lo que le deben, no por la ley.
- Separa siempre lo pendiente de lo que la ley añade. Son dos cifras distintas y la segunda es negociable.
- Di «lo que la ley añade», no «penalización» ni «recargo».
- Si hay una nota en la factura (el plazo recortado a 60 días, una posible prescripción), cuéntala en la línea de ese cliente con sus palabras.
- Si una cifra depende de algo no cerrado (el interés con IVA o sin IVA, cuando se piense ir a juicio), dilo en una frase y da la cifra prudente: `intereses_si_se_calculan_sin_iva`.
- No digas que se va a cobrar. Di lo que se puede reclamar.
- No recomiendes ir a juicio ni no ir. Si lo preguntan, explica qué hay después con `si-no-pagan.md`.
- Esto es un cálculo con las normas que cita. Dilo una vez, al final, si la persona habla de juzgados: «antes de ir al juzgado, que lo vea un abogado».

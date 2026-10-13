# Lo que se comprueba, y cómo se arregla

Qué mira el script, qué significa cada hallazgo y qué hacer con él. Las normas se leyeron en el texto consolidado del BOE el 13 de octubre de 2026.

## Contenido

- Errores: se corrigen antes de entregar
- Avisos: se confirman con la persona
- Posibles facturas que faltan
- Lo que solo se ve con la factura delante
- Cómo se corrige una factura
- La diferencia de IVA no es la liquidación
- Los plazos
- Lo que no se comprueba

## Errores: se corrigen antes de entregar

| Hallazgo | Qué significa | Qué hacer |
| --- | --- | --- |
| La cuota de IVA no corresponde a la base y al tipo | Base × tipo no da la cuota, con dos céntimos de margen por redondeo. | Mirar la factura original. Si está mal en la factura, se rectifica; si está mal copiada, se corrige el listado. |
| El total no es la suma | Bases más IVA más recargo, menos retención, no da el total. Lo más frecuente: una retención que no se ha restado, o una línea que falta. | Igual que el anterior. |
| El NIF no es correcto | El número tiene la forma de un NIF pero su letra o dígito de control no corresponde. Casi siempre es una errata. | Compararlo con otra factura del mismo cliente o proveedor. Una factura emitida con el NIF mal se rectifica. |
| Falta el NIF | En una factura completa es obligatorio el del emisor, y el del destinatario en las operaciones interiores (Real Decreto 1619/2012, art. 6.1.d). | Pedirlo. En una factura simplificada emitida no hace falta el del cliente (art. 7.1). |
| Falta el nombre | Obligatorio el de los dos (art. 6.1.c). | Completarlo. |
| El número está repetido | Dos facturas emitidas con el mismo número en la misma serie. | Una está mal numerada: se rectifica. |
| Ya está apuntada | La misma factura dos veces en el listado. Su IVA se declararía o se deduciría dos veces. | Quitar una. No cuenta en las sumas. |
| Fecha anterior al trimestre, en una emitida | Una factura emitida se declara en su trimestre. | Si quedó sin declarar, avisar a quien presenta los impuestos: hay que regularizarlo. |
| Simplificada de más de 3.000 € | Pasa del máximo que admite la norma en cualquier actividad (art. 4.2). | Tiene que ser una factura completa. |
| El recargo de equivalencia no corresponde | Al 21 % le toca el 5,2 %; al 10 %, el 1,4 %; al 4 %, el 0,5 % (Ley del IVA, art. 161). | Mirar la factura original. |

## Avisos: se confirman con la persona

| Hallazgo | Qué significa | Qué preguntar |
| --- | --- | --- |
| Falta una factura en la numeración | La numeración de cada serie tiene que ser correlativa (art. 6.1.a). Un hueco puede ser una factura que falta en el listado o un número saltado. | «¿Existe la factura 2026-026?» Si existe, se añade. Si se saltó o se anuló, tiene que poder explicarse. |
| Fecha anterior a la de una factura con número menor | Los números tienen que seguir el orden de las fechas. | Cuál de las dos fechas está mal. |
| Fecha posterior al trimestre | La factura es del trimestre siguiente. | Se saca de este. |
| Recibida de un trimestre anterior | Llega con retraso. | Se avisa a quien presenta los impuestos, que decide en qué declaración entra. No cuenta en las sumas de este trimestre. |
| Tipo de IVA no habitual | No es 21, 10, 4 ni 0. | Que confirme que es el que corresponde. |
| NIF de fuera de España | Las operaciones con el extranjero tienen sus propias reglas de IVA. | Se separan y se nombran en el resumen. |
| NIF sin forma de NIF español | No se puede comprobar. | Que lo revise. |
| Simplificada de más de 400 € | Solo vale por encima de 400 € en las actividades que lista la norma: venta al por menor a consumidores, hostelería, transporte de personas, peluquería y otras (art. 4.2). | Si su actividad es una de esas. |

## Posibles facturas que faltan

Un proveedor que factura dos meses del trimestre y no el segundo o el tercero: lo normal es que falte esa factura (el alquiler, la luz, una cuota). No se avisa cuando falta el primer mes, porque suele ser un proveedor nuevo.

Se pregunta una a una. Si la factura existe, se añade y se vuelve a ejecutar. Si de verdad no hubo, se deja.

## Lo que solo se ve con la factura delante

Un listado no enseña si la factura lleva todos sus datos. Con el PDF o la imagen, comprueba que una **factura completa** lleve (art. 6.1):

1. Número y, si la hay, serie.
2. Fecha de expedición.
3. Nombre y apellidos o razón social completa de quien la emite y de quien la recibe.
4. NIF de quien la emite, y de quien la recibe en las operaciones interiores.
5. Domicilio de los dos.
6. Descripción de lo vendido, con el precio unitario sin IVA y los descuentos.
7. El tipo o los tipos de IVA.
8. La cuota de IVA, por separado.
9. La fecha de la operación, si no es la de la factura.
10. Si está exenta, la referencia a la norma o la mención de que lo está.

Una **factura simplificada** (art. 7.1) lleva: número y serie, fecha, NIF y nombre de quien la emite, qué se vendió, el tipo de IVA y el total. Un cliente que es empresa o profesional puede exigir que lleve además su NIF, su domicilio y la cuota de IVA por separado (art. 7.2): es lo que la norma pide para la deducción.

Lo que falte en una emitida se apunta como error en el resumen, aunque el script no lo vea.

## Cómo se corrige una factura

Una factura emitida que está mal no se edita ni se borra: se emite una **factura rectificativa**, en serie propia (arts. 6.1.a y 15). Es obligatoria cuando la original no cumple alguno de sus requisitos o cuando la cuota de IVA estaba mal calculada (art. 15.1 y 15.2).

Una factura recibida que está mal se le pide al proveedor que la rectifique.

No expliques cómo se redacta una rectificativa ni qué efectos tiene en la declaración: eso lo dice quien presenta los impuestos.

## La diferencia de IVA no es la liquidación

La hoja da el IVA de las ventas menos el IVA de las compras, tal como están apuntadas. Sirve para tener un orden de magnitud y para detectar un trimestre raro. No es lo que saldrá a pagar, porque aquí no se mira:

- Qué gastos son deducibles y en qué parte.
- Cuotas a compensar de trimestres anteriores.
- Prorrata, bienes de inversión, criterio de caja, regímenes especiales.
- Operaciones con el extranjero.

Dilo siempre con la cifra, en la misma frase.

## Los plazos

Para el territorio común, según el calendario del contribuyente de la Agencia Tributaria de 2026:

| Qué | Plazo |
| --- | --- |
| IVA trimestral (modelo 303) y pago fraccionado del IRPF de autónomos (modelo 130) | Del 1 al 20 de abril, julio y octubre; el cuarto trimestre, hasta el 30 de enero |
| Retenciones de nóminas y profesionales (modelo 111) y de alquileres (modelo 115) | Hasta el 20 de abril, julio, octubre y enero |

El script pasa al lunes un plazo que cae en sábado o domingo. No conoce los festivos: si el último día lo es, el plazo acaba el siguiente día hábil.

Di solo los plazos que le tocan:

- El modelo 303, siempre que haya IVA.
- El modelo 130, solo si `forma` es `autonomo`.
- El modelo 115, si en las recibidas hay facturas de alquiler con retención.
- El modelo 111, si paga nóminas o facturas de profesionales con retención. El perfil no lo dice: si no lo sabes, pregúntalo en vez de darlo por hecho o de callarlo.

Si en las recibidas hay retenciones (`retenciones_que_has_practicado`), recuérdale que esas se ingresan.

El calendario de cada año lo publica la Agencia Tributaria. Para un año distinto de 2026, di que las fechas son las habituales y que confirme el calendario de ese año.

## Lo que no se comprueba

- Si un gasto está relacionado con la actividad.
- Si el tipo de IVA aplicado es el que corresponde a lo vendido.
- Si la factura se emitió dentro de plazo. Para clientes que son empresas, antes del día 16 del mes siguiente a la operación (art. 11.1).
- Los requisitos de los sistemas informáticos de facturación (Verifactu) y de la factura electrónica entre empresas.
- Nóminas, Seguridad Social, amortizaciones ni nada que no sea una factura.

# Lo que dice la ley sobre una factura pagada tarde

Todo lo de este fichero se leyó en el texto consolidado del BOE el 13 de octubre de 2026. Cada afirmación lleva su artículo. Lo que no está cerrado se dice que no lo está.

## Contenido

- A quién se aplica
- Cuándo vence una factura
- Qué se añade a la deuda
- El tipo de cada semestre, y qué hacer si falta uno
- Cómo se hace la cuenta
- Lo que no está cerrado
- Cuánto tiempo hay para reclamar
- Lo que esta skill no cubre
- Dónde está cada norma

## A quién se aplica

La Ley 3/2004 se aplica a los pagos entre empresas, y entre empresas y la Administración (art. 3.1). «Empresa» es cualquier persona física o jurídica que actúe en su actividad económica o profesional (art. 2.a): **un autónomo lo es**.

No se aplica a las operaciones en las que interviene un consumidor (art. 3.2.a), ni a las deudas de un cliente en concurso de acreedores (art. 3.2.c).

## Cuándo vence una factura

- Sin plazo pactado: a los treinta días naturales desde la entrega de la mercancía o la prestación del servicio, aunque la factura llegara antes (art. 4.1).
- Con plazo pactado: el pactado, que no puede pasar de sesenta días naturales «en ningún caso» (art. 4.3). Si una factura dice «a 90 días», el retraso empieza el día 60.
- Cuentan todos los días del año; son nulos los pactos que excluyen las vacaciones (art. 2.d).

El script toma la fecha de la factura como fecha de entrega. Si la entrega fue otro día, se apunta en la columna `entrega`.

## Qué se añade a la deuda

1. **Interés de demora** (art. 7). El pactado en el contrato; si no hay pacto, el tipo legal. Se debe automáticamente desde que pasa el plazo, «sin necesidad de aviso de vencimiento ni intimación alguna» (art. 5).
2. **Cuarenta euros por costes de cobro** (art. 8.1), que se añaden «en todo caso y sin necesidad de petición expresa a la deuda principal». Si los costes reales acreditados son mayores, también se pueden reclamar.

Para tener derecho a ambos, quien reclama tiene que haber cumplido su parte, y no cobra si el deudor prueba que el retraso no es culpa suya (arts. 6 y 8.2).

Una cláusula que excluya el interés de demora o la compensación es nula (art. 9.1). Que el contrato o las condiciones del cliente digan «sin intereses» no los quita.

## El tipo de cada semestre, y qué hacer si falta uno

El tipo legal es el del Banco Central Europeo más ocho puntos, y se fija para cada semestre natural (art. 7.2). Lo publica en el BOE la Secretaría General del Tesoro y Financiación Internacional, a finales de junio y de diciembre o en los primeros días del semestre.

La tabla `assets/tipos-demora.json` trae los tipos desde el segundo semestre de 2021, cada uno con su resolución. Los de 2026: 10,15 % el primer semestre y 10,40 % el segundo.

**Si el script dice que falta un semestre:**

1. Busca en `boe.es`: «tipo legal de interés de demora» y el semestre («primer semestre natural del año 2027»).
2. Abre la resolución y lee la frase «el tipo legal de interés de demora a aplicar durante el … semestre natural de … es el … por 100».
3. Ejecuta de nuevo añadiendo `--tipo 2027-1=10.40` con la cifra leída, y di en el resumen de qué resolución sale.

No uses el tipo del semestre anterior ni uno que recuerdes.

## Cómo se hace la cuenta

Interés simple, tramo a tramo por semestre:

```
importe pendiente × tipo del semestre × días de retraso en ese semestre ÷ 365
```

Los días se cuentan desde el siguiente al vencimiento hasta el día del cálculo. El resultado se redondea al céntimo una vez, por factura. La hoja «Cálculo» del libro enseña cada tramo.

La ley fija el tipo y su semestre, no la forma de contar los días: esta es la práctica habitual.

## Lo que no está cerrado

Dilo en el resumen cuando afecte a la decisión.

- **Si el interés se calcula con IVA o sin IVA.** Se discute. El script calcula sobre el importe con IVA, que es lo que se debe, y da también la cifra sobre la base cuando la tiene. Si se va a juicio, la prudente es la de la base.
- **Los 40 euros, por factura.** El Tribunal Supremo lo fijó así en mayo de 2021 (Sala de lo Contencioso-Administrativo, con un voto discrepante que pedía moderarlo), en un asunto contra una Administración. Es el criterio que se usa también entre empresas, pero no hay localizada una sentencia civil que lo diga con esas palabras.
- **La forma de contar los días.** Un juzgado puede usar 360 o 366: la diferencia es de céntimos.

## Cuánto tiempo hay para reclamar

- Cinco años desde que se pudo exigir el pago, con carácter general (art. 1964.2 del Código Civil).
- Tres años para algunas deudas: honorarios de ciertos profesionales, y género vendido por un comerciante a quien no lo es o se dedica a otra cosa (art. 1967).
- La prescripción se interrumpe con una reclamación extrajudicial del acreedor (art. 1973): reclamar por escrito, de forma que se pueda probar, pone el contador a cero.
- En Cataluña los plazos son otros (Código Civil de Cataluña): con una factura antigua, que lo vea un abogado.

El script marca las facturas de más de tres años y las de más de cinco.

## Lo que esta skill no cubre

- **Deudas de una Administración.** La ley se les aplica, pero con los plazos y el trámite de la contratación pública.
- **Facturas discutidas.** Si el cliente no paga porque discute el trabajo, la deuda no es pacífica: primero se resuelve eso.
- **Clientes en concurso de acreedores.**
- **Clientes de fuera de España.**
- **Los intereses de un pagaré, un cheque o una letra impagados**, que se rigen por su propia ley (art. 3.2.b).

## Dónde está cada norma

| Norma | Dirección |
| --- | --- |
| Ley 3/2004, de medidas de lucha contra la morosidad en las operaciones comerciales | `https://www.boe.es/buscar/act.php?id=BOE-A-2004-21830` |
| Tipo del segundo semestre de 2026 | `https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-14327` |
| Código Civil, arts. 1964, 1967 y 1973 | `https://www.boe.es/buscar/act.php?id=BOE-A-1889-4763` |

# Acordar los datos

Qué se quiere sacar de cada documento. Se acuerda una vez, se guarda en `campos.json` en la carpeta de trabajo y vale para todas las tandas siguientes.

## Cómo preguntarlo

Una sola pregunta, con una propuesta delante. Mira dos o tres de los documentos, y el perfil, y propón la lista:

> De cada factura puedo sacar: proveedor, NIF, número, fecha, base, IVA, total e IBAN. ¿Quitas alguno o falta alguno? Dime también si alguno lo necesitas sí o sí.

- Una sola pregunta. Lo que se pueda decidir con una regla de esta skill no se pregunta: un documento con varios productos va a una fila por producto; un dato dudoso se deja vacío y se dice después.
- Entre cinco y doce datos. Con más, la revisión cuesta más que copiar a mano.
- Con los nombres que usa su programa, si el perfil dice cuál es: la tabla va a acabar ahí.
- «Sí o sí» es `obligatorio`: si el documento no lo trae, irá a la lista de revisión.

## El formato

```json
{
  "campos": [
    {"nombre": "proveedor", "tipo": "texto", "obligatorio": true},
    {"nombre": "nif", "tipo": "nif", "obligatorio": true},
    {"nombre": "numero", "tipo": "texto", "obligatorio": true},
    {"nombre": "fecha", "tipo": "fecha", "obligatorio": true},
    {"nombre": "base", "tipo": "importe"},
    {"nombre": "iva", "tipo": "importe"},
    {"nombre": "total", "tipo": "importe", "obligatorio": true},
    {"nombre": "iban", "tipo": "iban"}
  ],
  "sumas": [{"total": "total", "sumandos": ["base", "iva"]}],
  "clave": ["nif", "numero"]
}
```

| Parte | Qué es |
| --- | --- |
| `nombre` | El nombre de la columna. Sin espacios ni tildes si va a importarse en otro programa. |
| `tipo` | `texto`, `numero`, `importe`, `fecha`, `nif`, `iban`, `email` o `telefono`. Decide cómo se comprueba. |
| `obligatorio` | `true` si un documento sin ese dato tiene que revisarse. Por defecto, no. |
| `sumas` | Opcional. Datos que tienen que sumar otro. Si en un documento no suman, se avisa: o el documento está mal o se ha leído mal. |
| `clave` | Opcional. Los datos que juntos identifican un documento. Si dos documentos coinciden en todos, se avisa de que puede ser el mismo dos veces. |

## Qué tipo poner

| El dato es | Tipo | Por qué |
| --- | --- | --- |
| Un nombre, un número de factura o de pedido, una referencia, una dirección | `texto` | Se comprueba que está escrito así en el documento. Un número de factura no es un `numero`: `2026-031` no es una cantidad. |
| Dinero | `importe` | Se lee igual escrito `1.234,56` que `1,234.56`. |
| Unidades, kilos, bultos, palés | `numero` | Como un importe, pero exacto. |
| Una fecha | `fecha` | Se lee en cualquier formato, si trae día, mes y año. |
| NIF, CIF, NIE | `nif` | Además se comprueba su letra o dígito de control. |
| Número de cuenta | `iban` | Además se comprueba su control. |

## Listas de partida

Sirven para proponer, no para imponer.

- **Facturas de proveedores**: proveedor, nif, numero, fecha, base, iva, total, iban. Suma: total = base + iva. Clave: nif y numero.
- **Pedidos que llegan por correo**: cliente, referencia, fecha_pedido, fecha_entrega, producto, cantidad, direccion_entrega, contacto. Clave: cliente y referencia.
- **Solicitudes de presupuesto**: nombre, empresa, email, telefono, que_pide, para_cuando.
- **Justificantes de pago**: pagador, fecha, importe, concepto, cuenta_origen.

## Cuando cambian los datos

Si la persona quiere añadir o quitar un dato, se cambia `campos.json` y se dice que las tablas hechas antes no lo tienen. No se mezclan tandas hechas con listas distintas.

# Cómo contar el resultado de la auditoría

Quien lee esto lleva un negocio, no una web. Quiere saber si hay algo roto, qué es lo primero y a quién se lo encarga.

## La estructura

1. **El marcador.** Cuántas de las nueve están bien, cuántas con aviso y cuántas fallan, y cuántas páginas se han mirado.
2. **Lo que falla**, de la comprobación con el número más bajo a la del más alto: las primeras rompen más. Una frase por fallo, con el ejemplo de la hoja y a quién se le pide.
3. **Los avisos**, agrupados en una o dos frases.
4. **Lo que está bien**, en una línea. Nombra lo que más cuesta: que el texto llega sin JavaScript, que los rastreadores entran.
5. **Lo que no se ha podido comprobar**, si hay algo, y cómo comprobarlo.
6. **El límite.** Una frase: esto asegura que una IA pueda leer la web, no que la recomiende.

Después, el nombre del fichero y dónde está.

## Ejemplo

> De las nueve comprobaciones, cinco están bien, dos tienen aviso y dos fallan. He mirado las 23 páginas del sitemap.
>
> Lo más grave: nueve páginas dicen que su versión buena es la portada, así que para un buscador esas nueve no existen. Lo arregla quien mantiene la web, en la plantilla.
>
> Además, `robots.txt` tiene un apartado para GPTBot que no repite las protecciones del general: ese rastreador puede entrar en `/panel` y `/api`. Es un fichero de texto; basta copiar las líneas `Disallow` en su apartado.
>
> Avisos: cinco páginas no llevan datos estructurados y dos repiten el mismo titular.
>
> Lo que está bien: el texto de todas las páginas llega sin JavaScript y todas las entradas al dominio acaban en la misma dirección.
>
> Arreglar esto hace que un asistente pueda leerte. Que te recomiende depende de lo que ofreces y de que haya quien lo cuente.
>
> La hoja está en `visibilidad-en-ia.xlsx`.

## Reglas

- Sin siglas sin explicar. «Datos estructurados», no «JSON-LD»; «dirección canónica», no «canonical» a secas. La palabra técnica va entre paréntesis una vez, para que pueda pedírselo a quien le lleva la web.
- Cada fallo lleva su ejemplo real de la hoja: una dirección, un nombre, una ruta.
- No digas «optimizar», «posicionar» ni «mejorar el SEO». Di qué se cambia.
- Nunca prometas apariciones, posiciones ni plazos. Un asistente no relee internet cada día: un cambio puede tardar semanas en notarse, y puede no notarse.
- Si no hay fallos, dilo en la primera línea y pasa pronto a lo que la auditoría no mira: preguntar a los asistentes por el negocio, la ficha de Google, las reseñas. Los avisos, si los hay, en dos líneas.
- Si la persona pregunta por qué no aparece y la web sale limpia, la respuesta honrada es que la causa no está en que la web no se pueda leer, y que esta auditoría no puede decir cuál es. No inventes un motivo.
- Si quien lo configura es un asesor (`quien_configura: asesor`), el resumen puede ser técnico: usa las palabras exactas y da el arreglo, no a quién pedírselo.

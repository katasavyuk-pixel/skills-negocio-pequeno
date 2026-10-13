# Las nueve comprobaciones

Qué mira cada una, por qué importa, cómo se arregla y a quién se le pide. El orden es el de la hoja. Las tres primeras rompen todo lo demás si están mal: unas preguntas frecuentes impecables no arreglan una página que no responde.

## Contenido

- 1. Cada página pública responde y no redirige
- 2. Cada página declara su propia dirección
- 3. Los rastreadores de IA pueden entrar, y lo privado sigue cerrado
- 4. El negocio se llama igual en todas partes
- 5. Las páginas llevan datos estructurados
- 6. Los datos estructurados no dicen nada que no se vea
- 7. El texto está en la página sin ejecutar JavaScript
- 8. Cada página tiene un titular propio
- 9. Todas las entradas al dominio acaban en el mismo sitio
- Lo que la auditoría no mira
- A quién se le pide cada arreglo

## 1. Cada página pública responde y no redirige

**Por qué.** Un rastreador pide un número limitado de páginas de cada web. Cada redirección gasta una petición y cada página que no existe la desperdicia. Lo que no llega a leer no lo puede citar.

**Qué mira.** Cada dirección del sitemap: tiene que responder 200, sin saltar a otra.

**Cómo se arregla.** El sitemap anuncia la dirección final de cada página, y solo páginas que existen y se pueden leer. Si sale «sin comprobar», no hay sitemap: se crea y se declara en `robots.txt`.

## 2. Cada página declara su propia dirección

**Por qué.** La dirección canónica le dice a un buscador cuál es la versión buena de una página. Si varias páginas declaran ser la portada, se le está diciendo que esas páginas no existen.

**Qué mira.** La etiqueta `link rel="canonical"` de cada página, comparada con la dirección de esa misma página.

**Cómo se arregla.** Cada página lleva en su canónica su propia dirección. Es un fallo frecuente en webs hechas con plantilla: la plantilla pone la de la portada en todas.

## 3. Los rastreadores de IA pueden entrar, y lo privado sigue cerrado

**Por qué.** `robots.txt` es lo primero que pide un rastreador. Tiene una trampa: **un rastreador que encuentra un apartado con su nombre ignora el apartado general por completo.** Darle la bienvenida a uno con un `Allow: /` a secas le abre todo lo que estaba cerrado para los demás.

**Qué mira.** Dos cosas: que ninguno de estos rastreadores tenga la web entera cerrada, y que cada apartado con nombre repita las protecciones del general. Los nombres: GPTBot, OAI-SearchBot, ChatGPT-User, PerplexityBot, ClaudeBot, Claude-Web, Google-Extended, Applebot-Extended, meta-externalagent, CCBot.

**Cómo se arregla.** En cada apartado con nombre se repiten las mismas líneas `Disallow` del apartado general. Cerrar la web a un rastreador es una decisión legítima: si es a propósito, se dice y no se cuenta como error.

## 4. El negocio se llama igual en todas partes

**Por qué.** Los datos estructurados dicen «esta página habla de esta entidad». Si la misma entidad aparece con tres nombres, un sistema que intente saber quién es recibe tres respuestas y no se fía de ninguna.

**Qué mira.** El nombre de la organización o del negocio local en los datos estructurados de todas las páginas, y lo compara con el `nombre` del perfil. En una marca personal mira a la persona.

**Cómo se arregla.** Se elige una forma de escribir el nombre y se usa esa en toda la web, en la ficha de Google y en los directorios. Con tildes, sin «S.L.» unas veces sí y otras no.

## 5. Las páginas llevan datos estructurados

**Por qué.** Los datos estructurados son rellenarle la ficha a la máquina en vez de dejar que la deduzca del diseño: quién es el negocio, qué ofrece, dónde está, cuánto cuesta. Una página sin ellos no está prohibida: pide que la interpreten a ojo.

**Qué mira.** Que cada página tenga al menos un bloque `application/ld+json`, y que se pueda leer.

**Cómo se arregla.** Por orden: la portada (negocio, dirección, teléfono, horario), las páginas de servicios y precios, y las preguntas frecuentes. Muchos gestores de contenido lo hacen con una opción o un complemento.

## 6. Los datos estructurados no dicen nada que no se vea

**Por qué.** Declarar en el marcado preguntas y respuestas que no están a la vista en la página es lo que las directrices de los buscadores tratan como contenido engañoso. Es la comprobación que más gente se salta y la que puede costar una penalización.

**Qué mira.** Cada pregunta declarada en los datos estructurados, buscada en el texto visible de su página.

**Cómo se arregla.** Se quita del marcado lo que no se lee en la página, o se enseña en la página.

## 7. El texto está en la página sin ejecutar JavaScript

**Por qué.** Es la que decide si la web existe para una máquina. Muchos rastreadores no ejecutan JavaScript, o lo hacen mucho más tarde. Si el texto aparece solo después de cargar el programa de la página, para ellos la página está vacía, por bien que se vea en un navegador.

**Qué mira.** Las palabras de texto visible que llegan en el HTML de cada página, y si páginas distintas sirven exactamente el mismo texto.

**Cómo se arregla.** Lo hace quien desarrolló la web. Las palabras para pedirlo: «renderizado en servidor» o «HTML estático». No se arregla con contenido nuevo: el contenido ya está, no llega.

## 8. Cada página tiene un titular propio

**Por qué.** El titular principal es la respuesta corta a «¿de qué va esta página?». Ocho páginas con el mismo son, para una máquina, ocho copias de una.

**Qué mira.** Que cada página tenga un `h1`, uno solo, y distinto del de las demás.

**Cómo se arregla.** Un titular por página que diga lo que esa página tiene de propio: «Cocinas a medida en Zaragoza», no «Servicios».

## 9. Todas las entradas al dominio acaban en el mismo sitio

**Por qué.** Si una forma de escribir la dirección no resuelve o sirve un certificado caducado, parte de quien enlaza y de quien rastrea se queda fuera antes de leer una línea. No se nota desde dentro, porque quien lleva la web entra siempre por la dirección buena.

**Qué mira.** La dirección con `http` y con `https`, y con y sin `www` cuando es un dominio principal: todas tienen que acabar en la misma, con `https` y sin error de certificado. A un subdominio (`tienda.ejemplo.es`) no se le exige `www`.

**Cómo se arregla.** Lo hace quien lleva el alojamiento o el dominio. Antes de renovar un certificado, comprobar que el dominio está asignado a la web: un dominio sin asignar no tiene certificado que renovar.

## Lo que la auditoría no mira

Se dice en el resumen si alguien lo da por cubierto.

- **Si un asistente recomienda ya el negocio.** Se comprueba preguntándoselo: cinco preguntas que haría un cliente («¿qué carpintero me recomiendas en Zaragoza para una cocina a medida?»), en tres asistentes, apuntando fecha y respuesta. Se repite al mes.
- **La ficha de Google, las reseñas y los directorios.** Pesan tanto como la web en un negocio local.
- **La calidad de lo que dice la web.** Que se pueda leer no hace que merezca citarse.
- **`llms.txt`.** El resumen dice si existe. Es un fichero opcional que describe la web a quien quiera leerlo; no es un requisito de ningún buscador ni garantiza nada.

## A quién se le pide cada arreglo

| Comprobación | Quién |
| --- | --- |
| 1, 2, 5, 6, 8 | Quien mantiene la web o su gestor de contenidos. |
| 3 | Quien mantiene la web. Es un fichero de texto. |
| 4 | El negocio decide el nombre; quien mantiene la web lo aplica. |
| 7 | Quien desarrolló la web. Puede ser un cambio grande. |
| 9 | Quien lleva el alojamiento o el dominio. |

---
name: empezar
description: 'Da la bienvenida y adapta las demás skills a un negocio concreto: pregunta a qué se dedica, a quién vende, cómo cobra y qué quiere resolver primero, y lo guarda en un perfil. Úsala la primera vez, cuando pidan "empezar", "configurar", "adaptar esto a mi negocio", "por dónde empiezo" o "actualizar el perfil", y cuando otra skill no encuentre el perfil del negocio.'
license: MIT
metadata:
  author: Kata Ivanovych
  version: "2.0.1"
---

# Empezar

La bienvenida del paquete. Conoce el negocio una vez, lo guarda en `perfil-negocio.md` y dice por dónde empezar. No hace trabajo de administración: deja a las demás skills listas para hacerlo con los datos de este negocio y no con un ejemplo genérico.

## Flujo

Siete pasos. Lleva la cuenta para ti; a la persona no se le enseña la lista.

1. Buscar un perfil que ya exista
2. Dar la bienvenida
3. Preguntar, en tres tandas
4. Escribir el perfil
5. Validarlo
6. Enseñarlo y corregir
7. Decir por dónde empezar

### 1. Buscar un perfil que ya exista

Búscalo como indica [references/perfil.md](references/perfil.md). Si existe, no des la bienvenida: resume lo que dice en cinco líneas, pregunta qué ha cambiado, cambia solo eso y sigue en el paso 5.

### 2. Dar la bienvenida

Di esto, con estas ideas y más o menos esta longitud, y **en el mismo mensaje** haz la primera tanda de preguntas. Ajusta el trato si ya sabes cuál prefiere; si no, de tú.

> Hola. Estas skills hacen trabajo de oficina de un negocio pequeño: reclamar lo que te deben, ver venir la caja, dejar el trimestre preparado. Para hacerlo con tus datos y no con un ejemplo genérico necesito conocer el negocio.
>
> Son tres tandas de preguntas y unos tres minutos. Lo que no sepas se queda apuntado como pendiente. Lo que me digas se guarda en un fichero tuyo, `perfil-negocio.md`, que puedes abrir y cambiar cuando quieras.

No añadas una lista de funciones ni expliques qué es una skill.

### 3. Preguntar, en tres tandas

Las preguntas, sus opciones y a qué dato del perfil va cada respuesta están en [references/preguntas.md](references/preguntas.md). Léelo antes de preguntar.

- Tres tandas, tres preguntas como mucho en cada una. Espera la respuesta antes de pasar a la siguiente.
- Lo que la persona ya haya contado no se pregunta: se confirma en una línea.
- Las preguntas que traen tabla de opciones se hacen con opciones, **cuatro como mucho** a la vista. Las demás, con un ejemplo de respuesta.
- «No lo sé» se ofrece solo donde `preguntas.md` lo marca. Ahí se apunta como `pendiente`, sin insistir. Una respuesta dudosa («creo que no») también es `pendiente`, y se le dice.
- Si tu entorno tiene una herramienta para preguntar con opciones, úsala. Si no, numera las opciones en el texto.
- No expliques leyes ni impuestos aquí. Eso lo hace cada skill cuando le toca.
- La redacción se adapta a la persona: si lo está montando para un cliente, se habla de «el negocio de tu cliente» y las opciones se pasan a tercera persona. El conjunto de opciones y las claves no cambian.

### 4. Escribir el perfil

Copia [assets/perfil-negocio.plantilla.md](assets/perfil-negocio.plantilla.md), rellena cada clave con los valores exactos que admite (tabla de [references/perfil.md](references/perfil.md)) y pon la fecha de hoy en `actualizado`. Guárdalo como `perfil-negocio.md`:

- **Con carpeta de trabajo**: en su raíz.
- **Sin carpeta** (una conversación suelta): entrégalo como fichero descargable y di, en una frase, que lo adjunte al empezar o lo añada al conocimiento de su proyecto para que las demás skills lo encuentren.

[ejemplos/perfil-negocio.md](ejemplos/perfil-negocio.md) es un perfil ya relleno, de un negocio inventado: sirve para ver el formato, nunca para copiar valores.

### 5. Validarlo

Desde la carpeta de esta skill:

```bash
python3 scripts/validar_perfil.py RUTA/perfil-negocio.md
```

- `PERFIL NO VÁLIDO`: corrige lo que señala cada línea y vuelve a ejecutarlo. No sigas hasta ver `PERFIL VÁLIDO`.
- Las líneas con `!` son avisos: cuéntaselos a la persona en el paso 6, cada uno en una frase.
- La línea con `…` lista lo que ha quedado pendiente: se nombra en el paso 6.
- Si no puedes ejecutar Python, comprueba cada clave contra la tabla de [references/perfil.md](references/perfil.md) y di que la comprobación automática no se ha hecho.

### 6. Enseñarlo y corregir

Enseña el perfil como un resumen de seis a ocho líneas en lenguaje normal, no el fichero crudo. Di dónde ha quedado guardado, qué ha quedado pendiente y los avisos del validador. Pregunta una sola vez: «¿Hay algo que corregir?». Si corrige algo, cámbialo y vuelve al paso 5.

### 7. Decir por dónde empezar

Con la `prioridad` del perfil, elige la skill y lo que hay que traer según [references/por-donde-empezar.md](references/por-donde-empezar.md). Termina diciendo qué skill usar y qué traer, por ejemplo: «Empieza por reclamar las facturas: pásame el listado de las que tienes sin cobrar, tal como lo saque tu programa».

- Si dio dos prioridades, se empieza por la guardada y se nombra la otra como lo siguiente.
- Si la skill que toca no está instalada, dilo en una frase y recomienda la siguiente de la lista que sí lo esté.
- Si no hay ninguna otra instalada, di cuál instalar y qué traer cuando la tenga. No describas lo que no puede usar todavía.

## Lo que no hace

- No pide contraseñas, números de cuenta ni datos de clientes. Si alguien los ofrece, se le dice que el perfil no es el sitio.
- No envía el perfil a ningún sitio ni lo copia en lo que se entrega a terceros.
- No hace más de nueve preguntas, más una de seguimiento. Lo que falte lo preguntará cada skill cuando lo necesite.

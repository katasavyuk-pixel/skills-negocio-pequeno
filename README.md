# Skills para llevar un negocio pequeño con IA

Seis skills en español que hacen trabajo de oficina de un negocio pequeño y dejan un fichero hecho: lo que te deben con los intereses que la ley añade, la semana en que la caja se queda corta, las facturas del trimestre revisadas antes de mandarlas a la gestoría.

Empiezan por una bienvenida que pregunta por tu negocio una vez, lo guarda, y hace que las demás trabajen con tus datos y no con un ejemplo genérico.

Funcionan en la aplicación de Claude, en Claude Code, en Codex, en OpenCode y en cualquier agente que lea el formato Agent Skills. Cómo instalarlas en cada uno, en [Instalar](#instalar).

[English summary](README.en.md)

## Qué hay

| Skill | Qué entrega | Cuándo se usa |
| --- | --- | --- |
| [`empezar`](skills/empezar/SKILL.md) | El perfil de tu negocio en un fichero, y por dónde empezar. | La primera vez. |
| [`reclamar-facturas`](skills/reclamar-facturas/SKILL.md) | Una hoja con cada factura vencida, sus intereses de demora y los 40 € por factura que añade la ley, y el borrador de la reclamación que toca a cada cliente. | Cada semana, o cuando un cliente no paga. |
| [`prever-caja`](skills/prever-caja/SKILL.md) | Una hoja con trece semanas de caja y tres escenarios: en qué semana te quedas corto y de qué cliente dependes. | Una vez al mes, o antes de un gasto grande. |
| [`cerrar-trimestre`](skills/cerrar-trimestre/SKILL.md) | Una hoja con los errores de las facturas del trimestre, el IVA por tipo y los plazos. | Al acabar marzo, junio, septiembre y diciembre. |
| [`visibilidad-en-ia`](skills/visibilidad-en-ia/SKILL.md) | Una hoja con nueve comprobaciones de si un asistente de IA puede encontrar y leer tu web, y a quién pedirle cada arreglo. | Antes y después de tocar la web. |
| [`datos-de-documentos`](skills/datos-de-documentos/SKILL.md) | Una tabla con los datos de tus facturas, pedidos o correos, cada uno con el trozo del documento del que sale. | Cuando copias datos a mano. |

## Qué se ve al usarlas

Lo que sale con los datos de ejemplo que trae cada skill. Son inventados; las cuentas, no.

- **`reclamar-facturas`**: 15.605,00 € pendientes en cuatro facturas, y 417,86 € más que la ley añade y que nadie había reclamado. Una factura «a 90 días» resulta llevar 44 días de retraso y no 14, porque la ley no admite plazos de más de 60.
- **`prever-caja`**: con 9.420,75 € en la cuenta, la caja baja del mínimo en dos semanas y entra en negativo a final de diciembre. El 60 % de lo que se espera cobrar depende de un solo cliente.
- **`cerrar-trimestre`**: en diecinueve facturas, cinco errores y dos facturas que faltan, encontrados antes de mandarlas a la gestoría.
- **`datos-de-documentos`**: de cuatro documentos, quita un total que se había sumado en vez de leerse y un IBAN que no estaba en el correo, y avisa de que dos son la misma factura.
- **`visibilidad-en-ia`**: en la web simulada de sus pruebas, ninguna de las nueve comprobaciones sale bien. Entre lo que encuentra: un rastreador con acceso a lo que estaba cerrado para los demás, una página que llega vacía si no se ejecuta JavaScript y un negocio que se llama de dos formas.

## Cómo funcionan

Las seis están hechas igual:

1. **Leen el perfil del negocio**, `perfil-negocio.md`, que crea `empezar`: a qué te dedicas, a quién vendes, cómo cobras, de tú o de usted. Si no existe, preguntan solo lo que necesitan.
2. **El modelo reúne y explica; un script hace lo que no se puede dejar a ojo.** Las sumas, los intereses, las comprobaciones de un NIF o de un total las hace un programa corto, siempre igual. El modelo no calcula.
3. **Dejan un fichero**: una hoja de Excel que se abre en cualquier programa, y un resumen corto que empieza por la respuesta.
4. **No envían nada ni presentan nada.** Dejan borradores y hojas. Lo manda quien lleva el negocio.

## Antes de instalar nada, léelas

Una skill es un conjunto de instrucciones que el agente (Claude, Codex, OpenCode…) sigue cuando la tarea encaja. Estas llevan además scripts en Python, y conviene saber qué hacen antes de dejarlos correr en tu equipo:

- Usan **solo la biblioteca estándar** de Python. No instalan nada.
- **No abren conexiones**, con una excepción: `visibilidad-en-ia` descarga las páginas públicas de la web que le digas, y ninguna otra.
- **No borran ni envían nada.** Leen los ficheros que les das y escriben las hojas.
- Son cortos y están comentados. Cada skill tiene los suyos en su carpeta `scripts/`.

Nada de esto hay que creérselo: [`.github/validar.py`](.github/validar.py) lo comprueba en cada cambio, y falla si un script importa algo de red o lanza otro programa sin que su skill esté en la lista con el motivo.

## Instalar

Las seis siguen el formato abierto de Agent Skills: cada una es una carpeta con su `SKILL.md`, sus referencias y sus scripts, y la puede usar cualquier agente que lea ese formato. Abajo, cómo instalarlas en cada uno. Cada apartado dice si lo he probado o si sigo la documentación del agente.

Hace falta Python 3.9 o posterior donde se ejecuten los scripts. Las aplicaciones de Claude traen el suyo; en tu equipo, compruébalo con `python3 --version`. Los comandos `npx` necesitan además Node.js.

### En la aplicación de Claude, sin terminal

En claude.ai o en la aplicación de escritorio:

1. Abre **Personalización** y, dentro, **Plugins**.
2. Pulsa **Añadir** y elige **Añadir marketplace**.
3. Elige **Añadir desde un repositorio**, escribe `katasavyuk-pixel/skills-negocio-pequeno` y pulsa **Sincronizar**.
4. El plugin aparece en la lista. Pulsa **Añadir**.

Las seis quedan en tu cuenta. Se usan escribiendo `/` en un chat y eligiendo una, por ejemplo `/empezar`, o describiendo la tarea. Probado el 13 de octubre de 2026 en claude.ai, en español.

También se puede subir una sola skill en un ZIP (la carpeta dentro del ZIP, no los ficheros sueltos) desde el apartado **Skills** de la personalización. Ese camino no lo he probado.

### En Claude Code

```
/plugin marketplace add katasavyuk-pixel/skills-negocio-pequeno
/plugin install negocio-pequeno@kata-ivanovych
```

Quedan disponibles como `/negocio-pequeno:empezar`, `/negocio-pequeno:reclamar-facturas` y así con las demás. También se activan solas cuando lo que pides encaja con su descripción. Probado el 13 de octubre de 2026.

### En Codex

Codex lee el mismo marketplace que Claude Code, sin ficheros aparte:

```
codex plugin marketplace add katasavyuk-pixel/skills-negocio-pequeno
codex plugin add negocio-pequeno@kata-ivanovych
```

Abre una sesión nueva después de instalarlo. Las seis aparecen como `negocio-pequeno:empezar`, `negocio-pequeno:prever-caja` y así con las demás, y se activan solas cuando lo que pides encaja con su descripción.

Sin el marketplace, con el instalador de Agent Skills:

```
npx skills add katasavyuk-pixel/skills-negocio-pequeno -a codex
```

Las deja en `.agents/skills/` de la carpeta donde lo ejecutes; con `-g`, en `~/.agents/skills/`, para todos tus proyectos. Te pregunta cuáles instalar; con `-y`, instala las seis sin preguntar.

`visibilidad-en-ia` necesita salir a internet para descargar la web, y el sandbox de Codex no lo deja por defecto: su script dice entonces que no ha podido llegar a la web. Para esa auditoría, arranca Codex con `-c sandbox_workspace_write.network_access=true`.

Probado el 15 de octubre de 2026 con Codex CLI 0.162.1. Por los dos caminos, Codex ve las seis. Con las instaladas con `npx skills`, `prever-caja` hizo su hoja con los datos de ejemplo, y bastó con «Quiero empezar» para que arrancara la bienvenida; con las respuestas, `empezar` escribió el perfil y lo validó con su script.

### En OpenCode

```
npx skills add katasavyuk-pixel/skills-negocio-pequeno -a opencode
```

Las deja en `.agents/skills/` de la carpeta donde lo ejecutes; con `-g`, en `~/.config/opencode/skills/`. Probado el 15 de octubre de 2026 con OpenCode 1.18.35: ve las seis, y `prever-caja` hizo su hoja con los datos de ejemplo.

### En Antigravity

```
npx skills add katasavyuk-pixel/skills-negocio-pequeno -a antigravity
```

Las deja en `.agents/skills/` del proyecto, que según su documentación leen la aplicación, el IDE y la CLI de Antigravity. Para todos tus proyectos, la CLI las lee de `~/.gemini/antigravity-cli/skills/` (`-a antigravity-cli -g` las deja ahí) y la aplicación y el IDE, de `~/.gemini/config/skills/`, donde puedes copiarlas. No lo he probado.

### En Gemini CLI

```
npx skills add katasavyuk-pixel/skills-negocio-pequeno -a gemini-cli
```

Las deja en `.agents/skills/` del proyecto; con `-g`, en `~/.gemini/skills/`. Las dos rutas, según su documentación. No lo he probado.

### En Cursor

```
npx skills add katasavyuk-pixel/skills-negocio-pequeno -a cursor
```

Las deja en `.agents/skills/` del proyecto; con `-g`, en `~/.cursor/skills/`. Las dos rutas, según su documentación. No lo he probado.

### En GitHub Copilot

```
npx skills add katasavyuk-pixel/skills-negocio-pequeno -a github-copilot
```

Las deja en `.agents/skills/` del repositorio; con `-g`, en `~/.copilot/skills/`. Según su documentación, las leen el agente de Copilot en GitHub, la CLI de Copilot y el modo agente de VS Code y JetBrains. No lo he probado.

### En cualquier otro agente compatible con Agent Skills

```
npx skills add katasavyuk-pixel/skills-negocio-pequeno -a NOMBRE-DEL-AGENTE
```

Los nombres que admite `-a` están en la [lista de agentes del instalador](https://github.com/vercel-labs/skills#supported-agents).

Sin instalador también vale: copia la carpeta entera de cada skill (por ejemplo `skills/prever-caja/`, con todo lo que lleva dentro) en la carpeta de skills de tu agente. Cada carpeta funciona sola: no necesita nada de fuera de ella.

## Por dónde empezar

Escribe «quiero empezar». La bienvenida hace nueve preguntas en tres tandas, unos tres minutos, guarda las respuestas en `perfil-negocio.md` y te dice cuál de las otras usar primero. El perfil es un fichero de texto tuyo: se puede abrir y cambiar.

Si prefieres ir directo a una, también vale: te preguntará lo que le falte.

Cada skill trae un ejemplo resuelto en su carpeta `ejemplos/`. Todos los negocios, personas, NIF y cuentas que aparecen en ellos son inventados.

## Lo que hacen y lo que no

- **No envían nada.** Los correos y las cartas se quedan en borrador.
- **No presentan impuestos ni rellenan modelos.** Dejan los libros revisados para quien lo hace.
- **No inventan.** Un importe que no se sabe no se pone a cero: se deja fuera y se dice. Un dato que no está en el documento se deja vacío.
- **No son asesoría jurídica ni fiscal.** Calculan con las normas que citan y lo dicen. Antes de ir a un juzgado o de presentar una declaración, que lo vea quien corresponde.
- **No prometen resultados.** Dicen lo que se puede reclamar, no que se vaya a cobrar; que una web se puede leer, no que la vayan a recomendar.

## Lo legal y lo fiscal

`reclamar-facturas` y `cerrar-trimestre` aplican normas españolas. Cada cifra y cada regla lleva su artículo, y todo se leyó en el texto consolidado del BOE el **13 de octubre de 2026**:

- El tipo legal de interés de demora de cada semestre, desde el segundo de 2021, con la resolución de la que sale.
- La Ley 3/2004 (plazos de pago, intereses y compensación), la Ley Orgánica 1/2025 (negociación previa a un juicio) y los artículos del proceso monitorio.
- El Reglamento de facturación (Real Decreto 1619/2012) y los tipos de IVA y de recargo de equivalencia.

Las normas cambian. Si usas esto mucho después de esa fecha, compruébalo. Cuando falta el tipo de un semestre, el script se para y dice cómo buscarlo: no calcula con uno supuesto.

Valen para el territorio común. En el País Vasco, Navarra, Canarias, Ceuta y Melilla cambian impuestos, modelos y plazos, y las skills avisan de lo que no cubren.

## Estado

- **Versión 2.1.0.** La 2.0 es nueva: sustituye a las ocho skills de solo instrucciones de la 1.x. La 2.0.1 arregla la instalación desde la aplicación de Claude. La 2.1 explica cómo instalarlas en Codex, OpenCode y los demás agentes compatibles con Agent Skills.
- **Pruebas de los scripts**: en Python 3.9 y 3.13, en cada cambio. Comparan cada cifra con la cuenta hecha a mano.
- **Pruebas de las skills**: cada una la ha ejecutado de principio a fin un modelo que no la conocía, sobre un negocio inventado, contestando alguien por el cliente. Lo que falló se corrigió.
- **Instalación**: probada desde cero en Claude Code, con `npx skills add` y en la aplicación de Claude (claude.ai) el 13 de octubre de 2026, donde la bienvenida se ejecutó en un chat; y en Codex y OpenCode el 15 de octubre, donde `prever-caja` hizo su hoja y, en Codex, `empezar` escribió y validó un perfil.
- **Lo que no se ha probado**: su uso en negocios reales, Cowork, los scripts de las otras cinco dentro de la aplicación de Claude (allí solo se ha ejecutado la bienvenida) y la instalación en Antigravity, Gemini CLI, Cursor y GitHub Copilot, que aquí se explica según su documentación. Si algo no encaja con tu caso, dímelo.
- **Fallos conocidos**: en [CHANGELOG.md](CHANGELOG.md).

Si una skill hace algo que no debería, abre una incidencia en este repositorio o escríbeme a info@ianexora.com.

## Quién las hace

Soy Kata Ivanovych. Documento en [kata.ianexora.com](https://kata.ianexora.com) los sistemas de IA que pongo en marcha en un negocio pequeño: qué hacen, sus números y lo que se rompió.

## Licencia

[MIT](LICENSE). Puedes usarlas, cambiarlas y adaptarlas a tu negocio o al de tus clientes.

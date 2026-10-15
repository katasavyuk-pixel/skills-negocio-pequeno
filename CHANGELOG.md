# Cambios

## 2.1.0 · 2026-10-15

Las skills ya no son solo para Claude: se instalan y se usan en Codex, en OpenCode y en cualquier agente que lea el formato Agent Skills. Las skills no cambian; cambia cómo se instalan y lo que lo explica.

- **Añadido**: en el README, cómo instalarlas en cada agente: la aplicación de Claude, Claude Code, Codex, OpenCode, Antigravity, Gemini CLI, Cursor, GitHub Copilot y cualquier otro compatible. Cada apartado dice si está probado o sale de la documentación del agente.
- **Probado**: Codex se instala desde el mismo marketplace que Claude Code (`codex plugin marketplace add` y `codex plugin add negocio-pequeno@kata-ivanovych`), sin un manifiesto propio, y también con `npx skills add … -a codex`; OpenCode, con `npx skills add … -a opencode`. En los dos, `prever-caja` hizo su hoja con los datos de ejemplo; en Codex, `empezar` dio la bienvenida, escribió el perfil y lo validó. Antigravity, Gemini CLI, Cursor y GitHub Copilot no los he probado.
- **Aviso**: en Codex, `visibilidad-en-ia` no llega a la web con el sandbox por defecto, que no tiene red. El script lo dice y no da ningún resultado. Para esa auditoría, Codex se arranca con `-c sandbox_workspace_write.network_access=true`.
- **Añadido**: `.github/validar.py` falla si los comandos de instalación de un README no coinciden con el repositorio, el plugin y el marketplace publicados, o si el README no dice la versión.
- **Corregido**: la página del plugin apuntaba a `kata.ianexora.com/sistemas`. Ahora apunta a `kata.ianexora.com/marketplace`.
- **Cambiado**: un comentario de `hoja_xlsx.py` hablaba solo del sandbox de las aplicaciones de Claude.

## 2.0.1 · 2026-10-13

- **Corregido**: el repositorio no se podía añadir desde la aplicación de Claude (Personalización > Plugins > Añadir marketplace). El `source` del plugin era `"."`, que Claude Code y `npx skills add` aceptan y la aplicación rechaza con «External plugin sources must be objects with a 'source' field». Ahora es `"./"`. Lo vi al instalarlo allí por primera vez; hasta entonces solo lo había instalado desde la terminal.
- **Corregido**: la aplicación enseñaba el plugin como «Negocio pequeno». Lleva ya su nombre visible, «Negocio pequeño».
- **Añadido**: `.github/validar.py` falla si el `source` de un plugin no empieza por `./`.
- **Añadido**: en el README, cómo instalarlo desde la aplicación de Claude, con los nombres de los menús en español.

## 2.0.0 · 2026-10-13

Seis skills nuevas sustituyen a las ocho de la 1.x. Aquellas eran solo instrucciones: decían al modelo cómo redactar cosas que ya redacta sin ellas, y tenerlas instaladas no cambiaba nada en un negocio.

Las nuevas se adaptan a cada negocio con una bienvenida, hacen las cuentas con un script y dejan un fichero:

- `empezar`: nueve preguntas, una vez, y el perfil del negocio en `perfil-negocio.md`.
- `reclamar-facturas`: lo que se debe, con los intereses de demora y los 40 € por factura de la Ley 3/2004, y la reclamación que toca a cada cliente.
- `prever-caja`: trece semanas de caja en tres escenarios.
- `cerrar-trimestre`: las facturas del trimestre revisadas, el IVA por tipo y los plazos.
- `visibilidad-en-ia`: nueve comprobaciones de si un asistente de IA puede leer una web.
- `datos-de-documentos`: datos de facturas, pedidos y correos en una tabla, cada uno con el trozo del documento del que sale.

**Desaparecen**: `seguimiento-cobros`, `proyeccion-caja`, `generar-factura`, `cierre-mensual`, `documentar-sop`, `onboarding`, `informe-semanal` y `seguir-pipeline`.

**Lo que salió mal al probarlas**, y cómo quedó:

- La bienvenida enseñaba hasta dieciséis opciones numeradas en una sola pregunta sobre impuestos. Ahora esa pregunta es abierta, con un ejemplo, y ninguna enseña más de cuatro opciones salvo la de prioridades.
- La bienvenida ofrecía «no lo sé» en preguntas que cualquiera sabe contestar de su negocio. Ahora solo donde tiene sentido.
- La auditoría de visibilidad exigía un «www» delante de un subdominio, que nadie escribe, y no reconocía una marca personal como identidad. Dos falsos positivos, vistos al ejecutarla contra una web real.
- El resumen de la previsión de caja decía que cobrar con retraso «daba el mismo resultado» cuando una semana concreta pasaba de −229 € a −7.969 €. El script da ahora el saldo de cada semana en cada escenario.
- La revisión del trimestre tomaba una factura apuntada dos veces por una factura con dos tipos de IVA, y avisaba de que el total no sumaba en vez de decir que estaba repetida.
- La revisión del trimestre avisaba de que faltaba una factura cuando un proveedor empezaba a facturar el segundo mes. Ahora solo pregunta por el mes de en medio y por el último.
- El requerimiento formal no llevaba los datos para pagar.
- `datos-de-documentos` no sabía qué hacer con un pedido de varios productos. Ahora va una fila por línea.

## 1.0.1 · 2026-10-13

- **Corregido**: cinco skills (`cierre-mensual`, `documentar-sop`, `informe-semanal`, `onboarding` y `seguimiento-cobros`) no se instalaban con `npx skills add`. Su descripción llevaba dos puntos sin comillas, que no es YAML válido. Claude Code lo toleraba y cargaba las ocho; el otro instalador se saltaba esas cinco. Lo vi al instalar el paquete desde cero con los dos, antes de abrir el repositorio. Ahora todas las descripciones van entre comillas.
- **Añadido**: una comprobación en cada cambio (`.github/validar.py`) que lee la cabecera de cada skill con un lector de YAML estricto.

## 1.0.0 · 2026-10-13

Primera versión, que no llegó a publicarse. Ocho skills de solo instrucciones:

- Finanzas: `seguimiento-cobros`, `proyeccion-caja`, `generar-factura`, `cierre-mensual`.
- Operaciones: `documentar-sop`, `onboarding`, `informe-semanal`.
- Ventas: `seguir-pipeline`.

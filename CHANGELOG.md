# Cambios

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

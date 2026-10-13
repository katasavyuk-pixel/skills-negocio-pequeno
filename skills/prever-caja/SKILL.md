---
name: prever-caja
description: 'Proyecta la caja de un negocio semana a semana durante un trimestre y dice en qué semana se queda corto, en una hoja de Excel con tres escenarios. Úsala cuando pidan "previsión de caja", "cómo voy de tesorería", "llego a fin de mes", "puedo pagar las nóminas", "cuánto aguanto", o antes de un gasto grande, una contratación o un trimestre flojo.'
license: MIT
metadata:
  author: Kata Ivanovych
  version: "2.0.1"
---

# Prever la caja

Entrega dos cosas: `prevision-caja.xlsx`, con trece semanas y tres escenarios, y un resumen de cinco líneas que dice en qué semana la cuenta baja del mínimo y por qué.

Las cuentas las hace `scripts/prever.py`. Tu trabajo es reunir los movimientos sin que falte ninguno, pasarlos al formato que el script entiende y explicar el resultado. No sumes a mano ni corrijas una cifra del script: si un número parece raro, el error está en los movimientos.

## Flujo

Copia esta lista y márcala según avances:

```
- [ ] 1. Leer el perfil del negocio
- [ ] 2. Reunir saldo, cobros, pagos, gastos fijos e impuestos
- [ ] 3. Escribir movimientos.csv
- [ ] 4. Ejecutar el script hasta que no dé errores
- [ ] 5. Resolver cada aviso
- [ ] 6. Entregar la hoja y el resumen
```

### 1. Leer el perfil del negocio

Como indica [references/perfil.md](references/perfil.md). Esta skill usa:

| Dato | Para qué |
| --- | --- |
| `caja_minima_eur` | El saldo por debajo del cual se avisa (`--minimo`). Si está pendiente, pregúntalo: «¿Con cuánto en la cuenta estás tranquilo?». |
| `plazo_cobro_dias` | La fecha de cobro de una factura que no dice su vencimiento. |
| `forma`, `gestoria` | Qué impuestos preguntar y a quién pedirle el importe. |
| `territorio` | Si no es `comun`, ejecuta el script con `--sin-calendario-fiscal` y pregunta sus fechas de impuestos. |

### 2. Reunir los datos

Qué pedir, en qué orden y la lista de pagos que la gente olvida están en [references/que-pedir.md](references/que-pedir.md). Léelo antes de pedir nada.

Acepta los datos como vengan: una exportación del programa, una hoja, un PDF, una foto o una lista dictada. Lo que no se pueda leer con seguridad se pregunta; no se adivina.

### 3. Escribir movimientos.csv

El formato exacto y cómo convertir cada tipo de dato están en [references/formato-csv.md](references/formato-csv.md). Tres reglas que no admiten excepción:

- **Lo que falta no es cero.** Un impuesto o un gasto cuyo importe no se sabe no se apunta a cero: se deja fuera y se dice en el resumen que falta.
- **Importes como salen del banco**: con IVA incluido.
- **Nada anterior a la fecha del saldo**, salvo lo que sigue pendiente (una factura vencida sin cobrar, un pago atrasado). Lo ya cobrado o pagado está dentro del saldo.

### 4. Ejecutar el script

Desde la carpeta de esta skill:

```bash
python3 scripts/prever.py RUTA/movimientos.csv --saldo 9420.75 --fecha 2026-10-13 \
    --minimo 8000 --salida RUTA/prevision-caja.xlsx
```

- `--saldo` y `--fecha`: lo que hay en la cuenta y el día en que se miró. Si el saldo tiene más de tres días, pide uno nuevo.
- Si el script lista problemas, cada uno trae su línea: corrige el CSV y vuelve a ejecutarlo. No sigas hasta que termine sin errores.
- El script imprime un resumen en JSON. Los números de tu resumen salen de ahí, sin redondear ni recalcular.
- Si no puedes ejecutar Python, dilo y no entregues una previsión hecha a mano: una suma de noventa líneas sin comprobar es peor que no tenerla.

### 5. Resolver cada aviso

Cada línea de `avisos` del resumen es una pregunta pendiente, no un adorno:

| Aviso | Qué hacer |
| --- | --- |
| Cobros ya vencidos | Pregunta si de verdad los espera esta semana. Si no, quítalos del CSV, vuelve a ejecutar y dilo en el resumen. |
| Un cliente pesa más de un tercio | Nómbralo en el resumen con su porcentaje. |
| Vence la declaración trimestral y no hay pago de impuestos | Pregunta el importe, a la persona o a su gestoría. Si no se sabe, dilo en el resumen como lo primero que falta. |
| No hay cobros, o no hay pagos | Falta una lista entera. Pídela antes de entregar nada. |

Si cambias el CSV, vuelve al paso 4.

### 6. Entregar

La hoja y un resumen con la estructura de [references/como-contarlo.md](references/como-contarlo.md). Di dónde ha quedado el fichero.

## Un ejemplo resuelto

[ejemplos/movimientos.csv](ejemplos/movimientos.csv) es una carpintería de cuatro personas con 9.420,75 € en la cuenta el 13 de octubre de 2026 y un mínimo de 8.000 €. El script devuelve [ejemplos/resumen.json](ejemplos/resumen.json): si todo va según lo previsto baja del mínimo la semana del 26 de octubre y entra en negativo la del 28 de diciembre; si los cobros se retrasan catorce días, entra en negativo la del 26 de octubre; y el 60 % de lo que espera cobrar depende de un solo cliente.

## Lo que no hace

- No recomienda créditos, pólizas ni inversiones. Señala la semana y las tres palancas evidentes (adelantar un cobro, aplazar un pago, retrasar un gasto), y ahí para.
- No es contabilidad ni una previsión para presentar a un banco.
- No lee el banco por su cuenta: trabaja con lo que se le da.

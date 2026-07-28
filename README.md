# Sistema de Control de Inventario y Costos — Bodega LP02

Sistema de gestión de inventario y control de costos para la bodega LP02 de una minera chilena, en el área de un tranque de relaves. Reemplaza una operación basada en planillas Excel por una aplicación con base de datos única, formularios validados y monitoreo de indicadores en tiempo real.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-F2C811?logo=powerbi&logoColor=black)

A continuación se presenta el panel de control de existencias con alertas de stock mínimo y filtros dinámicos. Las capturas de este README presentan columnas y/o datos ocultos y a su vez no se publican los datos reales por confidencialidad.

![Panel de control de existencias con alertas de stock](docs\img\control_stock.png)


---

## El problema

La bodega operaba sin un registro digital auditable: la gestión dependía de planillas Excel dispersas y de conocimiento no documentado. Esto producía tres efectos concretos:

- **Compras duplicadas**, por falta de visibilidad del stock real.
- **Diferencias de inventario** que en buena parte no eran pérdidas, sino errores de registro.
- **Auditorías lentas**, con horas de limpieza y consolidación manual antes de poder analizar nada.

## La solución

Una aplicación en Streamlit sobre SQLite que centraliza el catálogo de insumos y todos los movimientos de entrada y salida, con validación en el punto de ingreso y nomenclatura normalizada. Un tablero en Power BI consume la misma base de datos para el seguimiento presupuestario.

### Alcance y decisiones de diseño

El sistema fue construido para **una bodega específica**, con un operador principal y un volumen transaccional acotado. Esa restricción es deliberada y explica las decisiones técnicas:

- **SQLite en entorno local**, sin servidor ni infraestructura que mantener. Para un solo punto de uso, una base embebida elimina toda la complejidad operativa de un motor cliente-servidor sin costo en funcionalidad.
- **Stack íntegramente open source**, sin licencias ni dependencia de un ERP externo.
- **Cero costo de infraestructura**: la solución corre en el equipo existente de la bodega.

El criterio fue resolver un problema real y medible con la menor complejidad posible, en lugar de construir una plataforma corporativa para un alcance que no la requería.

---

## Línea de tiempo

| Periodo | Etapa |
|---|---|
| Hasta agosto 2025 | Gestión empírica. Planillas Excel dispersas, sin trazabilidad. Se construye la línea base mediante auditorías físicas y entrevistas. |
| Septiembre 2025 | Primer filtro digital: plantillas de control estructuradas. Se detienen las compras innecesarias y se sanea la data. |
| Octubre–diciembre 2025 | Desarrollo y despliegue de la aplicación en Streamlit sobre SQLite. Migración de la data saneada. |
| Enero 2026 | Entrada en régimen. El tablero de Power BI comienza a consumir datos en tiempo real. |

Periodo de validación medido: **3 meses**.

---

## Impacto medido

> **Desviación presupuestaria: de +2,97% a −0,07%** — una mejora de 3,04 puntos porcentuales sobre un presupuesto de 5,8 MMUSD.

### Ejecución presupuestaria

| Año | Presupuesto | Desviación | Ejecución |
|---|---|---|---|
| 2024 · gestión manual | 5.300.000 USD | +157.255 USD (+2,97%) | 103,0% |
| 2025 · sistema digital | 5.800.000 USD | −3.912 USD (−0,07%) | 99,9% |

El presupuesto creció 9,4% entre ambos periodos, por lo que el logro está en la **precisión de la ejecución**, no en la reducción del gasto absoluto. Presupuesto bajo gestión en 2026: 6.000.000 USD (≈ $5.460 MM CLP).

Los datos presentes en el dashboard a continuación corresponden a la base de datos de ejemplo que se proporciona en el isntructivo de uso de la aplicación

![Tablero de seguimiento presupuestario:](docs\img\control_costo.png)

El gasto acumulado contra objetivo, evolución mensual y desglose por clasificación y material corresponden a la base de datos ficticia que se brinda en el instructivo para poder utilizar la aplicación desarrollada y cumpliendo con la confidencialidad de los datos.
### Eficiencia operativa

| Métrica | Antes | Después | Mejora |
|---|---|---|---|
| Registro diario de movimientos | 15–25 min | 3–5 min | −80% |
| Consulta de existencias | 5–10 min (inspección física o búsqueda en Excel) | <30 s | −90% |
| Preparación de auditoría mensual | 4–6 h | <5 min | −98% |
| Correcciones y cuadratura | 10–15 h/mes | <1 h/mes | −93% |
| Errores de digitación | ~30% | <2% | −85% |

### Capacidades nuevas

Estas métricas no tienen comparación "antes" porque **no existía forma de medirlas** en el modelo manual. Que hoy sean cuantificables es en sí mismo parte del resultado:
- **Exactitud de inventario (ERI) medible por primera vez.** Antes el stock
  contable era una estimación sin verificación posible; hoy cada movimiento
  queda trazado y es conciliable contra el conteo físico, lo que permite
  calcular el ERI y detectar el origen de cada diferencia.
- **Visibilidad de sobrecosto en tiempo real.** Antes las desviaciones se detectaban al cierre de mes, cuando el gasto ya estaba comprometido; hoy el tablero permite gestión preventiva.
- **Fuente única de verdad.** Se eliminó el riesgo de duplicidad por versiones paralelas de planillas.

También se identificó que un **20% de las diferencias de inventario de 2024** correspondían a errores de registro y no a pérdidas reales — discrepancias que el sistema hoy previene en origen.

> **Nota metodológica:** la línea base 2024 fue reconstruida mediante auditorías físicas y revisión documental, al no existir un sistema digital previo, por lo que incorpora un margen de estimación. Las cifras posteriores a septiembre de 2025 provienen de registros del sistema.

---

## Funcionalidades

| Módulo | Qué resuelve |
|---|---|
| **Insumos** | Catálogo maestro con búsqueda, alta y edición de materiales. Fuente única de nomenclatura. |
| **Ingresos** | Registro de entradas con actualización automática de stock y reversión controlada. |
| **Salidas** | Registro de retiros con validación contra stock disponible. |
| **Control de stock** | Panel de existencias con alertas de stock mínimo, filtros dinámicos y métricas operativas. |
| **Dashboard Power BI** | Seguimiento presupuestario, gasto acumulado y análisis por clasificación de material. |


![Formulario de ingreso/modificación de insumos](docs\img\gestion_insumo.png)

la clasificación y la unidad de medida se seleccionan desde la metadata normalizada, evitando la digitación libre que originaba los errores de registro.
---

## Arquitectura

```
inventario_app/
├── inventory_stock.py          # Punto de entrada de la aplicación
├── pages/
│   ├── 1_insumos.py            # Catálogo de insumos
│   ├── ingresos.py             # Registro de entradas
│   ├── salidas.py              # Registro de retiros
│   └── stock.py                # Panel de control de existencias
├── src/
│   ├── create_sample_db.py     # Genera una base de datos ficticia de prueba
│   ├── database.py             # Persistencia: consultas, inserciones y reversión de stock
│   ├── data_process.py         # Normalización de clasificaciones y unidades
│   └── db/
│       └── inventario_lp02_sample.db
├── metadata/                   # JSON de clasificaciones y unidades de medida
├── docs/img/                   # Capturas de pantalla
└── requirements.txt
```

**Flujo de datos:** los formularios de `pages/` validan la entrada contra la metadata de `metadata/`, `data_process.py` normaliza los valores y `database.py` los persiste en SQLite. El dashboard de Power BI lee la misma base, garantizando una fuente única de verdad.

---

## Instalación

Requiere Python 3.10 o superior.
Estando ubicado en terminal utilizar los siguientes códigos:
```bash
# Clonar el repositorio
git clone https://github.com/farodd/proyecto-inventario.git
cd proyecto-inventario

# Crear y activar el entorno virtual
python -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows

# Instalar dependencias
pip install -r requirements.txt
```

## Uso
Por confidencialidad, los datos productivos no se incluyen en el repositorio. El proyecto trae un generador de base de datos ficticia para poder probar la aplicación con datos de ejemplo.

Desde la carpeta principal del repositorio:
```bash
# 1. Generar la base de datos de ejemplo
python src/create_sample_db.py

# 2. Habilitarla como base activa de la aplicación
cp src/db/inventario_lp02_sample.db src/db/inventario_lp02.db     # Linux / macOS
copy src\db\inventario_lp02_sample.db src\db\inventario_lp02.db   # Windows

# 3. Ejecutar la aplicación
streamlit run inventory_stock.py
```

La aplicación queda disponible en `http://localhost:8501`. La navegación entre Insumos, Ingresos, Salidas y Control de Stock se realiza desde la barra lateral.

---

## Limitaciones

- **Alcance de una bodega.** Los resultados no son extrapolables a otras bodegas sin analizar sus particularidades operativas.
- **Sin integración directa con SAP S/4 HANA**: la sincronización depende de un proceso ETL intermedio.
- **Periodo de validación de tres meses**, insuficiente para observar efectos estacionales en la rotación de materiales.
- **Concurrencia limitada.** SQLite es la elección correcta para un punto de uso; escalar a múltiples bodegas o usuarios simultáneos requeriría migrar a un motor cliente-servidor.

## Trabajo futuro

- [ ] Alertas automáticas por correo al alcanzar el punto de reorden.
- [ ] Historial de precios por insumo para análisis de variación de costos.
- [ ] Reporte automático de rotación e inventario inactivo.
- [ ] Migración a PostgreSQL, solo si el alcance se extiende a más bodegas.

---

## Autor

**Fabián Rodríguez Orellana**

## Licencia

MIT

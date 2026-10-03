# ROBOYORK Control System (RCS_2040)

Simulador en Python de gestión de emergencias para la base ROBOYORK VII. El operador
administra cuatro recursos (Energía, Agua, Alimentos y Comunicación) mientras ocurren
eventos aleatorios; cada decisión cambia los recursos, la puntuación y el estado de la misión.

## Cómo ejecutar

```bash
python main.py     # abre la interfaz gráfica (tkinter); si no hay tkinter, usa la consola
python gui.py      # solo la interfaz gráfica
python tests.py    # casos de prueba
```

Requiere Python 3.8+ y solo la librería estándar. Usuario de prueba: `admin` / `1234`.

## Estructura

| Archivo | Responsabilidad |
|---|---|
| `main.py` | Crea la misión, panel de consola (8 opciones) y arranque |
| `gui.py` | Interfaz gráfica (tkinter): solo muestra datos y llama a la lógica |
| `usuarios.py` | Login (3 intentos), crear operador, roles `admin` / `operador` |
| `recursos.py` | Recursos, valores iniciales aleatorios y límites 0–100 |
| `eventos.py` | Eventos, decisiones, dificultad, reglas de estado y algoritmo propio |
| `reportes.py` | Historial, estadísticas, reporte TXT y guardado de progreso en CSV |
| `utilidades.py` | Validación de entradas (vacías, inválidas, fuera de rango) |
| `tests.py` | Casos de prueba automáticos (`unittest`) |

## Cómo se juega

1. Inicia sesión (o crea un operador) y pulsa **Nueva misión**; elige la dificultad.
2. Los recursos empiezan con un valor **aleatorio** según la dificultad.
3. **Procesar evento** muestra un evento con 3 o 4 opciones. El **orden de las opciones cambia
   cada vez** y los efectos no se muestran: hay que decidir con criterio.
4. **Simular** ejecuta de 1 a 20 eventos con decisiones al azar.
5. La misión se **autoguarda** después de cada decisión y se puede retomar.

### Qué hace el juego más difícil

- Tras cada evento **todos los recursos se desgastan** un poco (consumo pasivo).
- Los efectos negativos se multiplican por un factor de castigo.
- Las opciones marcadas *(riesgoso)* dan más, pero **pueden fallar**: no aplican su mejora, pagan
  su costo y restan 5 puntos.
- Los eventos se eligen con más probabilidad cuando el recurso que afectan está bajo.
- Para resolver la misión hay que llegar a la meta **sin ningún recurso en alerta**.

## Dificultades

| | Fácil | Normal | Difícil |
|---|---|---|---|
| Recursos iniciales (aleatorios) | 70–100 | 55–90 | 40–75 |
| Eventos para resolver | 8 | 10 | 12 |
| Desgaste por evento (cada recurso) | 0–1 | 0–2 | 0–3 |
| Castigo a efectos negativos | ×1.0 | ×1.25 | ×1.4 |
| Variación aleatoria de efectos | ±2 | ±3 | ±4 |
| Probabilidad de acciones riesgosas | +10 % | base | −10 % |
| Bonus al resolver | +10 | +20 | +40 |

## Estados automáticos

Prioridad de arriba abajo (`evaluar_reglas`):

| Estado | Condición |
|---|---|
| `FALLIDA` | algún recurso llega a 0 |
| `CRÍTICA` | Energía < 20 |
| `ALERTA` | Agua < 15 o algún recurso < 30 |
| `RESUELTA` | eventos procesados ≥ meta (y ningún estado anterior) |
| `OPERATIVA` | cualquier otro caso |

`RESUELTA` y `FALLIDA` son finales: el estado ya no cambia.

## Puntuación

Cada opción da o quita puntos (de −12 a +12). Una acción riesgosa que falla resta 5. Al resolver
la misión se suma el bonus de la dificultad. Una decisión es *correcta* si suma puntos; la
**eficiencia** es `decisiones correctas / eventos × 100`.

## Algoritmo propio: índice de riesgo ponderado

Función: `eventos.indice_riesgo()` y `eventos.algoritmo_propio()`.

**Objetivo:** resumir en un solo número qué tan cerca está la misión del colapso, dando más
importancia a los recursos más críticos.

**Fórmula**

```
riesgo = Σ  peso_i × (100 − valor_i)
```

| Recurso | Peso |
|---|---|
| Energía | 0.4 |
| Agua | 0.3 |
| Alimentos | 0.2 |
| Comunicación | 0.1 |

Los pesos suman 1.0, así que el riesgo va de **0** (todos al 100 %) a **100** (todos en 0).

**Niveles:** `BAJO` (< 25), `MEDIO` (25 a < 50), `ALTO` (≥ 50).

**Pasos**
1. Para cada recurso calcular cuánto le falta: `100 − valor`.
2. Multiplicar esa carencia por el peso del recurso.
3. Sumar los resultados.
4. Clasificar el total en BAJO / MEDIO / ALTO.

**Ejemplo:** Energía 100, Agua 80, Alimentos 70, Comunicación 90
→ `0.4·0 + 0.3·20 + 0.2·30 + 0.1·10 = 13.0` → nivel **BAJO**.

**Complejidad:** O(n), con n = número de recursos (4).

**Dónde se usa:** al terminar una simulación en consola, en las estadísticas de consola y en la
tarjeta *Riesgo* de la interfaz gráfica.

## Casos de prueba

Se ejecutan con `python tests.py` (usa `unittest` y no escribe archivos en la carpeta del proyecto).

**Algoritmo propio**

| Recursos (E / A / Al / C) | Riesgo esperado | Nivel |
|---|---|---|
| 100 / 100 / 100 / 100 | 0.0 | BAJO |
| 100 / 80 / 70 / 90 | 13.0 | BAJO |
| todos 76 | 24.0 | BAJO |
| todos 74 | 26.0 | MEDIO |
| todos 55 | 45.0 | MEDIO |
| todos 45 | 55.0 | ALTO |
| 0 / 0 / 0 / 0 | 100.0 | ALTO |
| Energía 0, resto 100 | 40.0 | MEDIO |

**Otros grupos de pruebas**

| Grupo | Qué verifica |
|---|---|
| Recursos | límites 0–100, valores iniciales aleatorios dentro del rango de cada dificultad |
| Reglas | cada estado, los bordes (Energía 19 vs 20, Agua 14, recurso 29), meta por dificultad, bonus, estado final inmutable |
| Eventos | datos válidos de todos los eventos, orden aleatorio de opciones sin alterar la lista original, el azar depende de los recursos, acción riesgosa que falla y que acierta, recursos siempre entre 0 y 100 en miles de pasos, Difícil resuelve menos que Fácil |
| Progreso (CSV) | guardar y cargar, archivo inexistente, archivo dañado, borrar, nombre de archivo seguro |
| Entradas y usuarios | entradas vacías / texto / fuera de rango, login correcto, bloqueo tras 3 intentos, operador duplicado, roles |

## Requisitos del reto cubiertos

- **Funciones propias (más de 6):** `crear_mision`, `generar_evento`, `aplicar_opcion`, `evaluar_reglas`,
  `indice_riesgo`, `algoritmo_propio`, `simular`, `calcular_estadisticas`, `guardar_progreso`, entre otras.
- **Lista:** el historial de acciones. **Diccionario:** la misión, los recursos y los operadores.
- **`for`:** efectos, desgaste y simulación. **`while`:** validación de entradas en `utilidades.py`.
- **`if / elif / else`:** reglas de estado y niveles de riesgo.
- **`random`:** valores iniciales, elección y orden de eventos, variación de efectos, fallos y desgaste.

## Funciones avanzadas

- **TXT / CSV:** reporte en TXT y progreso por operador en `progreso_<usuario>.csv`.
- **tkinter:** interfaz gráfica con tema oscuro, barras animadas e historial en vivo.
- **Dificultad:** Fácil, Normal y Difícil (tabla arriba).
- **Permisos:** el rol `admin` ve el botón *Operadores* para listar usuarios y borrar su progreso guardado.

## Limitaciones

- Los operadores creados viven solo en memoria: al cerrar el programa solo queda `admin`.
- Las contraseñas no están cifradas; es un proyecto académico.
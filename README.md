# ROBOYORK Control System (RCS_2040)

Simulador en Python para manejar emergencias en la base ROBOYORK VII. El operador cuida
cuatro recursos (Energía, Agua, Alimentos y Comunicación) mientras van pasando eventos al
azar. Cada decisión cambia los recursos, los puntos y el estado de la misión.

## Cómo ejecutarlo

```bash
python main.py     # abre la interfaz gráfica; si no hay tkinter, usa la consola
python gui.py      # solo la interfaz gráfica
python tests.py    # pruebas
```

Necesita Python 3.8 o más y solo usa la librería estándar.
Usuario de prueba: `admin` / `1234`.

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `main.py` | Crea la misión, tiene el menú de consola (8 opciones) y arranca el programa |
| `gui.py` | Interfaz gráfica con tkinter. Solo muestra datos y llama a la lógica |
| `usuarios.py` | Login (3 intentos), crear operador, roles `admin` / `operador` y guardado en `usuarios.json` |
| `recursos.py` | Los cuatro recursos, sus valores iniciales y el límite de 0 a 100 |
| `eventos.py` | Eventos, decisiones, dificultad, reglas de estado y el algoritmo propio |
| `reportes.py` | Historial, estadísticas, reporte en TXT, progreso en CSV e historial por usuario en JSON |
| `utilidades.py` | Validación de lo que escribe el usuario (texto y numeros enteros)|
| `tests.py` | Pruebas automáticas con `unittest` |

## Cómo se juega

1. Inicia sesión (o crea un operador), pulsa **Nueva misión** y elige la dificultad.
2. Los recursos empiezan con un valor al azar que depende de la dificultad.
3. **Procesar evento** muestra un evento con 3 o 4 opciones. El orden cambia cada vez y no se
   ven los efectos, así que hay que decidir con criterio.
4. **Simular** ejecuta eventos con decisiones al azar, sin pasar de la meta de la dificultad:
   solo deja pedir los eventos que faltan.
5. La misión se guarda sola después de cada decisión y se puede retomar.
6. Los operadores quedan en `usuarios.json`. El progreso y el historial de cada uno se guardan en la carpeta `datos/`.

### Qué hace el juego más difícil

- Después de cada evento todos los recursos se desgastan un poco.
- Los efectos negativos se multiplican por un factor de castigo.
- Las opciones marcadas *(riesgoso)* dan más, pero pueden fallar: no aplican su mejora,
  pagan su costo y restan 5 puntos.
- Salen con más probabilidad los eventos que afectan a un recurso bajo.
- Para resolver la misión hay que llegar a la meta sin ningún recurso en alerta.

## Dificultades

| | Fácil | Normal | Difícil |
|---|---|---|---|
| Recursos iniciales (al azar) | 70–100 | 55–90 | 40–75 |
| Eventos para resolver | 8 | 10 | 12 |
| Desgaste por evento (cada recurso) | 0–1 | 0–2 | 0–3 |
| Castigo a efectos negativos | x1.0 | x1.25 | x1.4 |
| Variación aleatoria de efectos | ±2 | ±3 | ±4 |
| Probabilidad de acciones riesgosas | +10 % | base | −10 % |
| Bonus al resolver | +10 | +20 | +40 |

## Estados de la misión

Se revisan de arriba abajo en `evaluar_reglas`:

| Estado | Condición |
|---|---|
| `FALLIDA` | algún recurso llega a 0 |
| `CRÍTICA` | Energía menor a 20 |
| `ALERTA` | Agua menor a 15, o algún recurso menor a 30 |
| `RESUELTA` | eventos procesados ≥ meta (y no se cumple nada de lo anterior) |
| `OPERATIVA` | cualquier otro caso |

`RESUELTA` y `FALLIDA` son finales: el estado ya no cambia.

## Puntuación

Cada opción suma o resta puntos (entre −12 y +12). Si una acción riesgosa falla, resta 5.
Al resolver la misión se suma el bonus de la dificultad. Una decisión es *correcta* si suma
puntos, y la **eficiencia** es `decisiones correctas / eventos × 100`.

## Algoritmo propio: índice de riesgo ponderado

Está en `eventos.indice_riesgo()`.

**Objetivo:** resumir en un solo número qué tan cerca está la misión del colapso, dándole más
importancia a los recursos más críticos.

**Fórmula**

```
riesgo = suma de  peso_i * (100 - valor_i)
```

| Recurso | Peso |
|---|---|
| Energía | 0.4 |
| Agua | 0.3 |
| Alimentos | 0.2 |
| Comunicación | 0.1 |

Los pesos suman 1.0, así que el riesgo va de 0 (todo al 100 %) a 100 (todo en 0).

**Niveles:** `BAJO` (menos de 25), `MEDIO` (de 25 a menos de 50) y `ALTO` (50 o más).

**Pasos**
1. Para cada recurso se calcula cuánto le falta: `100 - valor`.
2. Se multiplica esa carencia por el peso del recurso.
3. Se suman los resultados.
4. Se clasifica el total en BAJO, MEDIO o ALTO.

**Ejemplo:** Energía 100, Agua 80, Alimentos 70, Comunicación 90
→ `0.4*0 + 0.3*20 + 0.2*30 + 0.1*10 = 13.0` → nivel **BAJO**.

**Dónde se usa:** al terminar una simulación en consola, en las estadísticas de consola y en
la tarjeta *Riesgo* de la interfaz gráfica.

## Pruebas

Se ejecutan con `python tests.py`. Usan `unittest` y no dejan archivos en la carpeta del proyecto.

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

**Otros grupos**

| Grupo | Qué comprueba |
|---|---|
| Recursos | límites de 0 a 100 y valores iniciales dentro del rango de cada dificultad |
| Reglas | cada estado, los casos límite (Energía 19 y 20, Agua 14, recurso 29), la meta y el bonus por dificultad, y que un estado final no cambia |
| Eventos | datos válidos, orden aleatorio de opciones sin cambiar la lista original, azar según los recursos, acción riesgosa que falla y que acierta, recursos siempre entre 0 y 100, y que Difícil se resuelve menos que Fácil |
| Progreso (CSV) | guardar, cargar, archivo inexistente, archivo dañado, borrar y nombre de archivo seguro |
| Historial (JSON) | un archivo por usuario, las misiones se acumulan sin duplicarse, archivo inexistente o dañado |
| Entradas y usuarios | entradas vacías, con texto o fuera de rango; login correcto; bloqueo tras 3 intentos; operador repetido; roles; guardado en `usuarios.json` |

## Extras

- **TXT, CSV y JSON:** reporte en TXT, operadores en `usuarios.json`, y dentro de la carpeta `datos/` el progreso de cada operador (`progreso_<usuario>.csv`) y su historial (`historial_<usuario>.json`).
- **tkinter:** interfaz con tema oscuro, barras animadas e historial en vivo.
- **Dificultad:** Fácil, Normal y Difícil.
- **Permisos:** solo el rol `admin` ve el botón *Operadores*, para listar usuarios y borrar su progreso.
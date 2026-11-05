# MAS for People

Agentes especializados (ingenieros, economistas, periodistas...) que discuten
en **salas** por turnos hasta llegar a un veredicto verificado. El MVP corre
como servidor MCP local en Claude Desktop y una ventana de escritorio
(PySide6) muestra lo guardado. Especificación: ERS del MVP.

## Estado

| Paso | Qué deja funcionando | Estado |
|---|---|---|
| 1 | Modelos de datos y catálogo: leer y validar `agente.md`, 3 agentes de ejemplo, pruebas | ✅ |
| 2 | Servidor MCP mínimo (`listar_agentes`, `ver_agente`) en Claude Desktop | ✅ |
| 3 | Protocolo panel + SQLite + ciclo de turnos (`abrir_sala`, `siguiente_turno`, `publicar_turno`, `veredicto`, `ver_sala`) | ✅ |
| 4 | Visor de escritorio (PySide6): catálogo, salas, mesa, hilos, veredicto; búsqueda, exportar y refresco automático | ✅ |
| 5 | Protocolo debate por rondas: crítica con resumen de mesa, cierre por consenso o por límite, avisos del moderador | ✅ |
| 6 | `guardar_agente` (crear y editar agentes propios), prompts MCP `debate`/`panel`/`crear_agente`, catálogo completo de 9 agentes y 18 skills | ✅ |
| 7 | Exportar a Claude Code y a Markdown, guía de instalación | ⏳ |

## Probarlo

Requiere Python 3.11+ y [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest          # pruebas del núcleo
uv run mas-validar     # muestra el catálogo y los errores de cada archivo
uv run mas-config      # bloque para pegar en la configuración de Claude Desktop
uv run mas-visor       # abre la ventana que muestra catálogo y salas
```

## Usarlo en Claude Desktop

Guía paso a paso (Windows, sin experiencia previa con uv):
[docs/claude-desktop.md](docs/claude-desktop.md).

En corto: `uv sync`, luego `uv run mas-config`, pega el bloque que imprime
en *Configuración → Desarrollador → Editar configuración* de Claude Desktop
y reinícialo. El servidor expone estas herramientas:

| Herramienta | Entrada | Salida |
|---|---|---|
| `listar_agentes` | `familia?`, `texto?` | `{agentes: [{id, nombre, familia, postura, descripcion, propio}], total, familias, errores}` |
| `ver_agente` | `id` | Ficha, formato de salida con secciones, límites, instrucciones, `agente_md` y skills que usa |
| `guardar_agente` | `nombre`, `especialidad`, `familia`, `postura`, `skills[]`, `formato_salida`, `instrucciones`; `id?`, `sensible?`, `aviso?`, `reemplazar?`, `solo_validar?` | `{ok, id, ruta, agente_md, guardado}` o `{ok: false, errores, formatos_validos, skills_disponibles}` |
| `abrir_sala` | `objetivo`, `agentes[]` (2–6), `protocolo` (`debate`/`panel`), `max_rondas` (1–4), `max_palabras`, `posturas?` | `{sala_id, plan}`: orden de turnos previsto (en debate, el máximo) |
| `siguiente_turno` | `sala_id` | `{turno_id, agente, ronda, objetivo, instrucciones, skills, hilo, resumen_mesa, formato_salida, max_palabras}` o `{estado: "listo_para_veredicto", motivo_cierre}` |
| `publicar_turno` | `sala_id`, `turno_id`, `contenido`, `artefacto` | `{ok: true, moderador?}` o `{ok: false, errores}` para corregir ese turno |
| `veredicto` | `sala_id`; en la 2.ª llamada `contenido`, `acuerdos`, `desacuerdos`, `confianza`, `plan` | 1.ª: turno del verificador (objetivo + mesa). 2.ª: veredicto guardado y sala cerrada |
| `ver_sala` | `sala_id?`, `vista` (`mesa`/`hilo`/`veredicto`), `agente?` | Markdown; sin `sala_id` lista las salas |

Y tres **prompts** (atajos que aparecen en Claude Desktop con el botón **+** →
*mas-for-people*): **debate** (objetivo, agentes opcionales, rondas), **panel**
(objetivo, agentes opcionales) y **crear_agente** (descripción opcional). Si no
eliges agentes, Claude sugiere un equipo de familias y posturas distintas.

### Catálogo

| Agente | Familia | Postura por defecto | Skills | Formato de salida |
|---|---|---|---|---|
| Ingeniero informático | ingenieria | pragmático | arquitectura-software, estimacion-esfuerzo | Propuesta técnica |
| Ingeniero industrial | ingenieria | conservador | mejora-procesos, analisis-costos | Propuesta técnica |
| Ingeniero ambiental | ingenieria | innovador | evaluacion-impacto, normativa-ambiental | Propuesta técnica |
| Economista ortodoxo | economia | conservador (mercado, disciplina fiscal) | analisis-costo-beneficio, indicadores-macro | Análisis económico |
| Economista heterodoxo | economia | no conservador (Estado activo, distribución) | analisis-costo-beneficio, economia-politica | Análisis económico |
| Especialista en marketing | comunicacion | centrado en el cliente | segmentacion, propuesta-de-valor | Plan de mercado |
| Periodista | comunicacion | escéptico | verificacion-fuentes, piramide-invertida | Nota o preguntas críticas |
| Investigador | investigacion | basado en evidencia | busqueda-literatura, evaluar-evidencia | Informe con fuentes |
| Abogado del diablo | transversal | escéptico | deteccion-sesgos | Objeciones priorizadas |

La postura se puede cambiar al abrir la sala (`posturas`). Además hay dos
skills de sistema: `protocolos-sala` (reglas del moderador, van en los
prompts) y `verificacion-objetivo` (la usa el verificador).

### Agentes propios

Pide en Claude Desktop "crea un agente…" o usa el prompt **crear_agente**.
Claude completa los campos, te muestra el borrador (`solo_validar=true`, no
escribe nada) y lo guarda cuando confirmas. Los agentes nuevos van a
`mis-agentes/<familia>/<id>/agente.md`, aparecen al instante en
`listar_agentes` y en el visor (marcados como *propio*) y se pueden usar en
cualquier sala. Para editar uno, pídelo: Claude llama a `guardar_agente` con
su id y `reemplazar=true` (si es un agente base, se edita en su sitio).

**Decisión del MVP:** los agentes propios son **locales y no se comparten**.
`mis-agentes/` está en `.gitignore`, así que no se suben al repositorio ni
se mezclan con el catálogo base al actualizar. Compartir agentes entre
usuarios queda para una fase siguiente.

### Cómo funciona una sala

```
abrir_sala → (siguiente_turno → Claude responde como ese agente → publicar_turno)… → veredicto ×2
```

Claude hace de cada agente por turnos; el servidor hace de moderador: decide
quién habla, entrega a cada uno solo su contexto, rechaza respuestas sin las
secciones del formato o demasiado largas (con un 10 % de margen) y no deja
saltar estados. Hay dos protocolos:

- **debate** (por defecto, CU-03): en la ronda 1 cada agente propone sin ver
  a los demás. En las rondas siguientes cada uno recibe el resumen de la mesa
  (la última intervención de cada compañero: postura, resumen y confianza) y
  responde con `apoyo`, `objecion` o `correccion`; las dos últimas deben decir
  a qué turno responden (`responde_a`). El moderador cierra por **consenso**
  (una ronda de crítica sin objeciones ni correcciones) o al llegar a
  `max_rondas` (1 a 4, por defecto 2), y avisa al cerrar cada ronda.
  `abierta → propuestas → critica → verificacion → cerrada`.
- **panel** (CU-04): una sola ronda en paralelo, nadie ve a los demás.
  `abierta → propuestas → verificacion → cerrada`.

En ambos, al final un verificador que no participó revisa la mesa contra el
objetivo. Para que cada turno quepa en ~3.000 palabras (RNF-02), el hilo de
un agente trae completa solo su última intervención (las anteriores,
resumidas) y el verificador recibe completo el último artefacto de cada
agente y, de los anteriores, postura y resumen.

Todo se guarda en `datos/mas.db` (SQLite en modo WAL) dentro de la carpeta
del proyecto, o donde diga la variable `MAS_BD`. No sale nada a internet.

El servidor no llama a ningún modelo: Claude razona y el servidor entrega
datos. Relee los archivos en cada consulta, así que un `agente.md` editado a
mano se ve sin reiniciar. Encuentra la carpeta del catálogo por la variable
`MAS_CARPETA`, la carpeta actual o la del repositorio, en ese orden.

## Ver las salas en la ventana

```bash
uv run mas-visor
```

Abre una ventana con dos pestañas: **Salas** (buscador, tabla y, al elegir
una, sus pestañas Mesa, Hilos con una columna por agente y Veredicto; botón
para exportarla a Markdown) y **Catálogo** (agentes por familia con su
ficha). Solo lee: abre `datos/mas.db` en modo lectura y la relee cada 3
segundos, así que una sala que Claude está llevando avanza sola en la
ventana sin molestar al servidor. Guía para Windows: [docs/visor.md](docs/visor.md).

## Formato `agente.md`

Cada agente vive en `agentes/<familia>/<id>/agente.md`. Es un superconjunto
del formato de subagentes de Claude Code: los campos `name`, `description`,
`tools`, `model` y `skills` significan lo mismo; el resto son propios.

```markdown
---
name: ingeniero-industrial        # id: minúsculas y guiones (obligatorio)
title: Ingeniero industrial       # nombre visible (opcional)
description: Mejora procesos...   # cuándo usarlo (obligatorio)
version: 0.1.0
family: ingenieria                # opcional: si falta, se toma de la carpeta
stance: conservador               # postura por defecto (obligatorio)
skills: [mejora-procesos, analisis-costos]   # deben existir en skills/
output_contract: propuesta-tecnica           # ver src/mas/core/formatos.py
limits: { max_turns: 6, max_words_per_turn: 400 }
tools: []                         # opcional
model: { preferred: claude, alternatives: [gpt, gemini] }   # opcional
sensitive: false                  # si es true, 'disclaimer' es obligatorio
---

Instrucciones del agente en Markdown...
```

Las skills usan el formato estándar `skills/<id>/SKILL.md` (`name` igual a la
carpeta y `description`).

Un archivo con errores no se carga; el catálogo informa el archivo, el campo
y qué corregir, por ejemplo:

```
agentes/ingenieria/malo/agente.md · stance: Falta el campo obligatorio.
```

## Estructura

```
src/mas/core/          # núcleo, sin MCP ni ventana
  modelos.py           # Agente, Skill, Sala, Hilo, Turno, Artefacto, Mesa, Veredicto
  catalogo.py          # carga, valida, lista y busca agentes y skills
  formatos.py          # formatos de salida (output_contract) y revisión de secciones
  salas.py             # gestor de salas: abrir, turnos, publicar, veredicto, ver
  creacion.py          # guardar_agente: crear y editar agentes propios
  protocolos/          # máquinas de estados: debate.py y panel.py
  almacen.py           # guardado en SQLite (WAL); el único lugar con SQL
  vistas.py            # salas y fichas en Markdown (ver_sala y visor)
  consulta.py          # lectura de salas para el visor (solo lectura)
  raiz.py              # ubica la carpeta del proyecto y la base de datos
  sistema/             # agentes de sistema (verificador)
  textos.py            # todos los mensajes al usuario (para traducir)
src/mas/servidor/      # capa MCP (no la importa el núcleo)
  app.py               # servidor y herramientas; comando mas-servidor
  config.py            # comando mas-config
src/mas/visor/         # ventana PySide6 de solo lectura; comando mas-visor
  app.py               # ventana principal y refresco
  vistas/              # catalogo.py, salas.py, sala_detalle.py
docs/claude-desktop.md # guía de conexión para Windows
docs/visor.md          # cómo abrir la ventana en Windows
agentes/               # un agente.md por agente, agrupados por familia
mis-agentes/           # agentes que crea el usuario (local, no va a git)
skills/                # una carpeta por skill con SKILL.md
datos/                 # mas.db con las salas (se crea solo; no va a git)
tests/
```

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
| 5 | Protocolo debate por rondas | ⏳ |
| 6 | `guardar_agente`, prompts MCP, catálogo completo | ⏳ |
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
| `listar_agentes` | `familia?`, `texto?` | `{agentes: [{id, nombre, familia, postura, descripcion}], total, familias, errores}` |
| `ver_agente` | `id` | Ficha, formato de salida con secciones, límites, instrucciones, `agente_md` y skills que usa |
| `abrir_sala` | `objetivo`, `agentes[]` (2–6), `protocolo` (`panel`), `max_palabras`, `posturas?` | `{sala_id, plan}`: orden de turnos previsto |
| `siguiente_turno` | `sala_id` | `{turno_id, agente, objetivo, instrucciones, skills, hilo, resumen_mesa, formato_salida, max_palabras}` o `{estado: "listo_para_veredicto"}` |
| `publicar_turno` | `sala_id`, `turno_id`, `contenido`, `artefacto` | `{ok: true}` o `{ok: false, errores}` para corregir ese turno |
| `veredicto` | `sala_id`; en la 2.ª llamada `contenido`, `acuerdos`, `desacuerdos`, `confianza`, `plan` | 1.ª: turno del verificador (objetivo + mesa). 2.ª: veredicto guardado y sala cerrada |
| `ver_sala` | `sala_id?`, `vista` (`mesa`/`hilo`/`veredicto`), `agente?` | Markdown; sin `sala_id` lista las salas |

### Cómo funciona una sala

```
abrir_sala → (siguiente_turno → Claude responde como ese agente → publicar_turno)… → veredicto ×2
```

Claude hace de cada agente por turnos; el servidor hace de moderador: decide
quién habla, entrega a cada uno solo su contexto, rechaza respuestas sin las
secciones del formato o demasiado largas (con un 10 % de margen) y no deja
saltar estados (`abierta → propuestas → verificacion → cerrada`). Por ahora
el único protocolo es **panel**: una ronda, nadie ve a los demás, y al final
un verificador que no participó revisa la mesa contra el objetivo. El debate
por rondas llega en el paso 5.

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
  protocolos/          # máquinas de estados (panel; debate en el paso 5)
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
skills/                # una carpeta por skill con SKILL.md
datos/                 # mas.db con las salas (se crea solo; no va a git)
tests/
```

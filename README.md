# MAS for People

Agentes especializados (ingenieros, economistas, periodistas...) que discuten
en **salas** por turnos hasta llegar a un veredicto verificado. El MVP corre
como servidor MCP local en Claude Desktop y una ventana de escritorio
(PySide6) muestra lo guardado. Especificación: ERS del MVP.

## Estado

| Paso | Qué deja funcionando | Estado |
|---|---|---|
| 1 | Modelos de datos y catálogo: leer y validar `agente.md`, 3 agentes de ejemplo, pruebas | ✅ |
| 2 | Servidor MCP mínimo (`listar_agentes`, `ver_agente`) en Claude Desktop | ⏳ |
| 3 | Protocolo panel + SQLite + ciclo de turnos | ⏳ |
| 4 | Visor mínimo (PySide6) | ⏳ |
| 5 | Protocolo debate por rondas | ⏳ |
| 6 | `guardar_agente`, prompts MCP, catálogo completo | ⏳ |
| 7 | Exportar a Claude Code y a Markdown, guía de instalación | ⏳ |

## Probarlo

Requiere Python 3.11+ y [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest          # pruebas del núcleo
uv run mas-validar     # muestra el catálogo y los errores de cada archivo
```

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
  formatos.py          # formatos de salida (output_contract)
  textos.py            # todos los mensajes al usuario (para traducir)
agentes/               # un agente.md por agente, agrupados por familia
skills/                # una carpeta por skill con SKILL.md
tests/
```

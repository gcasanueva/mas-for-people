# Instalar y usar MAS for People (Windows)

Guía de punta a punta para un equipo limpio: unos 10 minutos. Necesitas
**Claude Desktop** con tu cuenta (sirve el plan Pro; no hace falta API) y
**PowerShell** (botón Inicio → escribe "PowerShell" → Enter). En macOS y
Linux los pasos son los mismos con la Terminal.

| Paso | Qué haces | Detalle |
|---|---|---|
| 1 | Instalar `uv` | [claude-desktop.md, paso 1](claude-desktop.md#1-instalar-uv) |
| 2 | Descargar el proyecto | [paso 2](claude-desktop.md#2-descargar-el-proyecto) |
| 3 | `uv sync` y `uv run mas-validar` | [paso 3](claude-desktop.md#3-instalar-y-probar) |
| 4 | `uv run mas-config` y pegar el bloque en Claude Desktop | [pasos 4 y 5](claude-desktop.md#4-obtener-el-bloque-de-configuración) |
| 5 | Reiniciar Claude Desktop y probar | abajo |

## Resumen en comandos

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# cierra y abre PowerShell
cd $HOME
git clone https://github.com/gcasanueva/mas-for-people.git   # o descarga el ZIP
cd mas-for-people
uv sync
uv run mas-validar     # debe decir: 9 agentes y 18 skills cargados.
uv run mas-config      # copia el bloque que imprime
```

Pega el bloque en Claude Desktop → Configuración → Desarrollador → Editar
configuración, guarda y **cierra Claude Desktop por completo** (también
desde el ícono junto al reloj) antes de volver a abrirlo.

## Comprobar que quedó bien

En un chat nuevo de Claude Desktop:

1. "Muéstrame los ingenieros de MAS for People" → aparecen el informático
   (pragmático), el industrial (conservador) y el ambiental (innovador).
2. "Abre un debate de 2 rondas con el ingeniero industrial, el ingeniero
   ambiental, el economista ortodoxo y el economista heterodoxo para reducir
   30% el consumo energético de una planta de envasado." → Claude lleva los
   turnos solo y termina con un veredicto.
3. En otra ventana de PowerShell, dentro de la carpeta, `uv run mas-visor`
   → la sala aparece y avanza sola.

## Lo que puedes hacer

| Quieres… | Pídele a Claude Desktop |
|---|---|
| Ver agentes | "¿Qué agentes hay?", "Muéstrame completo al investigador" |
| Debate por rondas | "Abre un debate con … para …" o el atajo **debate** (botón **+** → mas-for-people) |
| Respuestas independientes | "Abre un panel con … para …" o el atajo **panel** |
| Crear tu propio agente | "Crea un agente …" o el atajo **crear_agente** |
| Editar un agente | "Cambia la postura del periodista a curioso" |
| Revisar una sala | "Muéstrame las salas guardadas", "Muéstrame el hilo del periodista en la sala <id>" |
| Guardar una sala en un archivo | "Exporta la sala <id> a Markdown" (queda en `exportados\`) |
| Usar agentes en Claude Code | "Exporta el periodista y el investigador a C:\Users\<tú>\mi-proyecto" |

## Usar los agentes en Claude Code

Exportar escribe cada agente como subagente en
`<carpeta>\.claude\agents\<id>.md` y copia sus skills en
`<carpeta>\.claude\skills\`. Desde PowerShell también se puede:

```powershell
uv run mas-exportar C:\Users\<tú>\mi-proyecto periodista investigador
uv run mas-exportar C:\Users\<tú>\mi-proyecto            # todos
```

Abre Claude Code en esa carpeta: los agentes aparecen con `/agents` y
Claude los llama cuando la tarea encaja (o si se lo pides por su nombre).
Ahí cada agente trabaja con su propio contexto. Si ya existe un archivo con
otro contenido (por ejemplo, lo editaste), no se pisa; usa `--reemplazar`
para sobrescribirlo.

## Dónde queda cada cosa

| Carpeta | Contenido | ¿Va a Git? |
|---|---|---|
| `agentes\`, `skills\` | Catálogo base (9 agentes, 18 skills) | Sí |
| `mis-agentes\` | Agentes que creas tú; solo en tu equipo | No |
| `datos\mas.db` | Salas, turnos y veredictos (SQLite) | No |
| `exportados\` | Salas exportadas a Markdown | No |

Nada sale a internet: el servidor no llama a ningún modelo; Claude Desktop
hace el razonamiento.

## Actualizar

```powershell
cd $HOME\mas-for-people
git pull          # o descarga el ZIP de nuevo y copia encima tus carpetas mis-agentes\ y datos\
uv sync
```

Luego cierra y abre Claude Desktop para que cargue las herramientas nuevas.

## Desinstalar

Quita la entrada `"mas-for-people"` del archivo de configuración de Claude
Desktop y borra la carpeta del proyecto (antes copia `mis-agentes\` y
`datos\` si quieres conservarlos).

Si algo falla, mira la tabla de problemas en
[claude-desktop.md](claude-desktop.md#si-algo-falla).

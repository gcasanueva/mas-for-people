# Conectar MAS for People a Claude Desktop (Windows)

Guía paso a paso para quien nunca usó `uv`. Toma unos 10 minutos. Los
comandos se escriben en **PowerShell** (botón Inicio → escribe
"PowerShell" → Enter).

## 1. Instalar uv

`uv` instala Python y las librerías del proyecto por ti; no hace falta
instalar Python aparte. Copia y pega en PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Cierra PowerShell y ábrelo de nuevo** (para que reconozca el comando).
Comprueba que funciona:

```powershell
uv --version
```

Si ves algo como `uv 0.x.y`, listo.

## 2. Descargar el proyecto

Elige una de dos formas:

- **Con Git** (si lo tienes instalado):
  ```powershell
  cd $HOME
  git clone https://github.com/gcasanueva/mas-for-people.git
  ```
- **Sin Git**: en GitHub, botón verde **Code → Download ZIP**, descomprime
  el ZIP y deja la carpeta en `C:\Users\<tu-usuario>\mas-for-people`
  (quítale el sufijo `-main` si lo trae).

Evita carpetas sincronizadas con OneDrive si puedes; a veces bloquean
archivos mientras se usan.

## 3. Instalar y probar

Entra a la carpeta y ejecuta:

```powershell
cd $HOME\mas-for-people
uv sync
uv run mas-validar
```

`uv sync` descarga Python (si hace falta) y las librerías; la primera vez
tarda un poco. `mas-validar` debe terminar con algo como
`3 agentes y 6 skills cargados.`

## 4. Obtener el bloque de configuración

En la misma carpeta:

```powershell
uv run mas-config
```

Imprime un bloque como este, **ya con las rutas de tu computador**:

```json
{
  "mcpServers": {
    "mas-for-people": {
      "command": "C:\\Users\\gabriel\\.local\\bin\\uv.exe",
      "args": [
        "--directory",
        "C:\\Users\\gabriel\\mas-for-people",
        "run",
        "mas-servidor"
      ]
    }
  }
}
```

Las barras dobles `\\` son correctas: así se escriben en JSON.

## 5. Pegarlo en Claude Desktop

1. Abre Claude Desktop → menú **Configuración** (Settings) → **Desarrollador**
   (Developer) → **Editar configuración** (Edit Config). Se abre la carpeta
   con el archivo `claude_desktop_config.json`; ábrelo con el Bloc de notas.
2. Si el archivo está vacío o solo tiene `{}`, reemplaza todo por el bloque
   que copiaste.
   Si ya tiene una sección `"mcpServers"` con otros servidores, agrega solo
   la parte `"mas-for-people": { ... }` dentro de ella, separada por una coma.
3. Guarda el archivo.
4. **Cierra Claude Desktop por completo** (también desde el ícono junto al
   reloj de Windows, clic derecho → Salir) y vuelve a abrirlo.

## 6. Primera prueba

En un chat nuevo de Claude Desktop escribe:

- "¿Qué agentes hay en MAS for People?"
- "Muéstrame los agentes de ingeniería."
- "Muéstrame completo al periodista."

Claude pedirá permiso para usar `listar_agentes` o `ver_agente` la primera
vez; acepta. En el botón de herramientas (ícono de enchufe o deslizadores
bajo el cuadro de texto) debe aparecer **mas-for-people** con 7 herramientas.

## 7. Primera sala (panel)

Pide algo como:

> Abre un panel con el ingeniero industrial, el economista ortodoxo y el
> periodista para reducir 30% el consumo energético de una planta de
> envasado.

Claude abre la sala y sigue solo: pide el turno de cada agente, escribe su
intervención, la publica y al final escribe el veredicto del verificador.
Verás una línea de avance por turno y, al final, el veredicto. Si el
servidor rechaza una respuesta (por ejemplo, le falta una sección), Claude
la corrige y la vuelve a publicar sin que tengas que intervenir.

Para revisar después: "Muéstrame las salas guardadas", "Muéstrame la mesa
de la sala <id>" o "Muéstrame el hilo del periodista en esa sala".

Las salas quedan en `datos\mas.db` dentro de la carpeta del proyecto.
Si actualizaste desde el paso 2, ejecuta `uv sync` y reinicia Claude
Desktop para ver las herramientas nuevas.

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| `uv` no se reconoce como comando | Cierra y abre PowerShell. Si sigue, repite el paso 1. |
| Claude Desktop dice que el servidor falló | Ejecuta `uv run mas-config` otra vez y compara las rutas con las del archivo. Revisa el registro en `%APPDATA%\Claude\logs\mcp-server-mas-for-people.log` (pega esa ruta en la barra del Explorador de archivos). |
| No aparece mas-for-people | Revisa que el JSON sea válido (comas y llaves) y que cerraste Claude Desktop por completo antes de abrirlo. |
| Claude se detiene a mitad de una sala | Dile "sigue con la sala <id>": `siguiente_turno` retoma donde quedó. |
| Un agente no aparece | Ejecuta `uv run mas-validar`: dice qué archivo y qué campo corregir. |

Los cambios hechos a mano en un `agente.md` se ven en la siguiente
consulta, sin reiniciar Claude Desktop. Si actualizas el código del
proyecto (por ejemplo con `git pull`), ejecuta `uv sync` y reinicia Claude
Desktop.

En macOS y Linux los pasos son iguales: instala uv con
`curl -LsSf https://astral.sh/uv/install.sh | sh` y `uv run mas-config`
muestra dónde está el archivo de configuración.

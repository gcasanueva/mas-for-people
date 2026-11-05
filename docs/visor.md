# Abrir el visor de escritorio (Windows)

El visor es una ventana que muestra lo que el servidor guarda: el catálogo
de agentes y las salas con su mesa, sus hilos y su veredicto. **Solo
muestra**: para conversar y abrir salas sigues usando Claude Desktop.

Supone que ya seguiste [la guía de Claude Desktop](claude-desktop.md)
(tienes `uv` y la carpeta del proyecto).

## 1. Actualizar el proyecto

En PowerShell:

```powershell
cd $HOME\mas-for-people
git pull          # o vuelve a descargar el ZIP si no usas Git
uv sync
```

`uv sync` descarga ahora también PySide6 (la biblioteca de la ventana,
unos 100 MB). Solo la primera vez.

## 2. Abrir la ventana

```powershell
uv run mas-visor
```

Deja PowerShell abierto mientras usas la ventana; al cerrarla, vuelve el
cursor. Puedes tener la ventana abierta al mismo tiempo que Claude Desktop.

## Qué ves

- **Salas**: tabla con fecha, objetivo, protocolo, estado y turnos
  publicados. Arriba, un buscador por texto del objetivo y el botón
  **Exportar a Markdown…** (guarda mesa, hilos y veredicto en un `.md`).
  Al elegir una sala, abajo aparecen tres pestañas:
  - **Mesa**: el artefacto de cada agente (resumen, supuestos, riesgos,
    confianza).
  - **Hilos**: una columna por agente con sus intervenciones completas.
  - **Veredicto**: el cierre del verificador.
- **Catálogo**: agentes agrupados por familia y, al elegir uno, su ficha
  (postura, skills, formato de salida e instrucciones). Si editas un
  `agente.md` a mano o creas uno desde Claude Desktop, pulsa **Recargar**
  (o F5). Los agentes que creaste llevan la marca *· propio*. Los archivos
  con errores aparecen al final del árbol con el motivo.

La ventana relee la base de datos cada 3 segundos: si Claude está
llevando una sala, los turnos aparecen solos, sin reiniciar nada.

## Si algo falla

- **"No se encontró la carpeta del proyecto"**: ejecuta el comando dentro
  de la carpeta `mas-for-people` (la que tiene `agentes\`).
- **"Aún no existe …\datos\mas.db"** en la barra de abajo: todavía no
  abriste ninguna sala en Claude Desktop. Abre una y aparecerá sola.
- **La ventana no muestra las salas que hiciste en Claude Desktop**: el
  visor y el servidor deben usar la misma carpeta. La barra de abajo dice
  qué base de datos lee el visor; si en tu configuración de Claude Desktop
  pusiste la variable `MAS_BD`, ponla también antes de abrir el visor:
  `$env:MAS_BD = "C:\ruta\a\mas.db"; uv run mas-visor`.

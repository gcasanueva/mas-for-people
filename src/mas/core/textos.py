"""Textos del sistema en un solo lugar (RNF-08).

Todo mensaje que vea el usuario sale de aquí, para poder traducir la
aplicación cambiando un solo archivo. Los mensajes de error dicen qué
corregir y nombran el campo y el archivo (RNF-07).
"""

from __future__ import annotations

# --- Errores al leer archivos ---------------------------------------------

ARCHIVO_ILEGIBLE = "No se pudo leer el archivo: {detalle}"
FRONTMATTER_INVALIDO = (
    "El encabezado YAML (entre las líneas ---) no es válido: {detalle}. "
    "Revisa la sangría y que cada campo tenga la forma 'campo: valor'."
)
FRONTMATTER_VACIO = (
    "Falta el encabezado YAML. El archivo debe empezar con una línea '---', "
    "luego los campos (name, description, ...) y otra línea '---'."
)
CUERPO_VACIO = (
    "Faltan las instrucciones del agente: escribe debajo del encabezado YAML "
    "cómo trabaja el agente."
)
SKILL_CUERPO_VACIO = "La skill no tiene contenido: escribe sus instrucciones debajo del encabezado."

# --- Errores de validación de campos ---------------------------------------

CAMPO_OBLIGATORIO = "Falta el campo obligatorio."
CAMPO_DESCONOCIDO = (
    "Campo desconocido. Revisa si está mal escrito; los campos válidos son: {validos}."
)
ID_INVALIDO = (
    "'{valor}' no sirve como identificador: usa solo minúsculas sin tildes, "
    "números y guiones, por ejemplo 'ingeniero-industrial'."
)
TEXTO_VACIO = "No puede estar vacío."
TEXTO_LARGO = "Es demasiado largo: máximo {maximo} caracteres."
VERSION_INVALIDA = "'{valor}' no es una versión válida: usa el formato 1.2.3."
FORMATO_DESCONOCIDO = (
    "El formato de salida '{valor}' no existe. Formatos disponibles: {validos}."
)
AVISO_OBLIGATORIO = (
    "Un agente con 'sensitive: true' (salud, derecho o finanzas personales) "
    "debe incluir el campo 'disclaimer' con el aviso que mostrará."
)
SKILLS_REPETIDAS = "La skill '{valor}' aparece más de una vez."
SKILL_INEXISTENTE = (
    "La skill '{valor}' no existe en la carpeta skills/. Créala en "
    "skills/{valor}/SKILL.md o quítala de la lista."
)
FAMILIA_NO_COINCIDE = (
    "La familia '{familia}' no coincide con la carpeta donde está el agente "
    "('{carpeta}'). Mueve el archivo a agentes/{familia}/ o corrige el campo 'family'."
)
NOMBRE_NO_COINCIDE_CARPETA = (
    "El nombre de la skill '{nombre}' no coincide con su carpeta '{carpeta}'. "
    "Deben ser iguales."
)
ID_DUPLICADO = (
    "Ya existe un agente con el nombre '{id}' en {otra_ruta}. "
    "Cada agente necesita un 'name' distinto."
)
SKILL_DUPLICADA = "Ya existe una skill con el nombre '{id}' en {otra_ruta}."

# --- Errores de dominio ----------------------------------------------------

AGENTES_REPETIDOS = "Un mismo agente no puede estar dos veces en la sala: '{valor}'."
AGENTE_NO_ENCONTRADO = "No existe un agente con el id '{id}'."
SKILL_NO_ENCONTRADA = "No existe una skill con el id '{id}'."
CATALOGO_SIN_CARPETA = "No se encontró la carpeta de agentes: {ruta}"

# Formato de una línea del informe de errores: archivo, campo y qué corregir.
LINEA_ERROR = "{archivo} · {campo}: {mensaje}"
LINEA_ERROR_SIN_CAMPO = "{archivo}: {mensaje}"

# Traducción de los errores genéricos de Pydantic. La clave es el 'type'
# del error; {ctx} se rellena con los datos que trae el error.
ERRORES_PYDANTIC: dict[str, str] = {
    "missing": CAMPO_OBLIGATORIO,
    "extra_forbidden": "Campo desconocido. Revisa si está mal escrito.",
    "string_type": "Debe ser un texto.",
    "string_too_short": TEXTO_VACIO,
    "string_too_long": "Es demasiado largo: máximo {max_length} caracteres.",
    "int_type": "Debe ser un número entero.",
    "int_parsing": "Debe ser un número entero.",
    "float_type": "Debe ser un número.",
    "float_parsing": "Debe ser un número.",
    "bool_type": "Debe ser true o false.",
    "bool_parsing": "Debe ser true o false.",
    "list_type": "Debe ser una lista, por ejemplo [a, b].",
    "dict_type": "Debe ser un grupo de campos (clave: valor).",
    "model_type": "Debe ser un grupo de campos (clave: valor).",
    "too_short": "Debe tener al menos {min_length} elementos.",
    "too_long": "Debe tener como máximo {max_length} elementos.",
    "greater_than_equal": "Debe ser mayor o igual que {ge}.",
    "less_than_equal": "Debe ser menor o igual que {le}.",
    "greater_than": "Debe ser mayor que {gt}.",
    "less_than": "Debe ser menor que {lt}.",
    "enum": "Valor no permitido. Opciones: {expected}.",
    "literal_error": "Valor no permitido. Opciones: {expected}.",
    "datetime_type": "Debe ser una fecha y hora.",
    "datetime_parsing": "Debe ser una fecha y hora.",
}
ERROR_GENERICO = "Valor no válido."

# --- Servidor MCP ------------------------------------------------------------

SERVIDOR_INSTRUCCIONES = (
    "MAS for People guarda un catálogo de agentes especializados (ingenieros, "
    "economistas, periodistas...). El servidor no razona: entrega las fichas e "
    "instrucciones de cada agente y tú (Claude) haces el trabajo. Usa "
    "listar_agentes para ver qué agentes hay y ver_agente para leer uno completo. "
    "Responde al usuario en español."
)
HERRAMIENTA_LISTAR = (
    "Lista los agentes del catálogo con su id, nombre, familia, postura y "
    "descripción corta. Filtra opcionalmente por familia (por ejemplo "
    "'ingenieria', 'economia', 'comunicacion') o por texto libre (busca en "
    "nombre, postura, descripción y skills; no distingue tildes ni mayúsculas). "
    "Si algún archivo de agente tiene errores, también los devuelve para "
    "que el usuario sepa qué corregir."
)
HERRAMIENTA_VER = (
    "Devuelve un agente completo por su id: ficha, formato de salida con sus "
    "secciones, límites, instrucciones, el archivo agente.md tal cual y las "
    "skills que usa con su descripción. Usa primero listar_agentes para "
    "conocer los ids."
)
PARAM_FAMILIA = "Familia a mostrar, por ejemplo 'ingenieria'. Vacío para todas."
PARAM_TEXTO = "Palabras a buscar, por ejemplo 'escéptico' o 'costos'. Vacío para no filtrar."
PARAM_ID = "Id del agente, por ejemplo 'ingeniero-industrial'."
SERVIDOR_INICIADO = "MAS for People: servidor MCP listo. Catálogo en {raiz} ({agentes} agentes, {skills} skills)."
SERVIDOR_ERRORES_CATALOGO = "MAS for People: {n} archivo(s) con errores en el catálogo:"
RAIZ_NO_ENCONTRADA = (
    "No se encontró la carpeta del proyecto (la que tiene agentes/ y skills/). "
    "Indica la ruta con la variable de entorno MAS_CARPETA o ejecuta el "
    "servidor con 'uv --directory <carpeta> run mas-servidor'."
)

# --- Comando mas-config ------------------------------------------------------

CONFIG_TITULO = "Configuración para Claude Desktop"
CONFIG_PASOS = (
    "1. En Claude Desktop abre Configuración > Desarrollador > Editar configuración.\n"
    "   Se abre el archivo {archivo}\n"
    "2. Si el archivo está vacío o solo tiene {{}}, reemplázalo por el bloque de abajo.\n"
    "   Si ya tiene \"mcpServers\", agrega solo la entrada \"mas-for-people\" dentro.\n"
    "3. Guarda el archivo, cierra Claude Desktop por completo y vuelve a abrirlo."
)
CONFIG_SIN_UV = (
    "Aviso: no encontré el programa 'uv' en esta terminal. Instálalo primero "
    "(ver docs/claude-desktop.md) y vuelve a ejecutar este comando."
)

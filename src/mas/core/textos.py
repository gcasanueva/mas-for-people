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
    "economistas, periodistas...) y lleva salas donde esos agentes trabajan por "
    "turnos sobre un objetivo. El servidor no razona: entrega a cada agente sus "
    "instrucciones y contexto, y tú (Claude) haces de cada uno. Usa "
    "listar_agentes para ver qué agentes hay y ver_agente para leer uno completo.\n\n"
    "Para una sala: abrir_sala (protocolo 'debate' por rondas o 'panel' de una "
    "ronda), luego repite siguiente_turno -> escribe la "
    "intervención de ese agente -> publicar_turno, hasta que siguiente_turno "
    "diga 'listo_para_veredicto'; entonces llama a veredicto (recibes el turno "
    "del verificador), escribe el veredicto y llama a veredicto otra vez con él. "
    "Hazlo todo seguido, sin pedir confirmación al usuario entre turnos; muestra "
    "solo una línea de avance por turno y, al final, el veredicto completo. En "
    "cada turno usa solo lo que entrega siguiente_turno (no lo que escribiste "
    "como otros agentes): así cada agente conserva su propio punto de vista. Si "
    "publicar_turno devuelve errores, corrige ese mismo turno y vuelve a "
    "publicarlo. ver_sala muestra salas anteriores. Responde al usuario en español."
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
SERVIDOR_INICIADO = (
    "MAS for People: servidor MCP listo. Catálogo en {raiz} ({agentes} agentes, "
    "{skills} skills). Salas en {bd}."
)
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

# --- Salas (paso 3) ----------------------------------------------------------

SALA_NO_ENCONTRADA = "No existe una sala con el id '{id}'. Usa ver_sala sin sala_id para ver las salas guardadas."
SALA_CERRADA = "La sala '{id}' ya está cerrada; su veredicto se puede leer con ver_sala."
SALA_AGENTE_INEXISTENTE = "El agente '{id}' no está en el catálogo. Usa listar_agentes para ver los ids disponibles."
SALA_POSTURA_FUERA = "Se indicó una postura para '{id}', pero ese agente no está en la sala."
PROTOCOLO_NO_DISPONIBLE = (
    "El protocolo '{protocolo}' todavía no está disponible en esta versión. "
    "Protocolos disponibles: {disponibles}."
)
PROTOCOLO_DESCONOCIDO = "Protocolo desconocido: '{protocolo}'. Usa uno de estos: {disponibles}."
TRANSICION_INVALIDA = "La sala no puede pasar del estado '{desde}' a '{hasta}'."

TURNO_NO_ENCONTRADO = (
    "El turno '{turno_id}' no pertenece a la sala '{sala_id}'. Llama a siguiente_turno para "
    "saber qué turno toca."
)
TURNO_YA_PUBLICADO = "El turno '{turno_id}' ya se publicó. Llama a siguiente_turno para seguir."
TURNO_FALTAN_SECCIONES = (
    "Al texto le faltan secciones del formato '{formato}': {faltan}. Cada sección debe empezar "
    "una línea con su nombre, por ejemplo '## {ejemplo}'."
)
TURNO_DEMASIADO_LARGO = (
    "El texto tiene {palabras} palabras y el límite de la sala es {limite}. Acórtalo y vuelve a publicar."
)
TURNO_POSTURA_NO_PERMITIDA = (
    "En esta ronda el artefacto solo puede tener postura {permitidas}; llegó '{postura}'."
)
TURNO_RESPONDE_A_INEXISTENTE = "artefacto.responde_a menciona el turno '{id}', que no es de esta sala."
TURNO_CORREGIR = (
    "No se guardó nada. Corrige lo indicado, sin cambiar de agente, y vuelve a llamar a "
    "publicar_turno con el mismo turno_id."
)
CONTENIDO_VACIO = "El contenido está vacío: escribe el texto de la intervención."
VEREDICTO_CORREGIR = (
    "No se guardó nada. Corrige lo indicado y vuelve a llamar a veredicto con el sala_id y la "
    "respuesta del verificador."
)
TURNO_INDICACION = (
    "Escribe la intervención de {nombre} (postura: {postura}) siguiendo sus instrucciones y sus "
    "skills, con las secciones del formato como encabezados ({secciones}) y en {max_palabras} "
    "palabras como máximo. Responde al objetivo de la sala{mesa}. Luego llama a publicar_turno "
    "con el contenido y el artefacto. No muestres la intervención completa al usuario: basta "
    "una línea de avance."
)
TURNO_INDICACION_MESA = " y ten en cuenta el resumen de la mesa"
TURNO_INDICACION_SIN_MESA = "; en este protocolo no ves lo que dijeron los demás"
TURNO_PUBLICADO_SIGUE = "Turno guardado. Llama a siguiente_turno para el próximo agente."
TURNO_PUBLICADO_VEREDICTO = "Turno guardado. Ya hablaron todos: llama a veredicto con el sala_id."
LISTO_PARA_VEREDICTO = "Ya no quedan turnos. Llama a veredicto con el sala_id para el cierre."

VEREDICTO_FALTAN_TURNOS = (
    "Aún quedan turnos sin publicar en la sala '{id}'. Llama a siguiente_turno hasta que diga "
    "'listo_para_veredicto'."
)
VEREDICTO_PRIMERO_SIN_CONTENIDO = (
    "Primero llama a veredicto solo con el sala_id para recibir el turno del verificador; "
    "luego vuelve a llamarlo con su respuesta."
)
VEREDICTO_FALTA_CONFIANZA = "Falta 'confianza' (un número de 0 a 1)."
VEREDICTO_INDICACION = (
    "Ahora actúa como el verificador: no participaste en la discusión. Revisa la mesa contra el "
    "objetivo y escribe el veredicto con las secciones {secciones} en {max_palabras} palabras como "
    "máximo. Luego llama otra vez a veredicto con sala_id, contenido, acuerdos, desacuerdos, "
    "confianza y plan."
)
VEREDICTO_GUARDADO = (
    "Veredicto guardado y sala cerrada. Muéstrale al usuario el veredicto completo; los hilos de "
    "cada agente se pueden leer con ver_sala."
)
VEREDICTO_YA_GUARDADO = "La sala ya estaba cerrada; este es el veredicto guardado."

# Textos de ver_sala (Markdown)
VISTA_DESCONOCIDA = "Vista desconocida: '{vista}'. Usa 'mesa', 'hilo' o 'veredicto'."
VISTA_SIN_SALAS = "Todavía no hay salas guardadas."
VISTA_TITULO_SALAS = "# Salas guardadas"
VISTA_RONDA = "### Ronda {ronda}"
VISTA_MESA_VACIA = "_La mesa está vacía: nadie ha publicado todavía._"
VISTA_HILO_VACIO = "_{nombre} no ha publicado turnos en esta sala._"
VISTA_SIN_VEREDICTO = "_La sala todavía no tiene veredicto (estado: {estado})._"
VISTA_AGENTE_FUERA = "El agente '{id}' no participa en esta sala. Participan: {agentes}."

# Descripciones de las herramientas de sala (las lee Claude).
HERRAMIENTA_ABRIR_SALA = (
    "Abre una sala con un objetivo y de 2 a 6 agentes del catálogo (sus ids). "
    "Protocolo 'debate' (por defecto): en la ronda 1 cada agente propone sin ver a "
    "los demás; en las rondas siguientes lee el resumen de la mesa y apoya, objeta "
    "o corrige. Termina por consenso (una ronda sin objeciones ni correcciones) o al "
    "llegar a max_rondas. Protocolo 'panel': una sola ronda, nadie ve a los demás. "
    "En ambos, al final un verificador revisa todo. Devuelve sala_id y el orden de "
    "turnos previsto (en debate, el máximo). Después llama a siguiente_turno."
)
HERRAMIENTA_SIGUIENTE_TURNO = (
    "Devuelve el turno que toca en la sala: qué agente habla, sus instrucciones, "
    "skills, su hilo, el resumen de la mesa (si el protocolo lo permite), el "
    "formato de salida y el límite de palabras. Escribe la intervención como ese "
    "agente y publícala con publicar_turno. Si responde estado "
    "'listo_para_veredicto', llama a veredicto. Si el turno sigue pendiente, "
    "devuelve el mismo turno otra vez."
)
HERRAMIENTA_PUBLICAR_TURNO = (
    "Publica la intervención de un agente: el texto completo (contenido) con las "
    "secciones de su formato como encabezados, y el artefacto estructurado que va "
    "a la mesa. Si algo no cumple, no se guarda y devuelve ok=false con la lista "
    "de errores para corregir ese mismo turno."
)
HERRAMIENTA_VEREDICTO = (
    "Cierre de la sala. Primera llamada, solo con sala_id: devuelve el turno del "
    "verificador (objetivo y mesa completa). Segunda llamada, con contenido, "
    "acuerdos, desacuerdos, confianza y plan: lo valida, lo guarda y cierra la sala."
)
HERRAMIENTA_VER_SALA = (
    "Muestra una sala guardada en Markdown. vista='mesa' (artefactos de todos), "
    "'hilo' (textos completos; con agente, solo los de ese agente) o 'veredicto'. "
    "Sin sala_id, lista las salas guardadas con su id, fecha y estado."
)
PARAM_OBJETIVO = "Qué debe resolver la sala, en palabras del usuario."
PARAM_AGENTES = "Ids de 2 a 6 agentes, en el orden en que hablarán."
PARAM_PROTOCOLO = "'debate' (rondas con crítica, por defecto) o 'panel' (una ronda en paralelo)."
PARAM_MAX_RONDAS = "Rondas máximas del debate (1 a 4; por defecto 2). El panel siempre usa 1."
PARAM_MAX_PALABRAS = "Palabras máximas por intervención (50 a 2000)."
PARAM_POSTURAS = (
    "Opcional: postura distinta a la habitual para algún agente, por ejemplo "
    "{\"ingeniero-industrial\": \"innovador\"}."
)
PARAM_SALA_ID = "Id de la sala que devolvió abrir_sala."
PARAM_TURNO_ID = "Id del turno que devolvió siguiente_turno."
PARAM_CONTENIDO = "Texto completo de la intervención, con cada sección del formato como encabezado."
PARAM_ARTEFACTO = "Resumen estructurado de la intervención, que va a la mesa."
PARAM_VEREDICTO_CONTENIDO = (
    "Solo en la segunda llamada: el veredicto completo con las secciones Acuerdos, "
    "Desacuerdos, Confianza y Plan de acción."
)
PARAM_ACUERDOS = "Segunda llamada: lista de acuerdos, uno por elemento."
PARAM_DESACUERDOS = "Segunda llamada: lista de desacuerdos con las posiciones en juego."
PARAM_CONFIANZA = "Segunda llamada: confianza en el veredicto, de 0 a 1."
PARAM_PLAN = "Segunda llamada: pasos del plan de acción, en orden."
PARAM_VISTA = "Qué mostrar: 'mesa', 'hilo' o 'veredicto'."
PARAM_AGENTE_HILO = "Solo para vista='hilo': id del agente cuyo hilo mostrar."
ARTEFACTO_CAMPOS: dict[str, str] = {
    "postura": (
        "Ronda 1 (y panel): 'propuesta'. Rondas de crítica del debate: 'apoyo', "
        "'objecion' o 'correccion' (estas dos exigen responde_a)."
    ),
    "resumen": "La idea central en 1 a 3 frases (máximo 600 caracteres).",
    "supuestos": "Hasta 5 supuestos de los que depende la propuesta (frases cortas).",
    "riesgos": "Hasta 5 riesgos principales (frases cortas).",
    "responde_a": "Ids de turnos (los turno_id del resumen de la mesa) a los que responde; vacío en la ronda 1 y en panel.",
    "confianza": "Confianza del agente en su propuesta, de 0 a 1.",
    "cambiaria_de_opinion_si": "Qué dato o hecho le haría cambiar de opinión.",
}
SALA_ABIERTA = "Sala abierta. Llama a siguiente_turno con este sala_id."
SALA_ABIERTA_DEBATE = (
    "Sala abierta. Llama a siguiente_turno con este sala_id y sigue sin pausas hasta "
    "'listo_para_veredicto'; el debate puede terminar antes de lo previsto si hay consenso."
)
TURNO_INDICACION_CRITICA = (
    " Es una ronda de crítica: revisa las intervenciones de la mesa desde tu postura y elige "
    "'apoyo' si las sostienes, 'objecion' si ves un problema o 'correccion' si propones un "
    "cambio concreto; en esos dos casos pon en responde_a los turno_id a los que respondes. "
    "No repitas tu propuesta: avanza la discusión."
)
DEBATE_FALTA_RESPONDE_A = (
    "Una '{postura}' debe indicar a qué responde: pon en artefacto.responde_a el turno_id de "
    "la intervención que objetas o corriges (están en resumen_mesa)."
)
MODERADOR_SIGUE = "Moderador: ronda {ronda} cerrada ({resumen}). Hay objeciones o correcciones: sigue la ronda {siguiente}."
MODERADOR_CONSENSO = "Moderador: ronda {ronda} cerrada ({resumen}). Hay consenso: el debate termina y toca el veredicto."
MODERADOR_LIMITE = "Moderador: ronda {ronda} cerrada ({resumen}). Se llegó al máximo de rondas: toca el veredicto."

# Visor de escritorio (paso 4, CU-07)
VISOR_TITULO = "MAS for People"
VISOR_PESTANA_CATALOGO = "Catálogo"
VISOR_PESTANA_SALAS = "Salas"
VISOR_PESTANA_MESA = "Mesa"
VISOR_PESTANA_HILOS = "Hilos"
VISOR_PESTANA_VEREDICTO = "Veredicto"
VISOR_COL_AGENTE = "Agente"
VISOR_COL_POSTURA = "Postura"
VISOR_COLUMNAS_SALAS = ("Fecha", "Objetivo", "Protocolo", "Estado", "Turnos")
VISOR_ELIGE_AGENTE = "Elige un agente de la lista para ver su ficha."
VISOR_SIN_SKILLS = "_Este agente no usa skills._"
VISOR_ERRORES_CATALOGO = "Archivos con errores ({n})"
VISOR_ERRORES_TITULO = "# Archivos con errores\n\nEstos archivos no se cargaron. Corrígelos y pulsa Recargar."
VISOR_RECARGAR = "Recargar"
VISOR_BUSCAR = "Buscar en el objetivo…"
VISOR_EXPORTAR = "Exportar a Markdown…"
VISOR_EXPORTAR_TITULO = "Exportar sala"
VISOR_EXPORTADA = "Sala exportada a {ruta}"
VISOR_EXPORTAR_ERROR = "No se pudo guardar el archivo: {detalle}"
VISOR_SIN_SALAS = (
    "Todavía no hay salas guardadas.\n\n"
    "Abre una desde Claude Desktop (por ejemplo: «abre un debate con el ingeniero "
    "industrial y el economista ortodoxo para…») y aparecerá aquí sola."
)
VISOR_SIN_RESULTADOS = "Ninguna sala tiene «{texto}» en el objetivo."
VISOR_ELIGE_SALA = "Elige una sala de la lista para ver su mesa, sus hilos y su veredicto."
VISOR_SALA_DESAPARECIDA = "La sala ya no está en la base de datos."
VISOR_EN_CURSO = "En curso: se actualiza sola cada {segundos} s · {pendientes} turno(s) en preparación"
VISOR_CERRADA = "Sala cerrada"
VISOR_ESTADO_BD = "Base de datos: {ruta}"
VISOR_ESTADO_SIN_BD = "Aún no existe {ruta}: se creará al abrir la primera sala en Claude Desktop."
VISOR_ACTUALIZADO = "Actualizado {hora}"
VISOR_SIN_RAIZ = "No se encontró la carpeta del proyecto"
VISOR_SIN_PYSIDE = (
    "Falta la biblioteca de la ventana (Qt para Python). En la carpeta del proyecto ejecuta "
    "«uv sync» y vuelve a intentarlo."
)

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
    "listar_agentes para ver qué agentes hay y ver_agente para leer uno completo. "
    "Para crear o editar un agente usa guardar_agente: primero con solo_validar=true "
    "para mostrar el borrador y, cuando el usuario lo confirme, para guardarlo.\n\n"
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
    "publicarlo. ver_sala muestra salas anteriores y exportar_sala las guarda en "
    "Markdown. exportar_agentes copia agentes a una carpeta para usarlos como "
    "subagentes en Claude Code. Responde al usuario en español."
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
VISTA_ORIGEN_PROPIO = "- **Origen:** creado por ti (mis-agentes/, solo en este equipo)"
VISTA_MARCA_PROPIO = " · propio"
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
    "supuestos": "Hasta 4 supuestos de los que depende la propuesta (frases cortas, hasta 120 caracteres).",
    "riesgos": "Hasta 4 riesgos principales (frases cortas, hasta 120 caracteres).",
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

# --- Crear y editar agentes (paso 6, CU-02) ----------------------------------

CREAR_ID_RESERVADO = "'{id}' es un agente de sistema; elige otro nombre."
CREAR_YA_EXISTE = (
    "Ya existe un agente con el id '{id}' ({ruta}). Si quieres modificarlo, vuelve a llamar con "
    "reemplazar=true; si es otro agente, cámbiale el nombre o pasa un id distinto."
)
CREAR_CORREGIR = (
    "No se guardó nada. Corrige lo indicado (formatos_validos y skills_disponibles dicen qué "
    "valores existen) y vuelve a llamar a guardar_agente."
)
CREAR_BORRADOR_OK = (
    "El borrador es válido y no se guardó todavía. Muéstrale al usuario el agente_md y, cuando "
    "lo confirme, llama otra vez a guardar_agente con los mismos datos y solo_validar=false."
)
CREAR_GUARDADO = (
    "Agente '{nombre}' guardado en {ruta}. Ya aparece en listar_agentes y se puede usar en una "
    "sala. Es local: está solo en este equipo y no se comparte."
)
HERRAMIENTA_GUARDAR_AGENTE = (
    "Crea un agente nuevo o edita uno existente y lo guarda como agente.md. Campos: nombre "
    "visible, especialidad (cuándo usarlo, 1 o 2 frases), familia (p. ej. 'ingenieria', "
    "'salud', 'derecho'), postura por defecto (p. ej. 'conservador', 'escéptico'), skills "
    "(ids existentes), formato_salida (id de formato) e instrucciones (cómo trabaja, en "
    "Markdown). Primero llama con solo_validar=true para obtener el borrador y mostrárselo al "
    "usuario; guarda (solo_validar=false) solo cuando el usuario confirme. Para editar un "
    "agente existente pasa su id y reemplazar=true. Si algo no cumple devuelve ok=false con "
    "los errores, los formatos válidos y las skills disponibles. Los agentes nuevos quedan en "
    "mis-agentes/, solo en este equipo."
)
PARAM_NOMBRE_AGENTE = "Nombre visible, por ejemplo 'Ingeniera de datos'. El id se crea a partir de él."
PARAM_ESPECIALIDAD = "Qué sabe hacer y cuándo usarlo, en 1 o 2 frases (máximo 400 caracteres)."
PARAM_FAMILIA_AGENTE = "Familia del agente: una existente (ver listar_agentes) o una nueva, en minúsculas."
PARAM_POSTURA = "Postura por defecto, por ejemplo 'conservador', 'innovador', 'escéptico' o 'pragmático'."
PARAM_SKILLS = "Ids de skills existentes (pueden ser ninguna). Si falta alguna, el error lista las disponibles."
PARAM_FORMATO = (
    "Formato de salida: propuesta-tecnica, analisis-economico, plan-de-mercado, nota-critica, "
    "informe-con-fuentes u objeciones-priorizadas."
)
PARAM_INSTRUCCIONES = (
    "Instrucciones del agente en Markdown: quién es, cómo trabaja (viñetas) y qué evita. "
    "Sin encabezado YAML."
)
PARAM_ID_AGENTE = "Opcional: id explícito (minúsculas y guiones). Para editar, el id del agente existente."
PARAM_SENSIBLE = "true si es de salud, derecho o finanzas personales; entonces 'aviso' es obligatorio."
PARAM_AVISO = "Aviso que mostrará un agente sensible, por ejemplo 'No reemplaza a un médico'."
PARAM_REEMPLAZAR = "true para sobrescribir un agente que ya existe (editar)."
PARAM_SOLO_VALIDAR = "true para validar y ver el borrador sin guardar nada."

# --- Prompts MCP (RF-13) -----------------------------------------------------

PROMPT_DEBATE_DESC = "Abre un debate por rondas entre agentes sobre un objetivo y lo lleva hasta el veredicto."
PROMPT_PANEL_DESC = "Abre un panel: cada agente responde una vez sin ver a los demás y luego hay veredicto."
PROMPT_CREAR_DESC = "Te guía para crear un agente propio: lo completa contigo, te muestra el borrador y lo guarda."
PROMPT_ARG_OBJETIVO = "Qué quieres resolver."
PROMPT_ARG_AGENTES = "Opcional: ids o nombres de los agentes, separados por comas. Vacío para que se sugiera un equipo."
PROMPT_ARG_RONDAS = "Opcional: rondas máximas del debate (1 a 4). Por defecto 2."
PROMPT_ARG_DESCRIPCION = "Opcional: describe con tus palabras el agente que quieres."

PROMPT_EQUIPO_ELEGIDO = "Usa estos agentes, en este orden (si alguno no es un id, búscalo con listar_agentes): {agentes}."
PROMPT_EQUIPO_SUGERIDO = (
    "No elegí agentes: llama a listar_agentes y sugiere un equipo de 3 o 4 agentes de familias "
    "distintas y con posturas que se contrapongan (por ejemplo un conservador y un innovador, "
    "y alguien escéptico). Dime el equipo en una línea con el porqué y ábrelo sin esperar, "
    "salvo que te pida cambiarlo."
)
PROMPT_DEBATE = (
    "Quiero un debate por rondas en MAS for People.\n\n"
    "Objetivo: {objetivo}\n\n{equipo}\n\n"
    "Abre la sala con abrir_sala (protocolo 'debate', max_rondas {rondas}) y llévala hasta el "
    "final sin pedirme confirmación entre turnos: siguiente_turno → escribe la intervención de "
    "ese agente usando solo lo que te entrega → publicar_turno, hasta 'listo_para_veredicto'; "
    "luego veredicto dos veces. Muéstrame una línea de avance por turno, los avisos del "
    "moderador al cerrar cada ronda y, al final, el veredicto completo y el sala_id.\n\n"
    "Reglas del moderador:\n{reglas}"
)
PROMPT_PANEL = (
    "Quiero un panel en MAS for People.\n\n"
    "Objetivo: {objetivo}\n\n{equipo}\n\n"
    "Abre la sala con abrir_sala (protocolo 'panel') y llévala hasta el final sin pedirme "
    "confirmación entre turnos: siguiente_turno → escribe la intervención de ese agente usando "
    "solo lo que te entrega → publicar_turno, hasta 'listo_para_veredicto'; luego veredicto dos "
    "veces. Muéstrame una línea de avance por turno y, al final, el veredicto completo y el "
    "sala_id.\n\nReglas del moderador:\n{reglas}"
)
PROMPT_CREAR = (
    "Quiero crear un agente propio en MAS for People.\n\n{descripcion}"
    "Ayúdame así:\n"
    "1. Completa los campos a partir de lo que te dije: nombre, especialidad, familia, postura, "
    "skills, formato de salida e instrucciones (quién es, cómo trabaja en viñetas y qué evita). "
    "Pregúntame solo lo que no puedas deducir, en un solo mensaje.\n"
    "2. Llama a guardar_agente con solo_validar=true y muéstrame el agente_md que devuelve.\n"
    "3. Si pido cambios, ajústalo y valida de nuevo. Cuando lo confirme, guárdalo con "
    "solo_validar=false y dime dónde quedó.\n"
    "Si es de salud, derecho o finanzas personales, márcalo como sensible con un aviso claro.\n\n"
    "Opciones disponibles:\n{opciones}"
)
PROMPT_SIN_DESCRIPCION = "Todavía no te he dicho cómo es: pregúntamelo primero.\n\n"
PROMPT_CON_DESCRIPCION = "Así lo imagino: {descripcion}\n\n"

# --- Exportar (paso 7, CU-06, RF-12, RF-15) ----------------------------------

EXPORTAR_CUERPO_INICIO = "Eres {nombre}. Tu postura por defecto es: {postura}."
EXPORTAR_FORMATO = "## Formato de respuesta\nResponde en el formato «{nombre}», con estas secciones como encabezados: {secciones}."
EXPORTAR_AVISO = "## Aviso obligatorio\nIncluye siempre este aviso al responder: {aviso}"
EXPORTAR_CARPETA_NO_EXISTE = (
    "La carpeta '{carpeta}' no existe. Indica la carpeta del proyecto donde usarás Claude Code "
    "(los agentes se escriben en su subcarpeta .claude)."
)
EXPORTAR_LISTO = (
    "Listo. Abre Claude Code en esa carpeta: los agentes aparecen con /agents y Claude los usa "
    "como subagentes cuando la tarea encaja con su descripción (o si se lo pides por su nombre)."
)
EXPORTAR_OMITIDOS = (
    "Algunos archivos ya existían con otro contenido y no se tocaron (ver 'omitidos'). Para "
    "sobrescribirlos vuelve a exportar con reemplazar=true."
)
HERRAMIENTA_EXPORTAR_AGENTES = (
    "Exporta agentes del catálogo a Claude Code: escribe cada uno como subagente en "
    "<carpeta>/.claude/agents/<id>.md y copia sus skills en <carpeta>/.claude/skills/. Sin "
    "'agentes' exporta todos. No sobrescribe archivos distintos salvo con reemplazar=true."
)
HERRAMIENTA_EXPORTAR_SALA = (
    "Guarda una sala completa (mesa, hilos y veredicto) en un archivo Markdown. Sin 'archivo' la "
    "guarda en la carpeta exportados/ del proyecto. Devuelve la ruta."
)
PARAM_CARPETA_EXPORTAR = (
    "Carpeta del proyecto donde se usará Claude Code, por ejemplo C:\\Users\\ana\\mi-proyecto. "
    "Debe existir."
)
PARAM_AGENTES_EXPORTAR = "Ids de los agentes a exportar. Vacío para exportar todos."
PARAM_REEMPLAZAR_EXPORTAR = "true para sobrescribir archivos que ya existan con otro contenido."
PARAM_ARCHIVO_SALA = "Opcional: ruta del archivo .md. Vacío para usar exportados/sala-<id>.md."
SALA_EXPORTADA = "Sala guardada en {ruta}. Ábrela con cualquier editor de texto o visor de Markdown."
SALA_ARCHIVO_ERROR = "No se pudo escribir el archivo '{ruta}': {detalle}"
CLI_EXPORTAR_USO = (
    "Uso: mas-exportar <carpeta-del-proyecto> [id-agente ...] [--reemplazar]\n"
    "Sin ids exporta todos los agentes del catálogo a <carpeta>/.claude/."
)
CLI_EXPORTAR_RESUMEN = "{n} agente(s) exportado(s) a {carpeta}"
CLI_EXPORTAR_OMITIDO = "  - omitido (ya existe con otro contenido): {ruta}"

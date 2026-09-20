"""Esquema de las autorías documentadas por HCDN."""

PARLIAMENTARY_SCHEMA = """
=== AUTORÍAS Y FIRMANTES: VISTA autorias_leyes ===

La vista autorias_leyes ya une leyes, proyectos y firmantes. Consultala directamente.
Una ley puede aparecer varias veces: una fila por firmante y proyecto cabecera.
Campos:
- ley_id: FK a leyes.id
- numero_norma, titulo_resumido, year: datos de la ley aprobada
- proyecto_id: identificador oficial HCDN del proyecto cabecera
- camara_origen: Diputados o Senado
- expediente_diputados, expediente_senado: identificadores del expediente
- fecha_publicacion: fecha de publicación del proyecto, YYYY-MM-DD
- firmante: nombre publicado; también puede ser una autoridad del Ejecutivo o comisión
- rol: 'autor' si coincide con AUTOR del catálogo oficial, o 'firmante'
- orden: posición en la ficha; puede ser NULL. No inferir autoría del orden.
- bloque: bloque HISTÓRICO de la ficha, o 'PODER EJECUTIVO', o NULL
- distrito: distrito de la ficha o NULL
- fuente_url: enlace oficial que documenta la firma
- fuente_autor_url: catálogo oficial que documenta el rol autor
- estado_ficha: ok, no_signers o error

Alcance: proyectos cabecera asociados a leyes de la base entre 2008 y 2025.
La cobertura es parcial: hay leyes y firmantes sin datos. No representa todos
los proyectos presentados, ni todas las iniciativas acumuladas en una ley.
El bloque parlamentario NO es necesariamente el partido; PODER EJECUTIVO
es una procedencia institucional, no un bloque partidario. NULL es desconocido.
No existen datos de votaciones, comisiones ni trámites en estas tablas.

Ejemplo: autor y demás firmantes de una ley:
SELECT DISTINCT numero_norma, firmante, rol, bloque, distrito,
 expediente_diputados, fuente_url, fuente_autor_url
FROM autorias_leyes WHERE numero_norma = '26618'
ORDER BY CASE WHEN rol='autor' THEN 0 ELSE 1 END, firmante LIMIT 20;

Ejemplo: leyes impulsadas como autor por un bloque:
SELECT DISTINCT numero_norma, titulo_resumido, year, firmante, rol, bloque, fuente_url
FROM autorias_leyes WHERE rol='autor' AND bloque LIKE '%SOCIALISTA%'
ORDER BY year DESC LIMIT 20;

Ejemplo: cantidad de leyes con firma de una persona, incluyendo cofirmas:
SELECT firmante, COUNT(DISTINCT ley_id) AS leyes_con_firma
FROM autorias_leyes WHERE firmante LIKE '%APELLIDO%' GROUP BY firmante LIMIT 20;
"""

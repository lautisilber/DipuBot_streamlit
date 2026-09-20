# Cobertura de autorías — carga del 20/09/2026

Base enriquecida: `data/raw/leyes-1997-2025_unificada.sqlite3`.

## Resultado

- 2.952 leyes originales conservadas, sin cambios en ninguna columna.
- 1.435 leyes locales sancionadas entre 2008 y 2025.
- **1.305 leyes con autor del proyecto cabecera: 90,9 % del período.**
- **5.966 registros de firmas**: 1.305 autores y 4.661 firmas adicionales.
- 1.294 leyes con bloque o procedencia institucional; 11 con ese dato desconocido.
- 990 nombres distintos y 135 valores distintos de bloque/procedencia institucional.
  Los nombres distintos no constituyen un registro desambiguado de personas.
- 1.305 fichas descargadas y validadas; ninguna descarga fallida.
- 130 leyes del período sin cruce en el conjunto oficial utilizado.

## Por año de sanción

| Año | Leyes locales | Con autor documentado | Sin cruce |
|---|---:|---:|---:|
| 2008 | 126 | 42 | 84 |
| 2009 | 111 | 81 | 30 |
| 2010 | 69 | 63 | 6 |
| 2011 | 79 | 76 | 3 |
| 2012 | 104 | 104 | 0 |
| 2013 | 87 | 87 | 0 |
| 2014 | 192 | 188 | 4 |
| 2015 | 126 | 125 | 1 |
| 2016 | 96 | 96 | 0 |
| 2017 | 87 | 87 | 0 |
| 2018 | 65 | 65 | 0 |
| 2019 | 41 | 41 | 0 |
| 2020 | 71 | 71 | 0 |
| 2021 | 55 | 55 | 0 |
| 2022 | 37 | 37 | 0 |
| 2023 | 34 | 34 | 0 |
| 2024 | 42 | 40 | 2 |
| 2025 | 13 | 13 | 0 |

La cobertura refiere a la colección local, no a todos los proyectos argentinos.
El corte por inicio del proyecto puede excluir leyes sancionadas después de
2008 cuyo proyecto se inició antes. Los faltantes individuales requieren
investigación adicional: no se dedujo una causa para cada caso ni se inventaron firmas.
El listado completo de números sin cruce está en `data/ingest/hcdn/report.json`.

## Fuentes efectivamente usadas

- [CSV de leyes sancionadas](https://datos.hcdn.gob.ar/dataset/5b1d2f38-e23f-412c-a286-02ab9dcf6082/resource/68dfd7f8-91f3-4ecf-aebf-a860d1ca1a98/download/leyes_sancionadas3.2.csv).
- [CSV de proyectos parlamentarios](https://datos.hcdn.gob.ar/dataset/839441fc-1b5c-45b8-82c9-8b0f18ac7c9b/resource/22b2d52c-7a0e-426b-ac0a-a3326c388ba6/download/proyectos_parlamentarios2.5.csv).
- Ficha de cada expediente, conservada en `data/ingest/hcdn/fichas/`.

Ejemplos de fichas y resultados comprobados:

- Ley 26.618: autora del proyecto cabecera Silvia Augsburger, Partido Socialista;
  [expediente 1737-D-2009](https://www.hcdn.gob.ar/comisiones/permanentes/clgeneral/proyecto.html?exp=1737-D-2009).
- Ley 26.485: autora del proyecto cabecera María Cristina Perceval, Frente para
  la Victoria - PJ; [expediente 0141-S-2008](https://www.hcdn.gob.ar/comisiones/permanentes/clgeneral/proyecto.html?exp=0141-S-2008).
- Ley 27.610: autor registrado Alberto Fernández, Poder Ejecutivo;
  [expediente 0011-PE-2020](https://www.hcdn.gob.ar/comisiones/permanentes/clgeneral/proyecto.html?exp=0011-PE-2020).

Estos ejemplos identifican el proyecto cabecera registrado, sin atribuir autoría
exclusiva de toda la ley ni descartar otras iniciativas antecedentes.

## Validación y despliegue

Se verificaron integridad SQLite, claves foráneas, igualdad de la tabla `leyes`
con su respaldo y consultas de autoría. Las pruebas automáticas cubren
idempotencia, archivos alterados, expediente incorrecto, bloque histórico y nulos.
La prueba con la API real quedó impedida por `credit_balance_exhausted` (HTTP 429).

La copia previa está en `data/raw/leyes-1997-2025_unificada.before-autorias-20260920-183253-803506.sqlite3`.
La base unificada ya está versionada: para producción hay que publicar también
su cambio o ejecutar la importación en destino. La caché y los respaldos quedan
excluidos. Ver [procedimiento](AUTORES_Y_BLOQUES.md).

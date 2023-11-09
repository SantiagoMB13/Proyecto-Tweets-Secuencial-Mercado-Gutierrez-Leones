El archivo se probó en Docker con la imagen provista y funcionó (a pesar de que mi codigo de python tenia 2 imports que no tenia el de ejemplo). No me quejo.

Se aprovechó el formato de carpetas y archivos para optimizar las decompresiones cuando hay filtros de fecha_inicial y fecha_final. Esto a su vez significa que el generador.py SOLO funciona en rutas de archivo con la siguiente estructura: path_asignado_con_-d/año/mes/dia/cualquier_path/archivo.bz2.json
Ej: data/2016/01/01/01/01.bz2.json 

El filtro de fecha_inicial y fecha_final es inclusivo, es decir que si por ejemplo fi es 01/01/2016, se incluiran los tweets del 01/01/2016 en adelante.

Para los hashtags puedes usar o no el #, es decir, tanto #DmMeCarter como DmMeCarter son validos en una línea del archivo de hashtags.

Espero una buena nota pls 🤠👍
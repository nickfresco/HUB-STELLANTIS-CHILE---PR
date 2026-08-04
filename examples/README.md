# Ejemplos

Noticias de muestra (ficticias) para probar el sistema directamente,
sin depender de los tests. Son los mismos casos que ya validan
`tests/test_brief_generator.py`, presentados aquí como ejemplos de uso
directo.

```bash
python main.py examples/ejemplo_recall_con_impacto_chile.json
python main.py examples/ejemplo_problema_tecnico_sin_impacto_chile.json
python main.py examples/ejemplo_lanzamiento_stellantis.json
python main.py examples/ejemplo_sin_event_type_explicito.json
```

Para probar con una noticia real: copia el formato de cualquiera de
estos archivos (ver `README.md` en la raíz del proyecto, sección
"Formato de entrada") y ejecuta:

```bash
python main.py ruta/a/tu_noticia.json
```

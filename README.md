# Sistema mínimo de recepción y validación de becas

Este paquete convierte tu validador en una aplicación web simple con Streamlit.

## Archivos
- `beca_validator.py`: lógica de validación.
- `app.py`: interfaz web para carga, validación y descarga de reportes.
- `requirements.txt`: dependencias mínimas.

## Cómo ejecutar

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Qué hace
1. La IES sube un `.xlsx` o `.csv`.
2. El sistema ejecuta las reglas del validador.
3. Muestra métricas y el detalle de errores.
4. Permite descargar un Excel con:
   - `datos_validados`
   - `errores`
   - `resumen`

## Cómo usarlo en red
- Puedes ejecutarlo en un servidor interno.
- Las universidades pueden entrar por navegador si la red institucional lo permite.
- Para una siguiente etapa, puedes agregar:
  - login por universidad,
  - historial de cargas,
  - base de datos,
  - almacenamiento de versiones.

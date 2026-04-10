from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from beca_validator import BecaValidator, build_output_workbook, read_input_file

st.markdown("""
<style>
h1, h2, h3, h4, h5, h6, p, label {
    font-family: Cambria, Georgia, "Times New Roman", serif !important;
}
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Validador de Becas", layout="wide")

st.title("Sistema de recepción y validación de becas")
st.caption("Carga un archivo Excel o CSV, ejecútalo contra las reglas del validador y descarga el reporte de resultados.")

st.info(""" 
Este sistema es únicamente para validación previa de archivos.
La información cargada no se almacena ni se conserva en el sistema.
""")

with st.sidebar:
    st.header("Configuración")
    sheet_name = st.text_input(
        "Hoja a leer",
        value="0",
        help="Usa 0 para la primera hoja o escribe el nombre exacto."
    )
    st.markdown("""
<div style="font-family: Cambria, Georgia, 'Times New Roman', serif; line-height: 1.8;">
<b>Flujo del proceso</b><br><br>
1. Cargue el archivo para la validación.<br>
2. El sistema valida automáticamente.<br>
3. Se visualizan errores por fila y columna.<br>
4. Se debe descargar el reporte en caso de errores para su corrección.
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Sube la plantilla de becas", type=["xlsx", "csv"])


def parse_sheet(value: str):
    value = value.strip()
    if value.isdigit():
        return int(value)
    return value


if uploaded_file is not None:
    try:
        df = read_input_file(uploaded_file, uploaded_file.name, parse_sheet(sheet_name))
        st.success(f"Archivo cargado correctamente: {uploaded_file.name}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Filas detectadas", len(df))
        with col2:
            st.metric("Columnas detectadas", len(df.columns))
        with col3:
            st.metric("Fecha de validación", datetime.now().strftime("%d/%m/%Y %H:%M"))

        with st.expander("Vista previa del archivo cargado", expanded=False):
            df_preview = df.head(20).copy()
            for col in df_preview.columns:
                df_preview[col] = df_preview[col].astype(str)
            st.dataframe(df_preview, width="stretch")

        if st.button("Ejecutar validación", type="primary"):
            validator = BecaValidator()
            df_validated, df_errors = validator.validate(df)
            workbook_bytes = build_output_workbook(df_validated, df_errors)

            st.subheader("Resultado")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Total registros", len(df_validated))
            with c2:
                st.metric("Registros con error", df_errors["fila_excel"].nunique() if not df_errors.empty else 0)
            with c3:
                st.metric("Total errores", len(df_errors))

            if df_errors.empty:
                st.success("El archivo no presenta errores según las reglas actuales.")
            else:
                st.error("El archivo presenta observaciones. Revisa el detalle y descarga el reporte.")

                filtro_tipo = st.multiselect(
                    "Filtrar por tipo de error",
                    options=sorted(df_errors["tipo_error"].dropna().unique().tolist()),
                    default=sorted(df_errors["tipo_error"].dropna().unique().tolist()),
                )
                filtro_columna = st.multiselect(
                    "Filtrar por columna",
                    options=sorted(df_errors["columna"].dropna().unique().tolist()),
                    default=sorted(df_errors["columna"].dropna().unique().tolist()),
                )

                df_show = df_errors.copy()
                if filtro_tipo:
                    df_show = df_show[df_show["tipo_error"].isin(filtro_tipo)]
                if filtro_columna:
                    df_show = df_show[df_show["columna"].isin(filtro_columna)]

                df_show_view = df_show.copy()
                for col in df_show_view.columns:
                    df_show_view[col] = df_show_view[col].astype(str)
                st.dataframe(df_show_view, width="stretch")

                resumen_tipo = (
                    df_errors.groupby("tipo_error", dropna=False)
                    .size()
                    .reset_index(name="total")
                    .sort_values("total", ascending=False)
                )
                st.subheader("Resumen por tipo de error")

                resumen_tipo_view = resumen_tipo.copy()
                for col in resumen_tipo_view.columns:
                    resumen_tipo_view[col] = resumen_tipo_view[col].astype(str)
                st.dataframe(resumen_tipo_view, width="stretch")

            st.download_button(
                label="Descargar reporte Excel",
                data=workbook_bytes,
                file_name=f"resultado_validacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            csv_errors = df_errors.to_csv(index=False).encode("utf-8-sig") if not df_errors.empty else b"fila_excel,columna,tipo_error,mensaje,valor\n"
            st.download_button(
                label="Descargar errores CSV",
                data=csv_errors,
                file_name=f"errores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

            with st.expander("Vista previa de datos validados", expanded=False):
                df_validated_view = df_validated.head(20).copy()
                for col in df_validated_view.columns:
                    df_validated_view[col] = df_validated_view[col].astype(str)
                st.dataframe(df_validated_view, width="stretch")

    except Exception as exc:
        st.exception(exc)
else:
    st.info("Sube un archivo para iniciar la validación.")
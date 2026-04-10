from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import unicodedata

# ============================================================
# ESTRUCTURA DE CAMPOS
# ============================================================
FIXED_COLUMNS = [
    "codigo_ies",
    "nombre_ies",
    "id_registro",
    "cedula",
    "nombres",
    "apellidos",
    "fecha_nacimiento",
    "genero",
    "autoidentificacion_etnica",
    "provincia_sede_estudia",
    "provincia_residencia",
    "canton_residencia",
    "parroquia_residencia",
    "codigo_carrera_sniese",
    "carrera",
    "nivel_formacion",
    "modalidad",
    "fecha_inicio_carrera",
    "duracion_carrera_periodos",
    "culmino_estudios",
    "observaciones",
]

P1_COLUMNS = [
    "tipo_beca_p1",
    "periodo_academico_p1",
    "nivel_cursa_p1",
    "costo_matricula_p1",
    "costo_arancel_p1",
    "motivo_beca_p1",
    "estado_beca_p1",
    "fecha_entrega_beca_p1",
    "monto_financiado_estado_matricula_p1",
    "monto_financiado_estado_arancel_p1",
    "monto_financiado_ies_matricula_p1",
    "monto_financiado_ies_arancel_p1",
]

P2_COLUMNS = [
    "tipo_beca_p2",
    "periodo_academico_p2",
    "nivel_cursa_p2",
    "costo_matricula_p2",
    "costo_arancel_p2",
    "motivo_beca_p2",
    "estado_beca_p2",
    "fecha_entrega_beca_p2",
    "monto_financiado_estado_matricula_p2",
    "monto_financiado_estado_arancel_p2",
    "monto_financiado_ies_matricula_p2",
    "monto_financiado_ies_arancel_p2",
]

EXPECTED_COLUMNS = FIXED_COLUMNS + P1_COLUMNS + P2_COLUMNS

REQUIRED_COLUMNS = [
    "codigo_ies",
    "nombre_ies",
    "id_registro",
    "cedula",
    "nombres",
    "apellidos",
    "fecha_nacimiento",
    "genero",
    "provincia_sede_estudia",
    "codigo_carrera_sniese",
    "carrera",
    "nivel_formacion",
    "modalidad",
    "fecha_inicio_carrera",
    "duracion_carrera_periodos",
    "tipo_beca_p1",
    "periodo_academico_p1",
    "nivel_cursa_p1",
    "costo_matricula_p1",
    "costo_arancel_p1",
    "estado_beca_p1",
    "tipo_beca_p2",
    "periodo_academico_p2",
    "nivel_cursa_p2",
    "costo_matricula_p2",
    "costo_arancel_p2",
    "estado_beca_p2",
    "culmino_estudios",
]

VALID_GENERO = {"HOMBRE", "MUJER", "OTRO", "SIN RESPUESTA"}
VALID_AUTOIDENTIFICACION_ETNICA = {
    "INDIGENA",
    "AFROECUATORIANO/A",
    "MONTUBIO/A",
    "MESTIZO/A",
    "BLANCO/A",
    "OTRO/A",
    "SIN INFORMACION",
}
VALID_NIVEL_FORMACION = {
    "TECNICO SUPERIOR",
    "TECNOLOGICO SUPERIOR",
    "TERCER NIVEL",
    "CUARTO NIVEL",
}
VALID_MODALIDAD = {"PRESENCIAL", "SEMIPRESENCIAL", "EN LINEA", "HIBRIDA", "DUAL"}
VALID_TIPO_BECA = {"TOTAL", "PARCIAL"}
VALID_ESTADO_BECA = {"NUEVA BECA", "MANTIENE LA BECA", "SIN BECA"}
VALID_CULMINO = {"SI", "NO"}
VALID_MOTIVO_BECA = {
    "MERITO ACADEMICO",
    "SOCIOECONOMICA",
    "PARA PERSONAS CON DISCAPACIDAD",
    "DEPORTIVA",
    "CULTURAL",
    "OTRO CONFORME NORMATIVA",
}


def normalize_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().upper()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = " ".join(text.split())
    return text


def safe_float(value: Any) -> Optional[float]:
    if pd.isna(value) or str(value).strip() == "":
        return None
    try:
        return float(str(value).replace(",", ""))
    except Exception:
        return None


def safe_int(value: Any) -> Optional[int]:
    f = safe_float(value)
    if f is None:
        return None
    if float(f).is_integer():
        return int(f)
    return None


def parse_date_ddmmyyyy(value: Any) -> Optional[datetime]:
    if pd.isna(value) or str(value).strip() == "":
        return None

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if isinstance(value, datetime):
        return value

    text = str(value).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    try:
        parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.to_pydatetime()
    except Exception:
        return None


def calculate_rango_from_percentage(pct: Optional[float]) -> Optional[str]:
    if pct is None:
        return None
    if pct == 0:
        return "SIN COBERTURA"
    if 0 < pct <= 25:
        return "1%-25%"
    if 25 < pct <= 50:
        return "25%-50%"
    if 50 < pct <= 75:
        return "50%-75%"
    if 75 < pct <= 100:
        return "75%-100%"
    return None


@dataclass
class ValidationError:
    fila_excel: int
    columna: str
    tipo_error: str
    mensaje: str
    valor: Any


class BecaValidator:
    def __init__(self) -> None:
        self.errors: List[ValidationError] = []

    def reset(self) -> None:
        self.errors = []

    def add_error(self, row_idx: int, column: str, error_type: str, message: str, value: Any) -> None:
        self.errors.append(
            ValidationError(
                fila_excel=row_idx + 2,
                columna=column,
                tipo_error=error_type,
                mensaje=message,
                valor=value,
            )
        )

    def normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df

    def validate_structure(self, df: pd.DataFrame) -> None:
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Faltan columnas obligatorias en la plantilla: {missing}")

    def validate_required_fields(self, df: pd.DataFrame) -> None:
        for col in REQUIRED_COLUMNS:
            if col not in df.columns:
                continue
            for idx, value in df[col].items():
                if pd.isna(value) or str(value).strip() == "":
                    self.add_error(idx, col, "obligatorio", "Campo obligatorio vacío.", value)

    def validate_catalogs(self, df: pd.DataFrame) -> None:
        catalog_rules = {
            "genero": VALID_GENERO,
            "autoidentificacion_etnica": VALID_AUTOIDENTIFICACION_ETNICA,
            "nivel_formacion": VALID_NIVEL_FORMACION,
            "modalidad": VALID_MODALIDAD,
            "culmino_estudios": VALID_CULMINO,
            "tipo_beca_p1": VALID_TIPO_BECA,
            "tipo_beca_p2": VALID_TIPO_BECA,
            "estado_beca_p1": VALID_ESTADO_BECA,
            "estado_beca_p2": VALID_ESTADO_BECA,
            "motivo_beca_p1": VALID_MOTIVO_BECA,
            "motivo_beca_p2": VALID_MOTIVO_BECA,
        }
        for col, valid_set in catalog_rules.items():
            if col not in df.columns:
                continue
            for idx, value in df[col].items():
                v = normalize_text(value)
                if v and v not in valid_set:
                    self.add_error(idx, col, "catalogo", f"Valor no permitido en catálogo de {col}.", value)

    def validate_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        date_cols = [
            "fecha_nacimiento",
            "fecha_inicio_carrera",
            "fecha_entrega_beca_p1",
            "fecha_entrega_beca_p2",
        ]
        for col in date_cols:
            if col not in df.columns:
                continue
            vals = []
            for idx, value in df[col].items():
                parsed = parse_date_ddmmyyyy(value)
                vals.append(parsed)
                if (not pd.isna(value)) and str(value).strip() != "" and parsed is None:
                    self.add_error(idx, col, "formato_fecha", "Formato de fecha inválido. Use DD/MM/AAAA.", value)
            df[col] = vals
        return df

    def validate_numeric_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        int_cols = ["duracion_carrera_periodos", "nivel_cursa_p1", "nivel_cursa_p2"]
        float_cols = [
            "costo_matricula_p1",
            "costo_arancel_p1",
            "monto_financiado_estado_matricula_p1",
            "monto_financiado_estado_arancel_p1",
            "monto_financiado_ies_matricula_p1",
            "monto_financiado_ies_arancel_p1",
            "costo_matricula_p2",
            "costo_arancel_p2",
            "monto_financiado_estado_matricula_p2",
            "monto_financiado_estado_arancel_p2",
            "monto_financiado_ies_matricula_p2",
            "monto_financiado_ies_arancel_p2",
        ]
        for col in int_cols:
            if col not in df.columns:
                continue
            vals = []
            for idx, value in df[col].items():
                parsed = safe_int(value)
                vals.append(parsed)
                if (not pd.isna(value)) and str(value).strip() != "" and parsed is None:
                    self.add_error(idx, col, "tipo_dato", "Debe ser un número entero.", value)
            df[col] = vals
        for col in float_cols:
            if col not in df.columns:
                continue
            vals = []
            for idx, value in df[col].items():
                parsed = safe_float(value)
                vals.append(parsed)
                if (not pd.isna(value)) and str(value).strip() != "" and parsed is None:
                    self.add_error(idx, col, "tipo_dato", "Debe ser numérico.", value)
            df[col] = vals
        return df

    def validate_numeric_ranges(self, df: pd.DataFrame) -> None:
        non_negative_cols = [
            "duracion_carrera_periodos",
            "nivel_cursa_p1",
            "costo_matricula_p1",
            "costo_arancel_p1",
            "monto_financiado_estado_matricula_p1",
            "monto_financiado_estado_arancel_p1",
            "monto_financiado_ies_matricula_p1",
            "monto_financiado_ies_arancel_p1",
            "nivel_cursa_p2",
            "costo_matricula_p2",
            "costo_arancel_p2",
            "monto_financiado_estado_matricula_p2",
            "monto_financiado_estado_arancel_p2",
            "monto_financiado_ies_matricula_p2",
            "monto_financiado_ies_arancel_p2",
        ]
        for col in non_negative_cols:
            if col not in df.columns:
                continue
            for idx, value in df[col].items():
                if value is not None and value < 0:
                    self.add_error(idx, col, "rango", "El valor no puede ser negativo.", value)
        for nivel_col in ["nivel_cursa_p1", "nivel_cursa_p2"]:
            if nivel_col not in df.columns:
                continue
            for idx, value in df[nivel_col].items():
                dur = df.loc[idx, "duracion_carrera_periodos"] if "duracion_carrera_periodos" in df.columns else None
                if value is not None and value < 1:
                    self.add_error(idx, nivel_col, "rango", "El nivel cursado debe ser mayor o igual a 1.", value)
                if value is not None and dur is not None and value > dur:
                    self.add_error(idx, nivel_col, "rango", "El nivel cursado no puede superar la duración de la carrera.", value)

    def validate_logic(self, df: pd.DataFrame) -> None:
        for idx, row in df.iterrows():
            fecha_nacimiento = row.get("fecha_nacimiento")
            fecha_inicio = row.get("fecha_inicio_carrera")
            if fecha_nacimiento and fecha_inicio and fecha_nacimiento > fecha_inicio:
                self.add_error(idx, "fecha_nacimiento", "consistencia", "La fecha de nacimiento no puede ser posterior al inicio de carrera.", fecha_nacimiento)

            for suffix in ["p1", "p2"]:
                estado = normalize_text(row.get(f"estado_beca_{suffix}"))
                tipo_beca = normalize_text(row.get(f"tipo_beca_{suffix}"))
                motivo = row.get(f"motivo_beca_{suffix}")
                fecha = row.get(f"fecha_entrega_beca_{suffix}")
                costo_matricula = row.get(f"costo_matricula_{suffix}") or 0
                costo_arancel = row.get(f"costo_arancel_{suffix}") or 0
                me_m = row.get(f"monto_financiado_estado_matricula_{suffix}") or 0
                me_a = row.get(f"monto_financiado_estado_arancel_{suffix}") or 0
                mi_m = row.get(f"monto_financiado_ies_matricula_{suffix}") or 0
                mi_a = row.get(f"monto_financiado_ies_arancel_{suffix}") or 0

                total_matricula_financiado = me_m + mi_m
                total_arancel_financiado = me_a + mi_a
                costo_total = costo_matricula + costo_arancel
                monto_estado_total = me_m + me_a
                monto_total = me_m + me_a + mi_m + mi_a

                if fecha_nacimiento and fecha and fecha_nacimiento > fecha:
                    self.add_error(idx, f"fecha_entrega_beca_{suffix}", "consistencia", "La fecha de nacimiento no puede ser posterior a la fecha de entrega de la beca.", fecha)

                if estado == "SIN BECA":
                    if pd.notna(fecha) and fecha is not None:
                        self.add_error(idx, f"fecha_entrega_beca_{suffix}", "consistencia", "Si el estado es SIN BECA, la fecha de entrega debe estar vacía.", fecha)
                    if monto_total != 0:
                        self.add_error(idx, f"estado_beca_{suffix}", "consistencia", "Si el estado es SIN BECA, todos los montos deben ser 0 o las celdas no deberían contener un valor.", monto_total)

                if estado in {"NUEVA BECA", "MANTIENE LA BECA"}:
                    if pd.isna(motivo) or str(motivo).strip() == "":
                        self.add_error(idx, f"motivo_beca_{suffix}", "consistencia", "Si existe beca, el motivo es obligatorio.", motivo)
                    if pd.isna(fecha) or fecha is None:
                        self.add_error(idx, f"fecha_entrega_beca_{suffix}", "consistencia", "Si existe beca, la fecha de entrega es obligatoria.", fecha)
                    if monto_total <= 0:
                        self.add_error(idx, f"estado_beca_{suffix}", "consistencia", "Si existe beca, al menos un monto financiado debe ser mayor a 0.", monto_total)
                    if tipo_beca == "TOTAL" and (costo_matricula > 0 or costo_arancel > 0):
                        if total_matricula_financiado < costo_matricula or total_arancel_financiado < costo_arancel:
                            self.add_error(idx, f"tipo_beca_{suffix}", "consistencia", "Si la beca es TOTAL, la cobertura de matrícula y arancel debe ser completa.", tipo_beca)

                if total_matricula_financiado > costo_matricula:
                    self.add_error(idx, f"monto_financiado_estado_matricula_{suffix}", "consistencia", "La suma financiada para matrícula no puede superar el costo de matrícula.", total_matricula_financiado)
                if total_arancel_financiado > costo_arancel:
                    self.add_error(idx, f"monto_financiado_estado_arancel_{suffix}", "consistencia", "La suma financiada para arancel no puede superar el costo de arancel.", total_arancel_financiado)
                if monto_total > costo_total:
                    self.add_error(idx, f"estado_beca_{suffix}", "consistencia", "La suma total financiada no puede superar el costo total del período.", monto_total)
                if monto_estado_total > costo_total:
                    self.add_error(idx, f"estado_beca_{suffix}", "consistencia", "El financiamiento estatal no puede superar el costo total del período.", monto_estado_total)

    def validate_duplicates(self, df: pd.DataFrame) -> None:
        key_cols = ["codigo_ies", "cedula", "codigo_carrera_sniese"]
        if not all(c in df.columns for c in key_cols):
            return
        dup_mask = df.duplicated(subset=key_cols, keep=False)
        dup_df = df.loc[dup_mask, key_cols]
        for idx in dup_df.index:
            self.add_error(
                idx,
                "codigo_ies|cedula|codigo_carrera_sniese",
                "duplicado",
                "Registro duplicado para la combinación universidad-estudiante-carrera.",
                tuple(df.loc[idx, key_cols].tolist()),
            )

    def add_derived_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for suffix in ["p1", "p2"]:
            costo_mat = f"costo_matricula_{suffix}"
            costo_ara = f"costo_arancel_{suffix}"
            me_m = f"monto_financiado_estado_matricula_{suffix}"
            me_a = f"monto_financiado_estado_arancel_{suffix}"
            mi_m = f"monto_financiado_ies_matricula_{suffix}"
            mi_a = f"monto_financiado_ies_arancel_{suffix}"

            df[f"costo_total_{suffix}"] = df[[costo_mat, costo_ara]].fillna(0).sum(axis=1)
            df[f"monto_estado_total_{suffix}"] = df[[me_m, me_a]].fillna(0).sum(axis=1)
            df[f"monto_ies_total_{suffix}"] = df[[mi_m, mi_a]].fillna(0).sum(axis=1)
            df[f"monto_total_financiado_{suffix}"] = df[[me_m, me_a, mi_m, mi_a]].fillna(0).sum(axis=1)

            def calc_pct_estado(row: pd.Series, suf: str = suffix) -> Optional[float]:
                costo = row[f"costo_total_{suf}"]
                monto_estado = row[f"monto_estado_total_{suf}"]
                if costo in (None, 0):
                    return None
                return round(100 * monto_estado / costo, 2)

            df[f"porcentaje_cobertura_estado_{suffix}"] = df.apply(calc_pct_estado, axis=1)
            df[f"rango_beca_{suffix}"] = df[f"porcentaje_cobertura_estado_{suffix}"].apply(calculate_rango_from_percentage)
        return df

    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        self.reset()
        df = self.normalize_columns(df)
        self.validate_structure(df)
        self.validate_required_fields(df)
        self.validate_catalogs(df)
        df = self.validate_dates(df)
        df = self.validate_numeric_fields(df)
        self.validate_numeric_ranges(df)
        self.validate_logic(df)
        self.validate_duplicates(df)
        df = self.add_derived_columns(df)
        error_df = pd.DataFrame([asdict(e) for e in self.errors])
        return df, error_df


def read_input_file(file_obj: Any, filename: str, sheet_name: str | int = 0) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    if suffix == ".xlsx":
        return pd.read_excel(file_obj, sheet_name=sheet_name)
    if suffix == ".csv":
        return pd.read_csv(file_obj)
    raise ValueError("Formato no soportado. Use .xlsx o .csv")


def build_output_workbook(df_validated: pd.DataFrame, df_errors: pd.DataFrame) -> bytes:
    from io import BytesIO

    output = BytesIO()
    df_out = df_validated.copy()
    df_out["tiene_error"] = "No"
    df_out["detalle_errores"] = ""

    if not df_errors.empty:
        errores_por_fila = (
            df_errors.groupby("fila_excel")[["columna", "mensaje"]]
            .apply(lambda x: " | ".join(f"{row['columna']}: {row['mensaje']}" for _, row in x.iterrows()))
            .to_dict()
        )
        for fila_excel, detalle in errores_por_fila.items():
            idx = fila_excel - 2
            if 0 <= idx < len(df_out):
                df_out.loc[idx, "tiene_error"] = "Sí"
                df_out.loc[idx, "detalle_errores"] = detalle

    resumen = pd.DataFrame(
        {
            "indicador": ["Total registros", "Registros con error", "Total errores detectados"],
            "valor": [len(df_out), (df_out["tiene_error"] == "Sí").sum(), len(df_errors)],
        }
    )

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_out.to_excel(writer, sheet_name="datos_validados", index=False)
        if df_errors.empty:
            pd.DataFrame({"resultado": ["Sin errores"]}).to_excel(writer, sheet_name="errores", index=False)
        else:
            df_errors.to_excel(writer, sheet_name="errores", index=False)
        resumen.to_excel(writer, sheet_name="resumen", index=False)

    output.seek(0)
    return output.getvalue()

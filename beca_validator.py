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
# Se usa "sexo" como nombre actual de la variable.
# Para compatibilidad, si el archivo viene con la columna "genero",
# normalize_columns() la renombra automáticamente a "sexo".
#
# Se incorporan variables por periodo para culminación/término de estudios:
#   - culmino_estudios_p1
#   - culmino_estudios_p2
# También se aceptan alias: termino_estudios_p1 / termino_estudios_p2.
# ============================================================
FIXED_COLUMNS = [
    "codigo_ies",
    "nombre_ies",
    "id_registro",
    "cedula",
    "nombres",
    "apellidos",
    "fecha_nacimiento",
    "sexo",
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
    "culmino_estudios_p1",
    "culmino_estudios_p2",
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
    "sexo",
    "provincia_sede_estudia",
    "codigo_carrera_sniese",
    "carrera",
    "nivel_formacion",
    "modalidad",
    "fecha_inicio_carrera",
    "duracion_carrera_periodos",
    "culmino_estudios_p1",
    "culmino_estudios_p2",
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
]

# ============================================================
# CATÁLOGOS
# ============================================================
VALID_SEXO = {"HOMBRE", "MUJER", "OTRO", "SIN RESPUESTA"}
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
VALID_TIPO_BECA = {"TOTAL", "PARCIAL", "SIN BECA"}

# Catálogo ajustado al documento de aclaración Estado Beca.
# Se aceptan variantes con y sin artículo "LA" para evitar errores por redacción.
VALID_ESTADO_BECA = {
    "NUEVA BECA",
    "MANTIENE BECA",
    "MANTIENE LA BECA",
    "PIERDE BECA",
    "PIERDE LA BECA",
    "NO APLICA",
    "SIN BECA",
}
VALID_CULMINO = {"SI", "NO"}
VALID_MOTIVO_BECA = {
    "MERITO ACADEMICO",
    "SOCIOECONOMICA",
    "PARA PERSONAS CON DISCAPACIDAD",
    "DEPORTIVA",
    "CULTURAL",
    "OTRO CONFORME NORMATIVA",
}

PROVINCIA_CANTONES = {
    "AZUAY": {
        "CUENCA", "GIRON", "GUALACEO", "NABON", "PAUTE", "PUCARA",
        "SAN FERNANDO", "SANTA ISABEL", "SIGSIG", "ONA", "CHORDELEG",
        "EL PAN", "SEVILLA DE ORO", "GUACHAPALA", "CAMILO PONCE ENRIQUEZ"
    },
    "BOLIVAR": {
        "GUARANDA", "CHILLANES", "CHIMBO", "ECHEANDIA",
        "SAN MIGUEL", "CALUMA", "LAS NAVES"
    },
    "CANAR": {
        "AZOGUES", "BIBLIAN", "CANAR", "LA TRONCAL", "EL TAMBO", "DELEG", "SUSCAL"
    },
    "CARCHI": {
        "TULCAN", "BOLIVAR", "ESPEJO", "MIRA", "MONTUFAR", "SAN PEDRO DE HUACA"
    },
    "COTOPAXI": {
        "LATACUNGA", "LA MANA", "PANGUA", "PUJILI", "SALCEDO", "SAQUISILI", "SIGCHOS"
    },
    "CHIMBORAZO": {
        "RIOBAMBA", "ALAUSI", "COLTA", "CHAMBO", "CHUNCHI", "GUAMOTE",
        "GUANO", "PALLATANGA", "PENIPE", "CUMANDA"
    },
    "EL ORO": {
        "MACHALA", "ARENILLAS", "ATAHUALPA", "BALSAS", "CHILLA", "EL GUABO",
        "HUAQUILLAS", "MARCABELI", "PASAJE", "PINAS", "PORTOVELO",
        "SANTA ROSA", "ZARUMA", "LAS LAJAS"
    },
    "ESMERALDAS": {
        "ESMERALDAS", "ELOY ALFARO", "MUISNE", "QUININDE",
        "SAN LORENZO", "ATACAMES", "RIOVERDE"
    },
    "GUAYAS": {
        "GUAYAQUIL", "ALFREDO BAQUERIZO MORENO (JUJAN)", "BALAO", "BALZAR",
        "COLIMES", "DAULE", "DURAN", "EL EMPALME", "EL TRIUNFO", "MILAGRO",
        "NARANJAL", "NARANJITO", "PALESTINA", "PEDRO CARBO", "SAMBORONDON",
        "SANTA LUCIA", "SALITRE (URBINA JADO)", "SAN JACINTO DE YAGUACHI",
        "PLAYAS", "SIMON BOLIVAR", "CORONEL MARCELINO MARIDUENA",
        "LOMAS DE SARGENTILLO", "NOBOL", "GENERAL ANTONIO ELIZALDE",
        "ISIDRO AYORA"
    },
    "IMBABURA": {
        "IBARRA", "ANTONIO ANTE", "COTACACHI", "OTAVALO", "PIMAMPIRO",
        "SAN MIGUEL DE URCUQUI"
    },
    "LOJA": {
        "LOJA", "CALVAS", "CATAMAYO", "CELICA", "CHAGUARPAMBA", "ESPINDOLA",
        "GONZANAMA", "MACARA", "PALTAS", "PUYANGO", "SARAGURO", "SOZORANGA",
        "ZAPOTILLO", "PINDAL", "QUILANGA", "OLMEDO"
    },
    "LOS RIOS": {
        "BABAHOYO", "BABA", "MONTALVO", "PUEBLOVIEJO", "QUEVEDO", "URDANETA",
        "VENTANAS", "VINCES", "PALENQUE", "BUENA FE", "VALENCIA", "MOCACHE",
        "QUINSALOMA"
    },
    "MANABI": {
        "PORTOVIEJO", "BOLIVAR", "CHONE", "EL CARMEN", "FLAVIO ALFARO",
        "JIPIJAPA", "JUNIN", "MANTA", "MONTECRISTI", "PAJAN", "PICHINCHA",
        "ROCAFUERTE", "SANTA ANA", "SUCRE", "TOSAGUA", "24 DE MAYO",
        "PEDERNALES", "OLMEDO", "PUERTO LOPEZ", "JAMA", "JARAMIJO", "SAN VICENTE"
    },
    "MORONA SANTIAGO": {
        "MORONA", "GUALAQUIZA", "LIMON INDANZA", "PALORA", "SANTIAGO", "SUCUA",
        "HUAMBOYA", "SAN JUAN BOSCO", "TAISHA", "LOGRONO", "PABLO SEXTO", "TIWINTZA"
    },
    "NAPO": {
        "TENA", "ARCHIDONA", "EL CHACO", "QUIJOS", "CARLOS JULIO AROSEMENA TOLA"
    },
    "PASTAZA": {
        "PASTAZA", "MERA", "SANTA CLARA", "ARAJUNO"
    },
    "PICHINCHA": {
        "QUITO", "CAYAMBE", "MEJIA", "PEDRO MONCAYO", "RUMINAHUI",
        "SAN MIGUEL DE LOS BANCOS", "PEDRO VICENTE MALDONADO", "PUERTO QUITO"
    },
    "TUNGURAHUA": {
        "AMBATO", "BANOS DE AGUA SANTA", "CEVALLOS", "MOCHA", "PATATE",
        "QUERO", "SAN PEDRO DE PELILEO", "SANTIAGO DE PILLARO", "TISALEO"
    },
    "ZAMORA CHINCHIPE": {
        "ZAMORA", "CHINCHIPE", "NANGARITZA", "YACUAMBI", "YANTZAZA (YANZATZA)",
        "EL PANGUI", "CENTINELA DEL CONDOR", "PALANDA", "PAQUISHA"
    },
    "GALAPAGOS": {
        "SAN CRISTOBAL", "ISABELA", "SANTA CRUZ"
    },
    "SUCUMBIOS": {
        "LAGO AGRIO", "GONZALO PIZARRO", "PUTUMAYO", "SHUSHUFINDI",
        "SUCUMBIOS", "CASCALES", "CUYABENO"
    },
    "ORELLANA": {
        "ORELLANA", "AGUARICO", "LA JOYA DE LOS SACHAS", "LORETO"
    },
    "SANTO DOMINGO DE LOS TSACHILAS": {
        "LA CONCORDIA", "SANTO DOMINGO"
    },
    "SANTA ELENA": {
        "SANTA ELENA", "LA LIBERTAD", "SALINAS"
    },
}

# Combinaciones válidas según la matriz Estado Beca / Culminó estudios para dos periodos.
# Canonización usada: MANTIENE LA BECA -> MANTIENE BECA; PIERDE LA BECA -> PIERDE BECA.
VALID_COMBINACIONES_ESTADO_CULMINO = {
    ("NUEVA BECA", "NO", "MANTIENE BECA", "NO"),
    ("NUEVA BECA", "NO", "PIERDE BECA", "NO"),
    ("NUEVA BECA", "NO", "NO APLICA", "NO"),
    ("MANTIENE BECA", "NO", "MANTIENE BECA", "NO"),
    ("MANTIENE BECA", "NO", "PIERDE BECA", "NO"),
    ("MANTIENE BECA", "NO", "PIERDE BECA", "SI"),
    ("MANTIENE BECA", "NO", "NO APLICA", "SI"),
    ("MANTIENE BECA", "NO", "NO APLICA", "NO"),
    ("PIERDE BECA", "NO", "NUEVA BECA", "NO"),
}


def normalize_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().upper()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = " ".join(text.split())
    return text


def canonical_estado_beca(value: Any) -> str:
    """Devuelve el estado de beca en forma canónica para validar transiciones."""
    estado = normalize_text(value)
    equivalencias = {
        "MANTIENE LA BECA": "MANTIENE BECA",
        "MANTIENE BECA": "MANTIENE BECA",
        "PIERDE LA BECA": "PIERDE BECA",
        "PIERDE BECA": "PIERDE BECA",
        "NUEVA BECA": "NUEVA BECA",
        "NO APLICA": "SIN BECA",
        "SIN BECA": "SIN BECA",
	"OTRO": "OTRO/A",
    }
    return equivalencias.get(estado, estado)


def canonical_si_no(value: Any) -> str:
    return normalize_text(value)


def is_empty(value: Any) -> bool:
    return pd.isna(value) or str(value).strip() == ""


def periodo_es_sin_beca(row: pd.Series, suffix: str) -> bool:
    """True si en el periodo se declaró SIN BECA en tipo o en estado."""
    tipo = normalize_text(row.get(f"tipo_beca_{suffix}"))
    estado = canonical_estado_beca(row.get(f"estado_beca_{suffix}"))
    return tipo == "SIN BECA" or estado == "SIN BECA"


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

        aliases = {
            "género": "sexo",
            "genero": "sexo",
            "termino_estudios_p1": "culmino_estudios_p1",
            "termino_estudios_p2": "culmino_estudios_p2",
            "terminó_estudios_p1": "culmino_estudios_p1",
            "terminó_estudios_p2": "culmino_estudios_p2",
        }
        df = df.rename(columns={col: aliases.get(col, col) for col in df.columns})

        # Compatibilidad temporal: si aún llega la columna antigua culmino_estudios,
        # se copia a P2 y se exige P1/P2 solo cuando no existan.
        if "culmino_estudios" in df.columns:
            if "culmino_estudios_p2" not in df.columns:
                df["culmino_estudios_p2"] = df["culmino_estudios"]
            if "culmino_estudios_p1" not in df.columns:
                df["culmino_estudios_p1"] = "NO"

        return df

    def validate_structure(self, df: pd.DataFrame) -> None:
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        extra = [c for c in df.columns if c not in EXPECTED_COLUMNS and c != "culmino_estudios"]
        if missing:
            raise ValueError(f"Faltan columnas obligatorias en la plantilla: {missing}")
        if extra:
            # No se detiene el proceso: se conservan columnas adicionales.
            print(f"Advertencia: existen columnas no esperadas que serán conservadas: {extra}")

    def validate_required_fields(self, df: pd.DataFrame) -> None:
        """
        Valida campos obligatorios.

        Regla especial:
        - Si en un periodo se registra SIN BECA en tipo_beca o estado_beca,
          no se exigen los campos asociados a beca de ese periodo.
        """
        campos_periodo = {
            "p1": {
                "tipo_beca_p1",
                "periodo_academico_p1",
                "nivel_cursa_p1",
                "costo_matricula_p1",
                "costo_arancel_p1",
                "estado_beca_p1",
                "motivo_beca_p1",
                "fecha_entrega_beca_p1",
                "monto_financiado_estado_matricula_p1",
                "monto_financiado_estado_arancel_p1",
                "monto_financiado_ies_matricula_p1",
                "monto_financiado_ies_arancel_p1",
            },
            "p2": {
                "tipo_beca_p2",
                "periodo_academico_p2",
                "nivel_cursa_p2",
                "costo_matricula_p2",
                "costo_arancel_p2",
                "estado_beca_p2",
                "motivo_beca_p2",
                "fecha_entrega_beca_p2",
                "monto_financiado_estado_matricula_p2",
                "monto_financiado_estado_arancel_p2",
                "monto_financiado_ies_matricula_p2",
                "monto_financiado_ies_arancel_p2",
            },
        }

        for idx, row in df.iterrows():
            for col in REQUIRED_COLUMNS:
                if col not in df.columns:
                    continue

                # Si el periodo está declarado como SIN BECA, no se exige
                # ningún campo del bloque de beca de ese periodo.
                if col in campos_periodo["p1"] and periodo_es_sin_beca(row, "p1"):
                    continue
                if col in campos_periodo["p2"] and periodo_es_sin_beca(row, "p2"):
                    continue

                value = row.get(col)
                if is_empty(value):
                    self.add_error(idx, col, "obligatorio", "Campo obligatorio vacío.", value)

    def validate_catalogs(self, df: pd.DataFrame) -> None:
        catalog_rules = {
            "sexo": VALID_SEXO,
            "autoidentificacion_etnica": VALID_AUTOIDENTIFICACION_ETNICA,
            "nivel_formacion": VALID_NIVEL_FORMACION,
            "modalidad": VALID_MODALIDAD,
            "culmino_estudios_p1": VALID_CULMINO,
            "culmino_estudios_p2": VALID_CULMINO,
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

    def validate_provincia_canton(self, df: pd.DataFrame) -> None:
        provincia_col = "provincia_residencia"
        canton_col = "canton_residencia"

        if provincia_col not in df.columns or canton_col not in df.columns:
            return

        for idx, row in df.iterrows():
            provincia = normalize_text(row.get(provincia_col))
            canton = normalize_text(row.get(canton_col))

            if not provincia or not canton:
                continue

            if provincia not in PROVINCIA_CANTONES:
                self.add_error(
                    idx,
                    provincia_col,
                    "catalogo",
                    "Provincia no reconocida en el catálogo provincia-cantón.",
                    row.get(provincia_col),
                )
                continue

            if canton not in PROVINCIA_CANTONES[provincia]:
                self.add_error(
                    idx,
                    canton_col,
                    "consistencia",
                    f"El cantón '{row.get(canton_col)}' no corresponde a la provincia '{row.get(provincia_col)}'.",
                    row.get(canton_col),
                )

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
                self.add_error(
                    idx,
                    "fecha_nacimiento",
                    "consistencia",
                    "La fecha de nacimiento no puede ser posterior al inicio de carrera.",
                    fecha_nacimiento,
                )

            for suffix in ["p1", "p2"]:
                estado = canonical_estado_beca(row.get(f"estado_beca_{suffix}"))
                tipo_beca = normalize_text(row.get(f"tipo_beca_{suffix}"))

                # Si el periodo está declarado como SIN BECA, no se aplican
                # reglas financieras ni de obligatoriedad propias de beca.
                if tipo_beca == "SIN BECA" or estado == "SIN BECA":
                    continue

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
                    self.add_error(
                        idx,
                        f"fecha_entrega_beca_{suffix}",
                        "consistencia",
                        "La fecha de nacimiento no puede ser posterior a la fecha de entrega de la beca.",
                        fecha,
                    )

                if estado in {"NUEVA BECA", "MANTIENE BECA"}:
                    if is_empty(motivo):
                        self.add_error(idx, f"motivo_beca_{suffix}", "consistencia", "Si existe beca, el motivo es obligatorio.", motivo)
                    if fecha is None or pd.isna(fecha):
                        self.add_error(idx, f"fecha_entrega_beca_{suffix}", "consistencia", "Si existe beca, la fecha de entrega es obligatoria.", fecha)
                    if monto_total <= 0:
                        self.add_error(idx, f"estado_beca_{suffix}", "consistencia", "Si existe beca, al menos un monto financiado debe ser mayor a 0.", monto_total)
                    if tipo_beca == "TOTAL" and (costo_matricula > 0 or costo_arancel > 0):
                        if total_matricula_financiado < costo_matricula or total_arancel_financiado < costo_arancel:
                            self.add_error(idx, f"tipo_beca_{suffix}", "consistencia", "Si la beca es TOTAL, la cobertura de matrícula y arancel debe ser completa.", tipo_beca)

                if estado == "NO APLICA":
                    if pd.notna(fecha) and fecha is not None:
                        self.add_error(idx, f"fecha_entrega_beca_{suffix}", "consistencia", "Si el estado es NO APLICA, la fecha de entrega debe estar vacía.", fecha)
                    if monto_total != 0:
                        self.add_error(idx, f"estado_beca_{suffix}", "consistencia", "Si el estado es NO APLICA, todos los montos deben ser 0 o estar vacíos.", monto_total)

                if total_matricula_financiado > costo_matricula:
                    self.add_error(idx, f"monto_financiado_estado_matricula_{suffix}", "consistencia", "La suma financiada para matrícula no puede superar el costo de matrícula.", total_matricula_financiado)
                if total_arancel_financiado > costo_arancel:
                    self.add_error(idx, f"monto_financiado_estado_arancel_{suffix}", "consistencia", "La suma financiada para arancel no puede superar el costo de arancel.", total_arancel_financiado)
                if monto_total > costo_total:
                    self.add_error(idx, f"estado_beca_{suffix}", "consistencia", "La suma total financiada no puede superar el costo total del período.", monto_total)
                if monto_estado_total > costo_total:
                    self.add_error(idx, f"estado_beca_{suffix}", "consistencia", "El financiamiento estatal no puede superar el costo total del período.", monto_estado_total)

    def validate_estado_culmino_relations(self, df: pd.DataFrame) -> None:
        """Valida combinaciones Estado Beca P1/P2 y Culminó Estudios P1/P2."""
        needed = ["estado_beca_p1", "culmino_estudios_p1", "estado_beca_p2", "culmino_estudios_p2"]
        if not all(c in df.columns for c in needed):
            return

        for idx, row in df.iterrows():
            e1 = canonical_estado_beca(row.get("estado_beca_p1"))
            c1 = canonical_si_no(row.get("culmino_estudios_p1"))
            e2 = canonical_estado_beca(row.get("estado_beca_p2"))
            c2 = canonical_si_no(row.get("culmino_estudios_p2"))
            t1 = normalize_text(row.get("tipo_beca_p1"))
            t2 = normalize_text(row.get("tipo_beca_p2"))

            # Si alguno de los periodos está declarado como SIN BECA,
            # no se evalúa la matriz de transición de becas.
            if "SIN BECA" in {e1, e2, t1, t2}:
                continue

            if not e1 or not c1 or not e2 or not c2:
                continue

            combo = (e1, c1, e2, c2)
            if combo not in VALID_COMBINACIONES_ESTADO_CULMINO:
                self.add_error(
                    idx,
                    "estado_beca_p1|culmino_estudios_p1|estado_beca_p2|culmino_estudios_p2",
                    "relacion_periodos",
                    "Combinación incorrecta entre estado de beca y culminación de estudios para P1 y P2, según la matriz de aclaración.",
                    combo,
                )

    def get_duplicados_cedula(self, df: pd.DataFrame) -> pd.DataFrame:
        if "cedula" not in df.columns:
            return pd.DataFrame()

        dup_mask = df.duplicated(subset=["cedula"], keep=False)
        duplicados = df.loc[dup_mask].copy()

        if duplicados.empty:
            return pd.DataFrame()

        duplicados["criterio_duplicado"] = "cedula"
        duplicados["veces_repetida_cedula"] = duplicados.groupby("cedula")["cedula"].transform("count")

        return duplicados.sort_values(["cedula"])

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
        self.validate_provincia_canton(df)
        df = self.validate_dates(df)
        df = self.validate_numeric_fields(df)
        self.validate_numeric_ranges(df)
        self.validate_logic(df)
        self.validate_estado_culmino_relations(df)
        df = self.add_derived_columns(df)
        duplicados_df = self.get_duplicados_cedula(df)
        error_df = pd.DataFrame([asdict(e) for e in self.errors])
        return df, error_df, duplicados_df


def read_input_file(file_obj: Any, filename: str, sheet_name: str | int = 0) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    if suffix == ".xlsx":
        return pd.read_excel(file_obj, sheet_name=sheet_name)
    if suffix == ".csv":
        return pd.read_csv(file_obj)
    raise ValueError("Formato no soportado. Use .xlsx o .csv")


def build_output_workbook(
    df_validated: pd.DataFrame,
    df_errors: pd.DataFrame,
    df_duplicados: pd.DataFrame
) -> bytes:
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
        if df_duplicados.empty:
    	    pd.DataFrame({"resultado": ["Sin duplicados por cédula"]}).to_excel(
                writer, sheet_name="duplicados_cedula", index=False
            )
        else:
            df_duplicados.to_excel(writer, sheet_name="duplicados_cedula", index=False)

    output.seek(0)
    return output.getvalue()

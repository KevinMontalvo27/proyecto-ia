from typing import Dict, Any
import re


class PlantMapper:
    """
    Utilidad para mapear etiquetas de HuggingFace a información de plantas.
    """

    # Mapeo de diagnósticos normalizados
    PLANT_MAPPING = {
        # Tomate (id=1)
        "tomato_bacterial_spot": {"plant": "tomate", "plant_id": 1, "diagnostic": "bacterial_spot"},
        "tomato_early_blight": {"plant": "tomate", "plant_id": 1, "diagnostic": "early_blight"},
        "tomato_late_blight": {"plant": "tomate", "plant_id": 1, "diagnostic": "late_blight"},
        "tomato_leaf_mold": {"plant": "tomate", "plant_id": 1, "diagnostic": "leaf_mold"},
        "tomato_septoria_leaf_spot": {"plant": "tomate", "plant_id": 1, "diagnostic": "septoria_leaf_spot"},
        "tomato_spider_mites": {"plant": "tomate", "plant_id": 1, "diagnostic": "spider_mites_two_spotted"},
        "tomato_target_spot": {"plant": "tomate", "plant_id": 1, "diagnostic": "target_spot"},
        "tomato_yellow_leaf_curl_virus": {"plant": "tomate", "plant_id": 1, "diagnostic": "yellow_leaf_curl_virus"},
        "tomato_mosaic_virus": {"plant": "tomate", "plant_id": 1, "diagnostic": "mosaic_virus"},
        "tomato_healthy": {"plant": "tomate", "plant_id": 1, "diagnostic": "healthy"},

        # Maíz (id=2)
        "corn_cercospora_leaf_spot": {"plant": "maiz", "plant_id": 2, "diagnostic": "cercospora_gray_leaf_spot"},
        "corn_gray_leaf_spot": {"plant": "maiz", "plant_id": 2, "diagnostic": "cercospora_gray_leaf_spot"},
        "corn_common_rust": {"plant": "maiz", "plant_id": 2, "diagnostic": "common_rust"},
        "corn_northern_leaf_blight": {"plant": "maiz", "plant_id": 2, "diagnostic": "northern_leaf_blight"},
        "corn_healthy": {"plant": "maiz", "plant_id": 2, "diagnostic": "healthy"},

        # Uva (id=3)
        "grape_black_rot": {"plant": "uva", "plant_id": 3, "diagnostic": "black_rot"},
        "grape_esca": {"plant": "uva", "plant_id": 3, "diagnostic": "esca_black_measles"},
        "grape_black_measles": {"plant": "uva", "plant_id": 3, "diagnostic": "esca_black_measles"},
        "grape_isariopsis_leaf_spot": {"plant": "uva", "plant_id": 3, "diagnostic": "isariopsis_leaf_spot"},
        "grape_leaf_blight": {"plant": "uva", "plant_id": 3, "diagnostic": "isariopsis_leaf_spot"},
        "grape_healthy": {"plant": "uva", "plant_id": 3, "diagnostic": "healthy"},

        # Papa (id=4)
        "potato_early_blight": {"plant": "papa", "plant_id": 4, "diagnostic": "early_blight"},
        "potato_late_blight": {"plant": "papa", "plant_id": 4, "diagnostic": "late_blight"},
        "potato_healthy": {"plant": "papa", "plant_id": 4, "diagnostic": "healthy"},
    }

    @classmethod
    def normalize_label(cls, label: str) -> str:
        """
        Normaliza un label de HuggingFace a formato consistente.

        Ejemplos:
            "Tomato with Septoria Leaf Spot" -> "tomato_septoria_leaf_spot"
            "Tomato___Bacterial_spot" -> "tomato_bacterial_spot"
            "Corn (maize) Common rust" -> "corn_common_rust"
        """
        # Convertir a minúsculas
        normalized = label.lower()

        print(f"  → Paso 1 (lowercase): '{normalized}'")

        # Remover palabras conectoras comunes
        words_to_remove = ['with', 'and', 'or', 'the']
        for word in words_to_remove:
            normalized = normalized.replace(f' {word} ', ' ')

        print(f"  → Paso 2 (sin conectores): '{normalized}'")

        # Remover paréntesis y contenido
        normalized = re.sub(r'\([^)]*\)', '', normalized)

        print(f"  → Paso 3 (sin paréntesis): '{normalized}'")

        # Reemplazar múltiples espacios o guiones por un solo espacio
        normalized = re.sub(r'[\s\-_]+', ' ', normalized)

        print(f"  → Paso 4 (espacios normalizados): '{normalized}'")

        # Limpiar espacios al inicio y final
        normalized = normalized.strip()

        print(f"  → Paso 5 (trim): '{normalized}'")

        # Convertir espacios a guiones bajos
        normalized = normalized.replace(' ', '_')

        print(f"  → Paso 6 (underscores): '{normalized}'")

        return normalized

    @classmethod
    def parse_label(cls, hf_label: str) -> Dict[str, Any]:
        """
        Parsea la etiqueta de HuggingFace y extrae información de planta y diagnóstico.

        Args:
            hf_label: Label del modelo (ej: "Tomato with Septoria Leaf Spot")

        Returns:
            Dict con plant, plant_id y diagnostic
        """
        print(f"\n{'=' * 60}")
        print(f" PARSEANDO LABEL DE HUGGINGFACE")
        print(f"{'=' * 60}")
        print(f"Label original: '{hf_label}'")

        # Normalizar el label
        normalized = cls.normalize_label(hf_label)
        print(f"Label normalizado final: '{normalized}'")

        # Buscar coincidencia exacta en el mapping
        if normalized in cls.PLANT_MAPPING:
            result = cls.PLANT_MAPPING[normalized]
            print(f" MATCH EXACTO encontrado en PLANT_MAPPING")
            print(f"   → plant: {result['plant']}")
            print(f"   → plant_id: {result['plant_id']}")
            print(f"   → diagnostic: {result['diagnostic']}")
            print(f"{'=' * 60}\n")
            return result

        print(f" No se encontró match exacto, intentando parsing manual...")

        # Determinar tipo de planta
        hf_lower = hf_label.lower()

        if 'tomato' in hf_lower:
            plant_id, plant = 1, "tomate"
        elif 'corn' in hf_lower or 'maize' in hf_lower:
            plant_id, plant = 2, "maiz"
        elif 'grape' in hf_lower:
            plant_id, plant = 3, "uva"
        elif 'potato' in hf_lower:
            plant_id, plant = 4, "papa"
        else:
            print(f" ERROR: Tipo de planta no reconocido")
            print(f"{'=' * 60}\n")
            raise ValueError(
                f"Tipo de planta no reconocido en label: '{hf_label}'. "
                f"Labels esperados deben contener: tomato, corn/maize, grape, o potato"
            )

        print(f"   → Planta identificada: {plant} (ID: {plant_id})")

        # Extraer diagnóstico del label normalizado
        # Remover el nombre de la planta del inicio
        diagnostic = normalized
        for plant_name in ['tomato', 'corn', 'grape', 'potato', 'maize']:
            if diagnostic.startswith(plant_name + '_'):
                diagnostic = diagnostic[len(plant_name) + 1:]
                print(f"   → Diagnóstico extraído (con '_'): '{diagnostic}'")
                break
            elif diagnostic.startswith(plant_name):
                diagnostic = diagnostic[len(plant_name):].lstrip('_')
                print(f"   → Diagnóstico extraído (sin '_'): '{diagnostic}'")
                break

        # Si está vacío, marcar como unknown
        if not diagnostic or len(diagnostic) < 2:
            diagnostic = "unknown"
            print(f"   → Diagnóstico muy corto o vacío, marcado como 'unknown'")

        # Verificar si es "healthy"
        if 'healthy' in diagnostic:
            diagnostic = 'healthy'
            print(f"   → Contiene 'healthy', normalizado a 'healthy'")

        print(f"\n RESULTADO FINAL:")
        print(f"   → plant: {plant}")
        print(f"   → plant_id: {plant_id}")
        print(f"   → diagnostic: {diagnostic}")
        print(f"{'=' * 60}\n")

        return {
            "plant": plant,
            "plant_id": plant_id,
            "diagnostic": diagnostic
        }

    @classmethod
    def get_plant_name(cls, plant_id: int) -> str:
        """Obtiene el nombre de la planta dado su ID."""
        plant_names = {
            1: "tomate",
            2: "maiz",
            3: "uva",
            4: "papa"
        }
        return plant_names.get(plant_id, "unknown")

    @classmethod
    def get_plant_id(cls, plant_name: str) -> int:
        """Obtiene el ID de la planta dado su nombre."""
        plant_ids = {
            "tomate": 1,
            "maiz": 2,
            "uva": 3,
            "papa": 4
        }
        return plant_ids.get(plant_name.lower(), 0)



# -*- coding: utf-8 -*-
"""Формирование номенклатурного имени изделия и поиск файла схемы.

Переносит функциональность из src/Model.py (build_scheme_filepath,
parse_scheme_filename, find_scheme_file) в чистое ядро.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from src.core.models import SchemeSearchConfig, SchemeSearchResult


class SchemeFinder:
    """Строит имя схемы по конфигурации оборудования и ищет файл .cdw."""

    def __init__(self, catalog_root: str = "Каталог") -> None:
        self.catalog_root = catalog_root

    # ------------------------------------------------------------------
    def build_scheme_filename(self, config: SchemeSearchConfig) -> str:
        """Формирует номенклатурную строку изделия.

        Например: ГРПШ_РДНК-50-400(1000)_1-1_0_4_0_0_У1_0_1_50-50_Л-П
        """
        # Модель регулятора: убираем разделители, чтобы имя было «чистым».
        regulator_part = str(config.regulator).replace("/", "").replace("\\", "")

        lines_block = (
            f"{config.working_lines}-{config.reserve_lines}_{config.removable_reserve}"
        )
        diameters_block = f"{config.valve_diameter_in}-{config.valve_diameter_out}"

        parts = [
            str(config.product_type or ""),
            regulator_part,
            lines_block,
            str(config.sto_gprg or ""),
            str(config.heating or ""),
            str(config.telemetry or ""),
            str(config.climate or ""),
            str(config.uirg or ""),
            str(config.gas_outputs or ""),
            diameters_block,
            str(config.direction or ""),
        ]
        return "_".join(parts)

    def parse_scheme_filename(self, filename: str) -> Dict[str, str]:
        """Разбирает имя файла схемы на части."""
        parts = filename.split("_")
        if len(parts) < 11:
            raise ValueError("Некорректный формат имени файла")
        return {
            "product_type": parts[0],
            "regulator_model": parts[1],
            "regulator_base": parts[1].split("-")[0],  # например, "РДНК"
            "full_name": filename,
        }

    def find_scheme_file(self, parse_data: Dict[str, str]) -> Optional[str]:
        """Ищет файл .cdw в каталоге по разобранному имени.

        Ожидаемая структура каталога:
            <Каталог>/<product_type>/<regulator_base>/<full_name>.cdw
        """
        product_type = parse_data["product_type"]
        sub_folder = parse_data["regulator_base"]
        file_name = parse_data["full_name"] + ".cdw"

        file_path = (
            Path(self.catalog_root) / product_type / sub_folder / file_name
        )
        full_path = Path.cwd() / file_path
        return str(full_path) if full_path.exists() else None

    # ------------------------------------------------------------------
    def search(
        self,
        regulator_name: str,
        config: SchemeSearchConfig,
    ) -> SchemeSearchResult:
        """Полный поиск схемы по имени регулятора и конфигурации оборудования."""
        filename = self.build_scheme_filename(config)
        parse_data = self.parse_scheme_filename(filename)
        full_path = self.find_scheme_file(parse_data)

        return SchemeSearchResult(
            regulator_name=regulator_name,
            scheme_name=parse_data.get("full_name", "Неизвестно"),
            file_path=full_path,
            found=full_path is not None,
        )
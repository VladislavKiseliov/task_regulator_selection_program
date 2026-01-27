import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


# Ensure project root on sys.path for direct runs
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.Model import Model


class TestModelPaths(unittest.TestCase):
    def setUp(self):
        self.model = Model()

    def test_build_scheme_filepath(self):
        config = {
            "Тип изделия": "ГРПШ",  # ГРПШ
            "Количество рабочих линий": 1,
            "Количество резервных линий": 1,
            "Наличие съемной резервной линии": 0,
            "Исполнение по СТО ГПРГ": 4,
            "Обогрев": "ОЭ",  # ОЭ
            "Телеметрия": 0,
            "Климатическое исполнение": "У1",  # У1
            "Оснащение УИРГ": 0,
            "Количество выходов газопроводов": 1,
            "Диаметр запорной арматуры на входе": 50,
            "Диаметр запорной арматуры на выходе": 50,
            "Направление": "Л-П",  # Л-П
        }
        filename = self.model.build_scheme_filepath(config, "РДНК-50/400(1000)")
        expected = "ГРПШ_РДНК-50400(1000)_1-1_0_4_ОЭ_0_У1_0_1_50-50_Л-П"
        self.assertEqual(filename, expected)

    def test_parse_scheme_filename(self):
        name = "ГРПБ_РДНК-50-400(1000)_1-1_0_4_А_0_У1_0_1_50-50_Л-Л"
        parsed = self.model.parse_scheme_filename(name)
        self.assertEqual(parsed["product_type"], "ГРПБ")  # ГРПБ
        self.assertEqual(parsed["regulator_model"], "РДНК-50-400(1000)")
        self.assertEqual(parsed["regulator_base"], "РДНК")
        self.assertEqual(parsed["full_name"], name)

    def test_find_scheme_file_found_and_missing(self):
        with TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            try:
                os.chdir(tmp)
                folder = Path("Каталог")  # Каталог
                product_type = "ГРПШ"  # ГРПШ
                regulator_base = "РДНК"
                filename = "test_file"
                file_path = folder / product_type / regulator_base / f"{filename}.cdw"
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text("x", encoding="utf-8")

                parse_data = {
                    "product_type": product_type,
                    "regulator_base": regulator_base,
                    "full_name": filename,
                }
                found = self.model.find_scheme_file(parse_data)
                self.assertIsNotNone(found)
                self.assertTrue(Path(found).exists())

                parse_data_missing = {
                    "product_type": product_type,
                    "regulator_base": "RDNK_MISSING",
                    "full_name": filename,
                }
                missing = self.model.find_scheme_file(parse_data_missing)
                self.assertIsNone(missing)
            finally:
                os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()

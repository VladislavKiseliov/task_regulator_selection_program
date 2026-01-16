import os
from typing import List, Dict
import logging
from src.utils import utils


class ExelMethod:
    def __init__(self):
        self.logger = logging.getLogger("App.ExelMethod")
        self.data = {}
        self.logger.info("ExelMethod инициализирован")

    @staticmethod
    def get_excel_column(index: int) -> str:
        """
        Данный код представляет собой метод  get_excel_column ,
        который принимает индекс в виде целого
        числа и возвращает столбец в формате Excel в виде строки.

        Шаги выполнения кода:
        1. Создается пустая строка  column .
        2. Пока значение  index  больше 0, выполняются следующие действия:
            - Уменьшаем значение  index  на 1.
            - Вычисляем остаток от деления  index  на 26 и прибавляем 65, чтобы получить ASCII-код символа.
            Затем преобразуем полученный ASCII-код в символ с помощью функции  chr() .
            - Полученный символ добавляем в начало строки  column .
            - Делим значение  index  на 26 с округлением в меньшую сторону.
        3. Возвращаем полученную строку  column .

        Таким образом, данный код преобразует числовой индекс в формате Excel в соответствующий столбец."""
        column = ""
        while index > 0:
            index -= 1
            column = chr(index % 26 + 65) + column
            index //= 26
        return column


    def filter_excel_file(self,file_paths:List[str]):
        """
        Фильтрует список путей, оставляя только файлы с расширением .xlsx (без учёта регистра).

        Args:
            file_paths: Список путей к файлам (в виде строк).

        Returns:
            Список путей с расширением .xlsx (например, 'report.xlsx', 'DATA.XLSX').
        """
        excel_ext = '.xlsx'
        filtered = []
        for path in file_paths:
            if os.path.splitext(path)[1].lower() == excel_ext:
                filtered.append(path)

        self.logger.debug(f"Из {len(file_paths)} путей отфильтровано {len(filtered)} .xlsx файлов")
        return filtered

    def search_one_controller_table_algorithm(self,
                                              inlet_pressure: float,
                                              output_pressure: float,
                                              traffic_capacity: float,
                                              sheet,
                                              load_range:tuple[float]) -> Dict[str, Dict[str, int]]:
        """Функция search_one_controller_table_algorithm, принимает
        данные поиска и лист с таблицей формата: одно устройство
        на одном листе. И добавляет девайс в найденные если
        его данные таблицы соответствуют найденным, и возвращает
        1 если устройство соответствует"""

        self.logger.info(f"Начало обработки листа '{sheet.title}' (одно устройство)")
        regulators_found = {}
        i_row = 0
        self.logger.info(f"Обрабатываем лист {sheet.title=}")
        for row in sheet.iter_rows(values_only=True):
            if i_row == 0:
                name_device = row[0]

                saddle = row[1]
                self.logger.debug(f"Устройство: {name_device}, седло: {saddle}")

            if i_row == 1:
                unit_Pin = row[0]
                unit_Out = row[1]

                self.logger.debug(f"Единицы измерения: Pin={unit_Pin}, Pout={unit_Out}")

            for i_cell in range(len(row)):
                if i_row == 2 and i_cell != 0:
                    # Ищим подходящие выходные давления, как по диапазону - так и по единичным значениям
                    mb_diap_Paut = str(row[i_cell]).replace("\xa0", '').replace(" ", '').replace(",", '.').split("-")
                    if len(mb_diap_Paut) == 2:
                        # Если ячейка выходного давления является диапазоном
                        if float(mb_diap_Paut[0]) <= float(output_pressure) <= float(mb_diap_Paut[1]):
                            row_scr_i = 0
                            for row_scr in sheet.iter_rows(values_only=True):
                                if row_scr_i > 2:
                                    mb_diap_Pain = str(row_scr[0]).replace("\xa0", '').replace(" ", '').replace(",",'.').split("-")
                                    # Если ячейка входного давления является диапазоном
                                    if len(mb_diap_Pain) == 2:
                                        if float(mb_diap_Pain[0]) <= float(inlet_pressure) <= float(mb_diap_Pain[1]):
                                            bandwidth = int(traffic_capacity)
                                            # Проверяем можем ли мы перевести значение пропускной способности в число
                                            if utils.is_int(row_scr[i_cell]):
                                                # Проверяем, найденная пропускная способность больше ли необходимой, и является ли регулятор для сжиженного газа если необходимо
                                                if (int(row_scr[i_cell])*load_range[0]) <= bandwidth <= (int(row_scr[i_cell])*load_range[1]):
                                                    print(f"Проверка условий на загрузку {(int(row_scr[i_cell])*load_range[0])} <={bandwidth=} <={(int(row_scr[i_cell])*load_range[1])} ")
                                                    regulators_found[name_device] = {"saddle": saddle,"currentBandwidth":row_scr[i_cell],"bandwidth":bandwidth}

                                    # Если ячейка входного давления НЕ является диапазоном
                                    else:
                                        if float(mb_diap_Pain[0]) == float(inlet_pressure):
                                            bandwidth = int(traffic_capacity)
                                            # Проверяем можем ли мы перевести значение пропускной способности в число
                                            if utils.is_int(row_scr[i_cell]):
                                                if (int(row_scr[i_cell])*load_range[0]) <= bandwidth <= (int(row_scr[i_cell])*load_range[1]):
                                                    print(f"Проверка условий на загрузку {(int(row_scr[i_cell]) * load_range[0])} <={bandwidth=} <={(int(row_scr[i_cell]) * load_range[1])} ")
                                                    regulators_found[name_device] = {"saddle": saddle,"currentBandwidth": row_scr[i_cell],"bandwidth":bandwidth}

                                row_scr_i += 1

                    # Если ячейка выходного давления НЕ является диапазоном
                    elif mb_diap_Paut[0] != "None":
                        if float(output_pressure) == float(mb_diap_Paut[0]):
                            row_scr_i = 0
                            for row_scr in sheet.iter_rows(values_only=True):
                                if row_scr_i > 2:
                                    mb_diap_Pain = str(row_scr[0]).replace("\xa0", '').replace(" ", '').replace(",",'.').split("-")

                                    # Если ячейка входного давления является диапазоном
                                    if len(mb_diap_Pain) == 2:
                                        if float(mb_diap_Pain[0]) <= float(inlet_pressure) <= float(mb_diap_Pain[1]):
                                            bandwidth = int(traffic_capacity) + (int(traffic_capacity) / 100)
                                            # Проверяем можем ли мы перевести значение пропускной способности в число
                                            if utils.is_int(row_scr[i_cell]):
                                                if (int(row_scr[i_cell])*load_range[0]) <= bandwidth <= (int(row_scr[i_cell])*load_range[1]):
                                                    print(f"Проверка условий на загрузку {(int(row_scr[i_cell]) * load_range[0])} <={bandwidth=} <={(int(row_scr[i_cell]) * load_range[1])} ")
                                                    regulators_found[name_device] = {"saddle": saddle,"currentBandwidth": row_scr[i_cell],"bandwidth":bandwidth}

                                    # Если ячейка входного давления НЕ является диапазоном
                                    else:
                                        if float(mb_diap_Pain[0]) == float(inlet_pressure):
                                            bandwidth = int(traffic_capacity)
                                            # Проверяем можем ли мы перевести значение пропускной способности в число
                                            if utils.is_int(row_scr[i_cell]):
                                                # Если это значение больше или равно необходимого
                                                if (int(row_scr[i_cell])*load_range[0]) <= bandwidth <= (int(row_scr[i_cell])*load_range[1]):
                                                    print(
                                                        f"Проверка условий на загрузку {(int(row_scr[i_cell]) * load_range[0])} <={bandwidth=} <={(int(row_scr[i_cell]) * load_range[1])} ")
                                                    regulators_found[name_device] = {"saddle": saddle,"currentBandwidth": row_scr[i_cell],"bandwidth":bandwidth}

                                row_scr_i += 1
            i_row += 1
        print(f"search one contoller table algoritm {regulators_found=}")
        return regulators_found

    def search_several_controller_table_algorithm(self,
                                                  inlet_pressure: float,
                                                  output_pressure: float,
                                                  traffic_capacity: float,
                                                  sheet,
                                                  load_range:tuple[float],reporter = None) -> Dict[str, Dict[str, int]]:
        """Функция search_several_controller_table_algorithm, принимает
        данные поиска и лист с таблицей формата: несколько устройств
        на одном листе. И добавляет девайс в найденные если
        его данные таблицы соответствуют найденным, и возвращает
        1 если устройство соответствует"""
        # Put your sheet in the loader
        regulators_found = {}
        i_row = 0
        if reporter:
            reporter.write_log(f"--- Начало анализа листа: {sheet.title} ---")
            reporter.write_log(
                f"Целевые параметры: Pвх={inlet_pressure}, Pвых={output_pressure}, Требуемый Q={traffic_capacity}")
        try:
            for row in sheet.iter_rows(values_only=True):

                if i_row == 0:
                    saddle = row[0]

                for i_cell in range(len(row)):
                    # print(f"{i_cell=}")
                    if i_row == 2 and i_cell != 0:

                        # Ищим подходящие выходные давления, как по диапазону - так и по единичным значениям
                        mb_diap_Paut = str(row[i_cell]).replace("\xa0", '').replace(" ", '').replace(",", '.').split("-")
                        if len(mb_diap_Paut) == 2:
                            # Если ячейка выходного давления является диапазоном
                            name_device = sheet[self.get_excel_column(i_cell + 1) + "1"].value
                            if float(mb_diap_Paut[0]) <= float(output_pressure) <= float(mb_diap_Paut[1]):
                                row_scr_i = 0
                                for row_scr in sheet.iter_rows(values_only=True):
                                    if row_scr_i > 2:
                                        mb_diap_Pain = str(row_scr[0]).replace("\xa0", '').replace(" ", '').replace(",",
                                                                                                                    '.').split("-")

                                        # Если ячейка входного давления является диапазоном
                                        if len(mb_diap_Pain) == 2:
                                            if float(mb_diap_Pain[0]) <= float(inlet_pressure) <= float(mb_diap_Pain[1]):

                                                bandwidth = int(traffic_capacity)
                                                # Проверяем можем ли мы перевести значение пропускной способности в число
                                                print(f"{row_scr[i_cell]}")
                                                if utils.is_int(row_scr[i_cell]):

                                                    # Проверяем, найденная пропускная способность больше ли необходимой, и является ли регулятор для сжиженного газа если необходимо
                                                    if (int(row_scr[i_cell]) * load_range[0]) <= bandwidth <= (
                                                            int(row_scr[i_cell]) * load_range[1]):
                                                        status_str = "ПОДХОДИТ"
                                                        regulators_found[name_device] = {"saddle": saddle,
                                                                                         "currentBandwidth": row_scr[
                                                                                             i_cell],
                                                                                         "bandwidth": bandwidth}
                                                    else:
                                                        status_str = "НЕ ПОДХОДИТ"
                                                    reporter.write_log(
                                                        f"Проверка модели: {name_device} | "
                                                        f"Макс.ПрСп: {row_scr[i_cell]} м3/ч | "
                                                        f"Диапазон [{(load_range[0] * 100)}%-{(load_range[1] * 100)}%]: {(int(row_scr[i_cell]) * load_range[0]):.1f} - {int(row_scr[i_cell]) * load_range[1]:.1f} м3/ч | "
                                                        f"Факт. загрузка: {load_percent:.1f}% | "
                                                        f"ИТОГ: {status_str}"
                                                    )



                                        # Если ячейка входного давления НЕ является диапазоном
                                        else:
                                            if float(mb_diap_Pain[0]) == float(inlet_pressure):
                                                bandwidth = int(traffic_capacity)
                                                print(f"{row_scr[i_cell]}, {bandwidth}")
                                                # Проверяем можем ли мы перевести значение пропускной способности в
                                                test = row_scr[i_cell]
                                                print(f"{test=},{utils.is_int(row_scr[i_cell])=}")
                                                if utils.is_int(row_scr[i_cell]):
                                                    print(
                                                        f"Проверка условий на загрузку {(int(row_scr[i_cell]) * load_range[0])} <={bandwidth=} <={(int(row_scr[i_cell]) * load_range[1])} ")
                                                    if (int(row_scr[i_cell]) * load_range[0]) <= bandwidth <= (
                                                            int(row_scr[i_cell]) * load_range[1]):
                                                        status_str = "ПОДХОДИТ"
                                                        regulators_found[name_device] = {"saddle": saddle,
                                                                                         "currentBandwidth": row_scr[
                                                                                             i_cell],
                                                                                         "bandwidth": bandwidth}
                                                    else:
                                                        status_str = "НЕ ПОДХОДИТ"

                                                    reporter.write_log(
                                                        f"Проверка модели: {name_device} | "
                                                        f"Макс.ПрСп: {row_scr[i_cell]} м3/ч | "
                                                        f"Диапазон [{(load_range[0] * 100)}%-{(load_range[1] * 100)}%]: {(int(row_scr[i_cell]) * load_range[0]):.1f} - {int(row_scr[i_cell]) * load_range[1]:.1f} м3/ч | "
                                                        f"Факт. загрузка: {((bandwidth*100)/row_scr[i_cell]):.1f}% | "
                                                        f"ИТОГ: {status_str}"
                                                    )

                                    row_scr_i += 1

                        # Если ячейка выходного давления НЕ является диапазоном и существует

                        elif mb_diap_Paut[0] != "None":
                            if float(output_pressure) == float(mb_diap_Paut[0]):
                                name_device = sheet[self.get_excel_column(i_cell + 1) + "1"].value
                                row_scr_i = 0
                                for row_scr in sheet.iter_rows(values_only=True):
                                    if row_scr_i > 2:
                                        mb_diap_Pain = str(row_scr[0]).replace("\xa0", '').replace(" ", '').replace(",",
                                                                                                                    '.').split("-")
                                        # Если ячейка входного давления является диапазоном
                                        if len(mb_diap_Pain) == 2:
                                            if float(mb_diap_Pain[0]) <= float(inlet_pressure) <= float(mb_diap_Pain[1]):
                                                bandwidth = int(traffic_capacity) + (int(traffic_capacity) / 100)
                                                # Проверяем можем ли мы перевести значение пропускной способности в число
                                                if utils.is_int(row_scr[i_cell]):
                                                    if (int(row_scr[i_cell]) * load_range[0]) <= bandwidth <= (
                                                            int(row_scr[i_cell]) * load_range[1]):
                                                        status_str = "ПОДХОДИТ"
                                                        regulators_found[name_device] = {"saddle": saddle,
                                                                                         "currentBandwidth": row_scr[
                                                                                             i_cell],
                                                                                         "bandwidth": bandwidth}
                                                    else:
                                                        status_str = "НЕ ПОДХОДИТ"
                                                    reporter.write_log(
                                                        f"Проверка модели: {name_device} | "
                                                        f"Макс.ПрСп: {row_scr[i_cell]} м3/ч | "
                                                        f"Диапазон [{(load_range[0] * 100)}%-{(load_range[1] * 100)}%]: {(int(row_scr[i_cell]) * load_range[0]):.1f} - {int(row_scr[i_cell]) * load_range[1]:.1f} м3/ч | "
                                                        f"Факт. загрузка: {load_percent:.1f}% | "
                                                        f"ИТОГ: {status_str}"
                                                    )

                                        # Если ячейка входного давления НЕ является диапазоном
                                        else:
                                            if float(mb_diap_Pain[0]) == float(inlet_pressure):
                                                bandwidth = int(traffic_capacity)
                                                # Проверяем можем ли мы перевести значение пропускной способности в число
                                                if utils.is_int(row_scr[i_cell]):
                                                    # Если это значение больше или равно необходимого
                                                    if (int(row_scr[i_cell]) * load_range[0]) <= bandwidth <= (
                                                            int(row_scr[i_cell]) * load_range[1]):
                                                        status_str = "ПОДХОДИТ"
                                                        regulators_found[name_device] = {"saddle": saddle,
                                                                                         "currentBandwidth": row_scr[
                                                                                             i_cell],
                                                                                         "bandwidth": bandwidth}
                                                    else:
                                                        status_str = "НЕ ПОДХОДИТ"
                                                    reporter.write_log(
                                                        f"Проверка модели: {name_device} | "
                                                        f"Макс.ПрСп: {row_scr[i_cell]} м3/ч | "
                                                        f"Диапазон [{(load_range[0] * 100)}%-{(load_range[1] * 100)}%]: {(int(row_scr[i_cell]) * load_range[0]):.1f} - {int(row_scr[i_cell]) * load_range[1]:.1f} м3/ч | "
                                                        f"Факт. загрузка: {load_percent:.1f}% | "
                                                        f"ИТОГ: {status_str}"
                                                    )

                                    row_scr_i += 1
                i_row += 1
        except ValueError as e:
            print(e)
        print(f"{regulators_found=}")
        return regulators_found

    def conduct_analysis(self, workbook, inlet_pressure, output_pressure, traffic_capacity, load_range,reporter=None) -> Dict[
        str, Dict[str, any]]:
        """
        Метод координирует анализ книги Excel по всем листам.
        """
        regulators_found = {}

        # Проверяем входные данные перед запуском циклов
        try:
            float(inlet_pressure)
            float(output_pressure)
            float(traffic_capacity)
        except (ValueError, TypeError):
            self.logger.error("Некорректные типы входных данных для анализа: %s, %s, %s",
                              inlet_pressure, output_pressure, traffic_capacity)
            raise ValueError("Параметры давления и расхода должны быть числами.")
        if reporter:
            reporter.write_log(f"СТАРТ АНАЛИЗА ФАЙЛА. Параметры: Pвх={inlet_pressure}, Pвых={output_pressure}, Q={traffic_capacity}")
        for sheet_name in workbook.sheetnames:
            try:
                sheet = workbook[sheet_name]
                c1_value = sheet["C1"].value

                # Логика выбора алгоритма в зависимости от формата листа
                if c1_value is None or c1_value == "":
                    self.logger.debug("Лист '%s': формат 'один регулятор на лист'", sheet_name)
                    found = self.search_one_controller_table_algorithm(
                        inlet_pressure, output_pressure, traffic_capacity, sheet, load_range,reporter)
                else:
                    self.logger.debug("Лист '%s': формат 'несколько регуляторов на лист'", sheet_name)
                    found = self.search_several_controller_table_algorithm(
                        inlet_pressure, output_pressure, traffic_capacity, sheet, load_range,reporter)

                regulators_found.update(found)

            except Exception as e:
                self.logger.error("Ошибка при обработке листа %s: %s", sheet_name, str(e), exc_info=True)
                # Мы не прерываем весь процесс, если один лист сломан, но фиксируем это в логе
                continue

        self.logger.info("Анализ завершен. Всего найдено моделей: %d", len(regulators_found))
        if reporter:
            self._write_final_summary(reporter, regulators_found, inlet_pressure, output_pressure, traffic_capacity)
        return regulators_found

    def _write_final_summary(self, reporter, found, p_in, p_out, q):
        """Внутренний метод для красивой таблицы в конце лога."""
        reporter.write_log("=" * 60)
        reporter.write_log("ИТОГОВАЯ СВОДКА ПОДОБРАННЫХ РЕГУЛЯТОРОВ")
        reporter.write_log(f"Запрос: Pвх={p_in} МПа, Pвых={p_out} МПа, Расход={q} м3/ч")
        reporter.write_log("-" * 60)

        if not found:
            reporter.write_log("РЕЗУЛЬТАТ: Подходящих моделей не обнаружено.")
        else:
            for name, data in found.items():
                max_bw = data['currentBandwidth']
                load = (q / max_bw) * 100
                line = f"Модель: {name:<20} | Седло: {data.get('saddle', '-'):<5} | Загрузка: {load:>5.1f}%"
                reporter.write_log(line)

        reporter.write_log("=" * 60)


import os
from typing import List
import logging
import src.utils.utils as utils

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
                                              sheet) -> int:
        """Функция search_one_controller_table_algorithm, принимает
        данные поиска и лист с таблицей формата: одно устройство
        на одном листе. И добавляет девайс в найденные если
        его данные таблицы соответствуют найденным, и возвращает
        1 если устройство соответствует"""

        self.logger.info(f"Начало обработки листа '{sheet.title}' (одно устройство)")
        regulators_found = 0
        i_row = 0
        self.logger.info(f"Обрабатываем лист {sheet.title=}")
        for row in sheet.iter_rows(values_only=True):
            if i_row == 0:
                name_device = row[0]
                if name_device not in self.data:
                    self.data[name_device] = {}

                saddle = row[1]
                self.data[name_device][saddle] = {}
                self.logger.debug(f"Устройство: {name_device}, седло: {saddle}")

            if i_row == 1:
                unit_Pin = row[0]
                unit_Out = row[1]

                self.data[name_device][saddle]['unit_Pin'] = unit_Pin
                self.data[name_device][saddle]['unit_Out'] = unit_Out
                self.data[name_device][saddle]['data_P'] = {}
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
                                    mb_diap_Pain = str(row_scr[0]).replace("\xa0", '').replace(" ", '').replace(",",
                                                                                                                '.').split(
                                        "-")

                                    # Если ячейка входного давления является диапазоном
                                    if len(mb_diap_Pain) == 2:
                                        if float(mb_diap_Pain[0]) <= float(inlet_pressure) <= float(mb_diap_Pain[1]):

                                            bandwidth = int(traffic_capacity)
                                            # Проверяем можем ли мы перевести значение пропускной способности в число
                                            if utils.is_int(row_scr[i_cell]):
                                                # Проверяем, найденная пропускная способность больше ли необходимой, и является ли регулятор для сжиженного газа если необходимо
                                                if int(row_scr[i_cell]) >= bandwidth:
                                                    regulators_found += 1

                                                    # self.__logging_found_device(name_device, saddle, row_scr[i_cell],
                                                    #                             bandwidth, traffic_capacity)


                                    # Если ячейка входного давления НЕ является диапазоном
                                    else:
                                        if float(mb_diap_Pain[0]) == float(inlet_pressure):
                                            bandwidth = int(traffic_capacity)
                                            # Проверяем можем ли мы перевести значение пропускной способности в число
                                            if utils.is_int(row_scr[i_cell]):
                                                if int(row_scr[i_cell]) >= bandwidth:
                                                    regulators_found += 1
                                                    # self.__logging_found_device(name_device, saddle, row_scr[i_cell],
                                                    #                             bandwidth, traffic_capacity)

                                row_scr_i += 1

                    # Если ячейка выходного давления НЕ является диапазоном
                    elif mb_diap_Paut[0] != "None":
                        if float(output_pressure) == float(mb_diap_Paut[0]):
                            row_scr_i = 0
                            for row_scr in sheet.iter_rows(values_only=True):
                                if row_scr_i > 2:
                                    mb_diap_Pain = str(row_scr[0]).replace("\xa0", '').replace(" ", '').replace(",",
                                                                                                                '.').split(
                                        "-")

                                    # Если ячейка входного давления является диапазоном
                                    if len(mb_diap_Pain) == 2:
                                        if float(mb_diap_Pain[0]) <= float(inlet_pressure) <= float(mb_diap_Pain[1]):
                                            bandwidth = int(self.traffic_capacity) + (int(self.traffic_capacity) / 100)
                                            # Проверяем можем ли мы перевести значение пропускной способности в число
                                            if utils.is_int(row_scr[i_cell]):
                                                if int(row_scr[i_cell]) >= bandwidth:
                                                    regulators_found += 1
                                                    # self.__logging_found_device(name_device, saddle, row_scr[i_cell],
                                                    #                             bandwidth, traffic_capacity)

                                    # Если ячейка входного давления НЕ является диапазоном
                                    else:
                                        if float(mb_diap_Pain[0]) == float(inlet_pressure):
                                            bandwidth = int(traffic_capacity)
                                            # Проверяем можем ли мы перевести значение пропускной способности в число
                                            if utils.is_int(row_scr[i_cell]):
                                                # Если это значение больше или равно необходимого
                                                if int(row_scr[i_cell]) >= bandwidth :
                                                    regulators_found += 1
                                                    # self.__logging_found_device(name_device, saddle, row_scr[i_cell],
                                                    #                             bandwidth, traffic_capacity)

                                row_scr_i += 1
            i_row += 1
        print(f"search one contoller table algoritm {regulators_found=}")
        return regulators_found


    def search_several_controller_table_algorithm(self,
                                                  inlet_pressure: float,
                                                  output_pressure: float,
                                                  traffic_capacity: float,
                                                  sheet) -> int:
        """Функция search_several_controller_table_algorithm, принимает
        данные поиска и лист с таблицей формата: несколько устройств
        на одном листе. И добавляет девайс в найденные если
        его данные таблицы соответствуют найденным, и возвращает
        1 если устройство соответствует"""
        # Put your sheet in the loader
        regulators_found = 0
        i_row = 0
        self.logger.info(f"Обрабатываем лист {sheet.title=}")
        for row in sheet.iter_rows(values_only=True):
            if i_row == 0:
                saddle = row[0]
                self.logger.debug(f"Седло: {saddle=}")

            for i_cell in range(len(row)):
                if i_row == 2 and i_cell != 0:

                    # Ищим подходящие выходные давления, как по диапазону - так и по единичным значениям
                    mb_diap_Paut = str(row[i_cell]).replace("\xa0", '').replace(" ", '').replace(",", '.').split("-")
                    self.logger.debug(f"Выходное давление (неск. устр.): {mb_diap_Paut}")

                    if len(mb_diap_Paut) == 2:
                        # Если ячейка выходного давления является диапазоном
                        name_device = sheet[self.get_excel_column(i_cell + 1) + "1"].value
                        self.logger.debug(f"Устройство: {name_device}")

                        if float(mb_diap_Paut[0]) <= float(output_pressure) <= float(mb_diap_Paut[1]):
                            print(mb_diap_Paut[0],output_pressure,mb_diap_Paut[1])
                            row_scr_i = 0
                            for row_scr in sheet.iter_rows(values_only=True):
                                if row_scr_i > 2:
                                    mb_diap_Pain = str(row_scr[0]).replace("\xa0", '').replace(" ", '').replace(",",'.').split("-")
                                    print(mb_diap_Pain)
                                    # Если ячейка входного давления является диапазоном
                                    if len(mb_diap_Pain) == 2:
                                        if float(mb_diap_Pain[0]) <= float(inlet_pressure) <= float(mb_diap_Pain[1]):

                                            bandwidth = int(traffic_capacity)
                                            # Проверяем можем ли мы перевести значение пропускной способности в число
                                            if utils.is_int(row_scr[i_cell]):

                                                # Проверяем, найденная пропускная способность больше ли необходимой, и является ли регулятор для сжиженного газа если необходимо
                                                if int(row_scr[i_cell]) >= bandwidth:
                                                    regulators_found += 1
                                                    self.logger.info(f"Найден регулятор (неск. устр.): {name_device}, седло {saddle}")
                                                    # self.__logging_found_device(name_device, saddle, row_scr[i_cell],
                                                    #                             bandwidth, traffic_capacity)

                                    # Если ячейка входного давления НЕ является диапазоном
                                    else:
                                        if float(mb_diap_Pain[0]) == float(inlet_pressure):
                                            bandwidth = int(traffic_capacity)
                                            # Проверяем можем ли мы перевести значение пропускной способности в число
                                            if utils.is_int(row_scr[i_cell]):
                                                if int(row_scr[i_cell]) >= bandwidth:
                                                    regulators_found += 1
                                                    self.logger.info(f"Найден регулятор (неск. устр.): {name_device}, седло {saddle}")
                                                    # self.__logging_found_device(name_device, saddle, row_scr[i_cell],
                                                    #                             bandwidth, traffic_capacity)

                                row_scr_i += 1

                    # Если ячейка выходного давления НЕ является диапазоном и существует

                    elif mb_diap_Paut[0] != "None":
                        if float(output_pressure) == float(mb_diap_Paut[0]):
                            name_device = sheet[self.get_excel_column(i_cell + 1) + "1"].valu
                            row_scr_i = 0
                            for row_scr in sheet.iter_rows(values_only=True):
                                if row_scr_i > 2:
                                    mb_diap_Pain = str(row_scr[0]).replace("\xa0", '').replace(" ", '').replace(",",
                                                                                                                '.').split(
                                        "-")
                                    # Если ячейка входного давления является диапазоном
                                    if len(mb_diap_Pain) == 2:
                                        if float(mb_diap_Pain[0]) <= float(inlet_pressure) <= float(mb_diap_Pain[1]):
                                            bandwidth = int(self.traffic_capacity) + (int(self.traffic_capacity) / 100)
                                            # Проверяем можем ли мы перевести значение пропускной способности в число
                                            if utils.is_int(row_scr[i_cell]):
                                                if int(row_scr[i_cell]) >= bandwidth:
                                                    regulators_found += 1
                                                    self.logger.info(f"Найден регулятор (точное совпадение, неск. устр.): {name_device}, седло {saddle}")
                                                    # self.__logging_found_device(name_device, saddle, row_scr[i_cell],
                                                    #                             bandwidth, traffic_capacity)

                                    # Если ячейка входного давления НЕ является диапазоном
                                    else:
                                        if float(mb_diap_Pain[0]) == float(inlet_pressure):
                                            bandwidth = int(traffic_capacity)
                                            # Проверяем можем ли мы перевести значение пропускной способности в число
                                            if utils.is_int(row_scr[i_cell]):
                                                # Если это значение больше или равно необходимого
                                                if int(row_scr[i_cell]) >= bandwidth:
                                                    regulators_found += 1
                                                    self.logger.info(f"Найден регулятор (точное совпадение, неск. устр.): {name_device}, седло {saddle}")
                                                    # self.__logging_found_device(name_device, saddle, row_scr[i_cell],
                                                    #                             bandwidth, traffic_capacity)

                                row_scr_i += 1
            i_row += 1

        self.logger.info(f"search several controller table algorithm: найдено {regulators_found} регуляторов")
        return regulators_found
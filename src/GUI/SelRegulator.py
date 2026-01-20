from typing import Callable, Union, Dict, Any, List

from PyQt5.QtWidgets import QFrame
from pyexpat.errors import messages

import src.utils.MathMethod as MathMethod
from imports import *
from pathlib import Path
import logging
import src.utils.utils as utils

from src.utils.CallbackRegister import CallbackRegistry

class SelRegulator:
    def __init__(self,callback_registry: CallbackRegistry):
        """
        Конструктор класса SelRegulator.

        Инициализирует объект класса SelRegulator. Загружает конфигурационный файл,
        создает папку для сохранения файлов и инициализирует пользовательский интерфейс.

        Атрибуты:
        - list_in_range_value: список значений в пределах диапазона
        - file_path_list: список путей к файлам
        - data: словарь для хранения данных
        - data_found: словарь для хранения найденных данных
        - data_found_id: идентификатор найденных данных
        - data_conf: конфигурационный словарь с путями
        - status_animation: итератор для анимации статуса
        """
        self.log = logging.getLogger("App.SelRegulator")
        self.log.info("Главное окно запущенно")
        self.list_in_range_value = []
        self.file_path_list = []
        self.data = {}
        self.data_found = {}
        self.data_found_id = 0
        self.selected_product_type = None  # Для хранения выбранного типа изделия
        self.gas_equipment_config = None  # Для хранения конфигурации газового оборудования

        self.data_conf = {"Path":{}}
        self.status_animation = itertools.cycle(["В работе.", "В работе..", "В работе..."])

        self.__conf_file_loader()
        utils.create_path_folder_for_save()

        # self.app = QtWidgets.QApplication(sys.argv)
        
        self.MainWindow = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.MainWindow)

        self.speed_or_diametr = "diametr"
        self.ui.pushButton_flag_diametr.setCheckable(True)
        self.ui.pushButton_flag_speed.setCheckable(True)
        self.ui.pushButton_flag_diametr.setChecked(True)
        self.ui.pushButton_flag_speed.setChecked(False)

        self.change_speed = False

        try:
            # Удаляем строку с self.app!
            self.MainWindow.setWindowIcon(QIcon('icon.ico'))  # Только для окна
        except Exception as e:
            # Логируем ошибку установки иконки
            self.log.warning(f"Не удалось установить иконку: {e}")

        self.action_menu_2 = QAction("Помощь", self.MainWindow)
        # Добавляем этот QAction на QMenuBar
        self.ui.menubar.addAction(self.action_menu_2)

        self.__drop_area_create();
        self.__connect_config();
        self.callback = callback_registry
    
    def show_error(self,error:str):
        self.ui.statusbar.showMessage(error)

    def __connect_config(self) -> None:
        """
        Приватный метод подключения сигналов и слотов для элементов GUI.

        Устанавливает соответствия между событиями пользовательского интерфейса
        и методами класса SelRegulator.
        """
        # Кнопка "Подобрать регулятор" - вызывает метод replacement_button_pressed
        self.ui.pushButton_selected_regulator.clicked.connect(lambda: self.callback.trigger("replacement_button_pressed"))

        # Кнопка "Открыть файл" - вызывает метод __open_file_dialog
        self.ui.pushButton_load_file.clicked.connect(self.__open_file_dialog)

        # Кнопка "Удалить" - вызывает метод remove_selected_file у drop_area
        self.ui.pushButton_delete_file.clicked.connect(self.drop_area.remove_selected_file)

        # Кнопка "Открыть папку сохранения логов" - вызывает метод folder_save_open
        # self.ui.open_folder_button.clicked.connect(self.folder_save_open) # Коннект на нажатие кнопки открытия папки сохранения логов

        # Кнопка переключения режима "Скорость" - вызывает метод switch_speed
        self.ui.pushButton_flag_speed.clicked.connect(self.switch_speed)

        # Кнопка переключения режима "Диаметр" - вызывает метод switch_diametr
        self.ui.pushButton_flag_diametr.clicked.connect(self.switch_diametr)

        # Пункт меню "Открыть" - вызывает метод __open_file_dialog
        self.ui.buttom_menu_bar_open.triggered.connect(self.__open_file_dialog)

        # Пункт меню "Выход" - закрывает главное окно
        self.ui.buttom_menu_bar_exit.triggered.connect(self.MainWindow.close)

        # Пункт меню "Помощь" - вызывает метод show_about
        self.action_menu_2.triggered.connect(self.show_about)

        # Кнопка "Выполнить расчет" - вызывает метод make_calculation
        self.ui.pushButton_make_calculation.clicked.connect(lambda: self.callback.trigger("make_calculation"))

        # # Кнопка "Подобрать изделие" - вызывает метод select_product_type
        # self.ui.pushButton_selected_scheme.clicked.connect(self.select_product_type)
        # self.ui.pushButton_selected_scheme.clicked.connect(lambda : self.show_error_message("Error"))
        self.ui.pushButton_selected_scheme.clicked.connect(lambda: self.callback.trigger("search_sheme"))

        #Подключение событий изменения текста в полях калькулятора

        # При завершении редактирования поля ввода входного давления вызывается make_calculation
        self.ui.input_Pressure_Input.editingFinished.connect(lambda: self.callback.trigger("auto_calculate_trigger"))

        # При завершении редактирования поля ввода скорости газа вызывается make_calculation
        self.ui.lineEdit_gas_speed_Input.editingFinished.connect(lambda: self.callback.trigger("auto_calculate_trigger"))

        # При завершении редактирования поля ввода диаметра газопровода вызывается make_calculatio
        self.ui.lineEdit_diameter_of_gas_pipeline_Input.editingFinished.connect(lambda: self.callback.trigger("auto_calculate_trigger"))

        #Подключение событий изменения текста в полях калькулятора выходного газопровода

        # При завершении редактирования поля ввода выходного давления вызывается make_calculation
        self.ui.input_Pressure_Output.editingFinished.connect(lambda: self.callback.trigger("auto_calculate_trigger"))

        # При завершении редактирования поля ввода скорости газа на выходе вызывается make_calculation
        self.ui.lineEdit_gas_speed_Output.editingFinished.connect(lambda: self.callback.trigger("auto_calculate_trigger"))

        # При завершении редактирования поля ввода диаметра газопровода на выходе вызывается make_calculation
        self.ui.lineEdit_diameter_of_gas_pipeline_Output.editingFinished.connect(lambda: self.callback.trigger("auto_calculate_trigger"))

        # При завершении редактирования поля ввода пропускной способности вызывается make_calculation
        self.ui.input_bandwidth.editingFinished.connect(lambda: self.callback.trigger("auto_calculate_trigger"))

    def get_count_work_line(self):
        """
            Получить количество рабочих линий
        """
        try:
            return int(self.ui.spinBox_working_lines.value())
        except Exception as e:
            self.ui.statusbar.showMessage(f"Ошибка: {str(e)}")

    def get_backup_lines(self):
        """
            Получить количество резервных линий
        """
        try:
            return int(self.ui.spinBox_reserve_lines.value())
        except Exception as e:
            self.ui.statusbar.showMessage(f"Ошибка: {str(e)}")

    def get_removable_backup_line(self):
        """
            Получить наличие съемной резервной линии
        """
        return self.ui.spinBox_removable_reserve.value()

    def get_sto_gprg_execution(self):
        """
            Получить исполнение по СТО ГПРГ
        """
        return self.ui.comboBox_sto_gprg.currentText()

    def get_heating_type(self) -> str:
        """
            Получить тип обогрева
        """
        try:
            if self.ui.radioButton_heating_og.isChecked():
                return "ОГ"
            elif self.ui.radioButton_heating_oe.isChecked():
                return "ОЭ"
            else:
                return "0"

        except Exception as e:
            self.ui.statusbar.showMessage(f"Ошибка: {str(e)}")

    def get_telemetry_type(self) -> str:
        """
            Получить тип телеметрии
        """
        try:
            if self.ui.radioButton_telemetry_t.isChecked():
                return "Т"
            elif self.ui.radioButton_telemetry_tm.isChecked():
                return "ТМ"
            else:
                return "0"

        except Exception as e:
            self.ui.statusbar.showMessage(f"Ошибка: {str(e)}")

    def get_climate_execution(self):
        """
            Получить климатическое исполнение
        """
        return self.ui.comboBox_climate.currentText()

    def get_uirg_equipment_type(self) -> str:
        """
            Получить тип оснащения УИРГ
        """
        try:
            if self.ui.radioButton_uirg_sg.isChecked():
                return "СГ"
            else:
                return "0"

        except Exception as e:
            self.ui.statusbar.showMessage(f"Ошибка: {str(e)}")

    def get_number_of_gas_pipeline_outlets(self):
        """
            Получить количество выходов газопроводов
        """
        try:
            return int(self.ui.spinBox_gas_outputs.value())
        except Exception as e:
            self.ui.statusbar.showMessage(f"Ошибка: {str(e)}")

    def get_valve_diameter_calc(self,ioType:str)->int:
        """
                Для получение диаметра которые мы получаем расчетным путем

                Поддерживаемые имена полей: input_Pressure_In, input_Pressure_Out.

                Параметры:
                    ioType (str): "Input" — вход, "Output" — выход.

                Возвращает:
                    float: Значение давления. При ошибке возвращается 0 и отображается сообщение.

                Пример:
                    pressure_in = self.get_pressure("Input")
                """
        if ioType not in ("Input", "Output"):
            self.show_error("Ошибка: ioType должен быть 'Input' или 'Output'")
            return 0

        widget_name = f"lineEdit_diameter_of_gas_pipeline_{ioType}"
        try:
            widget = getattr(self.ui, widget_name)
            text = widget.text().replace(",", ".").replace(" ", "")
            return int(text)
        except Exception as e:
            self.show_error(f"Ошибка при чтении диаметра ({ioType}): {e}")
            return 0

    def set_valve_diameter_calc(self,ioType:str,diametr:int)->None:
        """
            Устанавливаем значение диаметра в ячейку
        """
        widget_name = f"lineEdit_diameter_of_gas_pipeline_{ioType}"
        try:
            widget = getattr(self.ui, widget_name)
            with utils.block_signals(widget):
                widget.setText(str(diametr))

        except Exception as e:
            self.show_error(f"Ошибка при вставке диаметра ({ioType}): {e}")

    def get_valve_diameter_manual(self,ioType:str)->int:
        """
            Для получения диаметра, который вводится вручную.

            Поддерживаемые имена полей в UI:
            label_valve_diameter_Input  , label_valve_diameter_Output.

            Параметры:
                ioType (str): "Input" — вход, "Output" — выход.

            Возвращает:
                float: Значение диаметра. При ошибке возвращается 0.0.
            """
        if ioType not in ("Input", "Output"):
            self.show_error("Ошибка программирования: ioType должен быть 'Input' или 'Output'")
            return 0

        # Формируем имя виджета для ручного ввода
        widget_name = f"label_valve_diameter_{ioType}"

        try:
            widget = getattr(self.ui, widget_name)
            # Очищаем строку от пробелов и заменяем запятую на точку для float
            text = widget.text().replace(",", ".").strip()

            if not text:
                # Если поле пустое, можно либо вернуть 0, либо выдать предупреждение
                return 0

            return int(text)

        except AttributeError:
            self.show_error(f"Ошибка: Виджет {widget_name} не найден в UI")
            return 0
        except ValueError:
            self.show_error(f"Ошибка: В поле '{ioType}' введено не число")
            return 0
        except Exception as e:
            self.show_error(f"Непредвиденная ошибка ({ioType}): {e}")
            return 0

    def set_valve_diameter_manual(self,diametr:int)->None:
        pass

    def get_direction_type(self) -> str:
        """
            Получить тип направления
        """
        try:
            return self.ui.comboBox_direction.currentText()
        except Exception as e:
            self.ui.statusbar.showMessage(f"Ошибка: {str(e)}")

    def get_bandwidth(self) -> float:
        """
            Получить пропускную способность
        """
        try:
            return float(self.ui.input_bandwidth.text().replace(",", '.'.replace(" ", '')))
        except Exception as e:
            self.ui.statusbar.showMessage(f"Ошибка: {str(e)}")

    def get_pressure(self,ioType:str)->float:
        """
        Получает значение давления из текстового поля для указанного конца трубопровода.

        Поддерживаемые имена полей: input_Pressure_In, input_Pressure_Out.

        Параметры:
            ioType (str): "Input" — вход, "Output" — выход.

        Возвращает:
            float: Значение давления. При ошибке возвращается 0.0 и отображается сообщение.

        Пример:
            pressure_in = self.get_pressure("Input")
        """
        if ioType not in ("Input", "Output"):
            self.ui.statusbar.showMessage("Ошибка: suffix должен быть 'Input' или 'Output'")
            return 0.0

        widget_name = f"input_Pressure_{ioType}"
        try:
            widget = getattr(self.ui, widget_name)
            text = widget.text().replace(",", ".").replace(" ", "")
            return float(text)
        except Exception as e:
            self.ui.statusbar.showMessage(f"Ошибка при чтении давления ({ioType}): {e}")
            return 0.0

    def set_speed(self,ioType:str,gas_speed:float)->None:
        """
            Устанавливаем значение скорости в ячейку

        """
        widget_name = f"lineEdit_gas_speed_{ioType}"
        try:
            widget = getattr(self.ui, widget_name)
            with utils.block_signals(widget):
                widget.setText(f"{gas_speed:.1f}")

        except Exception as e:
            self.show_error(f"Ошибка при вставке скорости ({ioType}): {e}")

    def get_speed(self, ioType: str) -> float:  # Изменил возвращаемый тип на float
        if ioType not in ("Input", "Output"):
            self.show_error(f"Ошибка: ioType должен быть 'Input' или 'Output', получено '{ioType}'")
            return 0.0

        widget_name = f"lineEdit_gas_speed_{ioType}"
        try:
            widget = getattr(self.ui, widget_name)
            text = widget.text().replace(",", ".").strip()

            if not text:
                return 0.0

            # Сначала переводим во float, так как в строке может быть точка
            return float(text)
        except Exception as e:
            # Логируем ошибку чтения виджета
            self.log.debug(f"DEBUG: Error reading {widget_name}: {e}")
            return 0.0

    def switch_diametr(self) -> None:
        self.speed_or_diametr = "diametr"
        self.ui.pushButton_flag_speed.setChecked(False)

    def get_auto_speed_checked(self,ioType: str) -> bool:
        """
        Возвращает состояние флажка автоматической установки скорости
        для указанного конца трубопровода (вход или выход).

        Параметры:
            ioType (str): Указывает, о каком конце трубопровода идет речь.
                          Допустимые значения: 'In' (вход) или 'Out' (выход).

        Возвращает:
            bool: True, если соответствующий флажок в интерфейсе отмечен,
                  иначе False.

        Исключения:
            AttributeError: Если в объекте self.ui отсутствует виджет
                            с именем QCB_Auto_Speed_{ioType}.
            ValueError: Если передано недопустимое значение ioType.

        Пример:
            >>> self.get_auto_speed_checked('In')
            True
            >>> self.get_auto_speed_checked('Out')
            False
        """
        if ioType not in ('In', 'Out'):
            raise ValueError("Параметр 'suffix' должен быть 'In' или 'Out'")

        widget_name = f"QCB_Auto_Speed_{ioType}"
        widget = getattr(self.ui, widget_name)
        return widget.isChecked()

    def switch_speed(self) -> None:
        self.speed_or_diametr = "speed"
        self.ui.pushButton_flag_diametr.setChecked(False)

    def get_loading_range(self) -> tuple[int, int]:
        """
        Получает и валидирует диапазон процента загрузки из UI.

        Returns:
            Кортеж (min_load, max_load) — целые числа в диапазоне [0, 100],
            причём min_load <= max_load.

        Raises:
            ValueError: если значения отсутствуют, не являются целыми числами
                        или выходят за допустимые пределы.
        """
        min_text = self.ui.min_lebel_loading_range.text().strip()
        max_text = self.ui.max_lebel_loading_range.text().strip()

        if not min_text or not max_text:
            raise ValueError("Диапазон загрузки: оба поля должны быть заполнены.")

        try:
            min_val = int(min_text)
            max_val = int(max_text)
        except ValueError:
            raise ValueError("Диапазон загрузки: значения должны быть целыми числами.")

        if not (0 <= min_val <= 100):
            raise ValueError("Минимальный процент загрузки должен быть от 0 до 100.")
        if not (0 <= max_val <= 100):
            raise ValueError("Максимальный процент загрузки должен быть от 0 до 100.")
        if min_val > max_val:
            raise ValueError("Минимальное значение не может быть больше максимального.")

        return min_val, max_val

    def __drop_area_create(self) -> None:
        # Создаем виджет DropArea и добавляем его в scrollArea_2
        self.drop_area = DropArea();
        self.ui.scrollArea_2.setWidget(self.drop_area)

    def  __conf_file_loader(self) -> None:
        """Загружаем json с конфигом, в котором находятся пути сохраённных xmlx файлов"""
        try:
            # Получение текущей директории
            self.current_dir = os.getcwd()

            # Сборка пути к папке
            self.conf_file_name = "selRegulConf.json"
            self.conf_file_path = os.path.join(self.current_dir, self.conf_file_name)

            # Проверка существования папки и создание, если не существует
            if not os.path.exists(self.conf_file_path):
                with open(self.conf_file_path, 'w') as file:
                    json.dump(self.data_conf, file)
                    file.close()
                return 0
            else:
                with open(self.conf_file_path, 'r') as file:
                    self.data_conf = json.load(file)
                    file.close()

                for key,value in self.data_conf["Path"].items():
                    self.file_path_list.append(value)
        except:
            pass

    def show_error_message(self, text_err:str) -> None:
        """Функция show_error_message выводит сообщение об ошибке с заданным текстом
        в виде диалогового окна."""

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Внимание")
        msg.setText(text_err)
        #msg.setInformativeText("Дополнительная информация о предупреждении.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def show_warning_message(self, text_war:str) -> None:
        """Функция show_warning_message выводит сообщение (Внимание!) с заданным текстом
        в виде диалогового окна."""

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Внимание")
        msg.setText(text_war)
        #msg.setInformativeText("Дополнительная информация о предупреждении.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def show_info_message(self, text_war:str) -> None:
        """Функция show_info_message выводит дочернее окно (Внимание!) с заданным текстом
        в виде диалогового окна."""

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Внимание")
        msg.setText(text_war)
        #msg.setInformativeText("Дополнительная информация о предупреждении.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def status_work_cycle(self) -> None:
        """Функция status_work_cycle обновляет статус работы в статус-баре.
        Если статус содержит текст 'В работе', функция обновляет статус-бар и
        получает следующий элемент анимации статуса. Затем функция вызывает
        саму себя через 500 миллисекунд для продолжения цикла работы.
        Если статус не содержит текст 'В работе', функция просто обновляет статус-бар."""

        if "В работе" in self.status_text:
            self.ui.statusbar.showMessage(self.status_text)
            self.status_text = next(self.status_animation)
            QTimer.singleShot(500, self.status_work_cycle)  # Вызываем себя через 500 мс
        else:
            pass
            # self.ui.statusbar.showMessage(self.status_text)

    def update_status_worck(self, status_text) -> None:
        """Функция update_status_worck, является обёрткой
        над функцией status_worck_cycle. Позволяя корректно 
        останавливать самовызов этой функции"""
        self.status_text = status_text
        self.status_work_cycle()

    def __open_file_dialog(self):
        """Функция __open_file_dialog, отвечает
        за загрузку файла через контекстный
        диалог через проводник"""

        options = QFileDialog.Options()
        file_filter = "All Files (*);;Excel Files (*.xlsx);;Doc Files (*.doc);;Docx Files (*.docx)"
        file_path, _ = QFileDialog.getOpenFileName(self.ui.centralwidget, "Выберите файл", "", file_filter, options=options)
        if file_path:
            self.drop_area.add_file(file_path)


    def __saved_conf_search(self) -> None:
        """Функция __saved_conf_search, сохраняет конфигурацию
        поиска устройства для отдельного запуска"""
        
        # self.saved_conf_self_file_name_var = self.ui.self_file_name_var.isChecked()
        # self.saved_conf_input_name_file = self.ui.input_name_file.text()
        # self.saved_conf_left_to_right = self.ui.left_to_right.isChecked()
        # self.saved_conf_PZK_position_sensor = self.ui.PZK_position_sensor.isChecked()
        self.saved_conf_Regulator_for_liquefied_gas = False

        self.saved_conf_minimum_load = int(self.ui.min_lebel_loading_range.text())
        self.saved_conf_maximum_load =  int(self.ui.max_lebel_loading_range.text())

    def open_file(self):
        """Функция open_file, привязана
        к кнопке верхнего меню (окрыть)"""
        self.__open_file_dialog()
        # Логика открытия файла

    def show_about(self):
        """Функция show_about, привязана
        к кнопке верхнего меню (о программе)"""
        # Создаем диалоговое окно "О программе"
        about_window = QDialog(self.MainWindow)
        about_window.setWindowTitle("О программе")
        about_window.setGeometry(100, 100, 800, 600)
        try:
            about_window.setWindowIcon(QIcon('icon.ico'))
        except:
            pass
        
        layout = QVBoxLayout()
        
        text_widget = QTextEdit()
        text_widget.setReadOnly(True)
        
        # Увеличиваем размер шрифта для лучшей читаемости
        font = text_widget.font()
        font.setPointSize(12)  # Увеличиваем размер шрифта с обычного до 12
        text_widget.setFont(font)
        
        text = ("Программа подбора регулятора принимает 3 входных параметра: входное давление,\n"
                "выходное давление в МПа и пропускную способность. Для поиска регулятора\n"
                "необходимо добавить файл в формате xlsx содержащий следующую структуру и данные:\n"
                "Каждая новая таблица на отдельном листе. \n"
                "Ячейка A1-название регулятора.\n"
                "Ячейка В1 седло регулятора. \n"
                "А2 размерность выходного давление.\n"
                "В2 размерность выходного давления.\n"
                "А4-Аn единицы выходного давления.\n"
                "В3-(N)3 единицы выходного давления.\n"
                "Этапы работы с программой:\n"
                "1)Ввести параметры необходимого регулятора.\n"
                "Если нужно своё название файла результата анализа, \n"
                "поставить флажок 'Своё название результирующего файла' и ввести необходимое название. \n"
                "2)Перетащить таблицу формата xlsx с данными о регуляторах в дроп-зону. \n"
                "Либо используя кнопку 'Открыть файл'.\n"
                "3)Нажать кнопку 'Подобрать регулятор'.\n"
                "4)После того как программа завершить работу, откроется файл с проведённым анализом.")
        text_widget.setText(text)
        
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(about_window.close)
        
        layout.addWidget(text_widget)
        layout.addWidget(close_button)
        about_window.setLayout(layout)
        
        about_window.exec_()

    def draw_window(self) -> None:
        """
        Функция для отображения графического пользовательского интерфейса (GUI). 
        Она создает окно с помощью библиотеки TkinterDnD, в котором пользователь 
        может перетаскивать и откладывать файлы формата docx, которые отображаются 
        в списке. Пользователь может ввести цифровой маркер тега и нажать кнопку 
        "Заменить", чтобы заменить кириллические символы в тегах. Также есть 
        кнопка "Удалить" для удаления выбранных файлов из списка. Статус операции 
        отображается в метке, а анимация показывает, что операция выполняется.
        """

        self.MainWindow.show()

    def create_regulator_block(self, name, saddle, current_bw, required_bw) -> QtWidgets.QFrame:
        """
            Создает графический блок (карточку) с информацией о найденном регуляторе.

            Метод формирует сложный виджет на базе QFrame, включающий в себя:
            - Чекбокс для выбора регулятора пользователем.
            - Информационные метки (название, диаметр седла, макс. пропускная способность).
            - Визуальный индикатор процента загрузки (цветовая схема: зеленый/оранжевый/красный).

            Args:
                name (str): Модель/Наименование регулятора.
                saddle (str): Диаметр седла регулятора (мм).
                current_bw (float): Максимальная пропускная способность выбранной модели (м³/ч).
                required_bw (float): Требуемая пропускная способность по расчету пользователя (м³/ч).

            Returns:
                QtWidgets.QFrame: Готовый объект фрейма с настроенной версткой и стилями (QSS).
                Объект содержит динамические свойства .checkbox и .regulator_name для доступа извне.
            """

        frame = QtWidgets.QFrame()
        frame.setObjectName("regulatorCard")

        # Расчет процента загрузки (как было)
        try:
            load_percent = (float(required_bw) / float(current_bw)) * 100 if float(current_bw) > 0 else 0
            # Цвет: зеленый (<80%), оранжевый (80-95%), красный (>95%)
            load_color = "#27ae60" if load_percent < 80 else "#e67e22" if load_percent < 95 else "#c0392b"
        except:
            load_percent = 0
            load_color = "#7f8c8d"

        # Стили: Карточка + Увеличенный чекбокс
        frame.setStyleSheet(f"""
                #regulatorCard {{
                    background-color: white;
                    border: 1px solid #dcdde1;
                    border-radius: 8px;
                    margin: 2px;
                }}
                #regulatorCard:hover {{
                    border: 1px solid #3498db;
                    background-color: #f7f9fc;
                }}
                QCheckBox::indicator {{
                    width: 20px;
                    height: 20px;
                }}
            """)

        main_layout = QtWidgets.QHBoxLayout(frame)
        main_layout.setContentsMargins(15, 8, 15, 8)
        main_layout.setSpacing(15)

        # 1. Чекбокс
        checkbox = QtWidgets.QCheckBox()
        main_layout.addWidget(checkbox)

        # 2. Основная информация (слева)
        info_layout = QtWidgets.QVBoxLayout()
        name_label = QtWidgets.QLabel(f"<b>{name}</b>")
        name_label.setStyleSheet("font-size: 14px; color: #2c3e50;")

        details_text = f"Седло: {saddle} мм | Max Q: {current_bw} м³/ч"
        details_label = QtWidgets.QLabel(details_text)
        details_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")

        info_layout.addWidget(name_label)
        info_layout.addWidget(details_label)
        main_layout.addLayout(info_layout)

        # 3. Блок загрузки (справа)
        load_layout = QtWidgets.QVBoxLayout()
        load_layout.setAlignment(QtCore.Qt.AlignRight)

        load_val_label = QtWidgets.QLabel(f"{load_percent:.1f}%")
        load_val_label.setStyleSheet(f"color: {load_color}; font-weight: bold; font-size: 13px;")
        load_desc_label = QtWidgets.QLabel("загрузка")
        load_desc_label.setStyleSheet("color: #95a5a6; font-size: 9px; text-transform: uppercase;")

        load_layout.addWidget(load_val_label)
        load_layout.addWidget(load_desc_label)
        main_layout.addLayout(load_layout)

        # Ссылки для контроллера
        frame.checkbox = checkbox
        frame.regulator_name = name

        # --- ЛОГИКА КЛИКА ПО ВСЕЙ КАРТОЧКЕ ---
        def on_frame_clicked(event):
            # Переключаем состояние
            checkbox.setChecked(not checkbox.isChecked())
            # Визуальный эффект нажатия (опционально)
            frame.repaint()

        frame.mousePressEvent = on_frame_clicked
        frame.setCursor(QtCore.Qt.PointingHandCursor)

        return frame

    def show_found_regulators(self, regulators: Dict[str, Dict[str, Any]], inlet=None, outlet=None, capacity=None):
        """
            Отображает результаты поиска регуляторов в интерфейсе программы.

            Метод отвечает за визуализацию списка найденных моделей. Он очищает предыдущие
            результаты, формирует информационную панель с исходными параметрами расчета
            и динамически создает карточки для каждого подходящего регулятора.

            Args:
                regulators (Dict[str, Dict[str, Any]]): Словарь с данными найденных регуляторов.
                    Структура: { "Название": {"saddle": "25", "currentBandwidth": 500.0, ...} }.
                inlet (float, optional): Входное давление (МПа), использованное при поиске.
                    Используется для вывода в заголовке. По умолчанию None.
                outlet (float, optional): Выходное давление (МПа), использованное при поиске.
                    По умолчанию None.
                capacity (float, optional): Требуемый расход (м³/ч), использованный при поиске.
                    По умолчанию None.

            Returns:
                None: Метод напрямую модифицирует пользовательский интерфейс (regulatorsLayout).

            Raises:
                Exception: Логирует любые ошибки, возникающие в процессе отрисовки виджетов,
                    предотвращая аварийное завершение работы GUI.

            Note:
                Если словарь 'regulators' пуст, метод выведет сообщение "Ничего не найдено".
                Для создания каждой карточки вызывается вспомогательный метод 'create_regulator_block'.
            """

        try:
            # Очищаем старые результаты
            self.delete_block_result("regulatorsLayout")
            self.log.info("Отображение результатов поиска регуляторов")

            # 1. Шапка с исходными параметрами
            if all(v is not None for v in [inlet, outlet, capacity]):
                header_frame = QtWidgets.QFrame()
                header_frame.setStyleSheet("background-color: #34495e; border-radius: 6px; color: white;")
                h_layout = QtWidgets.QHBoxLayout(header_frame)

                summary_text = (
                    f"🎯 <b>Параметры подбора:</b> &nbsp;&nbsp;"
                    f"P<sub>вх</sub>: {inlet} МПа | P<sub>вых</sub>: {outlet} МПа | Q<sub>треб</sub>: {capacity} м³/ч"
                )
                lbl = QtWidgets.QLabel(summary_text)
                lbl.setStyleSheet("font-size: 12px; padding: 5px;")
                h_layout.addWidget(lbl)
                self.ui.regulatorsLayout.addWidget(header_frame)

            # 2. Если ничего не найдено
            if not regulators:
                no_res = QtWidgets.QLabel("❌ Подходящих регуляторов не обнаружено")
                no_res.setAlignment(QtCore.Qt.AlignCenter)
                no_res.setStyleSheet("color: #7f8c8d; padding: 20px; font-style: italic;")
                self.ui.regulatorsLayout.addWidget(no_res)
                return

            # 3. Список карточек
            for name, data in regulators.items():
                # Используем нашу новую функцию создания карточки
                block = self.create_regulator_block(
                    name=name,
                    saddle=data.get("saddle", "-"),
                    current_bw=data.get("currentBandwidth", 0),
                    required_bw=data.get("bandwidth", capacity if capacity else 0)
                )
                self.ui.regulatorsLayout.addWidget(block)

            # Распорка в конце, чтобы карточки не растягивались на весь экран
            self.ui.regulatorsLayout.addStretch()

        except Exception as e:
            self.log.error(f"Ошибка при отрисовке регуляторов: {e}", exc_info=True)
            self.show_error_message("Ошибка при отображении результатов")

    def get_selected_regulators(self) -> List[str]:
        """
        Сканирует область результатов и формирует список выбранных регуляторов.

        Метод итерируется по всем дочерним виджетам в 'regulatorsLayout', находит
        объекты карточек и проверяет состояние их внутренних чекбоксов. Используется
        Контроллером для определения списка моделей, для которых нужно подобрать схемы.

        Returns:
            List[str]: Список строк, содержащий названия (наименования) только тех
            регуляторов, которые были отмечены пользователем.

        Note:
            Метод игнорирует информационные заголовки, разделители и пустые области
            внутри лайаута благодаря проверке атрибутов hasattr(widget, 'checkbox').
        """
        selected_names = []
        layout = self.ui.regulatorsLayout

        # Проходим по всем элементам лайаута
        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget = item.widget()

            # Проверяем, что это виджет и у него есть нужные нам атрибуты
            # (чтобы не пытаться проверить чекбокс у распорок или заголовков)
            if widget and hasattr(widget, 'checkbox') and hasattr(widget, 'regulator_name'):
                if widget.checkbox.isChecked():
                    selected_names.append(widget.regulator_name)

        self.log.info(f"Выбрано регуляторов для подбора схем: {len(selected_names)}")
        return selected_names

    def select_product_type(self) -> Dict[str, str|int]:
        """
        Метод для обработки выбора типа изделия (ГРПБ, ГРПШ, ГРУ).
        Собирает данные о выбранном типе изделия и сохраняет их.
        """
        # Собираем дополнительную информацию о конфигурации газового оборудования
        gas_equipment_config = {
            "Тип изделия": self.ui.comboBox_product_type.currentText(),
            "Количество рабочих линий": self.get_count_work_line(),
            "Количество резервных линий": self.get_backup_lines(),
            "Наличие съемной резервной линии": self.get_removable_backup_line(),
            "Исполнение по СТО ГПРГ": self.get_sto_gprg_execution(),
            "Обогрев": self.get_heating_type(),
            "Телеметрия": self.get_telemetry_type(),
            "Климатическое исполнение": self.get_climate_execution(),
            "Оснащение УИРГ": self.get_uirg_equipment_type(),
            "Количество выходов газопроводов": self.get_number_of_gas_pipeline_outlets(),
            "Диаметр запорной арматуры на входе": self.get_valve_diameter_manual("Input"),
            "Диаметр запорной арматуры на выходе": self.get_valve_diameter_manual("Output"),
            "Направление": self.get_direction_type()
        }
        
        # Логируем конфигурацию оборудования
        return gas_equipment_config

    def delete_block_result(self,layout_name:str) -> None:
        """
            Данные метод позволяет отчистить от блоков данных в поле для вывода результатов по поиску регулятора и подбору схемы для него
        """
        try:
            layout = getattr(self.ui, layout_name)
            # Отключаем перерисовку для скорости
            self.ui.centralwidget.setUpdatesEnabled(False)

            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                elif item.layout() is not None:
                    # Если внутри есть вложенные лайауты, их тоже надо чистить
                    self._clear_layout(item.layout())

            self.ui.centralwidget.setUpdatesEnabled(True)
        except Exception as e:
            self.log.error(f"Ошибка при очистке {layout_name}: {e}")

    def create_scheme_block(self, regulator_name, scheme_name, file_path, found=True) -> QtWidgets.QFrame:
        """Создает визуальный блок для отображения найденной схемы."""
        frame = QtWidgets.QFrame()
        frame.setObjectName("schemeCard")

        # Стилизация карточки схемы
        status_color = "#2980b9" if found else "#c0392b"
        bg_color = "#f8f9fa" if found else "#fff5f5"

        frame.setStyleSheet(f"""
            #schemeCard {{
                background-color: {bg_color};
                border-left: 5px solid {status_color};
                border-top: 1px solid #dcdde1;
                border-right: 1px solid #dcdde1;
                border-bottom: 1px solid #dcdde1;
                border-radius: 4px;
                margin-bottom: 5px;
            }}
        """)

        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # Заголовок: Имя регулятора
        title = QtWidgets.QLabel(f"<b>📂 {regulator_name}</b>")
        title.setStyleSheet("font-size: 13px; color: #2c3e50;")

        # Описание схемы
        scheme_info = QtWidgets.QLabel(f"Схема: {scheme_name}")
        scheme_info.setStyleSheet("color: #34495e; font-size: 12px;")

        layout.addWidget(title)
        layout.addWidget(scheme_info)

        if found:
            # Ссылка на файл (стилизованная под кнопку или заметную ссылку)
            path_label = QtWidgets.QLabel(
                f"🔗 <a href='file:///{file_path}' style='color: #2980b9; text-decoration: none;'>"
                f"Открыть чертеж в формате CDW</a>"
            )
            path_label.setOpenExternalLinks(True)
            path_label.setToolTip(file_path)  # Показываем полный путь при наведении
            layout.addWidget(path_label)
        else:
            error_label = QtWidgets.QLabel("⚠️ Файл отсутствует в локальном каталоге")
            error_label.setStyleSheet("color: #e74c3c; font-size: 11px; font-weight: bold;")
            layout.addWidget(error_label)

        return frame

    def show_shemas(self, regulator_name: str, scheme_name: str, file_path: str, found: bool = True) -> None:
        """
        Отрисовка результата поиска схемы во View.

        Args:
            regulator_name (str): Наименование регулятора.
            scheme_name (str): Полное имя файла/схемы.
            file_path (str): Абсолютный путь к файлу.
            found (bool): Флаг успешного поиска файла на диске.
        """
        try:
            # Создаем красивый блок схемы
            scheme_block = self.create_scheme_block(regulator_name, scheme_name, file_path, found)

            # Находим лайаут. Если там есть распорка (stretch), удаляем её перед добавлением,
            # чтобы новые элементы всегда были сверху, либо просто добавляем в конец.
            layout = self.ui.ShemesLayout

            # Добавляем блок в интерфейс
            layout.addWidget(scheme_block)

            # Чтобы блоки не разъезжались, всегда держим один stretch в самом конце
            # (если он еще не добавлен)
            if layout.count() > 0:
                item = layout.itemAt(layout.count() - 1)
                if not isinstance(item, QtWidgets.QSpacerItem):
                    layout.addStretch()

            self.log.debug(f"Блок схемы для {regulator_name} отрисован (found={found})")

        except Exception as e:
            self.log.error(f"Ошибка при отрисовке блока схемы для {regulator_name}: {e}", exc_info=True)

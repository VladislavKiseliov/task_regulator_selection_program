from typing import Callable, Union, Dict, Any
import src.utils.MathMethod as MathMethod
from imports import *
from pathlib import Path
from contextlib import contextmanager
import logging

from src.utils.CallbackRegister import CallbackRegistry


@contextmanager
def block_signals(widget):
    widget.blockSignals(True)
    try:
        yield widget
    finally:
        widget.blockSignals(False)



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
        self.__create_path_folder_for_save()

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
            print(f"Не удалось установить иконку: {e}")  # Лучше выводить ошибку

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
        self.ui.pushButton_selected_regulator.clicked.connect(self.replacement_button_pressed)

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
        self.ui.pushButton_selected_scheme.clicked.connect(lambda: self.show_error("Error"))

        #Подключение событий изменения текста в полях калькулятора

        # При завершении редактирования поля ввода входного давления вызывается make_calculation
        # self.ui.input_Pressure_Input.editingFinished.connect(self.make_calculation)

        # При завершении редактирования поля ввода скорости газа вызывается make_calculation
        # self.ui.lineEdit_gas_speed.editingFinished.connect(self.make_calculation)

        # При завершении редактирования поля ввода диаметра газопровода вызывается make_calculatio
        # self.ui.lineEdit_diametet_of_gas_pipeline.editingFinished.connect(self.make_calculation)

        #Подключение событий изменения текста в полях калькулятора выходного газопровода

        # При завершении редактирования поля ввода выходного давления вызывается make_calculation
        # self.ui.input_Pressure_Output.editingFinished.connect(self.make_calculation)

        # При завершении редактирования поля ввода скорости газа на выходе вызывается make_calculation
        # self.ui.lineEdit_gas_speed_out.editingFinished.connect(self.make_calculation)

        # При завершении редактирования поля ввода диаметра газопровода на выходе вызывается make_calculation
        # self.ui.lineEdit_diametet_of_gas_pipeline_out.editingFinished.connect(self.make_calculation)

        # При завершении редактирования поля ввода пропускной способности вызывается make_calculation
        # self.ui.input_bandwidth.editingFinished.connect(self.make_calculation)

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

    def get_valve_diameter(self,ioType:str)->int:
        """
                Получить диаметр запорной арматуры  из текстового поля для указанного конца трубопровода.

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

    def set_valve_diametr(self,ioType:str,diametr:int)->None:
        """
            Устанавливаем значение диаметра в ячейку
        """
        widget_name = f"lineEdit_diameter_of_gas_pipeline_{ioType}"
        try:
            widget = getattr(self.ui, widget_name)
            with block_signals(widget):
                widget.setText(str(diametr))

        except Exception as e:
            self.show_error(f"Ошибка при вставке диаметра ({ioType}): {e}")

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
            with block_signals(widget):
                widget.setText(f"{gas_speed:.1f}")

        except Exception as e:
            self.show_error(f"Ошибка при вставке скорости ({ioType}): {e}")

    def get_speed(self,ioType:str)->int:
        """
                Получает значение скорости из текстового поля для указанного конца трубопровода.

                Поддерживаемые имена полей: lineEdit_gas_speed_Input, lineEdit_gas_speed_Output.

                Параметры:
                    ioType (str): "Input" — вход, "Output" — выход.

                Возвращает:
                    int: Значение давления. При ошибке возвращается 0 и отображается сообщение.

                Пример:
                    speed_in = self.get_speed("Input")
                """
        if ioType not in ("Input", "Output"):
            self.show_error("Ошибка: suffix должен быть 'Input' или 'Output'")
            return 0

        widget_name = f"lineEdit_gas_speed_{ioType}"
        try:
            widget = getattr(self.ui, widget_name)
            text = widget.text().replace(",", ".").replace(" ", "")
            return int(text)
        except Exception as e:
            self.show_error(f"Ошибка при чтении давления ({ioType}): {e}")
            return 0

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

    def __create_path_folder_for_save(self) -> None:
        """Создаём папку для сохранения файлов логов если её нет.
        получаем путь к этой папке."""
        # Получение текущей директории
        self.current_dir = os.getcwd()

        # Сборка пути к папке
        self.folder_save_name = "записи подборов регулятора"
        self.folder_path = os.path.join(self.current_dir, self.folder_save_name)

        # Проверка существования папки и создание, если не существует
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)

    def __conf_file_loader(self) -> None:
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

    def __add_load_save_path(self):
        #Добавляем полученные пути в лайibel для путей если они доступны
        for file in self.file_path_list:
            if os.path.exists(file):
                self.lb.insert(tk.END, file) 

    def __save_patch_in_conf(self, patch:str) -> None:
        try:
            """Сохраняем путь в файл конфигурации"""
            if patch not in self.file_path_list:
                self.file_path_list.append(patch)   

            # Проверка существования папки и создание, если не существует
            if not os.path.exists(self.conf_file_path):
                open(self.conf_file_path, 'w').close()
                return
            else:
                #with open(self.conf_file_path, 'r') as file:
                #    self.data_conf = json.load(file)
                #    file.close()

                #for _,value in self.data_conf["Path"].items():
                #   if value not in self.file_path_list:
                #       self.file_path_list.append(value)

                with open(self.conf_file_path, 'w') as file:
                    for elem in self.file_path_list:
                        self.data_conf["Path"][calculate_hash(elem)] = elem
                    
                    json.dump(self.data_conf, file)

                    file.close()
        except:
            pass

    def __split_and_insert_newline(self, text) -> None:
        """Функция для разделения строчки на двое если одна длинее 5 слов"""
        words = text.split()  # Разделение строки на список слов
        result = text
        if len(words) > 5:
            half_length = len(words) // 2
            first_half = ' '.join(words[:half_length])  # Объединение слов до середины
            second_half = ' '.join(words[half_length:])  # Объединение слов после середины
            result = f"{first_half}\n{second_half}"
        return result

    def __clear_widget_res_in_app(self) -> None:
        """Функция для очистки результата работы программы в виджете QPlainTextEdit"""
        self.ui.plainTextEdit.setReadOnly(False)  # Установка режима редактирования
        self.ui.plainTextEdit.clear()  # Очистка содержимого виджета
        self.ui.plainTextEdit.setReadOnly(True)  # Возвращение в режим только для чтения

    def __write_log_wrapper(self, mess:str) ->None:
        """Функция для добавления данных в виджет логирования в программе"""
        current_text = self.ui.plainTextEdit.toPlainText()
        new_text = current_text + "\n" + self.__split_and_insert_newline(mess)
        self.ui.plainTextEdit.setPlainText(new_text)

        self.logger.write_log(mess)

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

    def remove_button_pressed(self) -> None:
        """Функция для обработки нажатия кнопки <Удалить>""" 
        selected_index = self.lb.curselection()

        value = self.lb.get(selected_index)

        try:
            keys_to_remove = []
            dict_data = self.data_conf["Path"]

            for key, val in dict_data.items():
                if val == value:
                    
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del dict_data[key]

            self.file_path_list.remove(value)
        except:
            pass

        if selected_index:
            self.lb.delete(selected_index)

    def folder_save_open(self) -> None:
        """Функция для обработки нажатия кнопки <Удалить>""" 
        subprocess.Popen(f'explorer "{os.path.normpath(self.folder_path)}"')

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

    def is_int(self, value) -> bool:
        """Функция is_int, принимает значение
        и если это число возвращает True,
        иначе False"""
        try:
            int(value)
            return True
        except ValueError:
            return False

    def possible_copy(self, path_file:str, worck_patch:str) -> bool:
        """
        Проверяет возможность копирования файла из одного пути в другой. 
            И копирует его если это возможно.

        Args:
            path_file (str): Путь к исходному файлу.
            worck_patch (str): Путь к целевому файлу.

        Returns:
            bool: Возвращает True, если копирование прошло успешно. 
            В противном случае выводит сообщение об ошибке и возвращает False.
        """
        try:
            shutil.copyfile(path_file.lstrip(), worck_patch.lstrip())
            return True
        except PermissionError:
            self.show_error_message("Недоступно чтение исходного файла!")
            return False

    def __open_file_dialog(self):
        """Функция __open_file_dialog, отвечает
        за загрузку файла через контекстный
        диалог через проводник"""

        options = QFileDialog.Options()
        file_filter = "All Files (*);;Excel Files (*.xlsx);;Doc Files (*.doc);;Docx Files (*.docx)"
        file_path, _ = QFileDialog.getOpenFileName(self.ui.centralwidget, "Выберите файл", "", file_filter, options=options)
        if file_path:
            self.drop_area.add_file(file_path)

    def __file_placed_drop_zone(self, e:str) -> None:
        """Функция __file_placed_drop_zone, отвечает
        за добавление и форматировании пути файла
        в дроп зону при его перетаскивании туда"""
        list_path = "".join(e.data.replace("{", "")).split("}")[:-1]
        #Вводим пути в дроп бокс с форматированием
        [self.lb.insert(tk.END, file) for file in list_path]
        #Показываем пользователю какое название будет у файла
        # self.input_name_file.delete(0, tk.END)  # Очистка поля ввода
        # self.input_name_file.insert(0,  os.path.splitext(os.path.basename(list_path[-1]))[0]+"подбор"+".log")  # Вставка текста в поле ввода

    def __res_file_name(self) -> str:
        """Функция __res_file_name, собирает название
        файла логов в который будет записан результат"""
        if self.saved_conf_self_file_name_var:
            return self.saved_conf_input_name_file+".txt"

        # Сборка пути к файлу
        name_file = "Pвх-{0} Pвых-{1} ПрСп-{2}.txt".format(self.get_pressure("Input"),
                                                    self.get_pressure("Output"),
                                                    self.get_bandwidth())
        
        file_path = os.path.join(self.current_dir, self.folder_save_name, name_file)

        return file_path
  
    def __logging_found_device(self, name_devace:str, saddle:str, found_bandwidth:int, need_bandwidth:int, defolt_bandwidth:str)-> None:
        """Функция __logging_found_device, добавляет
        в словарь найденных устройств новые записи
        об устройствах"""
        print(f"{saddle=}")
        for i in saddle.split():
            if self.is_int(i):
                saddle=i
        
        #name_devace+="/"+saddle

        # if self.saved_conf_left_to_right:
        #     name_devace+='-01'
        #
        # if self.saved_conf_PZK_position_sensor:
        #     name_devace+=' Д'

        self.data_found_id+=1
        self.data_found[self.data_found_id] = {"Регулятор":name_devace,
                                               "Седло":saddle,
                                               "Пропускная":found_bandwidth,
                                               "Необходимая":need_bandwidth,
                                               "Процент":"{:.2f}".format(100-(((int(found_bandwidth)-int(need_bandwidth))/int(found_bandwidth))*100))}

    def start_initial_log(self) -> None:
        """start_initial_log добавляет стартовые данные о сканировании в логи"""
        self.__write_log_wrapper("======================")
        self.__write_log_wrapper("Поиск регуляторов по следующим параметрам: Входное давление-{0} \
                                 Выходное давление-{1} Пропускная способность-{2}".format(self.get_pressure("Input"),self.get_pressure("Output"), self.get_bandwidth()))
        
        # Добавляем информацию о выбранном типе изделия в лог, если она есть
        if hasattr(self, 'selected_product_type') and self.selected_product_type:
            self.__write_log_wrapper(f"Тип изделия: {self.selected_product_type}")
            
        # Добавляем информацию о конфигурации газового оборудования в лог, если она есть
        if hasattr(self, 'gas_equipment_config') and self.gas_equipment_config:
            self.__write_log_wrapper("Конфигурация газового оборудования:")
            for key, value in self.gas_equipment_config.items():
                self.__write_log_wrapper(f"  {key}: {value}")
         
        if self.saved_conf_left_to_right:
            direct = "справа налево"
        else:
            direct = "слева направо"
            
        self.__write_log_wrapper("Направление: {0}".format(direct))
        self.__write_log_wrapper("======================")

    def write_log_found_reg(self) -> int:
        """Функция write_log_found_reg, записывает
        в файл для логирования все найденные девайсы
        сортируя их по проценту загрузки"""
        number_found = 0

        sorted_data = sorted(self.data_found.items(), key=lambda x: float(x[1]["Процент"]), reverse=True)
        
        self.list_in_range_value = [item for item in sorted_data if self.saved_conf_minimum_load <= float(item[1]["Процент"]) <= self.saved_conf_maximum_load]

        for key, value in self.list_in_range_value:
            self.__write_log_wrapper("======================")
            self.__write_log_wrapper("Регулятор: {}".format(value["Регулятор"]))
            self.__write_log_wrapper("Седло: {}".format(value["Седло"]))
            self.__write_log_wrapper("Пропускная способность регулятора при выбранных параметрах: {}".format(value["Пропускная"]))
            self.__write_log_wrapper("Процент загрузки пропускной спос. регулятора c необходимой пропускной способностью ({}) составляет {}%".format(value["Необходимая"],value["Процент"]))

    def __clear_data_found_device(self) -> None:
        """очищает списки найденных регуляторов"""
        self.list_in_range_value = []
        self.data_found = {}

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
    
    def search_several_controller_table_algorithm(self,
                                            inlet_pressure:float, 
                                            output_pressure:float, 
                                            traffic_capacity:float,
                                            sheet) -> int:
        """Функция search_several_controller_table_algorithm, принимает
        данные поиска и лист с таблицей формата: несколько устройств
        на одном листе. И добавляет девайс в найденные если 
        его данные таблицы соответствуют найденным, и возвращает
        1 если устройство соответствует"""
        # Put your sheet in the loader
        regulators_found = 0
        i_row = 0

        for row in sheet.iter_rows(values_only=True):
            if i_row == 0:
                saddle = row[0]
                print(f"saddle: {saddle=}")
            
            for i_cell in range(len(row)):
                if i_row == 2 and i_cell!=0:

                    #Ищим подходящие выходные давления, как по диапазону - так и по единичным значениям
                    mb_diap_Paut = str(row[i_cell]).replace("\xa0", '').replace(" ", '').replace(",", '.').split("-")
                    
                    if len(mb_diap_Paut) == 2:
                        #Если ячейка выходного давления является диапазоном
                        name_devace = sheet[get_excel_column(i_cell+1)+"1"].value
                        if float(mb_diap_Paut[0]) <= float(output_pressure) <= float(mb_diap_Paut[1]):
                            row_scr_i=0
                            for row_scr in sheet.iter_rows(values_only=True):
                                if row_scr_i > 2:
                                    mb_diap_Pain = str(row_scr[0]).replace("\xa0", '').replace(" ", '').replace(",", '.').split("-")

                                    #Если ячейка входного давления является диапазоном
                                    if len(mb_diap_Pain) == 2: 
                                        if  float(mb_diap_Pain[0]) <= float(inlet_pressure) <= float(mb_diap_Pain[1]):

                                            bandwidth = int(traffic_capacity)
                                            #Проверяем можем ли мы перевести значение пропускной способности в число
                                            if self.is_int(row_scr[i_cell]):

                                                #Проверяем, найденная пропускная способность больше ли необходимой, и является ли регулятор для сжиженного газа если необходимо
                                                if int(row_scr[i_cell]) >= bandwidth:
                                                    regulators_found+=1
                                                    self.__logging_found_device(name_devace, saddle, row_scr[i_cell], bandwidth, traffic_capacity)

                                    
                                    #Если ячейка входного давления НЕ является диапазоном
                                    else:
                                        if  float(mb_diap_Pain[0]) == float(inlet_pressure):
                                            bandwidth = int(traffic_capacity)
                                            #Проверяем можем ли мы перевести значение пропускной способности в число
                                            if self.is_int(row_scr[i_cell]):
                                                if int(row_scr[i_cell]) >= bandwidth:
                                                    regulators_found+=1
                                                    self.__logging_found_device(name_devace, saddle, row_scr[i_cell], bandwidth, traffic_capacity)

                                row_scr_i+=1

                    #Если ячейка выходного давления НЕ является диапазоном и существует
                        
                    elif mb_diap_Paut[0] != "None":
                        if float(output_pressure) == float(mb_diap_Paut[0]):
                            name_devace = sheet[get_excel_column(i_cell+1)+"1"].valu
                            row_scr_i=0
                            for row_scr in sheet.iter_rows(values_only=True):
                                if row_scr_i > 2:
                                    mb_diap_Pain = str(row_scr[0]).replace("\xa0", '').replace(" ", '').replace(",", '.').split("-")
                                    #Если ячейка входного давления является диапазоном
                                    if len(mb_diap_Pain) == 2: 
                                        if  float(mb_diap_Pain[0]) <= float(inlet_pressure) <= float(mb_diap_Pain[1]):
                                            bandwidth = int(self.traffic_capacity)+(int(self.traffic_capacity)/100)
                                            #Проверяем можем ли мы перевести значение пропускной способности в число
                                            if self.is_int(row_scr[i_cell]):
                                                if int(row_scr[i_cell]) >= bandwidth :
                                                    regulators_found+=1
                                                    self.__logging_found_device(name_devace, saddle, row_scr[i_cell], bandwidth, traffic_capacity)
                                    
                                    #Если ячейка входного давления НЕ является диапазоном
                                    else:
                                        if  float(mb_diap_Pain[0]) == float(inlet_pressure):
                                            bandwidth = int(traffic_capacity)
                                            #Проверяем можем ли мы перевести значение пропускной способности в число
                                            if self.is_int(row_scr[i_cell]):          
                                                #Если это значение больше или равно необходимого
                                                if int(row_scr[i_cell]) >= bandwidth :
                                                    regulators_found+=1
                                                    self.__logging_found_device(name_devace, saddle, row_scr[i_cell], bandwidth, traffic_capacity)
                                    
                                row_scr_i+=1
            i_row += 1

        return regulators_found

    def search_one_controller_table_algorithm(self,
                                            inlet_pressure:float, 
                                            output_pressure:float, 
                                            traffic_capacity:float,
                                            sheet) -> int:
        """Функция search_one_controller_table_algorithm, принимает
        данные поиска и лист с таблицей формата: одно устройство
        на одном листе. И добавляет девайс в найденные если 
        его данные таблицы соответствуют найденным, и возвращает
        1 если устройство соответствует"""
        # Put your sheet in the loader
        regulators_found = 0
        i_row = 0
        self.log.info(f"Обрабатываем лист {sheet.title=}")
        for row in sheet.iter_rows(values_only=True):
            if i_row == 0:
                name_devace = row[0]
                if name_devace not in self.data:
                    self.data[name_devace] = {}

                saddle = row[1]
                self.data[name_devace][saddle]={}

            if i_row == 1:
                unit_Pin = row[0]
                unit_Out = row[1]

                self.data[name_devace][saddle]['unit_Pin'] = unit_Pin
                self.data[name_devace][saddle]['unit_Out'] = unit_Out
                self.data[name_devace][saddle]['data_P'] = {}

            for i_cell in range(len(row)):
                if i_row == 2 and i_cell!=0:
                    #Ищим подходящие выходные давления, как по диапазону - так и по единичным значениям
                    mb_diap_Paut = str(row[i_cell]).replace("\xa0", '').replace(" ", '').replace(",", '.').split("-")
                    if len(mb_diap_Paut) == 2:
                        #Если ячейка выходного давления является диапазоном
                        if float(mb_diap_Paut[0]) <= float(output_pressure) <= float(mb_diap_Paut[1]):
                            row_scr_i=0
                            for row_scr in sheet.iter_rows(values_only=True):
                                if row_scr_i > 2:
                                    mb_diap_Pain = str(row_scr[0]).replace("\xa0", '').replace(" ", '').replace(",", '.').split("-")

                                    #Если ячейка входного давления является диапазоном
                                    if len(mb_diap_Pain) == 2: 
                                        if  float(mb_diap_Pain[0]) <= float(inlet_pressure) <= float(mb_diap_Pain[1]):

                                            bandwidth = int(traffic_capacity)
                                            #Проверяем можем ли мы перевести значение пропускной способности в число
                                            if self.is_int(row_scr[i_cell]):
                                                #Проверяем, найденная пропускная способность больше ли необходимой, и является ли регулятор для сжиженного газа если необходимо
                                                if int(row_scr[i_cell]) >= bandwidth and (("Ж" in name_devace or "ж" in name_devace) == self.saved_conf_Regulator_for_liquefied_gas):
                                                    regulators_found+=1

                                                    
                                                    self.__logging_found_device(name_devace, saddle, row_scr[i_cell], bandwidth, traffic_capacity)

                                    
                                    #Если ячейка входного давления НЕ является диапазоном
                                    else:
                                        if  float(mb_diap_Pain[0]) == float(inlet_pressure):
                                            bandwidth = int(traffic_capacity)
                                            #Проверяем можем ли мы перевести значение пропускной способности в число
                                            if self.is_int(row_scr[i_cell]):
                                                if int(row_scr[i_cell]) >= bandwidth and (("Ж" in name_devace or "ж" in name_devace) == self.saved_conf_Regulator_for_liquefied_gas):
                                                    regulators_found+=1
                                                    self.__logging_found_device(name_devace, saddle, row_scr[i_cell], bandwidth, traffic_capacity)

                                row_scr_i+=1

                    #Если ячейка выходного давления НЕ является диапазоном
                    elif mb_diap_Paut[0] != "None":
                        if float(output_pressure) == float(mb_diap_Paut[0]):
                            row_scr_i=0
                            for row_scr in sheet.iter_rows(values_only=True):
                                if row_scr_i > 2:
                                    mb_diap_Pain = str(row_scr[0]).replace("\xa0", '').replace(" ", '').replace(",", '.').split("-")

                                    #Если ячейка входного давления является диапазоном
                                    if len(mb_diap_Pain) == 2: 
                                        if  float(mb_diap_Pain[0]) <= float(inlet_pressure) <= float(mb_diap_Pain[1]):
                                            bandwidth = int(self.traffic_capacity)+(int(self.traffic_capacity)/100)
                                            #Проверяем можем ли мы перевести значение пропускной способности в число
                                            if self.is_int(row_scr[i_cell]):
                                                if int(row_scr[i_cell]) >= bandwidth and (("Ж" in name_devace or "ж" in name_devace) == self.saved_conf_Regulator_for_liquefied_gas):
                                                    regulators_found+=1
                                                    self.__logging_found_device(name_devace, saddle, row_scr[i_cell], bandwidth, traffic_capacity)
                                    
                                    #Если ячейка входного давления НЕ является диапазоном
                                    else:
                                        if  float(mb_diap_Pain[0]) == float(inlet_pressure):
                                            bandwidth = int(traffic_capacity)
                                            #Проверяем можем ли мы перевести значение пропускной способности в число
                                            if self.is_int(row_scr[i_cell]):
                                                #Если это значение больше или равно необходимого
                                                if int(row_scr[i_cell]) >= bandwidth and (("Ж" in name_devace or "ж" in name_devace) == self.saved_conf_Regulator_for_liquefied_gas):
                                                    regulators_found+=1
                                                    self.__logging_found_device(name_devace, saddle, row_scr[i_cell], bandwidth, traffic_capacity)
                                    
                                row_scr_i+=1
            i_row += 1
        print(f"search one contoller table algoritm {regulators_found=}")
        return regulators_found

    def conduct_analysis(self, workbook:str,
                         inlet_pressure:float, 
                         output_pressure:float, 
                         traffic_capacity:float) -> int:
        """Функция conduct_analysis, распарсивает экселевский файл
        и ищет подходящие ячейки по входным данным.
        Возвращает колличество найденных девайсов в файле."""
        self.log.info("Начинаем анализ Excel-файла: %s", workbook)
        self.log.debug("Доступные листы в книге: %s", workbook.sheetnames)

        regulators_found = 0
        print(f"{workbook.sheetnames=}")


        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            self.log.debug("Обрабатываем лист: %s", sheet_name)

            try:
                # Проверяем признак типа таблицы в ячейке C1
                c1_value = sheet["C1"].value
                self.log.debug("Значение в C1 на листе %s: %r", sheet_name, c1_value)

                if c1_value is None or c1_value == "":
                    self.log.info("Лист %s: обнаружен формат «один регулятор на лист»", sheet_name)
                    found = self.search_one_controller_table_algorithm(
                        inlet_pressure, output_pressure, traffic_capacity, sheet
                    )
                    regulators_found += found
                    self.log.debug("На листе %s найдено регуляторов: %d", sheet_name, found)
                else:
                    self.log.info("Лист %s: обнаружен формат «несколько регуляторов на лист»", sheet_name)
                    found = self.search_several_controller_table_algorithm(
                        inlet_pressure, output_pressure, traffic_capacity, sheet
                    )
                    regulators_found += found
                    self.log.debug("На листе %s найдено регуляторов: %d", sheet_name, found)

            except Exception as e:
                self.log.error(
                    "Ошибка при обработке листа %s: %s",
                    sheet_name, str(e), exc_info=True
                )
                continue  # Пропускаем лист при ошибке

        self.log.info(
            "Анализ файла %s завершён. Найдено подходящих регуляторов: %d",
            workbook, regulators_found
        )
        return regulators_found

    def replacement_button_pressed(self) -> None:
        """
        """
        regulators_found = 0
        filename_log = False
        self.log.info("Начинаем подбор регулятора")
        print("Зашли в функцию")
        listbox_data = self.drop_area.get_file_paths()
        self.log.info("Получили список файлов из drop_area: %s", listbox_data)
        self.processed_urls = {}

        print(f"{listbox_data=}")
        self.__create_path_folder_for_save()
        self.log.info("Создали директорию для сохранения отчётов")

        # Фильтрация Excel-файлов
        for index in range(len(listbox_data)):
            print(f"{listbox_data[index]=}")
            if os.path.splitext(listbox_data[index])[1] == '.xlsx':
                self.processed_urls[listbox_data[index]] = 0
        self.log.info("Отфильтрованы Excel-файлы: %s", list(self.processed_urls.keys()))

        if len(self.processed_urls) == 0:
            self.show_error_message("Добавьте файлы xlsx")
            self.log.warning("Нет Excel-файлов для обработки")
            return
        
        if not self.is_int(self.ui.max_lebel_loading_range.text()) or not self.is_int(self.ui.min_lebel_loading_range.text()):
            self.show_error_message("Некорректный диапазон процента загрузки")
            self.log.error("Некорректный диапазон процента загрузки: max=%s, min=%s",
                              self.ui.max_lebel_loading_range.text(),
                              self.ui.min_lebel_loading_range.text())
            return

        #Очищаем виджет с результатами сканирования в самой программе
        self.__clear_widget_res_in_app()
        self.log.info("Виджет результатов очищен")

        for path_file, _ in self.processed_urls.items():
            try:
                if path_file.replace(" ", "") != "":

                    try:
                        PIn = self.get_pressure("Input")
                        POt = self.get_pressure("Output")
                        bandwidth = self.get_bandwidth()
                        self.log.info("Виджет результатов очищен")
                    except Exception as e:
                        self.show_error_message("Введите корректные значения для поиска регулятора")
                        self.log.error("Ошибка получения входных параметров: %s", str(e))
                        return 

                    self.__save_patch_in_conf(path_file)
                    self.log.info("Сохранён путь к файлу в конфиг: %s", path_file)

                    self.show_info_message(str("Поиск подходящего регулятора запущен"))
                    self.status_text = "В работе"
                    self.update_status_worck("В работе.")
                    self.log.info("Статус установлен: 'В работе'")

                    if PIn != "" and POt != "" and bandwidth != "":

                        ##Вот тут ошибка
                        self.__saved_conf_search()
                        # ###

                        #Открываем файл экселя
                        workbook = openpyxl.load_workbook(os.path.normpath(path_file))
                        self.log.info("Файл Excel открыт: %s", path_file)

                        #Если не был создан файл логов, создаём его
                        # if not filename_log:
                        #     filename_log = self.__res_file_name()
                        #     self.logger = FileWriter(filename_log)
                        #     self.log.info("Создаем файл результатов подбора")
                        #     self.logger.open_file()
                        #
                        # #Пишем в файл лога стартовые данные поиска
                        # self.start_initial_log()

                        #Запуск функции анализ
                        self.log.info("Запустился процесс подбора")
                        regulators_found += self.conduct_analysis(workbook, 
                                                                PIn,
                                                                POt, 
                                                                bandwidth)
                        print(f"{regulators_found=}")
                        if regulators_found == 0:
                            # self.__write_log_wrapper("Точного совпадения не найдено")
                            self.log.warning("Точного совпадения не найдено")
                            # self.__write_log_wrapper("Попытка найти регулятор с близкими параметрами.")

                            #Находим ближайшие допустимые значения
                            finding_real_value = FoundCorValue(workbook,PIn,POt)
                            PIn,POt = finding_real_value()

                            regulators_found += self.conduct_analysis(workbook, 
                                                                PIn,
                                                                POt, 
                                                                bandwidth)
                                

                        # if regulators_found == 0:
                        #     self.__write_log_wrapper("Регуляторы с необходимыми параметрами не найдены.")
                        # else:
                        #     print("Ok")
                        #     self.__write_log_wrapper("======================")
                        #     self.__write_log_wrapper("Выполнен поиск и найдены регуляторы по входному: {0} и выходному {1} давлению.".format(PIn,POt))
                        #     self.__write_log_wrapper("")
                        #     self.write_log_found_reg()
                        #
                        # # self.show_info_message("В файле {0} исправлено: {1} некорректных записей с кириллицей.".format(worck_patch,str(number_change),))
                        # self.__write_log_wrapper("!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-")
                        # self.__write_log_wrapper("В файле {0} найдено {1} подходящих регуляторов.".format(path_file,len(self.list_in_range_value)))
                        # self.__write_log_wrapper("!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!--!")
                        # #
                        # self.__clear_data_found_device()
                    else:
                        self.show_error_message("Введите все входные данные!")
            except:
                self.show_error_message(f"Критическая ошибка анализай файла - {path_file}")
                self.log.error(f"Критическая ошибка анализай файла - {path_file}")


        # Закрытие логгера
        # self.logger.close_file()

        self.update_status_worck("Ожидание работы")
        # Открытие файла в который записаны данные
        #subprocess.Popen(["notepad.exe", filename_log])
        #subprocess.Popen(f'explorer "{os.path.normpath(os.path.dirname(path_file))}"')

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
        # self.root = TkinterDnD.Tk()
        # self.root.title("Программа подбора регулятора")
        # self.root.geometry("800x710")
        # try:
        #     self.root.iconbitmap("icon.ico")
        # except:
        #     pass
        # self.style = ttk.Style()
        # self.style.configure("TFrame", background="lightgrey")
        # self.style.configure("TLabel", background="lightgrey")
        # self.style.configure("TButton",
        #                 background="#007bff",
        #                 foreground="black",
        #                 relief=tk.FLAT,
        #                 font=("Helvetica", 12),
        #                 padding=10,
        #                 width=20,
        #                 borderwidth=0)
        # self.style.map("TButton",
        #           background=[("active", "#0056b3")],
        #           foreground=[("active", "black")])
        
        #self.__core_render()

        #self.root.mainloop()

        self.MainWindow.show()

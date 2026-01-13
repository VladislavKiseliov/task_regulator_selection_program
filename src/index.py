from typing import Callable, Union, Dict, Any
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
        self.ui.pushButton_selected_scheme.clicked.connect(self.add_test_regulators)

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
            with utils.block_signals(widget):
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
            with utils.block_signals(widget):
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

    def __clear_widget_res_in_app(self) -> None:
        """Функция для очистки результата работы программы в виджете QPlainTextEdit"""
        self.ui.plainTextEdit.setReadOnly(False)  # Установка режима редактирования
        self.ui.plainTextEdit.clear()  # Очистка содержимого виджета
        self.ui.plainTextEdit.setReadOnly(True)  # Возвращение в режим только для чтения

    def __write_log_wrapper(self, mess:str) ->None:
        """Функция для добавления данных в виджет логирования в программе"""
        current_text = self.ui.plainTextEdit.toPlainText()
        new_text = current_text + "\n" + utils.split_and_insert_newline(mess)
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
            if utils.is_int(i):
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

    def create_regulator_block(self, name: str, saddle: str, inlet: float, outlet: float, kv: int):
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        frame.setFixedHeight(55)

        checkbox = QtWidgets.QCheckBox()
        label = QtWidgets.QLabel(
            f"<b>{name}</b><br>"
            f"Седло: {saddle} | Pвх: {inlet} МПа | Pвых: {outlet} МПа | Kv: {kv}"
        )
        label.setWordWrap(False)
        label.setStyleSheet("padding-left: 5px;")

        layout = QtWidgets.QHBoxLayout(frame)
        layout.addWidget(checkbox)
        layout.addWidget(label)
        layout.addStretch()

        # Сохраняем данные прямо в виджете
        frame.checkbox = checkbox
        frame.name = name

        return frame

    def add_test_regulators(self):
        try:
            # Очистка старых блоков
            while self.ui.regulatorsLayout.count():
                item = self.ui.regulatorsLayout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Тестовые данные
            test_regs = [
                {"name": "Регулятор РДСК-50", "saddle": "DN50", "inlet": 0.6, "outlet": 0.2, "kv": 120},
                {"name": "Регулятор РДГ-32", "saddle": "DN32", "inlet": 1.2, "outlet": 0.3, "kv": 85},
                {"name": "Регулятор РДУ-100", "saddle": "DN100", "inlet": 1.6, "outlet": 0.4, "kv": 210},
                {"name": "Регулятор РДУ-120", "saddle": "DN120", "inlet": 1.8, "outlet": 0.5, "kv": 220},
                {"name": "Регулятор РДУ-130", "saddle": "DN130", "inlet": 2.0, "outlet": 0.6, "kv": 230},
                {"name": "Регулятор РДУ-140", "saddle": "DN140", "inlet": 2.2, "outlet": 0.7, "kv": 240},

            ]

            for reg in test_regs:
                block = self.create_regulator_block(
                    name=reg["name"],
                    saddle=reg["saddle"],
                    inlet=reg["inlet"],
                    outlet=reg["outlet"],
                    kv=reg["kv"]
                )
                self.ui.regulatorsLayout.addWidget(block)

            # Добавляем растягиватель, чтобы блоки не прилипали к низу
            self.ui.regulatorsLayout.addStretch()
        except ValueError as e:
            print(e)


    def show_found_regulators(self, regulators_list):
        # Очистка старых блоков
        while self.regulatorsLayout.count():
            item = self.regulatorsLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Добавление новых
        for reg in regulators_list:
            block = self.create_regulator_block(
                name=reg["name"],
                saddle=reg["saddle"],
                inlet=reg["inlet_pressure"],
                outlet=reg["output_pressure"],
                kv=reg["capacity"]
            )
            self.regulatorsLayout.addWidget(block)

        # Добавим "растягиватель", чтобы блоки не прилипали к низу
        self.regulatorsLayout.addStretch()

    def get_selected_regulators(self) -> list[str]:
        selected = []
        for i in range(self.regulatorsLayout.count() - 1):  # -1, чтобы пропустить addStretch
            widget = self.regulatorsLayout.itemAt(i).widget()
            if hasattr(widget, 'checkbox') and widget.checkbox.isChecked():
                selected.append(widget.name)
        return selected
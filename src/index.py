from typing import Callable, Union, Dict, Any
import src.utils.MathMethod as MathMethod
from imports import *
from pathlib import Path
from contextlib import contextmanager


@contextmanager
def block_signals(widget):
    widget.blockSignals(True)      # ← 1. Делаем что-то ПЕРЕД
    try:
        yield widget               # ← 2. «Пауза» — выполняется тело `with`
    finally:
        widget.blockSignals(False) # ← 3. Делаем что-то ПОСЛЕ (даже при ошибке)



class SelRegulator:
    def __init__(self):
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

        self.app = QtWidgets.QApplication(sys.argv)
        
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
            self.app.setWindowIcon(QIcon('icon.ico'))
            self.MainWindow.setWindowIcon(QIcon('icon.ico'))
        except:
            pass

        self.action_menu_2 = QAction("Помощь", self.MainWindow)
        # Добавляем этот QAction на QMenuBar
        self.ui.menubar.addAction(self.action_menu_2)

        self.__drop_area_create();
        self.__connect_config();
    

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
        self.ui.pushButton_make_calculation.clicked.connect(self.make_calculation)

        # Кнопка "Подобрать изделие" - вызывает метод select_product_type
        self.ui.pushButton_selected_scheme.clicked.connect(self.select_product_type)

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
            self.ui.statusbar.showMessage("Ошибка: ioType должен быть 'Input' или 'Output'")
            return 0

        widget_name = f"lineEdit_diameter_of_gas_pipeline_{ioType}"
        try:
            widget = getattr(self.ui, widget_name)
            text = widget.text().replace(",", ".").replace(" ", "")
            return int(text)
        except Exception as e:
            self.ui.statusbar.showMessage(f"Ошибка при чтении диаметра ({ioType}): {e}")
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
            self.ui.statusbar.showMessage(f"Ошибка при вставке диаметра ({ioType}): {e}")

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

    def set_speed(self,ioType:str,speed:float,gas_speed:float)->None:
        """
            Устанавливаем значение скорости в ячейку

        """
        widget_name = f"lineEdit_gas_speed_{ioType}"
        try:
            widget = getattr(self.ui, widget_name)
            with block_signals(widget):
                widget.setText(f"{gas_speed:.1f}")

        except Exception as e:
            self.ui.statusbar.showMessage(f"Ошибка при вставке скорости ({ioType}): {e}")

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
            self.ui.statusbar.showMessage("Ошибка: suffix должен быть 'Input' или 'Output'")
            return 0

        widget_name = f"lineEdit_gas_speed_{ioType}"
        try:
            widget = getattr(self.ui, widget_name)
            text = widget.text().replace(",", ".").replace(" ", "")
            return int(text)
        except Exception as e:
            self.ui.statusbar.showMessage(f"Ошибка при чтении давления ({ioType}): {e}")
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

    def make_calculation(self) -> None:
        """
        Метод определения метода расчета в зависимости от наличия значения потребления газа.

        Вызывает методы calculate_gas_consumption или calculate_pressure_and_speed в зависимости
        от наличия значения в поле ввода потребления газа.


        Формула для расчёта давления газа при данном диаметре трубопровода и скорости газа
        gas_pressure = 1000 * ((gas_consumption * 293) / ((pipeline_diameter / 0.36238) ** 2 * gas_speed) - 0.1)

        Формула для расчёта расхода газа при данном давлении и диаметре трубопровода
        gas_consumption = ((pipeline_diameter / 0.36238) ** 2 * (0.1 + gas_pressure / 1000) * gas_speed) / 293
        """
        if (self.speed_or_diametr == "diametr"):
            print("Начали расчет диаметр для входа")
            self.calculated_diametr("Input")
            print("Начали расчет диаметр для выхода")
            self.calculated_diametr("Output")
        else:
            print("Начали расчет")
            self.calculated_speed_in()
            self.calculated_speed_out()

    def __calculate_gas_pipeline_params(self, pressure: float, speed, auto_speed: bool,gas_consumption) -> float:
        """
        Обобщенный метод для расчета параметров газопровода (Вход или Выход).

        Args:
            pressure: давления (PIn или POut).
            speed: значение скорости.
            auto_speed: Булево значение для автоматического выбора скорости.
        """
        try:
            print("Функция расчета берем параметры")
            gas_consumption = gas_consumption
            gas_pressure = pressure
            gas_speed = speed
            print("Взяли параметры")

            if not gas_consumption or not gas_pressure:
                return

            # Конвертация и масштабирование
            gas_consumption = float(gas_consumption)
            # Умножаем на 1000 для перевода МПа в кПа (как в исходном коде)
            gas_pressure_kpa = float(gas_pressure) * 1000

            # Логика автоматического выбора скорости
            if auto_speed:
                if gas_pressure_kpa < 50:
                    gas_speed = 15.0
                elif 50 <= gas_pressure_kpa <= 600:
                    gas_speed = 25.0
                else:
                    gas_speed = 30.0

            gas_speed = float(gas_speed)

            # Вызов чистой функции расчета
            print("Математическая функция расчет")
            print(f"{gas_consumption=},{gas_pressure=},{gas_speed=}")
            rounded_result = MathMethod.calculated_diametr(gas_consumption, gas_pressure_kpa, gas_speed)
            print(f"Расчет диаметра{round(rounded_result, 2)=}")
            return rounded_result

        except ValueError:
            self.ui.statusbar.showMessage("Ошибка: неверный ввод. Проверьте числовые поля.")
        except ZeroDivisionError:
            self.ui.statusbar.showMessage("Ошибка: деление на ноль.")
        except Exception as e:
            self.ui.statusbar.showMessage(f"Неизвестная ошибка: {str(e)}")


    def calculated_diametr(self,ioType:str) -> None:
        """Слот для расчета диаметра трубопровода по скорости"""
        print(f"Выполняем расчет для диаметра для {ioType=}")
        pressure = self.get_pressure(ioType)
        speed = self.get_speed(ioType)
        gas_consumption = self.get_bandwidth()
        auto_speed = False
        print(f"Все параметры для расчета для {ioType=} равны {pressure=},{speed=},{gas_consumption=},{auto_speed=}")

        сalculated_diameter = self.__calculate_gas_pipeline_params(pressure=pressure, speed=speed,
                                                       auto_speed=auto_speed, gas_consumption = gas_consumption
                                                       )
        print(f"Полученный результат диаметра для {сalculated_diameter=} трубопровода ")
        self.set_valve_diametr(ioType, сalculated_diameter)


    def calculate_gas_speed(self,
                            pressure: float,
                            diametr_line_edit,
                            speed_line_edit) -> None:
        """
        Обобщенный метод для расчета скорости газа (Вход или Выход).

        Args:
            pressure: Значение давления
            diametr_line_edit: Объект QLineEdit для диаметра.
            speed_line_edit: Объект QLineEdit для скорости, которую нужно обновить.
        """
        print("Зашли в расчет")
        try:
            gas_consumption = self.get_bandwidth()  # Предполагаем, что эта функция общая
            gas_pressure = pressure
            diametr = diametr_line_edit.text()

            if not gas_consumption or not gas_pressure or not diametr:
                return

            # Конвертация и масштабирование
            gas_consumption = float(gas_consumption)
            # Умножаем на 1000 для перевода МПа в кПа
            gas_pressure_kpa = float(gas_pressure) * 1000
            diametr = float(diametr)

            # Вызов чистой функции расчета
            rounded_result_speed = MathMethod.calculate_speed(gas_consumption, gas_pressure_kpa, diametr)
            print(f"{round(rounded_result_speed,2)=}")

            # --- Обновление GUI с блокировкой сигналов ---
            # Отключаем сигнал перед изменением значения
            speed_line_edit.blockSignals(True)

            speed_line_edit.setText(str(rounded_result_speed))

            # Включаем сигнал после изменения значения
            speed_line_edit.blockSignals(False)

        except ValueError:
            self.ui.statusbar.showMessage("Ошибка: неверный ввод. Проверьте числовые поля.")
        except ZeroDivisionError:
            self.ui.statusbar.showMessage("Ошибка: деление на ноль.")
        except Exception as e:
            self.ui.statusbar.showMessage(f"Неизвестная ошибка: {str(e)}")

    def calculated_speed_in(self) -> None:
        """Слот, вызываемый по изменению диаметра на ВХОДЕ."""
        self.calculate_gas_speed(
            pressure=self.get_pressure("Input"),
            diametr_line_edit=self.ui.lineEdit_diametet_of_gas_pipeline,
            speed_line_edit=self.ui.lineEdit_gas_speed
        )

    def calculated_speed_out(self) -> None:
        """Слот, вызываемый по изменению диаметра на ВЫХОДЕ."""
        self.calculate_gas_speed(
            pressure=self.get_pressure("Output"),
            diametr_line_edit=self.ui.lineEdit_diametet_of_gas_pipeline_out,
            speed_line_edit=self.ui.lineEdit_gas_speed_out
        )

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

        for i in saddle.split():
            if self.is_int(i):
                saddle=i
        
        #name_devace+="/"+saddle

        if self.saved_conf_left_to_right:
            name_devace+='-01'
        
        if self.saved_conf_PZK_position_sensor:
            name_devace+=' Д'

        self.data_found_id+=1
        self.data_found[self.data_found_id] = {"Регулятор":name_devace,
                                               "Седло":saddle,
                                               "Пропускная":found_bandwidth,
                                               "Необходимая":need_bandwidth,
                                               "Процент":"{:.2f}".format(100-(((int(found_bandwidth)-int(need_bandwidth))/int(found_bandwidth))*100))}
        
    def select_product_type(self) -> None:
        """
        Метод для обработки выбора типа изделия (ГРПБ, ГРПШ, ГРУ).
        Собирает данные о выбранном типе изделия и сохраняет их.
        """
        print(1)
        # # Получаем выбранный тип изделия из комбо-бокса
        selected_product = self.ui.comboBox_product_type.currentText()
        # #
        # # # Сохраняем информацию о выбранном типе изделия
        self.selected_product_type = selected_product
        #
        # # Собираем дополнительную информацию о конфигурации газового оборудования
        gas_equipment_config = {
            "Тип изделия": selected_product,
            "Количество рабочих линий": self.get_count_work_line(),
            "Количество резервных линий": self.get_backup_lines(),
            "Наличие съемной резервной линии": self.get_removable_backup_line(),
            "Исполнение по СТО ГПРГ": self.get_sto_gprg_execution(),
            "Обогрев": self.get_heating_type(),
            "Телеметрия": self.get_telemetry_type(),
            "Климатическое исполнение": self.get_climate_execution(),
            "Оснащение УИРГ": self.get_uirg_equipment_type(),
            "Количество выходов газопроводов": self.get_number_of_gas_pipeline_outlets(),
            "Диаметр запорной арматуры на входе": self.get_valve_diameter("Input"),
            "Диаметр запорной арматуры на выходе": self.get_valve_diameter("Output"),
            "Направление": self.get_direction_type()
        }

        # # Сохраняем всю конфигурацию
        self.gas_equipment_config = gas_equipment_config
        #
        # # Выводим сообщение в строке состояния
        # self.ui.statusbar.showMessage(f"Выбран тип изделия: {selected_product}", 3000)

        print(f"{gas_equipment_config=}")
        self.search_file_name()

        
        # Здесь можно добавить дополнительную логику обработки выбранного типа изделия
        # Например, изменение интерфейса в зависимости от выбранного типа

    def search_file_name(self):
        """
            Формирует номенклатурную строку изделия (например, ГРПШ_РДНК-50-400(1000)_1-1_0_4_0_0_У1_0_1_50-50_Л-П)
            на основе словаря self.gas_equipment_config.
            """

        # ПРОВЕРКА: Проверка наличия и заполненности словаря
        if not hasattr(self, 'gas_equipment_config') or not self.gas_equipment_config:
            # В случае ошибки возвращаем пустую строку
            return ""

        # Получаем конфигурацию
        config: Dict[str, Any] = self.gas_equipment_config

        # -----------------------------------------------------------
        # 2.1. Расчетные и фиксированные части
        # -----------------------------------------------------------

        # ВАЖНО: Модель регулятора (например, РДНК-50-400(1000)) должна быть определена
        # в другом месте (после подбора) и сохранена, например, в self.regulator_model_name.
        regulator_part = "РДНК-50-400(1000)"

        # -----------------------------------------------------------
        # 2.2. Преобразование значений из словаря в кодовые части
        # -----------------------------------------------------------

        # 1. Тип изделия: ГРПШ
        product_type = str(config.get("Тип изделия", ""))

        # 2. Блок линий: 1-1_0 (рабочие-резервные_съемная)
        working_lines = str(config.get("Количество рабочих линий", 0))
        reserve_lines = str(config.get("Количество резервных линий", 0))
        removable_reserve = str(config.get("Наличие съемной резервной линии", 0))
        lines_block = f"{working_lines}-{reserve_lines}_{removable_reserve}"

        # 3. Исполнение по СТО: 4
        sto_gprg_full = str(config.get("Исполнение по СТО ГПРГ", "0"))


        # 4. Обогрев: 0
        heating_value = str(config.get("Обогрев", "0"))

        # 5. Телеметрия: 0
        telemetry_value = str(config.get("Телеметрия", "0"))

        # 6. Климатическое исполнение: У1
        climate_code = str(config.get("Климатическое исполнение", "У1"))

        # 7. Оснащение УИРГ: 0
        uirg_equipment_full = str(config.get("Оснащение УИРГ", "0"))

        # 8. Количество выходов: 1
        gas_outputs = str(config.get("Количество выходов газопроводов", 1))

        # 9. Диаметры: 50-50
        valve_diameter_in = str(config.get("Диаметр запорной арматуры на входе", "НД"))
        valve_diameter_out = str(config.get("Диаметр запорной арматуры на выходе", "НД"))
        diameters_block = f"{valve_diameter_in}-{valve_diameter_out}"

        # 10. Направление: Л-П
        direction_value = str(config.get("Направление", "Л-П"))

        # -----------------------------------------------------------
        # 3. Сборка финальной строки в нужной последовательности
        # -----------------------------------------------------------

        parts = [
            product_type,
            regulator_part,
            lines_block,
            sto_gprg_full,
            heating_value,
            telemetry_value,
            climate_code,
            uirg_equipment_full,
            gas_outputs,
            diameters_block,
            direction_value
        ]

        # Объединяем все части через разделитель "_"
        print("_".join(map(str, parts)))
        stri = "_".join(map(str, parts))

        selected_product = stri.split("_")[0]
        regulator = (stri.split("_")[1]).split("-")[0]
        print(selected_product, regulator)



        # 1. Объединение частей пути с помощью оператора /
        # Python сам поставит нужный разделитель: '\' для Windows или '/' для Linux/Mac.
        folder = "Каталог"
        sub_folder = selected_product
        sub_sub_folder = regulator
        file_name = stri + ".cdw"

        file_path = Path(folder) / sub_folder /sub_sub_folder/ file_name

        print(f"Путь: {file_path}")

        # 2. Объединение с текущим рабочим каталогом
        full_path = Path.cwd() / file_path
        print(f"Полный путь: {full_path}")

        current_text = self.ui.plainTextEdit_2.toPlainText()
        new_text = current_text + "\n" + self.__split_and_insert_newline(str(full_path))
        self.ui.plainTextEdit_2.setPlainText(new_text)
        if full_path.exists():

            print(f"Путь существует: {full_path}")

        else:
            print(f"Путь не существует: {full_path}")

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
        # self.saved_conf_Regulator_for_liquefied_gas = self.ui.Regulator_for_liquefied_gas.isChecked()

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
                                                if int(row_scr[i_cell]) >= bandwidth and ((("Ж" in name_devace) or ("ж" in name_devace)) == self.saved_conf_Regulator_for_liquefied_gas):
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

        return regulators_found

    def conduct_analysis(self, workbook:str,
                         inlet_pressure:float, 
                         output_pressure:float, 
                         traffic_capacity:float) -> int:
        """Функция conduct_analysis, распарсивает экселевский файл
        и ищет подходящие ячейки по входным данным.
        Возвращает колличество найденных девайсов в файле."""

        regulators_found = 0
        print(workbook.sheetnames)
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            
            if sheet["C1"].value == "" or sheet["C1"].value == None:
                regulators_found+=self.search_one_controller_table_algorithm(inlet_pressure,output_pressure,traffic_capacity,sheet)
            else:
                regulators_found+=self.search_several_controller_table_algorithm(inlet_pressure,output_pressure,traffic_capacity,sheet)

            
        return regulators_found

    def replacement_button_pressed(self) -> None:
        """
        """
        regulators_found = 0
        filename_log = False
        print("Зашли в функцию")
        listbox_data = self.drop_area.get_file_paths()
        print("Получили файл")
        self.processed_urls = {}

        self.__create_path_folder_for_save()
        print("Создали директорию по созданию отчета")

        for index in range(len(listbox_data)):
            if os.path.splitext(listbox_data[index])[1] == '.xlsx':
                self.processed_urls[listbox_data[index]] = 0
        print("Анализ файла первичный")

        if len(self.processed_urls) == 0:
            self.show_error_message("Добавьте файлы xlsx")
            return
        print("На случай недобавленых файлов")
        
        if not self.is_int(self.ui.max_lebel_loading_range.text()) or not self.is_int(self.ui.min_lebel_loading_range.text()):
            self.show_error_message("Некорректный диапазон процента загрузки")
            return

        print("Некорректный диапазон процента загрузки")

        #Очищаем виджет с результатами сканирования в самой программе
        self.__clear_widget_res_in_app()

        print("Очистили виджет результатов")

        for path_file, _ in self.processed_urls.items():
            try:
                if path_file.replace(" ", "") != "":

                    try:
                        PIn = self.get_pressure("Input")
                        POt = self.get_pressure("Output")
                        bandwidth = self.get_bandwidth()
                        print(PIn,POt,bandwidth)
                    except:
                        self.show_error_message("Введите корректные значения для поиска регулятора")
                        return 

                    self.__save_patch_in_conf(path_file)
                    print("Начали поиск")
                    #self.show_info_message(str("Поиск подходящего регулятора запущен"))
                    self.status_text = "В работе"
                    self.update_status_worck("В работе.")
                    print("Проверка входных условий")
                    if PIn != "" and POt!="" and bandwidth!="":

                        ##Вот тут ошибка
                        self.__saved_conf_search()
                        ###

                        #Открываем файл экселя
                        workbook = openpyxl.load_workbook(os.path.normpath(path_file))
                        print("Открыли файл екселя")
                        #Если не был создан файл логов, создаём его
                        if not filename_log:
                            filename_log = self.__res_file_name()
                            self.logger = FileWriter(filename_log)
                            self.logger.open_file()

                        #Пишем в файл лога стартовые данные поиска
                        self.start_initial_log()
                        print("Записали в файл лога стартовые данные поиска")
                        #Запуск функции анализа

                        regulators_found += self.conduct_analysis(workbook, 
                                                                PIn,
                                                                POt, 
                                                                bandwidth)
                        print("Проверка найнедых количества регуляторов")
                        if regulators_found == 0:
                            self.__write_log_wrapper("Точного совпадения не найдено")
                            self.__write_log_wrapper("Попытка найти регулятор с близкими параметрами.")

                            #Находим ближайшие допустимые значения
                            #finding_real_value = FoundCorValue(workbook,PIn,POt)
                            #PIn,POt = finding_real_value()

                            regulators_found += self.conduct_analysis(workbook, 
                                                                PIn,
                                                                POt, 
                                                                bandwidth)
                                

                        if regulators_found == 0:
                            self.__write_log_wrapper("Регуляторы с необходимыми параметрами не найдены.")
                        else:
                            self.__write_log_wrapper("======================")
                            self.__write_log_wrapper("Выполнен поиск и найдены регуляторы по входному: {0} и выходному {1} давлению.".format(PIn,POt))
                            self.__write_log_wrapper("")
                            self.write_log_found_reg()

                        #self.show_info_message("В файле {0} исправлено: {1} некорректных записей с кириллицей.".format(worck_patch,str(number_change),))
                        self.__write_log_wrapper("!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-")
                        self.__write_log_wrapper("В файле {0} найдено {1} подходящих регуляторов.".format(path_file,len(self.list_in_range_value)))
                        self.__write_log_wrapper("!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!--!")
                        
                        self.__clear_data_found_device()
                    else:
                        self.show_error_message("Введите все входные данные!")
            except:
                self.show_error_message(f"Критическая ошибка анализай файла - {path_file}")


        # Закрытие логгера
        self.logger.close_file()

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
        sys.exit(self.app.exec_())
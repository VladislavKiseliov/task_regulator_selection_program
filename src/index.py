import tkinter as tk
import shutil
import openpyxl
import os
import tkinter.ttk as ttk
import itertools
import subprocess
import json
import math
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from src.DropArea import *
from src.mainwindow import Ui_MainWindow
from src.FoundCorValue import FoundCorValue
from src.MiniFunc import *
from src.MyLogger import *

from decimal import Decimal
from tkinter import messagebox, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from openpyxl_image_loader import SheetImageLoader

class SelRegulator:
    def __init__(self):
        self.list_in_range_value = []
        self.file_path_list = []
        self.data = {}
        self.data_found = {}
        self.data_found_id = 0

        self.data_conf = {"Path":{}}
        self.status_animation = itertools.cycle(["В работе.", "В работе..", "В работе..."])

        self.__conf_file_loader()
        self.__create_path_folder_for_save()

        self.app = QtWidgets.QApplication(sys.argv)
        self.MainWindow = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.MainWindow)

        self.__drop_area_create();
        self.__connect_config();

    def __connect_config(self) -> None:
        self.ui.select_button.clicked.connect(self.replacement_button_pressed) #Коннект на нажатие кнопки подбора регулятора
        self.ui.open_button.clicked.connect(self.__open_file_dialog) #Коннект на нажатие кнопки подбора регулятора
        self.ui.remove_button.clicked.connect(self.drop_area.remove_selected_file) #Коннект на нажатие кнопки подбора регулятора
        self.ui.open_folder_button.clicked.connect(self.folder_save_open) # Коннект на нажатие кнопки открытия папки сохранения логов

        #Подключение событий изменения текста в полях калькулятора
        self.ui.lineEdit_gas_consumption.textChanged.connect(self.on_gas_consumption_changed)
        self.ui.lineEdit_gas_pressure.textChanged.connect(self.on_gas_consumption_changed)
        # self.ui.lineEdit_gas_speed.textChanged.connect(self.on_gas_consumption_changed)
        self.ui.lineEdit_diametet_of_gas_pipeline.editingFinished.connect(self.determine_calculation_method)


    def determine_calculation_method(self):
        gas_consumption = self.ui.lineEdit_gas_consumption.text()

        if gas_consumption == "":
            self.calculate_gas_consumption("")
        else:
            self.calculate_pressure_and_speed("")
    
    def on_gas_consumption_changed(self, text):
        try:
            gas_consumption = self.ui.lineEdit_gas_consumption.text()
            gas_pressure = self.ui.lineEdit_gas_pressure.text()

            if not gas_consumption or not gas_pressure:
                return

            gas_consumption = float(gas_consumption)
            gas_pressure = float(gas_pressure)

            if gas_pressure < 50:
                gas_speed = 15
            elif gas_pressure <= 600:
                gas_speed = 25
            else:
                gas_speed = 30

            # Отключаем сигнал перед изменением значения
            self.ui.lineEdit_gas_speed.blockSignals(True)
            self.ui.lineEdit_diametet_of_gas_pipeline.blockSignals(True)

            self.ui.lineEdit_gas_speed.setText(str(gas_speed))
            
            result = (0.036238) * math.sqrt(gas_consumption * 293 / (0.1 + gas_pressure / 1000) / gas_speed) * 10
            rounded_result = math.ceil(result)

            self.ui.lineEdit_gas_speed.setText(str(gas_speed))
            self.ui.lineEdit_diametet_of_gas_pipeline.setText(str(rounded_result))

            # Включаем сигнал после изменения значения
            self.ui.lineEdit_gas_speed.blockSignals(False)
            self.ui.lineEdit_diametet_of_gas_pipeline.blockSignals(False)

        except ValueError:
            self.ui.lineEdit_diametet_of_gas_pipeline.setText("Ошибка: неверный ввод")
        except ZeroDivisionError:
            self.ui.lineEdit_diametet_of_gas_pipeline.setText("Ошибка: деление на ноль")
        except Exception as e:
            self.ui.lineEdit_diametet_of_gas_pipeline.setText(f"Ошибка: {str(e)}")

    def calculate_pressure_and_speed(self, text):
        try:
            gas_consumption = self.ui.lineEdit_gas_consumption.text()
            pipeline_diameter = self.ui.lineEdit_diametet_of_gas_pipeline.text()

            if not gas_consumption or not pipeline_diameter:
                return

            gas_consumption = float(gas_consumption)
            pipeline_diameter = float(pipeline_diameter)

            if pipeline_diameter <= 0:
                self.ui.lineEdit_gas_pressure.setText("Ошибка: неверный диаметр")
                return

            gas_speed = 30

            # Формула для расчёта давления газа при данном диаметре трубопровода и скорости газа
            gas_pressure = 1000 * ((gas_consumption * 293) / ((pipeline_diameter / 0.36238) ** 2 * gas_speed) - 0.1)

            if (gas_pressure < 0):
                gas_speed = 25
                gas_pressure = 1000 * ((gas_consumption * 293) / ((pipeline_diameter / 0.36238) ** 2 * gas_speed) - 0.1)
            
            if (gas_pressure < 0):
                gas_speed = 15
                gas_pressure = 1000 * ((gas_consumption * 293) / ((pipeline_diameter / 0.36238) ** 2 * gas_speed) - 0.1)

            if(gas_pressure < 0):
                gas_pressure = "Ошибка: некорректные данные"
            else:
                gas_pressure = round(gas_pressure, 2)

            # Отключаем сигнал перед изменением значения
            self.ui.lineEdit_gas_speed.blockSignals(True)
            self.ui.lineEdit_gas_pressure.blockSignals(True)

            self.ui.lineEdit_gas_speed.setText(str(gas_speed))
            self.ui.lineEdit_gas_pressure.setText(str(gas_pressure))

            # Включаем сигнал после изменения значения
            self.ui.lineEdit_gas_speed.blockSignals(False)
            self.ui.lineEdit_gas_pressure.blockSignals(False)

        except ValueError:
            self.ui.lineEdit_gas_pressure.setText("Ошибка: неверный ввод")
            self.ui.lineEdit_gas_speed.setText("Ошибка: неверный ввод")
        except ZeroDivisionError:
            self.ui.lineEdit_gas_pressure.setText("Ошибка: деление на ноль")
            self.ui.lineEdit_gas_speed.setText("Ошибка: деление на ноль")
        except Exception as e:
            self.ui.lineEdit_gas_pressure.setText(f"Ошибка: {str(e)}")
            self.ui.lineEdit_gas_speed.setText(f"Ошибка: {str(e)}")

    def calculate_gas_consumption(self, text):
        try:
            gas_pressure = self.ui.lineEdit_gas_pressure.text()
            pipeline_diameter = self.ui.lineEdit_diametet_of_gas_pipeline.text()

            if not gas_pressure or not pipeline_diameter:
                return

            gas_pressure = float(gas_pressure)
            pipeline_diameter = float(pipeline_diameter)

            if pipeline_diameter <= 0:
                self.ui.lineEdit_gas_consumption.setText("Ошибка: неверный диаметр")
                return

            if gas_pressure < 50:
                gas_speed = 15
            elif gas_pressure <= 600:
                gas_speed = 25
            else:
                gas_speed = 30

            # Формула для расчёта расхода газа при данном давлении и диаметре трубопровода
            gas_consumption = ((pipeline_diameter / 0.36238) ** 2 * (0.1 + gas_pressure / 1000) * gas_speed) / 293


            # Отключаем сигнал перед изменением значения
            self.ui.lineEdit_gas_speed.blockSignals(True)
            self.ui.lineEdit_gas_consumption.blockSignals(True)

            self.ui.lineEdit_gas_speed.setText(str(gas_speed))
            self.ui.lineEdit_gas_consumption.setText(str(round(gas_consumption, 2)))

            # Включаем сигнал после изменения значения
            self.ui.lineEdit_gas_speed.blockSignals(False)
            self.ui.lineEdit_gas_consumption.blockSignals(False)

        except ValueError:
            self.ui.lineEdit_gas_consumption.setText("Ошибка: неверный ввод")
            self.ui.lineEdit_gas_speed.setText("Ошибка: неверный ввод")
        except ZeroDivisionError:
            self.ui.lineEdit_gas_consumption.setText("Ошибка: деление на ноль")
            self.ui.lineEdit_gas_speed.setText("Ошибка: деление на ноль")
        except Exception as e:
            self.ui.lineEdit_gas_consumption.setText(f"Ошибка: {str(e)}")
            self.ui.lineEdit_gas_speed.setText(f"Ошибка: {str(e)}")
    

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
        #Добавляем полученные пути в лайбел для путей если они доступны
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
            self.ui.statusbar.showMessage(self.status_text)

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
        name_file = "Pвх-{0} Pвых-{1} ПрСп-{2}.txt".format(self.ui.input_PIn.text(), 
                                                    self.ui.input_POt.text(), 
                                                    self.ui.input_bandwidth.text())
        
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
        
    def start_initial_log(self) -> None:
        """start_initial_log добавляет стартовые данные о сканировании в логи"""
        self.__write_log_wrapper("======================")
        self.__write_log_wrapper("Поиск регуляторов по следущим параметрам: Входное давление-{0} \
                                 Выходное давление-{1} Пропускная способность-{2}".format(self.ui.input_PIn.text(),self.ui.input_POt.text(), self.ui.input_bandwidth.text()))
        
        if self.saved_conf_left_to_right:
            direct = "справа налево"
        else:
            direct = "слева направо"

        if self.saved_conf_PZK_position_sensor:
            PZK = "есть ПЗК"
        else:
            PZK = "нету ПЗК"

        if self.saved_conf_Regulator_for_liquefied_gas:
            liquefied_gas = "Регулятор для сжиженного газа."
        else:
            liquefied_gas = "Регулятор для сетевого газа."
        
        self.__write_log_wrapper("{} Направление регулятора {}. Наличие датчика положения ПЗК: {}.".format(liquefied_gas,direct,PZK))
        

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
            #self.__write_log_wrapper("Необходимая пропускная способность с учётом +20%: {}".format(value["Необходимая"]))
            self.__write_log_wrapper("Процент загрузки пропускной спос. регулятора c необходимой пропускной способностью ({}) составляет {}%".format(value["Необходимая"],value["Процент"]))
        

    def __clear_data_found_device(self) -> None:
        """очищает списки найденных регуляторов"""
        self.list_in_range_value = []
        self.data_found = {}

    def __saved_conf_search(self) -> None:
        """Функция __saved_conf_search, сохраняет конфигурацию
        поиска устройства для отдельного запуска"""
        
        self.saved_conf_self_file_name_var = self.ui.self_file_name_var.isChecked()
        self.saved_conf_input_name_file = self.ui.input_name_file.text()
        self.saved_conf_left_to_right = self.ui.left_to_right.isChecked()
        self.saved_conf_PZK_position_sensor = self.ui.PZK_position_sensor.isChecked()
        self.saved_conf_Regulator_for_liquefied_gas = self.ui.Regulator_for_liquefied_gas.isChecked()

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
                            name_devace = sheet[get_excel_column(i_cell+1)+"1"].value
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

        listbox_data = self.drop_area.get_file_paths()
        self.processed_urls = {}



        for index in range(len(listbox_data)):
            print(listbox_data[index])
            if os.path.splitext(listbox_data[index])[1] == '.xlsx':
                self.processed_urls[listbox_data[index]] = 0

        print(listbox_data)
        print(self.processed_urls)

        if len(self.processed_urls) == 0:
            self.show_error_message("Добавьте файлы xlsx")
            return
        
        if not self.is_int(self.ui.max_lebel_loading_range.text()) or not self.is_int(self.ui.min_lebel_loading_range.text()):
            self.show_error_message("Некорректный диапазон процента загрузки")
            return
        
        #Очищаем виджет с результатами сканирования в самой программе
        self.__clear_widget_res_in_app()

        for path_file, _ in self.processed_urls.items():
            if path_file.replace(" ", "") != "":

                try:
                    PIn = float(self.ui.input_PIn.text().replace(",", '.').replace(" ", ''))
                    POt = float(self.ui.input_POt.text().replace(",", '.').replace(" ", ''))
                    bandwidth = float(self.ui.input_bandwidth.text().replace(",", '.'.replace(" ", '')))
                except:
                    self.show_error_message("Введите корректные значения для поиска регулятора")
                    return 

                self.__save_patch_in_conf(path_file)

                #self.show_info_message(str("Поиск подходящего регулятора запущен"))
                self.status_text = "В работе"
                self.update_status_worck("В работе.")

                if PIn != "" and POt!="" and bandwidth!="":
                    self.__saved_conf_search()

                    #Открываем файл экселя
                    workbook = openpyxl.load_workbook(os.path.normpath(path_file))

                    #Если не был создан файл логов, создаём его
                    if not filename_log:
                        filename_log = self.__res_file_name()
                        self.logger = FileWriter(filename_log)
                        self.logger.open_file()

                    #Пишем в файл лога стартовые данные поиска
                    self.start_initial_log()
                    #Запуск функции анализа

                    regulators_found += self.conduct_analysis(workbook, 
                                                              PIn,
                                                              POt, 
                                                              bandwidth)

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
                    self.__write_log_wrapper("!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-")
                    
                    self.__clear_data_found_device()
                else:
                    self.show_error_message("Введите все входные данные!")

        # Закрытие логгера
        self.logger.close_file()

        self.update_status_worck("Ожидание работы")
        # Открытие файла в который записаны данные
        #subprocess.Popen(["notepad.exe", filename_log])
        #subprocess.Popen(f'explorer "{os.path.normpath(os.path.dirname(path_file))}"')

    def __core_render(self) -> None:
        """Функция __core_render, производит отрисовку
        основных элементов и фреймов"""
        self.status_frame = ttk.Frame(self.root, style="TFrame")
        self.status_frame.pack(fill=tk.X, side=tk.TOP)
        self.status_label = ttk.Label(self.status_frame, text="Ожидание работы", style="TLabel")
        self.status_label.pack(pady=10)
        

        self.update_status_worck("Ожидание работы")

        self.frame = ttk.Frame(self.root, style="TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)

        self.__create_menu()
        self.__drop_zone_render()

        #Добавляем в дроп зону пути из сохранений
        self.__add_load_save_path()

        self.in_data_frame = ttk.Frame(self.root, style="TFrame")
        self.in_data_frame.pack(side=tk.RIGHT,anchor="n", expand=True)

        self.__input_data_render()
        self.__button_render()

    def __create_menu(self):
        """Функция __create_menu, производит отрисовку
        верхнего меню"""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label="Открыть", command=self.open_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Выход", command=self.root.quit)

        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.help_menu.add_command(label="О программе", command=self.show_about)

        self.menubar.add_cascade(label="Файл", menu=self.file_menu)
        self.menubar.add_cascade(label="Помощь", menu=self.help_menu)

    def open_file(self):
        """Функция open_file, привязана
        к кнопке верхнего меню (окрыть)"""
        self.__open_file_dialog()
        # Логика открытия файла

    def show_about(self):
        """Функция show_about, привязана
        к кнопке верхнего меню (о программе)"""
        # Логика отображения информации о программе
        about_window = tk.Toplevel(self.root)
        about_window.title("О программе")
        about_window.geometry("800x600")
        try:
            about_window.iconbitmap("icon.ico")
        except:
            pass
        self.style.configure("Custom.TLabel", font=("Times New Roman", 12), background="white")
        
        text_widget = tk.Text(about_window, height=30, width=95)
        text_widget.pack()

        text="Программа подбора регулятора принимает 3 входных параметра: входное давление,\nвыходное давление в МПа и пропускную способность. Для поиска регулятора\nнеобходимо добавить файл в формате xlsx содержащий следующую структуру и данные:\nКаждая новая таблица на отдельном листе. \nЯчейка A1-название регулятора.\nЯчейка В1 седло регулятора. \nА2 размерность выходного давление.\nВ2 размерность выходного давления.\nА4-Аn единицы выходного давления.\nВ3-(N)3 единицы выходного давления.\nЭтапы работы с программой:\n1)Ввести параметры необходимого регулятора.\nЕсли нужно своё название файла результата анализа, \nпоставить флажок 'Своё название результирующего файла' и ввести необходимое название. \n2)Перетащить таблицу формата xlsx с данными о регуляторах в дроп-зону. \nЛибо используя кнопку 'Открыть файл'.\n3)Нажать кнопку 'Подобрать регулятор'.\n4)После того как программа завершить работу, откроется файл с проведённым анализом."

        text_widget.insert(tk.END, text)
        text_widget.config(state=tk.DISABLED)

        text_widget.pack(pady=20)

        close_button = ttk.Button(about_window, text="Закрыть", command=about_window.destroy)
        close_button.pack()

    def __drop_zone_render(self) -> None:
        """Функция __drop_zone_render, рендер
        дроп зоны и виджета статуса работы"""        
        self.lb = tk.Listbox(self.frame, width=30, height=5)
        self.lb.insert(1, "Перетащите xlsx таблицу с данными о регуляторах")
        self.lb.configure(justify=tk.CENTER)
        self.lb.drop_target_register(DND_FILES)
        self.lb.dnd_bind('<<Drop>>', self.__file_placed_drop_zone)
        self.lb.pack(fill=tk.BOTH, expand=True, side=tk.TOP)


        #Виджет отображения результатов поиска 
        self.text_widget_res = tk.Text(self.frame, height=30, width=67)
        self.text_widget_res.pack()

        text="Ожидание начала подбора..."

        self.text_widget_res.insert(tk.END, text)
        self.text_widget_res.config(state=tk.DISABLED)

        self.text_widget_res.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM)

    def __input_data_render(self) -> None:
        """Функция __input_data_render, рендер
        элементов ввода и конфигурации поиска регулятора"""  
                
        self.label_PIn = ttk.Label(self.in_data_frame, text="Входное давление - Рвх МПа:", style="TLabel")
        self.label_PIn.grid(row=0, column=0, pady=3)

        self.input_PIn = ttk.Entry(self.in_data_frame)
        self.input_PIn.grid(row=1, column=0,sticky="ew",padx=(10))

        self.label_POt = ttk.Label(self.in_data_frame, text="Выходное давление - Рвых МПа:", style="TLabel")
        self.label_POt.grid(row=2, column=0, pady=3)

        self.input_POt = ttk.Entry(self.in_data_frame)
        self.input_POt.grid(row=3, column=0,sticky="ew",padx=(10))

        self.label_bandwidth = ttk.Label(self.in_data_frame, text="Пропускная способность", style="TLabel")
        self.label_bandwidth.grid(row=4, column=0, pady=3)

        self.input_bandwidth = ttk.Entry(self.in_data_frame)
        self.input_bandwidth.grid(row=5, column=0, pady=(0,10),sticky="ew",padx=(10))
        
        #Показать регуляторы с загрузкой от - до
        self.lebel_loading_range = ttk.Label(self.in_data_frame, text="Диапазон процента загрузки:", style="TLabel")
        self.lebel_loading_range.grid(row=6, column=0, pady=3)

        self.frame_loading_range = ttk.Frame(self.in_data_frame, style="TFrame")
        self.frame_loading_range.grid(row=7, column=0, pady=3)

        self.min_lebel_loading_range = ttk.Label(self.frame_loading_range, text="Min % :", style="TLabel")
        self.min_lebel_loading_range.pack(side="left")

        self.minimum_load = ttk.Entry(self.frame_loading_range, width=10)
        self.minimum_load.pack(side="left")
        self.minimum_load.insert(0, "20")

        self.max_lebel_loading_range = ttk.Label(self.frame_loading_range, text="- Max % :", style="TLabel")
        self.max_lebel_loading_range.pack(side="left")

        self.maximum_load = ttk.Entry(self.frame_loading_range, width=10)
        self.maximum_load.pack(side="left")
        self.maximum_load.insert(0, "100")
        ###

        self.label_name = ttk.Label(self.in_data_frame, text="Название файла:", style="TLabel")
        self.label_name.grid(row=8, column=0, pady=(20,0))

        self.self_file_name_var = tk.BooleanVar()
        self.checkbox = ttk.Checkbutton(self.in_data_frame, text="Своё название результирующего файла", variable=self.self_file_name_var, style="TCheckbutton")
        self.checkbox.grid(row=9, column=0, pady=(0,10),sticky="ew",padx=(10))

        self.input_name_file = ttk.Entry(self.in_data_frame)
        self.input_name_file.grid(row=10, column=0, pady=(0,10),sticky="ew",padx=(10))

        self.left_to_right = tk.BooleanVar()
        self.checkbox = ttk.Checkbutton(self.in_data_frame, text="Регуляторы справа налево\n (по умолчанию слева направо)", variable=self.left_to_right, style="TCheckbutton")
        self.checkbox.grid(row=11, column=0, pady=(0,10),sticky="ew",padx=(10))

        self.PZK_position_sensor = tk.BooleanVar()
        self.checkbox = ttk.Checkbutton(self.in_data_frame, text="Датчик положения ПЗК", variable=self.PZK_position_sensor, style="TCheckbutton")
        self.checkbox.grid(row=12, column=0, pady=(0,10),sticky="ew",padx=(10))

        self.Regulator_for_liquefied_gas = tk.BooleanVar()
        self.checkbox = ttk.Checkbutton(self.in_data_frame, text="Регулятор для сжиженного газа", variable=self.Regulator_for_liquefied_gas, style="TCheckbutton")
        self.checkbox.grid(row=13, column=0, pady=(0,10),sticky="ew",padx=(10))

    def __button_render(self) -> None:
        """Функция __button_render, рендер
        рабочих кнопок""" 
        self.select_button = ttk.Button(self.in_data_frame, text="Подобрать регулятор", command=self.replacement_button_pressed, style="TButton")
        self.select_button.grid(row=14, column=0, pady=5)

        self.open_button = ttk.Button(self.in_data_frame, text="Загрузить файл", command=self.__open_file_dialog, style="TButton")
        self.open_button.grid(row=15, column=0, pady=5)

        self.remove_button = ttk.Button(self.in_data_frame, text="Удалить", command=self.remove_button_pressed, style="TButton")
        self.remove_button.grid(row=16, column=0, pady=5)

        self.open_folder_button = ttk.Button(self.in_data_frame, text="Открыть папку логов", command=self.folder_save_open, style="TButton")
        self.open_folder_button.grid(row=17, column=0, pady=5)

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
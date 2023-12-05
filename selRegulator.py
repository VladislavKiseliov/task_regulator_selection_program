"""
# Документация для программы selRegulator 
 
Программа  selRegulator  предназначена для помощи пользователям в выборе подходящих 
регуляторов на основе заданных параметров и анализа данных в файлах Excel. 
Она обеспечивает графический пользовательский интерфейс (GUI) для удобного 
взаимодействия и использует различные библиотеки, такие как  tkinter ,  
openpyxl ,  docx  и другие, для выполнения своих функций. 
 
## Возможности 
 
1. Функция перетаскивания файлов: 
   - Пользователи могут перетаскивать файлы Excel (.xlsx) в программу для анализа. 
 
2. Входные параметры: 
   - Пользователи могут вводить следующие параметры для анализа: 
     - Входное давление (PIn): давление на входе в МПа. 
     - Выходное давление (POt): желаемое давление на выходе в МПа. 
     - Пропускная способность: требуемая пропускная способность. 
 
3. Поиск и анализ: 
   - Программа анализирует файлы Excel на основе заданных параметров и ищет подходящие регуляторы. 
   - Она проверяет диапазоны входного и выходного давления в файле Excel, чтобы найти соответствующие регуляторы. 
   - Если найдено совпадение, программа регистрирует соответствующую информацию, включая название регулятора, седло и пропускную способность. 
 
4. Журналирование и результаты: 
   - Программа генерирует файл журнала с результатами анализа, включая найденные регуляторы и их подробности. 
   - После завершения анализа файл журнала открывается автоматически. 
 
## Использование 
 
1. Запуск программы: 
   - Запустите программу, и появится графический пользовательский интерфейс (GUI). 
 
2. Ввод параметров: 
   - Введите значения входного давления (PIn), выходного давления (POt) и пропускной способности в соответствующие поля ввода. 
 
3. Перетаскивание файлов Excel: 
   - Перетащите файлы Excel (.xlsx), содержащие данные о регуляторах, в программу. 
   - Программа проанализирует файлы на основе заданных параметров. 
 
4. Анализ и просмотр результатов: 
   - Нажмите кнопку "Подобрать регулятор", чтобы начать анализ. 
   - Программа будет искать подходящие регуляторы на основе заданных параметров. 
   - Результаты будут отображены в текстовой области, а также будет сгенерирован файл журнала с подробной информацией. 
 
5. Просмотр файла журнала: 
   - После завершения анализа файл журнала откроется автоматически. 
   - Файл журнала содержит информацию о найденных регуляторах и их подробностях. 
 
## Зависимости 
 
Программа  selRegulator  зависит от следующих библиотек: 
-  tkinter : для создания графического пользовательского интерфейса. 
-  openpyxl : для работы с файлами Excel (.xlsx). 
-  docx : для работы с документами Word (.docx). 
-  tkinterdnd2 : для реализации функции перетаскивания файлов в tkinter. 
 
Пожалуйста, убедитесь, что эти библиотеки установлены перед запуском программы. 
 
## Ограничения 
 
- Программа в настоящее время поддерживает только файлы Excel (.xlsx) для анализа. 
- Программа предполагает определенную структуру в файлах Excel, как указано в документации кода. 
- Программа разработана для конкретного случая использования и может не подходить для других сценариев без модификаций. 
 
## Заключение 
 
Программа  selRegulator  предоставляет удобный интерфейс для анализа файлов Excel и выбора 
подходящих регуляторов на основе заданных параметров. Она автоматизирует процесс поиска и 
регистрации соответствующей информации, что упрощает выполнение задач анализа для пользователей.


Для корректной работы openpyxl_image_loader в файле библиотеки: sheet_image_loader.py

import io
import string
import openpyxl
from PIL import Image

class SheetImageLoader:
    _images = {}
    def __init__(self, sheet):
        sheet_images = sheet._images
        for image in sheet_images:
            row = image.anchor._from.row + 1
            col = openpyxl.utils.cell.get_column_letter(image.anchor._from.col + 1)
            self._images[f'{col}{row}'] = image._data
    def image_in(self, cell):
        return cell in self._images
    def get(self, cell):
        if cell not in self._images:
            raise ValueError("Cell {} doesn't contain an image".format(cell))
        else:
            image = io.BytesIO(self._images[cell]())
            return Image.open(image)


Для сборки в exe 
Добавить файл https://github.com/pmgagne/tkinterdnd2/blob/master/hook-tkinterdnd2.py в 
папку откуда запускается pyinstaller. И запустить через команду:
pyinstaller --windowed --onefile --icon=icon.ico selRegulator.py --additional-hooks-dir=.
"""

import tkinter as tk
import shutil
import openpyxl
import os
import tkinter.ttk as ttk
import itertools
import subprocess
import json
import math
import hashlib

from MyLogger import *
from decimal import Decimal
from tkinter import messagebox, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from openpyxl_image_loader import SheetImageLoader

def calculate_hash(string:str) -> str:
    # Создаем объект хеша
    hash_object = hashlib.sha256()

    # Обновляем хеш с данными из строки
    hash_object.update(string.encode('utf-8'))

    # Получаем хеш-сумму в виде шестнадцатеричной строки
    hash_string = hash_object.hexdigest()

    return hash_string

class selRegulator:
    def __init__(self):
        self.file_path_list = []
        self.data = {}
        self.data_found = {}
        self.data_found_id = 0

        self.__create_path_folder_for_save()
        self.__conf_file_loader()



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

            data_for_writte = {"Path":{}}

            # Проверка существования папки и создание, если не существует
            if not os.path.exists(self.conf_file_path):
                with open(self.conf_file_path, 'w') as file:
                    json.dump(data_for_writte, file)
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
        """Сохраняем путь в файл конфигурации"""
        try:
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



    def get_excel_column(self, index:int) -> str:
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
        """Функция для очистки результата работы программы в виджете"""
        self.text_widget_res.config(state=tk.NORMAL)  # Установка состояния виджета в NORMAL
        self.text_widget_res.delete('1.0', tk.END)
        self.text_widget_res.config(state=tk.DISABLED)  # Возвращение состояния виджета
        self.root.update()

    def __write_log_wrapper(self, mess:str) ->None:
        """Функция для добавления данных в виджет логирования в программе"""
        self.text_widget_res.config(state=tk.NORMAL)  # Установка состояния виджета в NORMAL
        self.text_widget_res.insert(tk.END, "\n"+self.__split_and_insert_newline(mess))
        self.text_widget_res.config(state=tk.DISABLED)  # Возвращение состояния виджета

        self.logger.write_log(mess)
        self.root.update()

    def show_error_message(self, text_err:str) -> None:
        """Функция show_error_message выводит сообщение об ошибке с заданным текстом
        в виде диалогового окна."""

        messagebox.showerror("Ошибка", text_err)

    def show_warning_message(self, text_war:str) -> None:
        """Функция show_warning_message выводит сообщение (Внимание!) с заданным текстом
        в виде диалогового окна."""

        messagebox.showwarning("Внимание!", text_war)

    def show_info_message(self, text_war:str) -> None:
        """Функция show_info_message выводит дочернее окно (Внимание!) с заданным текстом
        в виде диалогового окна."""

        top = tk.Toplevel()
        top.title("Внимание!")
        label = tk.Label(top, text=text_war)
        label.pack(padx=20, pady=20)
        button = tk.Button(top, text="OK", command=top.destroy)
        button.pack(pady=10)
        top.update()

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

    def status_worck_cycle(self) -> None:
        """Функция status_worck_cycle, обновляет статус работы. 
        Если статус содержит текст "В работе", то функция обновляет 
        метку статуса и получает следующий элемент анимации статуса. 
        Затем функция вызывает саму себя через 500 миллисекунд, 
        чтобы продолжить цикл работы. Если статус не содержит текст 
        "В работе", то функция просто обновляет метку статуса."""

        if "В работе" in self.status_text:
            self.status_label.config(text=self.status_text)
            self.status_text = next(self.status_animation)
            self.status_frame.after(500, self.status_worck_cycle)
        else:
            self.status_label.config(text=self.status_text)

    def update_status_worck(self, status_text) -> None:
        """Функция update_status_worck, является обёрткой
        над функцией status_worck_cycle. Позволяя корректно 
        останавливать самовызов этой функции"""
        self.status_text = status_text
        self.status_worck_cycle()

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

    def __open_file_dialog(self) -> None:
        """Функция __open_file_dialog, отвечает
        за загрузку файла через контекстный
        диалог через проводник"""


        file_path = filedialog.askopenfilename(filetypes=[("All Files", "*"),
                                                        ("Excel Files", "*.xlsx"),
                                                          ("Doc Files",  "*.doc", ),
                                                          ("Docx File",  "*.docx")])
        if file_path:
            self.lb.insert(tk.END, file_path)

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
        name_file = "Pвх-{0} Pвых-{1} ПрСп-{2}.txt".format(self.input_PIn.get(), 
                                                    self.input_POt.get(), 
                                                    self.input_bandwidth.get())
        
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
        #Очищаем виджет с результатами сканирования в самой программе
        self.__clear_widget_res_in_app()

        self.__write_log_wrapper("======================")
        self.__write_log_wrapper("Поиск регуляторов по следущим параметрам: Входное давление-{0} Выходное давление-{1} Пропускная способность-{2}".format(self.input_PIn.get(),self.input_POt.get(), self.input_bandwidth.get()))
        
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
        
        self.saved_conf_self_file_name_var = self.self_file_name_var.get()
        self.saved_conf_input_name_file = self.input_name_file.get()
        self.saved_conf_left_to_right = self.left_to_right.get()
        self.saved_conf_PZK_position_sensor = self.PZK_position_sensor.get()
        self.saved_conf_Regulator_for_liquefied_gas = self.Regulator_for_liquefied_gas.get()

        self.saved_conf_minimum_load = int(self.minimum_load.get())
        self.saved_conf_maximum_load =  int(self.maximum_load.get())
    
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
                        name_devace = sheet[self.get_excel_column(i_cell+1)+"1"].value
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
                            name_devace = sheet[self.get_excel_column(i_cell+1)+"1"].value
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

    def conduct_analysis(self, file_path:str,
                         inlet_pressure:float, 
                         output_pressure:float, 
                         traffic_capacity:float) -> int:
        """Функция conduct_analysis, распарсивает экселевский файл
        и ищет подходящие ячейки по входным данным.
        Возвращает колличество найденных девайсов в файле."""

        regulators_found = 0
        workbook = openpyxl.load_workbook(file_path)
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            
            if sheet["C1"].value == "" or sheet["C1"].value == None:
                regulators_found+=self.search_one_controller_table_algorithm(inlet_pressure,output_pressure,traffic_capacity,sheet)
            else:
                regulators_found+=self.search_several_controller_table_algorithm(inlet_pressure,output_pressure,traffic_capacity,sheet)

            
        return regulators_found

    def replacement_button_pressed(self) -> None:
        """Функция для поиска и исправления кириллицы 
        в тегах файлов формата docx. Функция принимает путь к файлу 
        и маркер тега в виде цифрового ID. Если файлы не являются форматом 
        docx или doc, то выводится сообщение об ошибке. Если маркер тега не указан, 
        то также выводится сообщение об ошибке. После исправления кириллицы 
        в тегах, функция выводит количество исправленных записей и записывает 
        лог в файл.
        """
        regulators_found = 0
        filename_log = False
        listbox_data = self.lb.get(0, tk.END)
        self.processed_urls = {}

        for index in range(1, len(listbox_data)):
            if os.path.splitext(listbox_data[index])[1] == '.xlsx':
                self.processed_urls[listbox_data[index]] = 0

        if len(self.processed_urls) == 0:
            self.show_error_message("Добавьте файлы xlsx")
            return
        
        if not self.is_int(self.maximum_load.get()) or not self.is_int(self.minimum_load.get()):
            self.show_error_message("Некорректный диапазон процента загрузки")
            return

        for path_file, _ in self.processed_urls.items():
            if path_file.replace(" ", "") != "":

                try:
                    PIn = float(self.input_PIn.get().replace(",", '.').replace(" ", ''))
                    POt = float(self.input_POt.get().replace(",", '.').replace(" ", ''))
                    bandwidth = float(self.input_bandwidth.get().replace(",", '.'.replace(" ", '')))
                except:
                    self.show_error_message("Введите корректные значения для поиска регулятора")
                    return 

                self.__save_patch_in_conf(path_file)

                #self.show_info_message(str("Поиск подходящего регулятора запущен"))
                self.status_text = "В работе"
                self.update_status_worck("В работе.")

                if PIn != "" and POt!="" and bandwidth!="":
                    self.__saved_conf_search()

                    #Если не был создан файл логов, создаём его
                    if not filename_log:
                        filename_log = self.__res_file_name()
                        self.logger = FileWriter(filename_log)
                        self.logger.open_file()

                    #Пишем в файл лога стартовые данные поиска
                    self.start_initial_log()
                    #Запуск функции анализа
                    regulators_found += self.conduct_analysis(os.path.normpath(path_file), 
                                                              PIn,
                                                              POt, 
                                                              bandwidth)

                    if regulators_found == 0:
                        value = Decimal(math.ceil(POt * 100) / 100)
                        step = Decimal('0.0001')
                        
                        self.__write_log_wrapper("Точного совпадения не найдено")
                        self.__write_log_wrapper("Попытка найти регулятор с большим выходным давлением.")
                        while value<(Decimal("{:.4f}".format(POt)))*2:
                            value = Decimal("{:.4f}".format(value))
                            #Запуск функции анализа
                            regulators_found += self.conduct_analysis(os.path.normpath(path_file), 
                                                              PIn,
                                                              value, 
                                                              bandwidth)
                            if regulators_found!=0:
                                self.__write_log_wrapper("======================")
                                self.__write_log_wrapper("Выполнен поиск и найдены регуляторы по входному: {0} и выходному {1} давлению.".format(PIn,value))
                                self.__write_log_wrapper("")
                                break
                            
                            if value >= Decimal('0.01'):
                                step = Decimal('0.001')
                            elif value >= Decimal('0.1'):
                                step = Decimal('0.01')
                            elif value >= Decimal('1'):
                                step = Decimal('0.1')
                            
                            value+=step

                    if regulators_found == 0:
                        self.__write_log_wrapper("Регуляторы с необходимыми параметрами не найдены.")
                    else:
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
        
        self.status_animation = itertools.cycle(["В работе.", "В работе..", "В работе..."])
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
        self.root = TkinterDnD.Tk()
        self.root.title("Программа подбора регулятора")
        self.root.geometry("800x710")
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        self.style = ttk.Style()
        self.style.configure("TFrame", background="lightgrey")
        self.style.configure("TLabel", background="lightgrey")
        self.style.configure("TButton",
                        background="#007bff",
                        foreground="black",
                        relief=tk.FLAT,
                        font=("Helvetica", 12),
                        padding=10,
                        width=20,
                        borderwidth=0)
        self.style.map("TButton",
                  background=[("active", "#0056b3")],
                  foreground=[("active", "black")])
        
        self.__core_render()

        self.root.mainloop()

if __name__ == "__main__":
    selRegulator().draw_window()

    
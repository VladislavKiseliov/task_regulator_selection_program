"""
Данный код представляет собой программу, которая выполняет замену кириллических символов в тегах docx файлов на латинские символы.  
 
Шаги выполнения кода: 
1. Импортируются необходимые модули и библиотеки. 
2. Создается класс "Find_and_fix_in_doc". 
3. В конструкторе класса настраивается логгер для записи в файл, инициализируются переменные и 
создается словарь для хранения ссылок на файлы, которые нужно проверить. 
4. В классе определены несколько методов:  
   - "get_excel_column" - для получения буквенного обозначения столбца в Excel по его индексу. 
   - "show_error_message" - для отображения окна с ошибкой. 
   - "show_warning_message" - для отображения предупреждения. 
   - "remove_button_pressed" - для обработки нажатия кнопки "Удалить" в окне программы. 
   - "status_worck_cycle" - для отображения анимации статуса работы программы. 
   - "update_status_worck" - для обновления статуса работы программы. 
   - "possible_copy" - для копирования файла. 
   - "replace_cyrillic_with_latin" - для замены кириллических символов на латинские в слове. 
   - "read_and_fix_docx_file" - для чтения и исправления docx файла. 
   - "replacement_button_pressed" - для обработки нажатия кнопки "Заменить" в окне программы. 
   - "draw_window" - для отрисовки графического интерфейса программы. 
5. В блоке "if __name__ == "__main__":" создается экземпляр класса "Find_and_fix_in_docx" 
и вызывается метод "draw_window" для отображения окна программы.

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
pyinstaller --windowed --onefile --icon=icon.ico uREcyrillic.py --additional-hooks-dir=.
"""

import tkinter as tk
import shutil
import openpyxl
import os
import tkinter.ttk as ttk
import itertools
import structlog
import logging.config
import subprocess

from tkinter import messagebox, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from openpyxl.styles import PatternFill	
from openpyxl_image_loader import SheetImageLoader
from docx import Document


class Find_and_fix_in_doc:
    def __init__(self):
        # Настройка логгера для записи в файл
        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        structlog.stdlib.recreate_defaults(log_level=None)
        self.logger = structlog.get_logger("Test_log")

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
        if selected_index:
            self.lb.delete(selected_index)

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

    def open_file_dialog(self) -> None:
        file_path = filedialog.askopenfilename(filetypes=[("All Files", "*"),
                                                        ("Excel Files", "*.xlsx"),
                                                          ("Doc Files",  "*.doc", ),
                                                          ("Docx File",  "*.docx")])
        if file_path:
            self.lb.insert(tk.END, file_path)

    def __file_placed_drop_zone(self, e:str) -> None:
        list_path = "".join(e.data.replace("{", "")).split("}")[:-1]
        #Вводим пути в дроп бокс с форматированием
        [self.lb.insert(tk.END, file) for file in list_path]
        #Показываем пользователю какое название будет у файла
        # self.input_name_file.delete(0, tk.END)  # Очистка поля ввода
        # self.input_name_file.insert(0,  os.path.splitext(os.path.basename(list_path[-1]))[0]+"подбор"+".log")  # Вставка текста в поле ввода

    def __res_file_name(self) -> str:
        if self.self_file_name_var:
            return self.input_name_file.get()+".txt"
        
        return "Pвх-{0} Pвых-{1} ПрСп-{2}.txt".format(self.input_PIn.get(), 
                                                    self.input_POt.get(), 
                                                    self.input_bandwidth.get())
  


    def conduct_analysis(self, file_path:str,):
        workbook = openpyxl.load_workbook(file_path)
        self.logger.info("======================")
        self.logger.info("Поиск тегов для замены в файле: "+file_path)
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            i_row = 0

            # Put your sheet in the loader

            image_loader = SheetImageLoader(sheet)

            for row in sheet.iter_rows(values_only=True):
    
                for i_cell in range(len(row)):
                    cell = row[i_cell]

                    index_change_cell = self.get_excel_column(i_cell+1)+str(i_row+1) #+1 так как 1 это А и в экселе нумерация с 1
                    if cell is not None:
                    # Проверяем наличие картинки в клетке, если её нет, дальше реализовываем логику работы с текстом
                        if not (image_loader.image_in(index_change_cell)):
                            list_word_in_cell = str(cell).split()

                            print(list_word_in_cell)

                i_row += 1

    def replacement_button_pressed(self) -> None:
        """Функция для поиска и исправления кириллицы 
        в тегах файлов формата docx. Функция принимает путь к файлу 
        и маркер тега в виде цифрового ID. Если файлы не являются форматом 
        docx или doc, то выводится сообщение об ошибке. Если маркер тега не указан, 
        то также выводится сообщение об ошибке. После исправления кириллицы 
        в тегах, функция выводит количество исправленных записей и записывает 
        лог в файл.
        """
        filename_log = False
        listbox_data = self.lb.get(0, tk.END)
        self.processed_urls = {}
        self.status_text = "В работе"
        self.update_status_worck("В работе.")

        for index in range(1, len(listbox_data)):
            if os.path.splitext(listbox_data[index])[1] == '.xlsx':
                self.processed_urls[listbox_data[index]] = 0

        if len(self.processed_urls) == 0:
            self.show_error_message("Добавьте файлы xlsx")

        self.show_info_message(str("Поиск подходящего регулятора запущено"))

        for path_file, _ in self.processed_urls.items():
            if path_file.replace(" ", "") != "":
                PIn = self.input_PIn.get()
                POt = self.input_POt.get()
                bandwidth = self.input_bandwidth.get()

                if PIn != "" and POt!="" and bandwidth!="":
                    #Если не был создан файл логов, создаём его
                    if not filename_log:
                        filename_log = self.__res_file_name()
                        logging.basicConfig(filename= filename_log, encoding='utf-8', level=logging.INFO)


                    #Запуск функции анализа
                    self.conduct_analysis(os.path.normpath(path_file))
                    
                    #self.show_info_message("В файле {0} исправлено: {1} некорректных записей с кириллицей.".format(worck_patch,str(number_change),))
                    self.logger.info("")
                    self.logger.info("!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-")
                    self.logger.info("В файле {0} найдено *** подходящих регуляторов.".format(path_file))
                    self.logger.info("!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-")
                    self.logger.info("")
                else:
                    self.show_error_message("Введите маркер тега!")

        # Закрытие логгера
        logging.shutdown()
        # Открытие файла в который записаны данные
        subprocess.Popen(f'explorer "{os.path.normpath(os.path.dirname(path_file))}"')
        subprocess.Popen(["notepad.exe", filename_log])


    def __core_render(self) -> None:
        self.status_frame = ttk.Frame(self.root, style="TFrame")
        self.status_frame.pack(fill=tk.X)
        self.status_label = ttk.Label(self.status_frame, text="Ожидание работы", style="TLabel")
        self.status_label.pack(pady=10)
        
        self.status_animation = itertools.cycle(["В работе.", "В работе..", "В работе..."])
        self.update_status_worck("Ожидание работы")

        self.frame = ttk.Frame(self.root, style="TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.__drop_zone_render()

        self.in_data_frame = ttk.Frame(self.frame, style="TFrame")
        self.in_data_frame.pack(side=tk.RIGHT,anchor="n")

        self.__input_data_render()
        self.__button_render()

    def __drop_zone_render(self) -> None:
        self.lb = tk.Listbox(self.frame, width=50, height=10)
        self.lb.insert(1, "Перетащите xlsx таблицу с данными о регуляторах")
        self.lb.configure(justify=tk.CENTER)
        self.lb.drop_target_register(DND_FILES)
        self.lb.dnd_bind('<<Drop>>', self.__file_placed_drop_zone)
        self.lb.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)

    def __input_data_render(self) -> None:
        self.label_PIn = ttk.Label(self.in_data_frame, text="Входное давление - Рвх:", style="TLabel")
        self.label_PIn.grid(row=0, column=0, pady=3)

        self.input_PIn = ttk.Entry(self.in_data_frame)
        self.input_PIn.grid(row=1, column=0,sticky="ew",padx=(10))

        self.label_POt = ttk.Label(self.in_data_frame, text="Выходное давление - Рвых:", style="TLabel")
        self.label_POt.grid(row=2, column=0, pady=3)

        self.input_POt = ttk.Entry(self.in_data_frame)
        self.input_POt.grid(row=3, column=0,sticky="ew",padx=(10))

        self.label_bandwidth = ttk.Label(self.in_data_frame, text="Пропускная способность", style="TLabel")
        self.label_bandwidth.grid(row=4, column=0, pady=3)

        self.input_bandwidth = ttk.Entry(self.in_data_frame)
        self.input_bandwidth.grid(row=5, column=0, pady=(0,10),sticky="ew",padx=(10))


        self.label_name = ttk.Label(self.in_data_frame, text="Название файла:", style="TLabel")
        self.label_name.grid(row=6, column=0, pady=(20,0))

        self.self_file_name_var = tk.BooleanVar()
        self.checkbox = ttk.Checkbutton(self.in_data_frame, text="Своё название результирующего файла", variable=self.self_file_name_var, style="TCheckbutton")
        self.checkbox.grid(row=7, column=0, pady=(0,10),sticky="ew",padx=(10))

        self.input_name_file = ttk.Entry(self.in_data_frame)
        self.input_name_file.grid(row=8, column=0, pady=(0,10),sticky="ew",padx=(10))



    def __button_render(self) -> None:
        self.select_button = ttk.Button(self.in_data_frame, text="Подобрать регулятор", command=self.replacement_button_pressed, style="TButton")
        self.select_button.grid(row=9, column=0, pady=5)

        self.open_button = ttk.Button(self.in_data_frame, text="Открыть файл", command=self.open_file_dialog, style="TButton")
        self.open_button.grid(row=10, column=0, pady=5)

        self.remove_button = ttk.Button(self.in_data_frame, text="Удалить", command=self.remove_button_pressed, style="TButton")
        self.remove_button.grid(row=11, column=0, pady=5)

        

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
        self.root.geometry("800x600")
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        style = ttk.Style()
        style.configure("TFrame", background="lightgrey")
        style.configure("TLabel", background="lightgrey")
        style.configure("TButton",
                        background="#007bff",
                        foreground="black",
                        relief=tk.FLAT,
                        font=("Helvetica", 12),
                        padding=10,
                        width=20,
                        borderwidth=0)
        style.map("TButton",
                  background=[("active", "#0056b3")],
                  foreground=[("active", "black")])
        
        self.__core_render()

        self.root.mainloop()

if __name__ == "__main__":
    Find_and_fix_in_doc().draw_window()

    
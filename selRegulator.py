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


    def conduct_analysis(self):
        

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
            if os.path.splitext(listbox_data[index])[1] == '.docx' or os.path.splitext(listbox_data[index])[1] == '.doc' or  os.path.splitext(listbox_data[index])[1] == '.xlsx':
                self.processed_urls[listbox_data[index]] = 0

        if len(self.processed_urls) == 0:
            self.show_error_message("Добавьте файлы xlsx")

        self.show_info_message(str("Поиск подходящего регулятора запущено"))

        for path_file, _ in self.processed_urls.items():
            if path_file.replace(" ", "") != "":
                digital_tag_ID = self.input_field_ID_tag.get()

                if digital_tag_ID != "":
                    worck_patch  = (os.path.splitext(path_file)[0].lstrip()+'_result'+os.path.splitext(path_file)[1])

                    #Если не был создан файл логов, создаём его
                    if not filename_log:
                        filename_log = os.path.splitext(path_file)[0]+'_log'+'.log'
                        logging.basicConfig(filename= filename_log, encoding='utf-8', level=logging.INFO)


                    ###Место функции анализа
                    
                    #self.show_info_message("В файле {0} исправлено: {1} некорректных записей с кириллицей.".format(worck_patch,str(number_change),))
                    self.logger.info("")
                    self.logger.info("!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-")
                    self.logger.info("В файле {0} найдено и исправлено {1} тегов.".format(worck_patch))
                    self.logger.info("!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-")
                    self.logger.info("")
                else:
                    self.show_error_message("Введите маркер тега!")

        # Закрытие логгера
        logging.shutdown()
        # Открытие файла в который записаны данные
        print(worck_patch)
        subprocess.Popen(f'explorer "{os.path.normpath(os.path.dirname(path_file))}"')
        subprocess.Popen(["notepad.exe", filename_log])

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
        self.root.title("Замена кириллицы в тегах файлов формата doc и xlsx")
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
        self.status_frame = ttk.Frame(self.root, style="TFrame")
        self.status_frame.pack(fill=tk.X)
        self.status_label = ttk.Label(self.status_frame, text="Ожидание работы", style="TLabel")
        self.status_label.pack(pady=10)
        frame = ttk.Frame(self.root, style="TFrame")
        frame.pack(fill=tk.BOTH, expand=True)
        self.lb = tk.Listbox(frame, width=50, height=10)
        self.lb.insert(1, "Перетащите doc или docx файлы, которые нужно проверить и в которых нужно заменить кириллицу в тегах")
        self.lb.configure(justify=tk.CENTER)
        self.lb.drop_target_register(DND_FILES)
        self.lb.dnd_bind('<<Drop>>', lambda e: [self.lb.insert(tk.END, file) for file in "".join(e.data.replace("{", "")).split("}")[:-1]])
        self.lb.pack(fill=tk.BOTH, expand=True)

        def __label_frame() -> None:
            global in_data_frame

            in_data_frame = ttk.Frame(frame, style="TFrame")
            in_data_frame.pack()

            label_data_frame = ttk.Frame(in_data_frame, style="TFrame")
            label_data_frame.pack()

            label_num = ttk.Label(label_data_frame, text="Цифровой маркер тега:", style="TLabel")
            label_num.pack(side=tk.LEFT)

            label_pas = ttk.Label(label_data_frame, text=" "*90, style="TLabel")
            label_pas.pack(side=tk.LEFT)
            
        __label_frame()

        self.input_field_ID_tag = ttk.Entry(in_data_frame)
        self.input_field_ID_tag.pack(side=tk.LEFT, padx=10)
        checkbox_frame = ttk.Frame(in_data_frame, style="TFrame")
        checkbox_frame.pack(side=tk.LEFT,pady=10)
        self.search_combined_paragraphs_var = tk.BooleanVar()
        self.search_combined_paragraphs_var.set(True)
        checkbox = ttk.Checkbutton(checkbox_frame, text="Word: Поиск по объединенным параграфам\n(возможна потеря форматирования)", variable=self.search_combined_paragraphs_var, style="TCheckbutton")
        checkbox.pack(side=tk.LEFT)

        button_frame = ttk.Frame(frame, style="TFrame")
        button_frame.pack(pady=10)
        open_button = ttk.Button(button_frame, text="Открыть файл", command=self.open_file_dialog, style="TButton")
        open_button.pack(side=tk.LEFT, padx=10)
        button = ttk.Button(button_frame, text="Заменить", command=self.replacement_button_pressed, style="TButton")
        button.pack(side=tk.LEFT, padx=10)
        remove_button = ttk.Button(button_frame, text="Удалить", command=self.remove_button_pressed, style="TButton")
        remove_button.pack(side=tk.LEFT, padx=10)
        self.status_animation = itertools.cycle(["В работе.", "В работе..", "В работе..."])
        self.update_status_worck("Ожидание работы")
        self.root.mainloop()

if __name__ == "__main__":
    Find_and_fix_in_doc().draw_window()

    
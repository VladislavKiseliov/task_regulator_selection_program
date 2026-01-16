import datetime
import os


class FileWriter:
    """Класс для создания подробных инженерных отчетов по результатам поиска."""

    def __init__(self, p_in, p_out, q, encoding='utf-8'):
        # Формируем имя файла на основе входных параметров
        # Получаем текущую дату и время для имени файла
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

        # Формируем имя: 2024-05-20_14-30_Pвх-0.5 Pвых-0.06 ПрСп-30000.txt
        self.filename = f"{now}_Pвх-{p_in} Pвых-{p_out} ПрСп-{q}.txt"
        self.encoding = encoding
        self.file = None
        self.encoding = encoding
        self.file = None

    def open_file(self):
        # Создаем папку reports, если её нет
        if not os.path.exists("reports"):
            os.makedirs("reports")

        path = os.path.join("reports", self.filename)
        self.file = open(path, 'w', encoding=self.encoding)

    def write_log(self, data, n=1):
        if self.file is not None:
            current_datetime = datetime.datetime.now().replace(microsecond=0)
            for _ in range(n):
                line = f"{current_datetime}\t{data}\n"
                self.file.write(line)

    def close_file(self):
        if self.file is not None:
            self.file.close()
            self.file = None
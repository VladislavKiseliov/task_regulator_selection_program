import datetime

class FileWriter:
    def __init__(self, filename, encoding='utf-8'):
        self.filename = filename
        self.encoding = encoding
        self.file = None

    def open_file(self):
        self.file = open(self.filename, 'w', encoding=self.encoding)

    def write_log(self, data, n=1):
        if self.file is None:
            raise Exception("Файл не открыт")
        
        current_datetime = datetime.datetime.now().replace(microsecond=0)
        for _ in range(n):
            line = f"{current_datetime}\t{data}\n"
            self.file.write(line)

    def close_file(self):
        if self.file is not None:
            self.file.close()
            self.file = None


if __name__ == "__main__":
    # Пример использования
    try:
        writer = FileWriter('log.txt')
        writer.open_file()
        writer.write_log("Привет, мир!")
    finally:
        writer.close_file()
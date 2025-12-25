import os
from typing import List

class ExelMethod:
    def __init__(self, file_path):
        self.file_path = file_path


    def filter_excel_file(self,file_paths:List[str]):
        """
        Фильтрует список путей, оставляя только файлы с расширением .xlsx (без учёта регистра).

        Args:
            file_paths: Список путей к файлам (в виде строк).

        Returns:
            Список путей с расширением .xlsx (например, 'report.xlsx', 'DATA.XLSX').
        """
        excel_ext = '.xlsx'
        filtered = []
        for path in file_paths:
            if os.path.splitext(path)[1].lower() == excel_ext:
                filtered.append(path)
        return filtered
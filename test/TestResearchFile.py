str = "ГРПБ_РДНК-50-400(1000)_1-0_0_1_0_0_У1_0_1_50-50_Л-П"
selected_product = str.split("_")[0]
regulator = (str.split("_")[1]).split("-")[0]
print(selected_product,regulator)

from pathlib  import Path


# 1. Объединение частей пути с помощью оператора /
# Python сам поставит нужный разделитель: '\' для Windows или '/' для Linux/Mac.
folder = "Каталог"
sub_folder = selected_product
sub_sub_folder = regulator
file_name = str+".cdw"

file_path = Path(folder) / sub_folder / file_name

print(f"Путь: {file_path}")
# На Windows: docs\temp\config.txt
# На Linux/Mac: docs/temp/config.txt

# 2. Объединение с текущим рабочим каталогом
full_path = Path.cwd() / file_path
print(f"Полный путь: {full_path}")

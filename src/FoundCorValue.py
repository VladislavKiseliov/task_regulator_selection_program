import math
from decimal import Decimal

class FoundCorValue:
    """Определяет, наиболее близкие значения входного и выходного
     давления которые реально есть в таблице. Используется тогда, когда
     точного совпадения не было найдено"""
    def __init__(self,  workbook, input_press:float, output_press:float):
        self.workbook = workbook
        self.input_press = input_press
        self.output_press = output_press

    def finding_an_exact_match(self,
                         workbook:str,
                         inlet_pressure:float, 
                         output_pressure:float) -> int:
        """Функция determine_type_table, распарсивает экселевский файл
        и выбирает подходящий алгоритм для его обработки."""

        exact_match = 0
        
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            
            if sheet["C1"].value == "" or sheet["C1"].value == None:
                exact_match+=self.search_one_controller_table_algorithm_introductory_notes(inlet_pressure,output_pressure,sheet)
            else:
                exact_match+=self.search_several_controller_table_algorithm_introductory_notes(inlet_pressure,output_pressure,sheet)

            
        return exact_match

    def search_one_controller_table_algorithm_introductory_notes(self,
                                            inlet_pressure:float, 
                                            output_pressure:float, 
                                            sheet) -> int:
        """Функция search_one_controller_table_algorithm, принимает
        данные поиска и лист с таблицей формата: одно устройство
        на одном листе. Если в таблице есть точные совпадения ячейки и столбца по
        входным параметрам, тогда возвращает 1, в противном случае 0"""
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
                                            return 1       

                                    #Если ячейка входного давления НЕ является диапазоном
                                    else:
                                        if  float(mb_diap_Pain[0]) == float(inlet_pressure):
                                            return 1 

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
                                            return 1 
                                    
                                    #Если ячейка входного давления НЕ является диапазоном
                                    else:
                                        if  float(mb_diap_Pain[0]) == float(inlet_pressure):
                                            return 1 
                                    
                                row_scr_i+=1
            i_row += 1

        return 0

    def search_several_controller_table_algorithm_introductory_notes(self,
                                            inlet_pressure:float, 
                                            output_pressure:float, 
                                            sheet) -> int:
        """Функция search_several_controller_table_algorithm, принимает
        данные поиска и лист с таблицей формата: несколько устройств
        на одном листе. Если в таблице есть точные совпадения ячейки и столбца по
        входным параметрам, тогда возвращает 1, в противном случае 0"""
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
                                            return 1 

                                    
                                    #Если ячейка входного давления НЕ является диапазоном
                                    else:
                                        if  float(mb_diap_Pain[0]) == float(inlet_pressure):
                                            return 1 

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
                                            return 1 
                                    
                                    #Если ячейка входного давления НЕ является диапазоном
                                    else:
                                        if  float(mb_diap_Pain[0]) == float(inlet_pressure):
                                            return 1 
                                    
                                row_scr_i+=1
            i_row += 1

        return 0

    def check_input_parameters(self):
        pass

    def __call__(self):
        """Если есть точное совпадение параметров, возвращает их, если нет, тогда
        начинает пдбор для того что бы найти эти точные совпадения"""
        if self.finding_an_exact_match(self.workbook, self.input_press, self.output_press):
            return self.input_press, self.output_press
        else:
            value = Decimal(math.ceil(self.output_press * 100) / 100)
            step = Decimal('0.0001')
            
            #Точного совпадения не найдено
            #Попытка найти регулятор с большим выходным давлением.
            while value<(Decimal("{:.4f}".format(self.output_press)))*2:
                value = Decimal("{:.4f}".format(value))
                #Запуск функции анализа
                regulators_found += self.finding_an_exact_match(self.workbook, 
                                                    self.input_press,
                                                    value)
                if regulators_found!=0:
                    #"Выполнен поиск и найдены регуляторы по входному: {0} и выходному {1} давлению.".format(PIn,value))

                    break
                
                if value >= Decimal('0.01'):
                    step = Decimal('0.001')
                elif value >= Decimal('0.1'):
                    step = Decimal('0.01')
                elif value >= Decimal('1'):
                    step = Decimal('0.1')
                
                value+=step

            return  

import math
from decimal import Decimal
from src.MiniFunc import *
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
            
            exact_match+=self.search_several_controller_table_algorithm_introductory_notes(inlet_pressure,output_pressure,sheet)

            
        return exact_match

    def search_introductory_notes_for_y_outputs_press(self,
                                            workbook:str,
                                            inlet_pressure:float) -> int:
        """Функция search_one_controller_table_algorithm, принимает
        данные поиска и лист с таблицей формата: одно устройство
        на одном листе. Если в таблице есть точные совпадения ячейки и столбца по
        входным параметрам, тогда возвращает 1, в противном случае 0"""
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            i_row = 0

            for row in sheet.iter_rows(values_only=True):
                if i_row > 1:

                    mb_diap_Pain = str(row[0]).replace("\xa0", '').replace(" ", '').replace(",", '.').split("-")

                    #Если ячейка входного давления является диапазоном
                    if len(mb_diap_Pain) == 2:
                        if  float(mb_diap_Pain[0]) <= float(inlet_pressure) <= float(mb_diap_Pain[1]):
                            return 1       

                    #Если ячейка входного давления НЕ является диапазоном
                    elif mb_diap_Pain[0] != "None":
                        if  float(mb_diap_Pain[0]) == float(inlet_pressure):
                            return 1   
                i_row += 1

        return 0

    def search_introductory_notes_for_x_inputs_press(self,
                                            workbook:str,
                                            output_pressure:float, 
                                            ) -> int:
        """Функция search_several_controller_table_algorithm, принимает
        данные поиска и лист с таблицей формата: несколько устройств
        на одном листе. Если в таблице есть точные совпадения ячейки и столбца по
        входным параметрам, тогда возвращает 1, в противном случае 0"""
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]

            i_row = 0

            for row in sheet.iter_rows(values_only=True):      
                for i_cell in range(len(row)):
                    if i_row == 2 and i_cell!=0:

                        #Ищим подходящие выходные давления, как по диапазону - так и по единичным значениям
                        mb_diap_Paut = str(row[i_cell]).replace("\xa0", '').replace(" ", '').replace(",", '.').split("-")
                        
                        if len(mb_diap_Paut) == 2:
                            #Если ячейка выходного давления является диапазоном
                            if float(mb_diap_Paut[0]) <= float(output_pressure) <= float(mb_diap_Paut[1]):
                                return 1
                                
                        #Если ячейка выходного давления НЕ является диапазоном и существует
                            
                        elif mb_diap_Paut[0] != "None":
                            if float(output_pressure) == float(mb_diap_Paut[0]):
                                return 1               
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
        values_found=0

        value_output = Decimal(math.ceil(self.output_press * 100) / 100)

        value_input = Decimal(math.ceil(self.input_press * 100) / 100)

        if self.finding_an_exact_match(self.workbook, self.input_press, self.output_press):
            return self.input_press, self.output_press
        else: 
            step = Decimal('0.0001')
            
            #Точного совпадения не найдено
            #Попытка найти регулятор с большим выходным давлением.
            while value_output<(Decimal("{:.4f}".format(self.output_press)))*Decimal(1.5):
                value_output = Decimal("{:.4f}".format(value_output))
                #Запуск функции анализа
                values_found += self.search_introductory_notes_for_x_inputs_press(self.workbook, value_output)
                if values_found!=0:
                    #"Выполнен поиск и найдены регуляторы по входному: {0} и выходному {1} давлению.".format(PIn,value))

                    break
                
                if value_output >= Decimal('0.01'):
                    step = Decimal('0.001')
                elif value_output >= Decimal('0.1'):
                    step = Decimal('0.01')
                elif value_output >= Decimal('1'):
                    step = Decimal('0.1')
                
                value_output+=step
            
            values_found=0
            if not self.search_introductory_notes_for_y_outputs_press(self.workbook, self.input_press):
                step = Decimal('0.01')
            
                #Точного совпадения не найдено
                #Попытка найти регулятор с большим выходным давлением.

                while value_input>(Decimal("{:.4f}".format(self.input_press)))/Decimal(1.5):
                    value_input = Decimal("{:.4f}".format(value_input))
                    #Запуск функции анализа
                    values_found += self.search_introductory_notes_for_y_outputs_press(self.workbook, 
                                                        value_input)
                    if values_found!=0:
                        #"Выполнен поиск и найдены регуляторы по входному: {0} и выходному {1} давлению.".format(PIn,value))

                        break
                    if value_input <= Decimal('1'):
                        step = Decimal('0.01')
                    elif value_input <= Decimal('0.1'):
                        step = Decimal('0.001')
                    elif value_input <= Decimal('0.01'):
                        step = Decimal('0.0001')
                  
                    value_input-=step

            return float(value_input),float(value_output)

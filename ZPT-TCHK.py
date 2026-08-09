"""
LITIUM - Утилита для обработки файлов мебельного производства.

Модуль предоставляет GUI-интерфейс для:
- Проверки и исправления пазов в файлах .SCX
- Замены запятых на точки в файлах .SCX
- Подсчета деталей и сравнения файлов .csv и .pgmx
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Dict, Set, Tuple, List
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk, font, messagebox


class FileProcessor:
    """Класс для обработки файлов различных форматов."""
    
    # Константы для проверки ширины панелей
    MAX_PANEL_WIDTH = 1200.0
    
    # Константы для исправления параметров SCX
    TARGET_DIAMETER = '12.222'
    TARGET_WIDTH_OLD = '12.6'
    TARGET_WIDTH_NEW = '12,6'
    
    def __init__(self, text_widget: scrolledtext.ScrolledText):
        """
        Инициализация процессора файлов.
        
        Args:
            text_widget: Виджет Text для вывода результатов.
        """
        self.text_widget = text_widget
    
    def _insert_text(self, text: str) -> None:
        """Вставка текста в виджет вывода."""
        self.text_widget.insert(tk.INSERT, text)
    
    def select_directory(self) -> Optional[str]:
        """
        Открытие диалога выбора директории.
        
        Returns:
            Путь к выбранной директории или None если выбор отменен.
        """
        directory_path = filedialog.askdirectory(title="Выбрать папку")
        return directory_path if directory_path else None
    
    def count_details(self) -> None:
        """
        Подсчет количества деталей по материалам и сравнение файлов .pgmx с .csv.
        
        Анализирует CSV файлы для подсчета деталей и сравнивает списки файлов
        CSV и PGMX для выявления отсутствующих файлов или оборотов.
        """
        direc_file = self.select_directory()
        if not direc_file:
            return
        
        detal_csv: Dict[str, str] = {}
        name_dict: Dict[str, int] = {}
        csv_files_count = 0
        pgmx_files_count = 0
        oborot_keys: List[str] = []
        missing_keys: List[str] = []
        
        try:
            for filename in os.listdir(direc_file):
                f_path = os.path.join(direc_file, filename)
                
                if os.path.isfile(f_path) and filename.endswith('.csv'):
                    self._process_csv_file(f_path, filename, detal_csv, csv_files_count)
                    csv_files_count += 1
                    
                elif os.path.isfile(f_path) and filename.endswith('.pgmx'):
                    name_dict[filename] = 1
                    pgmx_files_count += 1
            
            self._insert_text(f'Всего файлов = {pgmx_files_count} шт.\n\n')
            self._compare_file_lists(detal_csv, name_dict, oborot_keys, missing_keys)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при обработке файлов: {str(e)}")
    
    def _process_csv_file(self, f_path: str, filename: str, 
                         detal_csv: Dict[str, str], csv_files_count: int) -> None:
        """
        Обработка одного CSV файла.
        
        Args:
            f_path: Полный путь к файлу.
            filename: Имя файла.
            detal_csv: Словарь для хранения данных о деталях.
            csv_files_count: Счетчик обработанных CSV файлов.
        """
        try:
            with open(f_path, 'r', encoding='utf-8') as file_read:
                content_csv = file_read.read()
            
            # Корректная обрезка содержимого (удаляем последний символ если он есть)
            if content_csv:
                content_csv = content_csv.rstrip()
            
            content_csv_det = content_csv.split("\n")
            summ = 0
            
            for detal in content_csv_det:
                detal_spl = detal.split(";")
                if len(detal_spl) >= 2:
                    keys = str(detal_spl[0])[18:]
                    values = str(detal_spl[1])[11:]
                    
                    try:
                        detal_csv[keys] = values
                        summ += int(values)
                    except ValueError:
                        continue
            
            self._insert_text(f'{filename} = {summ} шт.\n')
            
        except Exception as e:
            messagebox.showwarning("Предупреждение", 
                                 f"Ошибка при чтении файла {filename}: {str(e)}")
    
    def _compare_file_lists(self, detal_csv: Dict[str, str], name_dict: Dict[str, int],
                           oborot_keys: List[str], missing_keys: List[str]) -> None:
        """
        Сравнение списков файлов из CSV и PGMX.
        
        Args:
            detal_csv: Словарь с данными из CSV файлов.
            name_dict: Словарь с именами PGMX файлов.
            oborot_keys: Список ключей содержащих 'OBOROT'.
            missing_keys: Список отсутствующих ключей.
        """
        csv_keys = set(detal_csv.keys())
        pgmx_keys = set(name_dict.keys())
        
        if csv_keys == pgmx_keys:
            self._insert_text('Все файлы есть. Оборотов нет!\n\n\n')
        else:
            different_keys = csv_keys.symmetric_difference(pgmx_keys)
            
            for key in different_keys:
                if 'OBOROT' in key:
                    oborot_keys.append(key)
                else:
                    missing_keys.append(key)
            
            oborot_keys.sort()
            missing_keys.sort()
            
            for item in oborot_keys:
                self._insert_text(f'{item}\n')
            
            for item in missing_keys:
                self._insert_text(f'!ФАЙЛА НЕТ -- {item}\n')
    
    def replace_commas(self) -> None:
        """
        Замена запятых на точки в файлах .SCX.
        
        Используется для подготовки файлов сверлильного станка,
        который не корректно обрабатывает запятые в числовых значениях.
        """
        direc_file = self.select_directory()
        if not direc_file:
            return
        
        scx_files_count = 0
        
        try:
            for filename in os.listdir(direc_file):
                f_path = os.path.join(direc_file, filename)
                
                if os.path.isfile(f_path) and filename.endswith('.SCX'):
                    self._replace_commas_in_file(f_path)
                    scx_files_count += 1
            
            if scx_files_count > 0:
                self._insert_text(f'Запятых заменено в {scx_files_count} файлов\n\n')
            else:
                self._insert_text('Файлы .SCX не найдены\n\n')
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при замене запятых: {str(e)}")
    
    def _replace_commas_in_file(self, f_path: str) -> None:
        """
        Замена запятых на точки в одном файле.
        
        Args:
            f_path: Полный путь к файлу.
        """
        try:
            with open(f_path, 'r', encoding='utf-8') as file_r:
                content = file_r.read()
            
            new_string = content.replace(",", ".")
            
            with open(f_path, 'w', encoding='utf-8') as file_w:
                file_w.write(new_string)
                
        except Exception as e:
            messagebox.showwarning("Предупреждение", 
                                 f"Ошибка при обработке файла {os.path.basename(f_path)}: {str(e)}")
    
    def fix_scx_errors(self) -> None:
        """
        Исправление ошибок Базиса в файлах .SCX и поиск панелей не проходящих по ширине.
        
        Функция выполняет:
        - Исправление диаметров и параметров пазов
        - Проверку ширины панелей на соответствие ограничениям
        """
        direc_file = self.select_directory()
        if not direc_file:
            return
        
        count = 1
        count_w = 0
        
        try:
            for filename in os.listdir(direc_file):
                f_path = os.path.join(direc_file, filename)
                
                if os.path.isfile(f_path) and filename.endswith('.SCX'):
                    self._process_scx_file(f_path, count, count_w)
                    count += 1
            
            if count > 1:
                self._insert_text(f'Готово {count - 1} файлов\n\n')
            else:
                self._insert_text('Файлы .SCX не найдены\n\n')
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при исправлении SCX: {str(e)}")
    
    def _process_scx_file(self, f_path: str, count: int, count_w: int) -> None:
        """
        Обработка одного SCX файла.
        
        Args:
            f_path: Полный путь к файлу.
            count: Счетчик обработанных файлов.
            count_w: Счетчик панелей не прошедших проверку по ширине.
        """
        try:
            # Парсинг XML
            tree = ET.parse(f_path)
            root = tree.getroot()
            
            swith = 0
            fase = '0'
            zet = '0'
            
            # Обработка элементов Machining
            for elem in root.findall('.//Machining'):
                mach_type = elem.attrib.get('Type', '')
                
                if mach_type == '1':
                    if elem.attrib.get('Diameter') == self.TARGET_DIAMETER:
                        fase = elem.attrib.get('Face', '0')
                        zet = elem.attrib.get('Z', '0')
                        elem.clear()
                        elem.set('Type', 'None')
                        elem.set('Face', '0')
                        swith = 1
                        
                elif mach_type == '4':
                    if elem.attrib.get('Width') == self.TARGET_WIDTH_OLD:
                        elem.set('Width', self.TARGET_WIDTH_NEW)
                    
                    if swith == 1:
                        elem.set('Face', fase)
                        elem.set('Z', zet)
                        elem.set('EndZ', zet)
            
            # Проверка ширины панелей
            for wid in root.findall('.//Panel'):
                try:
                    width_value = float(wid.attrib.get('Width', '0'))
                    if width_value >= self.MAX_PANEL_WIDTH:
                        fname_w = os.path.basename(f_path)
                        self._insert_text(
                            f'деталь {fname_w} не входит, ширина = {wid.attrib.get("Width")}\n'
                        )
                        count_w += 1
                except ValueError:
                    continue
            
            # Сохранение измененного файла
            tree.write(f_path, encoding="utf-8", xml_declaration=True)
            
        except ET.ParseError as e:
            messagebox.showwarning("Предупреждение", 
                                 f"Ошибка XML в файле {os.path.basename(f_path)}: {str(e)}")
        except Exception as e:
            messagebox.showwarning("Предупреждение", 
                                 f"Ошибка при обработке файла {os.path.basename(f_path)}: {str(e)}")


class Application(tk.Tk):
    """Основное приложение с GUI интерфейсом."""
    
    def __init__(self):
        super().__init__()
        
        self.title("LITIUM")
        self.geometry('1800x700')
        
        # Настройка шрифтов
        self.font_main = font.Font(family="Arial", size=16, weight="normal")
        
        # Текстовый виджет будет создан в _create_ui
        self.txt = None
        self.file_processor = None
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Создание пользовательского интерфейса."""
        # Верхняя панель с кнопками
        frame = ttk.Frame(self, borderwidth=1, padding=[10, 10])
        frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Панель с константами (сразу после кнопок, чтобы гарантировать видимость)
        constants_frame = ttk.LabelFrame(self, text="Константы для исправления параметров SCX", padding=[10, 10])
        constants_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        # Отображение констант
        const_labels = [
            ("Макс. ширина панели:", f"{FileProcessor.MAX_PANEL_WIDTH} мм"),
            ("Целевой диаметр:", FileProcessor.TARGET_DIAMETER),
            ("Старая ширина паза:", FileProcessor.TARGET_WIDTH_OLD),
            ("Новая ширина паза:", FileProcessor.TARGET_WIDTH_NEW),
        ]
        
        for row, (label_text, value_text) in enumerate(const_labels):
            lbl_name = ttk.Label(constants_frame, text=label_text, font=self.font_main)
            lbl_name.grid(row=row, column=0, sticky=tk.W, padx=10, pady=2)
            
            lbl_value = ttk.Label(constants_frame, text=value_text, font=self.font_main)
            lbl_value.grid(row=row, column=1, sticky=tk.W, padx=10, pady=2)
        
        constants_frame.grid_columnconfigure(0, weight=1)
        constants_frame.grid_columnconfigure(1, weight=1)
        
        # Текстовый виджет для вывода информации (занимает оставшееся пространство)
        self.txt = scrolledtext.ScrolledText(
            self, width=100, height=50, font=self.font_main
        )
        self.txt.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.file_processor = FileProcessor(self.txt)
        
        # Кнопки управления
        buttons_config = [
            ("1) Проверить и исправить пазы", self.file_processor.fix_scx_errors),
            ("2) Заменить запятые на точки", self.file_processor.replace_commas),
            ("3) Подсчитать детали", self.file_processor.count_details),
            ("4) Очистить", self.clear_text),
        ]
        
        for col, (text, command) in enumerate(buttons_config):
            btn = tk.Button(frame, text=text, command=command, font=self.font_main)
            btn.grid(row=0, column=col, padx=5)
        
        # Настройка растягивания колонок
        for col in range(len(buttons_config)):
            frame.grid_columnconfigure(col, weight=1)
    
    def clear_text(self) -> None:
        """Очистка текстового поля вывода."""
        self.txt.delete(1.0, tk.END)


def main():
    """Точка входа в приложение."""
    app = Application()
    app.mainloop()


if __name__ == "__main__":
    main()
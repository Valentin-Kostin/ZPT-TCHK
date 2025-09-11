from tkinter import *
from tkinter import filedialog
import os

def select_directory():  
    directory_path = filedialog.askdirectory(title="Выбрать папку")  
    """if directory_path:  
        print("Папка выбрана:", directory_path)"""
    return directory_path


def clickedReplace():    
    direcFile = select_directory()
    for filename in os.listdir(direcFile):
        f = os.path.join(direcFile, filename)
        if os.path.isfile(f) and filename.endswith('.SCX'):
            print (f)
            fileR = open(f, 'r', encoding='utf-8')
            "print (fileR)"
            content = fileR.read()
            string = str(content)
            new_string = string.replace(",", ".")
            print(new_string)
            fileR.close()
            fileW = open(f, 'w', encoding='utf-8')
            fileW.write(new_string)            
            lbl = Label(window, text='ГОТОВО')
            lbl.grid(column=2, row=2)    
            fileW.close()


window = Tk()
window.title("Меняем зяпятые на точки")
window.geometry('350x200')
lbl = Label(window, text="Привет!")
lbl.grid(column=2, row=0)
btn = Button(window, text="Открыть папку", command=clickedReplace)
btn.grid(column=2, row=1)

window.mainloop()

from tkinter import *
import sete_cliques_para_as_estrelas
import re

class Application(Frame):

    def run(self):
        """ Start crawling the Wiki """
        try:
            regex = re.compile(r'http[s|]\://[a-z]{2}\.wikipedia\.org')
            source = regex.sub('', self.txt_source_link.get())
            target = regex.sub('', self.txt_target_link.get())
            sete_cliques_para_as_estrelas.run(source, target)
            return True
        except:
            return False

    def create_widget(self):
        self.lbl_source_link.grid(row=0, column=0, ipadx=10, ipady=10)
        self.txt_source_link['textvariable'] = self.var_source_link
        self.txt_source_link.grid(row=0, column=1, columnspan=3, stick=E+W)

        self.lbl_target_link.grid(row=1, column=0, ipadx=10, ipady=10)
        self.txt_target_link['textvariable'] = self.var_target_link
        self.txt_target_link.grid(row=1, column=1, columnspan=3, stick=E+W)

        self.btn_run['text'] = 'Run'
        self.btn_run['command'] = self.run
        self.btn_run.grid(row=2, column=0)

        self.btn_quit['text'] = 'QUIT'
        self.btn_quit['fg'] = 'red'
        self.btn_quit['command'] = self.quit
        self.btn_quit.grid(row=2, column=1)

    def __init__(self, master=None):
        Frame.__init__(self, master)

        # Values
        self.var_source_link = StringVar()
        self.var_target_link = StringVar()

        # Widgets
        self.lbl_source_link = Label(self, text='Source Link:')
        self.lbl_target_link = Label(self, text='Target Link:')
        self.txt_source_link = Entry(self, width=50)
        self.txt_target_link = Entry(self, width=50)
        self.btn_run = Button(self)
        self.btn_quit = Button(self)
        self.pack()
        self.create_widget()


root = Tk()
app = Application(master=root)
app.master.maxsize(500, 300)
app.master.minsize(500, 300)
app.master.resizable(0, 0)
app.master.title('Sete Cliques Para As Estrelas')
app.master.iconbitmap('assets/scpae.ico')
app.mainloop()
try:
    root.destroy()
except TclError as e:
    print(e)

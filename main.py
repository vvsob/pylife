import builtins
import random
import copy
import base64
from threading import Timer
from tkinter import *

cell_size = 20
field_size = 20


def make_empty_field():
    return [[False] * field_size for _ in range(field_size)]


def make_random_field():
    k = random.random()
    res = make_empty_field()
    for i in range(field_size):
        for j in range(field_size):
            if 5 <= i <= 14 and 5 <= j <= 14:
                res[i][j] = random.random() <= k
    return res


def field_to_str(field):
    flatten = [item for sublist in field for item in sublist]
    if len(flatten) % 8 != 0:
        flatten += [False] * (8 - (len(flatten) % 8))
    b = bytes([sum([byte[b] << b for b in range(0, 8)])
               for byte in zip(*(iter(flatten),) * 8)])
    b64 = base64.b64encode(b)
    return b64.decode()


def str_to_field(b64):
    def make_bits(n):
        return [((n >> i) & 1) == 1 for i in range(8)]

    b = [int(x) for x in base64.b64decode(b64)]
    pool = []
    for x in b:
        pool += make_bits(x)
    pool.reverse()
    res = make_empty_field()
    for i in range(field_size):
        for j in range(field_size):
            res[i][j] = pool.pop()
    return res


fld = str_to_field('AAAAAAAAAAAAAMADAAINEAABARAAAAEAEAAAAQAQEAABAhggAAEMCgBHAAAAAAAAAAA=')
print(field_to_str(fld) == 'AAAAAAAAAAAAAMADAAINEAABARAAAAEAEAAAAQAQEAABAhggAAEMCgBHAAAAAAAAAAA=')


class Event:
    __list = list()

    def add(self, func):
        if not callable(func):
            raise ValueError
        self.__list.append(func)

    def remove(self, func):
        if func in self.__list:
            self.__list.remove(func)

    def __call__(self, *args, **kwargs):
        for func in self.__list:
            func(*args, **kwargs)


class LifeCanvas(Canvas):
    after_tick = Event()
    after_update = Event()

    def reset(self, field_method=None):
        if not field_method:
            field_method = self.field_method
        self.field = field_method()
        self.update_field()

    def tick(self):
        new_field = make_empty_field()
        for i, row in enumerate(self.field):
            for j, elem in enumerate(row):
                neighbours = 0
                for di in range(-1, 2):
                    for dj in range(-1, 2):
                        if (not (0 <= i + di < field_size)) or \
                                (not (0 <= j + dj < field_size)) or \
                                (di, dj) == (0, 0):
                            continue
                        neighbours += self.field[i + di][j + dj]
                if self.field[i][j]:
                    new_field[i][j] = 2 <= neighbours <= 3
                else:
                    new_field[i][j] = neighbours == 3
        self.field = new_field
        self.after_tick()

    def update_field(self):
        self.delete("all")
        for i, row in enumerate(self.field):
            for j, elem in enumerate(row):
                rect = self.create_rectangle(j * cell_size, i * cell_size,
                                             (j + 1) * cell_size, (i + 1) * cell_size,
                                             fill=('green' if elem else 'black'),
                                             outline='#101010')
        self.after_update()

    def on_space(self, event):
        self.tick()
        self.update_field()

    def on_click(self, event):
        x, y = event.x, event.y
        j, i = x // cell_size, y // cell_size
        if i >= field_size or j >= field_size:
            return
        self.field[i][j] = not self.field[i][j]
        self.update_field()

    def count(self):
        res = {'total': 0, 'alive': 0, 'dead': 0}
        for i, row in enumerate(self.field):
            for j, elem in enumerate(row):
                res['total'] += 1
                if elem:
                    res['alive'] += 1
                else:
                    res['dead'] += 1
        return res

    def load(self, b64):
        self.field = str_to_field(b64)

    def __init__(self, tk, root, *args, field_method=make_empty_field, **kwargs):
        super().__init__(root, *args, **kwargs)
        self.field_method = field_method
        self.field = None
        self.reset()
        self.bind("<Button-1>", self.on_click)
        tk.bind("<space>", self.on_space)
        self.update_field()


class ControlButtons(Frame):
    def play(self):
        if not self.timer_running:
            self.timer_running = True
            self.after(1000, self.__tick)
        self.play_button['state'] = 'disabled'
        self.pause_button['state'] = 'normal'

    def pause(self):
        if self.timer_running:
            self.timer_running = False
        self.play_button['state'] = 'normal'
        self.pause_button['state'] = 'disabled'

    def step(self):
        self.pause()
        self.canvas.tick()
        self.canvas.update_field()

    def reset(self):
        self.pause()
        self.canvas.reset(field_method=make_empty_field)

    def __tick(self):
        if self.timer_running:
            self.canvas.tick()
            self.canvas.update_field()
            self.after(1000, self.__tick)

    def __init__(self, root, canvas, *args, **kwargs):
        super().__init__(root, *args, **kwargs)
        self.canvas = canvas

        self.timer_running = False
        self.play_button = Button(self, text='Play',
                                  command=self.play)
        self.play_button.pack(side='left')

        self.pause_button = Button(self, text='Pause', state='disabled',
                                   command=self.pause)
        self.pause_button.pack(side='left')

        self.step_button = Button(self, text='Step',
                                  command=self.step)
        self.step_button.pack(side='left')

        self.reset_button = Button(self, text='Reset',
                                   command=self.reset)
        self.reset_button.pack(side='left')


class FieldLoader(Frame):
    def load(self):
        self.canvas.load(self.b64_entry.get('1.0', END))
        self.canvas.update_field()
        self.controls.pause()

    def __init__(self, root, canvas, controls, *args, **kwargs):
        super().__init__(root, *args, **kwargs)
        self.canvas = canvas
        self.controls = controls
        self.b64_label = Label(self, text='Enter b64 string:')
        self.b64_label.pack()
        self.b64_entry = Text(self)
        self.b64_entry.pack()
        self.b64_load = Button(self, text='Load', command=self.load)
        self.b64_load.pack()


class InfoLabel(Label):
    def update_info(self):
        self['text'] = str(self.canvas.count())

    def __init__(self, root, canvas, *args, **kwargs):
        super().__init__(root, *args, **kwargs)
        self.canvas = canvas
        self.update_info()
        canvas.after_update.add(self.update_info)


class Generator(Frame):
    def start(self):
        self.controls.pause()
        best_config = (0, None)
        for i in range(self.max_count):
            self.info_label['text'] = f"Progress: {i + 1}/{self.max_count}"
            self.canvas.reset()
            config = field_to_str(self.canvas.field)
            self.canvas.tick()
            cnt = self.canvas.count()['alive']
            if cnt > best_config[0]:
                best_config = (cnt, config)
                print(cnt)
            self.canvas.update_field()
            self.root.update()
            self.root.update_idletasks()
        print(best_config[1])
        self.canvas.field = str_to_field(best_config[1])
        self.root.update()
        self.root.update_idletasks()
        self.canvas.update_field()
        self.info_label['text'] = "Generation offline"

    def __init__(self, tk, root, canvas, controls, *args, max_count=50_000, **kwargs):
        super().__init__(root, *args, **kwargs)
        self.root = root
        self.canvas = canvas
        self.controls = controls
        self.max_count = max_count

        self.info_label = Label(self, text='Generation offline')
        self.info_label.pack(side='left')

        self.start_button = Button(self, text='Start generating', command=self.start)
        self.start_button.pack(side='left')


def main():
    root = Tk()
    root.geometry("500x500+300+300")

    left_frame = Frame(root)

    canvas = LifeCanvas(root, left_frame,
                        field_method=make_random_field,
                        width=cell_size * field_size,
                        height=cell_size * field_size)
    canvas.pack()

    control_frame = ControlButtons(left_frame, canvas)
    control_frame.pack()

    info_label = InfoLabel(left_frame, canvas)
    info_label.pack()

    generator = Generator(root, left_frame, canvas, control_frame)
    generator.pack()

    left_frame.pack(side='left')

    right_frame = FieldLoader(root, canvas, control_frame)
    right_frame.pack(side='left')

    root.mainloop()


if __name__ == '__main__':
    main()

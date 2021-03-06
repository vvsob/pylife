import random
import base64
import copy
import tkinter.ttk
from tkinter import *
from tkinter.ttk import Notebook, Combobox


def make_empty_field(field_size):
    return [[False] * field_size for _ in range(field_size)]


def make_random_field(field_size, gen_size_x, gen_size_y):
    field_mid = field_size // 2
    gen_mid_x = gen_size_x // 2
    gen_add_x = gen_size_x % 2
    gen_mid_y = gen_size_y // 2
    gen_add_y = gen_size_y % 2
    k = random.uniform(0.2, 0.8)
    res = make_empty_field(field_size)
    for i in range(field_size):
        for j in range(field_size):
            if field_mid - gen_mid_x <= i < field_mid + gen_mid_y + gen_add_x and \
                    field_mid - gen_mid_y <= j < field_mid + gen_mid_y + gen_add_y:
                res[i][j] = random.random() <= k
    return res


def mutate(field_size, gen_size_x, gen_size_y, initial_config):
    field_mid = field_size // 2
    gen_mid_x = gen_size_x // 2
    gen_add_x = gen_size_x % 2
    gen_mid_y = gen_size_y // 2
    gen_add_y = gen_size_y % 2
    k = random.uniform(0.01, 0.1)
    res = make_empty_field(field_size)
    for i in range(field_size):
        for j in range(field_size):
            if field_mid - gen_mid_x <= i < field_mid + gen_mid_y + gen_add_x and \
                    field_mid - gen_mid_y <= j < field_mid + gen_mid_y + gen_add_y:
                res[i][j] = (initial_config[i][j]) != (random.random() <= k)
    return res


def field_to_str(field):
    flatten = [item for sublist in field for item in sublist]
    if len(flatten) % 8 != 0:
        flatten += [False] * (8 - (len(flatten) % 8))
    b = bytes([sum([byte[b] << b for b in range(0, 8)])
               for byte in zip(*(iter(flatten),) * 8)])
    b64 = base64.b64encode(b)
    return b64.decode()


def str_to_field(b64, field_size):
    def make_bits(n):
        return [((n >> i) & 1) == 1 for i in range(8)]

    b = [int(x) for x in base64.b64decode(b64)]
    pool = []
    for x in b:
        pool += make_bits(x)
    pool.reverse()
    res = make_empty_field(field_size)
    for i in range(field_size):
        for j in range(field_size):
            res[i][j] = pool.pop()
    return res


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
        self.field = field_method(self.field_size)
        self.update_field()

    def tick(self):
        new_field = make_empty_field(self.field_size)
        for i, row in enumerate(self.field):
            for j, elem in enumerate(row):
                neighbours = 0
                for di in range(-1, 2):
                    for dj in range(-1, 2):
                        if (not (0 <= i + di < self.field_size)) or \
                                (not (0 <= j + dj < self.field_size)) or \
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
                rect = self.create_rectangle(j * self.cell_size, i * self.cell_size,
                                             (j + 1) * self.cell_size, (i + 1) * self.cell_size,
                                             fill=('green' if elem else 'black'),
                                             outline='#101010', width=1 if self.borders else 0)
        self.after_update()

    def on_space(self, event):
        self.tick()
        self.update_field()

    def on_click(self, event):
        if event.widget != self:
            return
        x, y = event.x, event.y
        j, i = x // self.cell_size, y // self.cell_size
        if i >= self.field_size or j >= self.field_size:
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
        self.field = str_to_field(b64, self.field_size)

    def __init__(self, window, root,
                 controllable=True, borders=True,
                 field_size=20, cell_size=20,
                 field_method=make_empty_field,
                 **kwargs):
        super().__init__(root, **kwargs)
        self.window = window
        self.root = root
        self.controllable = controllable
        self.borders = borders
        self.field_method = field_method
        self.field_size = field_size
        self.cell_size = cell_size

        self['width'] = cell_size * field_size
        self['height'] = cell_size * field_size

        self.field = None
        self.reset()
        if self.controllable:
            self.window.bind("<Button-1>", self.on_click)
            self.window.bind("<space>", self.on_space)
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

    def __init__(self, root, canvas, **kwargs):
        super().__init__(root, **kwargs)
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

    def save(self):
        self.b64_entry.delete(1.0, END)
        self.b64_entry.insert(END, field_to_str(self.canvas.field))

    def copy(self):
        self.clipboard_clear()
        self.clipboard_append(self.b64_entry.get('1.0', END))

    def __init__(self, root, canvas, controls, **kwargs):
        super().__init__(root, **kwargs)
        self.canvas = canvas
        self.controls = controls
        self.b64_label = Label(self, text='Enter b64 string:')
        self.b64_label.pack()
        self.b64_entry = Text(self)
        self.b64_entry.pack()

        self.buttons_frame = Frame(self)

        self.b64_load = Button(self.buttons_frame, text='Load', command=self.load)
        self.b64_load.pack(side='left')
        self.b64_save = Button(self.buttons_frame, text='Save', command=self.save)
        self.b64_save.pack(side='left')
        self.b64_copy = Button(self.buttons_frame, text='Copy', command=self.copy)
        self.b64_copy.pack(side='left')

        self.buttons_frame.pack()


class InfoLabel(Label):
    def update_info(self):
        self['text'] = str(self.canvas.count())

    def __init__(self, root, canvas, **kwargs):
        super().__init__(root, **kwargs)
        self.canvas = canvas
        self.update_info()
        canvas.after_update.add(self.update_info)


class GeneratorSettings(Frame):
    def get_attempts(self):
        return int(self.attempts_entry.get())

    def get_iterations(self):
        return int(self.iterations_entry.get())

    def get_size(self):
        return tuple(
            map(int, [self.generated_size_entry_x.get(), self.generated_size_entry_y.get()]))

    def __init__(self, root, **kwargs):
        super().__init__(root, **kwargs)
        self.root = root

        self.attempts_label = Label(self, text="Number of attempts:")
        self.attempts_entry = Spinbox(self, width=20, from_=1000, to=10_000_000, increment=1000)

        self.attempts_label.grid(row=1, column=0)
        self.attempts_entry.grid(row=1, column=1, columnspan=3)

        self.iterations_label = Label(self, text="Number of iterations:")
        self.iterations_entry = Spinbox(self, width=20, from_=1, to=50, increment=1)

        self.iterations_label.grid(row=2, column=0)
        self.iterations_entry.grid(row=2, column=1, columnspan=3)

        self.generated_size_label_x = Label(self, text="Generated configuration width:")
        self.generated_size_entry_x = Spinbox(self, width=5, from_=3, to=30, increment=1)
        self.generated_size_label_y = Label(self, text="height:")
        self.generated_size_entry_y = Spinbox(self, width=5, from_=3, to=30, increment=1)

        self.generated_size_label_x.grid(row=3, column=0)
        self.generated_size_entry_x.grid(row=3, column=1)
        self.generated_size_label_y.grid(row=3, column=2)
        self.generated_size_entry_y.grid(row=3, column=3)


class Generator(Frame):
    def start(self):
        self.controls.pause()
        best_config = (0, None)
        self.running = True
        self.start_button['state'] = DISABLED
        self.stop_button['state'] = NORMAL
        for i in range(self.settings.get_attempts()):
            if not self.running:
                break

            self.canvas.reset(
                field_method=lambda size: make_random_field(size, *self.settings.get_size()))
            config = field_to_str(self.canvas.field)

            for tick in range(self.settings.get_iterations()):
                self.canvas.tick()
            cnt = self.canvas.count()['alive']

            if cnt > best_config[0]:
                best_config = (cnt, config)
                print(cnt, config)

            if i % 10 == 0:
                self.info_label['text'] = f"Progress: {i}/{self.settings.get_attempts()}"
                self.canvas.update_field()
                self.root.update()
                self.root.update_idletasks()

        print(best_config[1])
        self.canvas.field = str_to_field(best_config[1], self.canvas.field_size)
        self.canvas.update_field()
        self.info_label['text'] = "Generation offline"

    def stop(self):
        self.running = False
        self.start_button['state'] = NORMAL
        self.stop_button['state'] = DISABLED

    def __init__(self, tk, root, canvas, controls, **kwargs):
        super().__init__(root, **kwargs)
        self.running = False
        self.root = root
        self.canvas = canvas
        self.controls = controls

        self.settings = GeneratorSettings(self)
        self.settings.pack()

        self.info_label = Label(self, text='Generation offline')
        self.info_label.pack()

        self.start_button = Button(self, text='Start generating', command=self.start)
        self.start_button.pack()
        self.stop_button = Button(self, text='Stop generating', command=self.stop, state=DISABLED)
        self.stop_button.pack()


class MutatorGenerator(Frame):
    def start(self):
        init_config = copy.deepcopy(self.canvas.field)
        self.controls.pause()
        best_config = (0, None)
        self.running = True
        self.start_button['state'] = DISABLED
        self.stop_button['state'] = NORMAL
        for i in range(self.settings.get_attempts()):
            if not self.running:
                break

            self.canvas.reset(
                field_method=lambda size:
                mutate(size, *self.settings.get_size(), initial_config=init_config))
            config = field_to_str(self.canvas.field)

            for tick in range(self.settings.get_iterations()):
                self.canvas.tick()
            cnt = self.canvas.count()['alive']

            if cnt > best_config[0]:
                best_config = (cnt, config)
                print(cnt, config)

            if i % 10 == 0:
                self.info_label['text'] = f"Progress: {i}/{self.settings.get_attempts()}"
                self.canvas.update_field()
                self.root.update()
                self.root.update_idletasks()

        print(best_config[1])
        self.canvas.field = str_to_field(best_config[1], self.canvas.field_size)
        self.canvas.update_field()
        self.info_label['text'] = "Generation offline"

    def stop(self):
        self.running = False
        self.start_button['state'] = NORMAL
        self.stop_button['state'] = DISABLED

    def __init__(self, tk, root, canvas, controls, **kwargs):
        super().__init__(root, **kwargs)
        self.running = False
        self.root = root
        self.canvas = canvas
        self.controls = controls

        self.settings = GeneratorSettings(self)
        self.settings.pack()

        self.info_label = Label(self, text='Generation offline')
        self.info_label.pack()

        self.start_button = Button(self, text='Start generating', command=self.start)
        self.start_button.pack()
        self.stop_button = Button(self, text='Stop generating', command=self.stop, state=DISABLED)
        self.stop_button.pack()


def main():
    root = Tk()
    root.geometry("800x500+300+300")

    left_frame = Frame(root)

    canvas = LifeCanvas(root, left_frame,
                        field_method=make_empty_field,
                        field_size=40, cell_size=10)
    canvas.pack()

    control_frame = ControlButtons(left_frame, canvas)
    control_frame.pack()

    info_label = InfoLabel(left_frame, canvas)
    info_label.pack()
    left_frame.pack(side='left')

    right_frame = Frame(root)
    tabs = Notebook(right_frame)

    b64_tab = FieldLoader(tabs, canvas, control_frame)

    tabs.add(b64_tab, text='Import/Export')

    generator = Generator(root, tabs, canvas, control_frame)
    tabs.add(generator, text='Generator')

    mutator_generator = MutatorGenerator(root, tabs, canvas, control_frame)
    tabs.add(mutator_generator, text='Mutator Generator')

    tabs.pack(expand=1, fill="both")
    right_frame.pack(side='left')

    root.mainloop()


if __name__ == '__main__':
    main()

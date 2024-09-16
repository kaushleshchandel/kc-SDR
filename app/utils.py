from Xlib import display, X

def set_strut(root, taskbar_height):
    d = display.Display()
    screen = d.screen()
    root_window = screen.root
    win_id = root.winfo_id()
    win = d.create_resource_object('window', win_id)

    screen_width = root.winfo_screenwidth()
    strut = [0, 0, 0, taskbar_height, 0, 0, 0, 0, 0, 0, 0, screen_width]
    win.change_property(d.intern_atom('_NET_WM_STRUT_PARTIAL'),
                        d.intern_atom('CARDINAL'), 32,
                        strut)

    win.configure(stack_mode=X.Below)
    d.sync()
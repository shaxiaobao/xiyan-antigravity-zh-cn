"""Desktop installer, packaged with its own Python/Tk runtime."""
import json
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import contextlib
import io

import patch_asar as patch
import installer_service as service


class Installer:
    def __init__(self, root):
        self.root = root
        root.title('希言 · Antigravity 汉化安装器')
        root.geometry('760x590')
        root.minsize(680, 520)
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.busy = False
        self.events = queue.Queue()
        self.path = tk.StringVar()
        self.status = tk.StringVar(value='正在查找 Antigravity…')
        frame = ttk.Frame(root, padding=28)
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(8, weight=1)
        ttk.Label(frame, text='安装简体中文', font=('TkDefaultFont', 23, 'bold')).grid(row=0, column=0, sticky='w')
        ttk.Label(frame, text='安装完成后，重新打开原来的 Antigravity 图标即可。').grid(row=1, column=0, sticky='w', pady=(8, 25))
        ttk.Label(frame, text='Antigravity 安装位置').grid(row=2, column=0, sticky='w')
        location = ttk.Frame(frame)
        location.grid(row=3, column=0, sticky='ew', pady=(7, 12))
        location.columnconfigure(0, weight=1)
        self.entry = ttk.Entry(location, textvariable=self.path)
        self.entry.grid(row=0, column=0, sticky='ew', padx=(0, 8))
        self.controls = [self.entry]
        self.button(location, '选择…', self.choose).grid(row=0, column=1)
        self.button(location, '检测', self.detect).grid(row=0, column=2, padx=(8, 0))
        ttk.Label(frame, textvariable=self.status, wraplength=680).grid(row=4, column=0, sticky='w', pady=(0, 16))
        actions = ttk.Frame(frame)
        actions.grid(row=5, column=0, sticky='w')
        self.button(actions, '安装／修复汉化', lambda: self.execute('install')).pack(side='left', padx=(0, 10))
        self.button(actions, '恢复英文', lambda: self.execute('restore')).pack(side='left', padx=(0, 10))
        self.button(actions, '打开 Antigravity', self.open_app).pack(side='left')
        self.progress = ttk.Progressbar(frame, mode='indeterminate')
        self.progress.grid(row=6, column=0, sticky='ew', pady=18)
        ttk.Label(frame, text='操作详情').grid(row=7, column=0, sticky='w', pady=(0, 6))
        self.details = tk.Text(frame, height=8, wrap='word', relief='solid', borderwidth=1, padx=10, pady=10)
        self.details.grid(row=8, column=0, sticky='nsew')
        self.details.insert('end', '请先保存工作并完全退出 Antigravity，再安装或恢复。\n官方更新可能覆盖汉化，届时在这里点击“安装／修复汉化”。\n')
        self.details.configure(state='disabled')
        footer = ttk.Frame(frame)
        footer.grid(row=9, column=0, sticky='ew', pady=(16, 0))
        self.button(footer, '导入旧版备份…', self.import_old).pack(side='left')
        self.button(footer, '查看许可', self.license).pack(side='right')
        ttk.Label(frame, text='仅限非商业使用 · Windows 界面兼容性尚待实机验证', wraplength=680).grid(row=10, column=0, sticky='w', pady=(14, 0))
        root.after(100, self.detect)
        root.after(100, self.poll)

    def button(self, parent, text, command):
        widget = ttk.Button(parent, text=text, command=command)
        self.controls.append(widget)
        return widget

    def log(self, text):
        self.details.configure(state='normal')
        self.details.insert('end', text + '\n')
        self.details.see('end')
        self.details.configure(state='disabled')

    def configure(self):
        target = patch.locate_app(self.path.get().strip() or None)
        service.configure(target)
        self.path.set(str(target))

    def detect(self):
        try:
            self.configure()
            self.status.set(service.describe())
        except Exception as error:
            self.status.set('未完成检测，请选择安装位置。')
            self.log(str(error))

    def choose(self):
        selected = filedialog.askdirectory(title='选择 Antigravity.app 或 Windows 安装文件夹', mustexist=True)
        if selected:
            self.path.set(selected)
            self.detect()

    def import_old(self):
        selected = filedialog.askopenfilename(title='选择旧语言包中的 patch-state.json', filetypes=[('旧版状态文件', '*.json')])
        if not selected:
            return
        try:
            self.configure()
            with service.exclusive():
                if not service.import_legacy(Path(selected).parent):
                    raise RuntimeError('当前已有备份记录，或所选目录没有旧版记录。')
            self.log('已校验并导入旧版备份，旧目录保留不变。')
            self.detect()
        except Exception as error:
            self.log(str(error))

    def execute(self, action):
        try:
            self.configure()
            patch.require_stopped()
        except Exception as error:
            self.log(str(error))
            return
        self.busy = True
        for control in self.controls:
            control.configure(state='disabled')
        self.progress.start(12)
        self.status.set('正在安装并保存备份…' if action == 'install' else '正在恢复原版…')
        def work():
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    service.operate(action)
                self.events.put((True, output.getvalue(), action))
            except Exception as error:
                self.events.put((False, output.getvalue() + '\n' + str(error), action))
        threading.Thread(target=work, daemon=True).start()

    def poll(self):
        try:
            success, text, action = self.events.get_nowait()
            self.busy = False
            self.progress.stop()
            for control in self.controls:
                control.configure(state='normal')
            self.log(text)
            self.status.set(('汉化安装完成。请从原图标打开 Antigravity。' if action == 'install' else '已恢复英文。请重新打开 Antigravity。') if success else '操作未完成，请查看下方详情。')
            if not success:
                self.log('权限错误：macOS 请检查“隐私与安全性 → App 管理”；Windows 请检查安装目录写入权限。旧版补丁请先导入原始备份。')
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def open_app(self):
        try:
            self.configure()
            service.open_app()
        except Exception as error:
            self.log(str(error))

    def license(self):
        window = tk.Toplevel(self.root)
        window.title('希言非商业源码许可协议')
        window.geometry('720x520')
        text = tk.Text(window, wrap='word', padx=20, pady=20)
        text.pack(fill='both', expand=True)
        text.insert('end', (patch.PACKAGE_DIR / 'LICENSE').read_text(encoding='utf-8'))
        text.configure(state='disabled')

    def close(self):
        if self.busy:
            messagebox.showinfo('操作进行中', '请等待安装或恢复完成后关闭窗口。')
        else:
            self.root.destroy()


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        # Executed on each platform against the bundled binary, never touches installed apps.
        root = tk.Tk()
        root.withdraw()
        assert patch.load_injector()
        assert (patch.PACKAGE_DIR / 'LICENSE').is_file()
        Path(sys.argv[2]).write_text(json.dumps({'ok': True, 'platform': sys.platform, 'tk': root.tk.call('info', 'patchlevel')}), encoding='utf-8')
        root.destroy()
    else:
        root = tk.Tk()
        Installer(root)
        root.mainloop()

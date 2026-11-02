# -*- coding: utf-8 -*-
"""
Builder script for ClassroomReservationApp.exe.
Fixes the Python 3.10.0 dis.py opcode constant index bug, then runs PyInstaller.
"""

import dis
import os

# Fix Python 3.10.0 dis.py IndexError bug
orig_get_const_info = dis._get_const_info

def safe_get_const_info(arg, constants):
    try:
        return orig_get_const_info(arg, constants)
    except IndexError:
        return None, repr(arg)

dis._get_const_info = safe_get_const_info

import PyInstaller.__main__

if __name__ == "__main__":
    print("Starting ClassroomReservationApp build...")
    PyInstaller.__main__.run([
        '--noconfirm',
        '--clean',
        '--onefile',
        '--name', 'ClassroomReservationApp',
        '--add-data', f'reservation-app/dist{os.pathsep}reservation-app/dist',
        '--add-data', f'RoomService{os.pathsep}RoomService',
        '--add-data', f'Database{os.pathsep}Database',
        '--add-data', f'AuthService{os.pathsep}AuthService',
        '--add-data', f'Reservation{os.pathsep}Reservation',
        '--add-data', f'ApiGateway{os.pathsep}ApiGateway',
        'desktop_app.py'
    ])

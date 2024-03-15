# -*- coding: utf-8 -*-
import base64
import os
import re
import subprocess
import time
import urllib.request

from urllib.parse import urlparse

import requests
import rotatescreen
import win32api

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox

downloadPath = f"{os.getcwd()}\Downloads\\"


class ItemObject(object):
    def __init__(self, url, file_name, text, command):
        super().__init__()
        self.url = url
        self.file_name = file_name
        self.text = text
        self.command = command


class WorkerThread(QThread):
    progressChanged = pyqtSignal(int)
    progressFinished = pyqtSignal(bool)
    failedItems = []
    progressLabel = pyqtSignal(str)
    internetFailed = pyqtSignal(bool)

    def __init__(self, items, progressTasks):
        super().__init__()
        self.items = items
        self.increment = int(100 / progressTasks)
        self.progress = self.increment

    def isInternetConnected(self):
        try:
            urllib.request.urlopen("http://www.google.com")
            return True
        except:
            return False

    def downloadFiles(self):
        down_list = list(filter(lambda x: (x.url != ""), self.items))
        if down_list:
            if not self.isInternetConnected(): self.internetFailed.emit(True)
            for i in down_list:
                self.progressLabel.emit(f"Downloading {i.text}")
                self.downloadFile(i.url, i.file_name, i.text)

    def downloadFile(self, url, file, name):

        attempts = 3
        file_path = downloadPath + file

        if not os.path.exists(downloadPath):
            os.makedirs("Downloads")

        print(f'Downloading {url} content to {file_path}')
        url_sections = urlparse(url)
        if not url_sections.scheme:
            print('The given url is missing a scheme. Adding http scheme')
            url = f'http://{url}'
            print(f'New url: {url}')
        for attempt in range(1, attempts + 1):
            try:
                if attempt > 1:
                    time.sleep(10)  # 10 seconds wait time between downloads
                with requests.get(url, stream=True) as response:
                    response.raise_for_status()
                    with open(file_path, 'wb') as out_file:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                            out_file.write(chunk)
                    print('Download finished successfully')
                    break
            except Exception as e:
                print(f'Attempt #{attempt} failed with error: {e}')
                self.failedItems.append("[ " + name + " ]" + f"\n {e}\n")
        self.progressChanged.emit(self.progress)
        self.progress += self.increment

    def runCommand(self, command, name, timeout=300):
        try:
            proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if timeout:
                proc.wait(timeout=timeout)
                output = proc.communicate()[0].__str__().lower()
                if name not in self.failedItems.__str__():
                    if proc.returncode == 1 or any(ext in output for ext in ["error", "exception"]):
                        self.failedItems.append("[ " + name + " ]" + f"\n {output}\n\n")
        except Exception as e:
            if name not in self.failedItems.__str__():
                self.failedItems.append("[ " + name + " ]" + f"\n {e}\n")
        self.progressChanged.emit(self.progress)
        self.progress += self.increment

    def installItems(self):
        for i in self.items:
            self.progressLabel.emit(f"Installing {i.text}")
            if "power_driver.exe" in i.file_name:
                self.runCommand(i.command, i.text, None)
                time.sleep(10)
                subprocess.Popen("taskkill /IM dpinst.exe", shell=True)
                continue

            self.runCommand(i.command, i.text)

    def run(self):
        self.downloadFiles()
        self.installItems()
        self.progressFinished.emit(True)


class Ui_Dialog(object):
    checkedItems = []
    progressTasks = 0

    # Enable high DPI scaling & Use high DPI icons
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    def getOneDriveUrl(self, url):
        base64Url = "u!" + base64.b64encode(bytes(url, "utf-8")).decode("utf-8")
        return f"https://api.onedrive.com/v1.0/shares/{base64Url}/root/content"

    def resetApp(self):
        QtCore.QCoreApplication.quit()
        QtCore.QProcess.startDetached(sys.executable, sys.argv)
        # sys.exit()

    def selAllCheckBoxes(self, checkbox, layout):
        if checkbox.isChecked():
            status = True
        else:
            status = False
        for x in range(layout.__len__()):
            widget = layout.itemAt(x).widget()
            if "QCheckBox" in widget.__str__():
                if "checkBox_page_file" not in widget.objectName() or status is False:
                    widget.setChecked(status)

    def collectItems(self):
        # Drivers
        if self.checkBox_audio_driver.isChecked():
            file = "audio_driver.exe"
            text = self.checkBox_audio_driver.text()
            self.checkedItems.append(ItemObject("https://download.lenovo.com/consumer/mobiles/pfx8030fpjnc3ff0.exe", file,
                                                text, f"\"{downloadPath}{file}\" /verysilent"))
        if self.checkBox_bt_driver.isChecked():
            file = "bluetooth_driver.exe"
            text = self.checkBox_bt_driver.text()
            self.checkedItems.append(ItemObject("https://download.lenovo.com/consumer/mobiles/pfx8030fls0evff0.exe", file, text,
                                                f"\"{downloadPath}{file}\" /verysilent"))
        if self.checkBox_creader_driver.isChecked():
            file = "reader_driver.exe"
            text = self.checkBox_creader_driver.text()
            self.checkedItems.append(ItemObject("https://download.lenovo.com/consumer/mobiles/pfx8010febhfyff0.exe", file, text,
                                                f"\"{downloadPath}{file}\" /verysilent"))
        if self.checkBox_chipset_driver.isChecked():
            file = "chipset_driver.exe"
            text = self.checkBox_chipset_driver.text()
            self.checkedItems.append(ItemObject("https://download.lenovo.com/consumer/mobiles/pfx8020f17vz1ff0.exe", file, text,
                                                f"\"{downloadPath}{file}\" /verysilent"))
        if self.checkBox_power_driver.isChecked():
            file = "power_driver.exe"
            text = self.checkBox_power_driver.text()
            self.checkedItems.append(ItemObject("https://download.lenovo.com/consumer/mobiles/wwe00mae40.exe", file, text,
                                                f"\"{downloadPath}{file}\" /verysilent"))
        if self.checkBox_apu_driver.isChecked():
            file = "apu_driver.exe"
            text = self.checkBox_apu_driver.text()
            self.checkedItems.append(ItemObject("https://download.lenovo.com/consumer/mobiles/pfx8040f88t32ff0.exe", file, text,
                                                f"\"{downloadPath}{file}\" /verysilent"))
        if self.checkBox_adrenalin.isChecked():
            file = "adrenalin.msix"
            text = self.checkBox_adrenalin.text()
            self.checkedItems.append(ItemObject(self.getOneDriveUrl("https://1drv.ms/u/s!AjAnO264xsYV1iYaNLLwZ7ju0YqW"), file, text,
                                                f"PowerShell -NoProfile -ExecutionPolicy Bypass -Command \"Add-AppPackage -path '{downloadPath}{file}'\" -ForceApplicationShutdown"))
        if self.checkBox_space.isChecked():
            file = "space.exe"
            text = self.checkBox_space.text()
            self.checkedItems.append(ItemObject("https://download.lenovo.com/consumer/mobiles/wwls061ewyx3aff0.exe", file, text,
                                                f"\"{downloadPath}{file}\" /verysilent"))
        # Must Installs
        if self.checkBox_dot_net.isChecked():
            file = "dot_net.exe"
            text = self.checkBox_dot_net.text()
            self.checkedItems.append(ItemObject(
                "https://download.visualstudio.microsoft.com/download/pr/81531ad6-afa9-4b61-9d05-6a76dce81123/2885d26c1a58f37176fd7859f8cc80f1/dotnet-sdk-6.0.417-win-x64.exe",
                file, text,
                f"\"{downloadPath}{file}\" /quiet /norestart"))
        if self.checkBox_vc.isChecked():
            file = "vcc.exe"
            text = self.checkBox_vc.text()
            self.checkedItems.append(
                ItemObject("https://github.com/abbodi1406/vcredist/releases/download/v0.77.0/VisualCppRedist_AIO_x86_x64.exe", file, text,
                           f"\"{downloadPath}{file}\" /ai"))
        if self.checkBox_directx.isChecked():
            file = "directx.exe"
            text = self.checkBox_directx.text()
            self.checkedItems.append(
                ItemObject("https://download.microsoft.com/download/1/7/1/1718CCC4-6315-4D8E-9543-8E28A4E18C4C/dxwebsetup.exe", file, text,
                           f"\"{downloadPath}{file}\" /Q"))
        # Software
        if self.checkBox_soft_handheld.isChecked():
            file = "handheld.exe"
            text = self.checkBox_soft_handheld.text()
            self.checkedItems.append(
                ItemObject("https://github.com/Valkirie/HandheldCompanion/releases/download/0.20.4.1/HandheldCompanion-0.20.4.1.exe", file, text,
                           f"\"{downloadPath}{file}\" /verysilent /allusers /norestart"))
        if self.checkBox_soft_chrome.isChecked():
            file = "chrome.exe"
            text = self.checkBox_soft_chrome.text()
            self.checkedItems.append(ItemObject(
                "https://dl.google.com/tag/s/appguid%3D%7B8A69D345-D564-463C-AFF1-A69D9E530F96%7D%26iid%3D%7B04F50E1E-55EF-FA8E-646E-26A38F938B79%7D%26lang%3Den%26browser%3D3%26usagestats%3D0%26appname%3DGoogle%2520Chrome%26needsadmin%3Dprefers%26ap%3Dx64-stable-statsdef_1%26installdataindex%3Dempty/chrome/install/ChromeStandaloneSetup64.exe",
                file, text,
                f"\"{downloadPath}{file}\" /silent /install"))
        if self.checkBox_soft_7zip.isChecked():
            file = "7zip.exe"
            text = self.checkBox_soft_7zip.text()
            self.checkedItems.append(ItemObject("https://7-zip.org/a/7z2201-x64.exe", file, text,
                                                f"\"{downloadPath}{file}\" /S"))
        if self.checkBox_sof_fxsound.isChecked():
            file = "fxsound_setup.exe"
            text = self.checkBox_sof_fxsound.text()
            self.checkedItems.append(
                ItemObject("https://drive.fxsound.com/cs/hcn8vdevn5DxT2S/downloads3.fxsound.com/fxsound/1.1.22.0/fxsound_setup.exe/download", file, text,
                           f"\"{downloadPath}{file}\" /exenoui /noprereqs"))

        # Tweaks
        if self.checkBox_hibernate.isChecked():
            text = self.checkBox_hibernate.text()
            self.checkedItems.append(
                ItemObject("", "", text, "powercfg.exe /hibernate on"))
        if self.checkBox_ms_gamebar.isChecked():
            text = self.checkBox_ms_gamebar.text()
            self.checkedItems.append(
                ItemObject("", "", text, "reg add HKCR\ms-gamebar /f /ve /d URL:ms-gamebar && " \
                                         "reg add HKCR\ms-gamebar /f /v \"URL Protocol\" /d \" \" && " \
                                         "reg add HKCR\ms-gamebar /f /v \"NoOpenWith\" /d \" \" && " \
                                         "reg add HKCR\ms-gamebar\shell\open\command /f /ve /d \"`\"$env:SystemRoot\System32\systray.exe`\"\" &&" \
                                         "reg add HKCR\ms-gamebarservices /f /ve /d URL:ms-gamebarservices && " \
                                         "reg add HKCR\ms-gamebarservices /f /v \"URL Protocol\" /d \" \" && " \
                                         "reg add HKCR\ms-gamebarservices /f /v \"NoOpenWith\" /d \" \" && " \
                                         "reg add HKCR\ms-gamebarservices\shell\open\command /f /ve /d \"`\"$env:SystemRoot\System32\systray.exe`\"\""))
        if self.checkBox_keyboard.isChecked():
            text = self.checkBox_keyboard.text()
            self.checkedItems.append(
                ItemObject("", "", text,
                           "reg add HKEY_CURRENT_USER\SOFTWARE\Microsoft\TabletTip\\1.7 /t REG_DWORD /v EnableDesktopModeAutoInvoke /d 1 /f"))
        if self.checkBox_login_screen.isChecked():
            text = self.checkBox_login_screen.text()
            self.checkedItems.append(
                ItemObject("", "", text,
                           "reg add HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System /t REG_DWORD /v DisableLockWorkstation /d 1 /f"))
        if self.checkBox_power_hibernate.isChecked():
            text = self.checkBox_power_hibernate.text()

            power_cheme_guid = \
                re.findall("[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
                           subprocess.check_output('powercfg /GetActiveScheme').__str__())[0]
            self.checkedItems.append(
                ItemObject("", "", text,
                           f"powercfg /setACvalueindex {power_cheme_guid} 4f971e89-eebd-4455-a8de-9e59040e7347 7648efa3-dd9c-4e3e-b566-50f929386280 2 && " \
                           f"powercfg /setDCvalueindex {power_cheme_guid} 4f971e89-eebd-4455-a8de-9e59040e7347 7648efa3-dd9c-4e3e-b566-50f929386280 2"))
        if self.checkBox_page_file.isChecked():
            text = self.checkBox_page_file.text()
            path = f"{os.getcwd()}\page.ps1"
            drive = self.comboBox_page_drive.currentText()
            min = int(self.comboBox_page_min.currentText().split(" ")[0]) * 1000
            max = int(self.comboBox_page_max.currentText().split(" ")[0]) * 1000
            self.checkedItems.append(
                ItemObject("", "", text, f"PowerShell -NoProfile -ExecutionPolicy Bypass -Command \"& '{path}' '{drive}:\pagefile.sys' {min} {max}"))

    def collectProgressTasks(self):
        install_layouts = [self.verticalLayout_drivers, self.verticalLayout_must, self.verticalLayout_soft, self.verticalLayout_tweaks]
        for l in install_layouts:
            for i in range(l.__len__()):
                widget = l.itemAt(i).widget()
                if "QCheckBox" in widget.__str__() and widget.isChecked():
                    self.progressTasks += 1
                    if any(ext in l.objectName() for ext in ["_drivers", "_must", "_soft"]):
                        self.progressTasks += 1

    def rebootPc(self):
        subprocess.call(["shutdown", "-r", "-t", "0"])

    def finish(self, failed_items):
        if self.checkedItems.__len__() > 0:
            ok_button = self.finishMsg.addButton('OK', QtWidgets.QMessageBox.NoRole)
            reboot_button = self.finishMsg.addButton(' Reboot Now ', QtWidgets.QMessageBox.NoRole)
            ok_button.clicked.connect(self.resetApp)
            reboot_button.clicked.connect(self.rebootPc)
            self.progressBar.setValue(100)
            if failed_items.__len__() > 0:
                self.finishMsg.setIcon(QMessageBox.Critical)
                self.finishMsg.setText("Following Components FAILED To Install:")
                self.finishMsg.setInformativeText('\n'.join(map(str, failed_items)))
            else:
                self.finishMsg.setIcon(QMessageBox.Information)
                self.finishMsg.setText("All Components Successfully Installed")
                self.finishMsg.setInformativeText("Reboot Recommended")
            self.finishMsg.exec_()

    def pageFile(self):
        if self.checkBox_page_file.isChecked():
            status = True
        else:
            status = False
        self.comboBox_page_min.setEnabled(status)
        self.comboBox_page_max.setEnabled(status)
        self.comboBox_page_drive.setEnabled(status)

    def installWlan(self):
        proc = subprocess.run("wlan_driver.exe /verysilent", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
        if proc.returncode == 1 or any(ext in proc.stdout.decode().lower() for ext in ["error", "exception"]):
            self.finishMsg.setIcon(QMessageBox.Critical)
            self.finishMsg.setText(f"Wlan Driver Installation Failed\n\n {proc.stdout.decode()}")
        else:
            self.finishMsg.setIcon(QMessageBox.Information)
            self.finishMsg.setText("Wlan Driver Successfully Installed")
        self.progressBar.setValue(100)
        self.finishMsg.exec_()
        self.resetApp()

    def rotateScreen(self):
        rotatescreen.get_primary_display().set_portrait()

    def openKeyboard(self):
        subprocess.Popen("osk", shell=True)

    def disableElements(self):
        self.pushButton_start.setEnabled(False)
        self.pushButton_driver_wlan.setEnabled(False)
        layouts = [self.verticalLayout_drivers, self.verticalLayout_must, self.verticalLayout_soft, self.verticalLayout_tweaks, self.gridLayout_page_file]
        for l in layouts:
            for i in range(l.__len__()):
                widget = l.itemAt(i).widget()
                if widget is not None:
                    l.itemAt(i).widget().setEnabled(False)

    def failInternet(self):
        self.worker.terminate()
        self.finishMsg.setIcon(QMessageBox.Warning)
        self.finishMsg.setText("There is no internet connection")
        self.finishMsg.setInformativeText("Please check that WLAN driver Is installed and internet is connected")
        self.finishMsg.buttonClicked.connect(self.resetApp)
        self.finishMsg.exec_()

    def getListOfDrives(self):
        return win32api.GetLogicalDriveStrings().split(":\\\x00")[:-1]

    def start(self):
        self.collectItems()
        self.collectProgressTasks()
        if self.checkedItems.__len__() > 0:
            self.disableElements()
            self.worker = WorkerThread(self.checkedItems, self.progressTasks)
            self.worker.progressChanged.connect(self.progressBar.setValue)
            self.worker.progressFinished.connect(lambda: self.finish(self.worker.failedItems))
            self.worker.progressLabel.connect(self.label_progress.setText)
            self.worker.internetFailed.connect(self.failInternet)
            self.worker.start()

    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.NonModal)
        Dialog.resize(690, 515)
        Dialog.setMinimumSize(QtCore.QSize(690, 515))
        Dialog.setMaximumSize(QtCore.QSize(690, 515))
        Dialog.setStyleSheet("font-size: 14px")
        Dialog.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        Dialog.setAcceptDrops(False)
        Dialog.setWindowTitle("LegionGoHelper")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("logo.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        Dialog.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.progressBar = QtWidgets.QProgressBar(Dialog)
        self.progressBar.setGeometry(QtCore.QRect(30, 400, 631, 31))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setTextVisible(True)
        self.progressBar.setObjectName("progressBar")
        self.verticalLayoutWidget = QtWidgets.QWidget(Dialog)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(30, 50, 191, 281))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout_drivers = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_drivers.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_drivers.setSpacing(10)
        self.verticalLayout_drivers.setObjectName("verticalLayout_drivers")
        self.checkBox_drivers_all = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.checkBox_drivers_all.setText("Select All")
        self.checkBox_drivers_all.setObjectName("checkBox_drivers_all")
        self.verticalLayout_drivers.addWidget(self.checkBox_drivers_all)
        self.checkBox_audio_driver = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.checkBox_audio_driver.setText("Audio Driver")
        self.checkBox_audio_driver.setObjectName("checkBox_audio_driver")
        self.verticalLayout_drivers.addWidget(self.checkBox_audio_driver)
        self.checkBox_bt_driver = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.checkBox_bt_driver.setText("Bluetooth Driver")
        self.checkBox_bt_driver.setObjectName("checkBox_bt_driver")
        self.verticalLayout_drivers.addWidget(self.checkBox_bt_driver)
        self.checkBox_creader_driver = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.checkBox_creader_driver.setText("Card Reader Driver")
        self.checkBox_creader_driver.setObjectName("checkBox_creader_driver")
        self.verticalLayout_drivers.addWidget(self.checkBox_creader_driver)
        self.checkBox_chipset_driver = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.checkBox_chipset_driver.setText("Chipset Driver")
        self.checkBox_chipset_driver.setObjectName("checkBox_chipset_driver")
        self.verticalLayout_drivers.addWidget(self.checkBox_chipset_driver)
        self.checkBox_power_driver = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.checkBox_power_driver.setText("Power Mgmt. Driver")
        self.checkBox_power_driver.setObjectName("checkBox_power_driver")
        self.verticalLayout_drivers.addWidget(self.checkBox_power_driver)
        self.checkBox_apu_driver = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.checkBox_apu_driver.setText("APU Driver")
        self.checkBox_apu_driver.setObjectName("checkBox_apu_driver")
        self.verticalLayout_drivers.addWidget(self.checkBox_apu_driver)
        self.checkBox_adrenalin = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.checkBox_adrenalin.setText("AMD Adrenalin")
        self.checkBox_adrenalin.setObjectName("checkBox_adrenalin")
        self.verticalLayout_drivers.addWidget(self.checkBox_adrenalin)
        self.checkBox_space = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.checkBox_space.setText("Legion Space")
        self.checkBox_space.setObjectName("checkBox_space")
        self.verticalLayout_drivers.addWidget(self.checkBox_space)
        self.verticalLayoutWidget_2 = QtWidgets.QWidget(Dialog)
        self.verticalLayoutWidget_2.setGeometry(QtCore.QRect(250, 50, 191, 121))
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.verticalLayout_must = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_must.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_must.setSpacing(10)
        self.verticalLayout_must.setObjectName("verticalLayout_must")
        self.checkBox_must_all = QtWidgets.QCheckBox(self.verticalLayoutWidget_2)
        self.checkBox_must_all.setText("Select All")
        self.checkBox_must_all.setObjectName("checkBox_must_all")
        self.verticalLayout_must.addWidget(self.checkBox_must_all)
        self.checkBox_dot_net = QtWidgets.QCheckBox(self.verticalLayoutWidget_2)
        self.checkBox_dot_net.setText("Microsoft .NET")
        self.checkBox_dot_net.setObjectName("checkBox_dot_net")
        self.verticalLayout_must.addWidget(self.checkBox_dot_net)
        self.checkBox_vc = QtWidgets.QCheckBox(self.verticalLayoutWidget_2)
        self.checkBox_vc.setText("Visual C++ ")
        self.checkBox_vc.setObjectName("checkBox_vc")
        self.verticalLayout_must.addWidget(self.checkBox_vc)
        self.checkBox_directx = QtWidgets.QCheckBox(self.verticalLayoutWidget_2)
        self.checkBox_directx.setText("DirectХ")
        self.checkBox_directx.setObjectName("checkBox_directx")
        self.verticalLayout_must.addWidget(self.checkBox_directx)
        self.verticalLayoutWidget_3 = QtWidgets.QWidget(Dialog)
        self.verticalLayoutWidget_3.setGeometry(QtCore.QRect(250, 210, 191, 153))
        self.verticalLayoutWidget_3.setObjectName("verticalLayoutWidget_3")
        self.verticalLayout_soft = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_soft.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_soft.setSpacing(10)
        self.verticalLayout_soft.setObjectName("verticalLayout_soft")
        self.checkBox_soft_all = QtWidgets.QCheckBox(self.verticalLayoutWidget_3)
        self.checkBox_soft_all.setText("Select All")
        self.checkBox_soft_all.setObjectName("checkBox_soft_all")
        self.verticalLayout_soft.addWidget(self.checkBox_soft_all)
        self.checkBox_soft_handheld = QtWidgets.QCheckBox(self.verticalLayoutWidget_3)
        self.checkBox_soft_handheld.setText("Handheld Companion")
        self.checkBox_soft_handheld.setObjectName("checkBox_soft_handheld")
        self.verticalLayout_soft.addWidget(self.checkBox_soft_handheld)
        self.checkBox_soft_chrome = QtWidgets.QCheckBox(self.verticalLayoutWidget_3)
        self.checkBox_soft_chrome.setText("Chrome")
        self.checkBox_soft_chrome.setObjectName("checkBox_soft_chrome")
        self.verticalLayout_soft.addWidget(self.checkBox_soft_chrome)
        self.checkBox_soft_7zip = QtWidgets.QCheckBox(self.verticalLayoutWidget_3)
        self.checkBox_soft_7zip.setText("7-Zip")
        self.checkBox_soft_7zip.setObjectName("checkBox_soft_7zip")
        self.verticalLayout_soft.addWidget(self.checkBox_soft_7zip)
        self.checkBox_sof_fxsound = QtWidgets.QCheckBox(self.verticalLayoutWidget_3)
        self.checkBox_sof_fxsound.setText("Fx Sound")
        self.checkBox_sof_fxsound.setObjectName("checkBox_sof_fxsound")
        self.verticalLayout_soft.addWidget(self.checkBox_sof_fxsound)
        self.verticalLayoutWidget_4 = QtWidgets.QWidget(Dialog)
        self.verticalLayoutWidget_4.setGeometry(QtCore.QRect(470, 50, 191, 331))
        self.verticalLayoutWidget_4.setObjectName("verticalLayoutWidget_4")
        self.verticalLayout_tweaks = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_4)
        self.verticalLayout_tweaks.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_tweaks.setSpacing(14)
        self.verticalLayout_tweaks.setObjectName("verticalLayout_tweaks")
        self.checkBox_tweaks_all = QtWidgets.QCheckBox(self.verticalLayoutWidget_4)
        self.checkBox_tweaks_all.setText("Select All")
        self.checkBox_tweaks_all.setObjectName("checkBox_tweaks_all")
        self.verticalLayout_tweaks.addWidget(self.checkBox_tweaks_all)
        self.checkBox_hibernate = QtWidgets.QCheckBox(self.verticalLayoutWidget_4)
        self.checkBox_hibernate.setText("Enable Hibernate")
        self.checkBox_hibernate.setObjectName("checkBox_hibernate")
        self.verticalLayout_tweaks.addWidget(self.checkBox_hibernate)
        self.checkBox_ms_gamebar = QtWidgets.QCheckBox(self.verticalLayoutWidget_4)
        self.checkBox_ms_gamebar.setText("Disable \'ms-gamebar\' error")
        self.checkBox_ms_gamebar.setObjectName("checkBox_ms_gamebar")
        self.verticalLayout_tweaks.addWidget(self.checkBox_ms_gamebar)
        self.checkBox_login_screen = QtWidgets.QCheckBox(self.verticalLayoutWidget_4)
        self.checkBox_login_screen.setText("Disable Login Screen")
        self.checkBox_login_screen.setObjectName("checkBox_login_screen")
        self.verticalLayout_tweaks.addWidget(self.checkBox_login_screen)
        self.checkBox_keyboard = QtWidgets.QCheckBox(self.verticalLayoutWidget_4)
        self.checkBox_keyboard.setText("Enable Virtual Keyboard")
        self.checkBox_keyboard.setObjectName("checkBox_keyboard")
        self.verticalLayout_tweaks.addWidget(self.checkBox_keyboard)
        self.checkBox_power_hibernate = QtWidgets.QCheckBox(self.verticalLayoutWidget_4)
        self.checkBox_power_hibernate.setText("Hibernate On Power Button")
        self.checkBox_power_hibernate.setObjectName("checkBox_power_hibernate")
        self.verticalLayout_tweaks.addWidget(self.checkBox_power_hibernate)
        self.checkBox_page_file = QtWidgets.QCheckBox(self.verticalLayoutWidget_4)
        self.checkBox_page_file.setText("PageFile.sys")
        self.checkBox_page_file.setObjectName("checkBox_page_file")
        self.verticalLayout_tweaks.addWidget(self.checkBox_page_file)
        self.gridLayout_page_file = QtWidgets.QGridLayout()
        self.gridLayout_page_file.setContentsMargins(-1, -1, 0, -1)
        self.gridLayout_page_file.setVerticalSpacing(6)
        self.gridLayout_page_file.setObjectName("gridLayout_page_file")
        self.comboBox_page_min = QtWidgets.QComboBox(self.verticalLayoutWidget_4)
        self.comboBox_page_min.setEnabled(False)
        self.comboBox_page_min.setObjectName("comboBox_page_min")
        self.comboBox_page_min.addItem("")
        self.comboBox_page_min.setItemText(0, "8 GB")
        self.comboBox_page_min.addItem("")
        self.comboBox_page_min.setItemText(1, "10 GB")
        self.comboBox_page_min.addItem("")
        self.comboBox_page_min.setItemText(2, "12 GB")
        self.comboBox_page_min.addItem("")
        self.comboBox_page_min.setItemText(3, "16 GB")
        self.comboBox_page_min.addItem("")
        self.comboBox_page_min.setItemText(4, "14 GB")
        self.comboBox_page_min.addItem("")
        self.comboBox_page_min.setItemText(5, "18 GB")
        self.comboBox_page_min.addItem("")
        self.comboBox_page_min.setItemText(6, "20 GB")
        self.comboBox_page_min.addItem("")
        self.comboBox_page_min.setItemText(7, "22 GB")
        self.comboBox_page_min.addItem("")
        self.comboBox_page_min.setItemText(8, "24 GB")
        self.comboBox_page_min.addItem("")
        self.comboBox_page_min.setItemText(9, "26 GB")
        self.comboBox_page_min.addItem("")
        self.comboBox_page_min.setItemText(10, "28 GB")
        self.comboBox_page_min.addItem("")
        self.comboBox_page_min.setItemText(11, "30 GB")
        self.comboBox_page_min.addItem("")
        self.comboBox_page_min.setItemText(12, "32 GB")
        self.gridLayout_page_file.addWidget(self.comboBox_page_min, 1, 1, 1, 1)
        self.comboBox_page_max = QtWidgets.QComboBox(self.verticalLayoutWidget_4)
        self.comboBox_page_max.setEnabled(False)
        self.comboBox_page_max.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.comboBox_page_max.setObjectName("comboBox_page_max")
        self.comboBox_page_max.addItem("")
        self.comboBox_page_max.setItemText(0, "8 GB")
        self.comboBox_page_max.addItem("")
        self.comboBox_page_max.setItemText(1, "10 GB")
        self.comboBox_page_max.addItem("")
        self.comboBox_page_max.setItemText(2, "12 GB")
        self.comboBox_page_max.addItem("")
        self.comboBox_page_max.setItemText(3, "14 GB")
        self.comboBox_page_max.addItem("")
        self.comboBox_page_max.setItemText(4, "16 GB")
        self.comboBox_page_max.addItem("")
        self.comboBox_page_max.setItemText(5, "18 GB")
        self.comboBox_page_max.addItem("")
        self.comboBox_page_max.setItemText(6, "20 GB")
        self.comboBox_page_max.addItem("")
        self.comboBox_page_max.setItemText(7, "22 GB")
        self.comboBox_page_max.addItem("")
        self.comboBox_page_max.setItemText(8, "24 GB")
        self.comboBox_page_max.addItem("")
        self.comboBox_page_max.setItemText(9, "26 GB")
        self.comboBox_page_max.addItem("")
        self.comboBox_page_max.setItemText(10, "28 GB")
        self.comboBox_page_max.addItem("")
        self.comboBox_page_max.setItemText(11, "30 GB")
        self.comboBox_page_max.addItem("")
        self.comboBox_page_max.setItemText(12, "32 GB")
        self.gridLayout_page_file.addWidget(self.comboBox_page_max, 2, 1, 1, 1)
        self.label_page_min = QtWidgets.QLabel(self.verticalLayoutWidget_4)
        self.label_page_min.setEnabled(False)
        self.label_page_min.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_page_min.setText("Min")
        self.label_page_min.setObjectName("label_page_min")
        self.gridLayout_page_file.addWidget(self.label_page_min, 1, 0, 1, 1)
        self.label_page_drive = QtWidgets.QLabel(self.verticalLayoutWidget_4)
        self.label_page_drive.setEnabled(False)
        self.label_page_drive.setText("Drive")
        self.label_page_drive.setObjectName("label_page_drive")
        self.gridLayout_page_file.addWidget(self.label_page_drive, 0, 0, 1, 1)
        self.label_page_max = QtWidgets.QLabel(self.verticalLayoutWidget_4)
        self.label_page_max.setEnabled(False)
        self.label_page_max.setText("Max")
        self.label_page_max.setObjectName("label_page_max")
        self.gridLayout_page_file.addWidget(self.label_page_max, 2, 0, 1, 1)
        self.comboBox_page_drive = QtWidgets.QComboBox(self.verticalLayoutWidget_4)
        self.comboBox_page_drive.setEnabled(False)
        self.comboBox_page_drive.setObjectName("comboBox_page_drive")
        self.gridLayout_page_file.addWidget(self.comboBox_page_drive, 0, 1, 1, 1)
        self.gridLayout_page_file.setColumnStretch(0, 1)
        self.gridLayout_page_file.setColumnStretch(1, 3)
        self.verticalLayout_tweaks.addLayout(self.gridLayout_page_file)
        self.pushButton_driver_wlan = QtWidgets.QPushButton(Dialog)
        self.pushButton_driver_wlan.setGeometry(QtCore.QRect(30, 342, 141, 30))
        self.pushButton_driver_wlan.setMinimumSize(QtCore.QSize(0, 0))
        self.pushButton_driver_wlan.setFocusPolicy(QtCore.Qt.NoFocus)
        self.pushButton_driver_wlan.setText("Install WLAN Driver")
        self.pushButton_driver_wlan.setObjectName("pushButton_driver_wlan")
        self.horizontalLayoutWidget = QtWidgets.QWidget(Dialog)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(30, 450, 631, 41))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(20)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_start = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.pushButton_start.setMinimumSize(QtCore.QSize(0, 30))
        self.pushButton_start.setFocusPolicy(QtCore.Qt.NoFocus)
        self.pushButton_start.setText("START")
        self.pushButton_start.setObjectName("pushButton_start")
        self.horizontalLayout.addWidget(self.pushButton_start)
        self.pushButton_cancel = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.pushButton_cancel.setMinimumSize(QtCore.QSize(0, 30))
        self.pushButton_cancel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.pushButton_cancel.setText("CANCEL")
        self.pushButton_cancel.setObjectName("pushButton_cancel")
        self.horizontalLayout.addWidget(self.pushButton_cancel)
        self.pushButton_rotate = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.pushButton_rotate.setMinimumSize(QtCore.QSize(0, 30))
        self.pushButton_rotate.setFocusPolicy(QtCore.Qt.NoFocus)
        self.pushButton_rotate.setText("Landscape Screen")
        self.pushButton_rotate.setObjectName("pushButton_rotate")
        self.horizontalLayout.addWidget(self.pushButton_rotate)
        self.pushButton_keyboard = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.pushButton_keyboard.setMinimumSize(QtCore.QSize(0, 30))
        self.pushButton_keyboard.setFocusPolicy(QtCore.Qt.NoFocus)
        self.pushButton_keyboard.setText("Open Keyboard")
        self.pushButton_keyboard.setIconSize(QtCore.QSize(16, 16))
        self.pushButton_keyboard.setObjectName("pushButton_keyboard")
        self.horizontalLayout.addWidget(self.pushButton_keyboard)
        self.label_drivers = QtWidgets.QLabel(Dialog)
        self.label_drivers.setGeometry(QtCore.QRect(30, 20, 191, 21))
        self.label_drivers.setText("Legion GO Drivers")
        self.label_drivers.setObjectName("label_drivers")
        self.label_drivers.setStyleSheet("font-size: 11pt; font-weight: bold")
        self.label_must = QtWidgets.QLabel(Dialog)
        self.label_must.setGeometry(QtCore.QRect(250, 20, 191, 21))
        self.label_must.setText("Must Have Installs")
        self.label_must.setObjectName("label_must")
        self.label_must.setStyleSheet("font-size: 11pt; font-weight: bold")
        self.label_tweaks = QtWidgets.QLabel(Dialog)
        self.label_tweaks.setGeometry(QtCore.QRect(470, 20, 191, 21))
        self.label_tweaks.setText("Windows Tweaks")
        self.label_tweaks.setObjectName("label_tweaks")
        self.label_tweaks.setStyleSheet("font-size: 11pt; font-weight: bold")
        self.label_soft = QtWidgets.QLabel(Dialog)
        self.label_soft.setGeometry(QtCore.QRect(250, 180, 191, 21))
        self.label_soft.setText("Software")
        self.label_soft.setObjectName("label_soft")
        self.label_soft.setStyleSheet("font-size: 11pt; font-weight: bold")

        self.label_progress = QtWidgets.QLabel(Dialog)
        self.label_progress.setGeometry(QtCore.QRect(43, 408, 251, 16))
        self.label_progress.setObjectName("label_progress")
        self.label_progress.setStyleSheet("font-size: 10pt")

        # Disable buttons selection
        self.pushButton_driver_wlan.setDefault(False)
        self.pushButton_driver_wlan.setAutoDefault(False)

        # Add minimize button on main window
        Dialog.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        Dialog.setWindowFlag(Qt.WindowMinimizeButtonHint, True)

        # Finish Message Box
        self.finishMsg = QtWidgets.QMessageBox()
        self.finishMsg.setWindowTitle("LegionGoHelper")

        # Hide Finish Message Box close and min buttons
        self.finishMsg.setWindowFlags(QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint)

        # Connections
        self.checkBox_drivers_all.stateChanged.connect(lambda: self.selAllCheckBoxes(self.checkBox_drivers_all, self.verticalLayout_drivers))
        self.checkBox_must_all.stateChanged.connect(lambda: self.selAllCheckBoxes(self.checkBox_must_all, self.verticalLayout_must))
        self.checkBox_soft_all.stateChanged.connect(lambda: self.selAllCheckBoxes(self.checkBox_soft_all, self.verticalLayout_soft))
        self.checkBox_tweaks_all.stateChanged.connect(lambda: self.selAllCheckBoxes(self.checkBox_tweaks_all, self.verticalLayout_tweaks))
        self.checkBox_page_file.stateChanged.connect(self.pageFile)
        self.pushButton_start.pressed.connect(self.start)
        self.pushButton_cancel.clicked.connect(self.resetApp)
        self.pushButton_driver_wlan.pressed.connect(self.installWlan)
        self.pushButton_rotate.pressed.connect(self.rotateScreen)
        self.pushButton_keyboard.pressed.connect(self.openKeyboard)
        self.comboBox_page_drive.addItems(self.getListOfDrives())

        QtCore.QMetaObject.connectSlotsByName(Dialog)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    Dialog.raise_()
    sys.exit(app.exec_())
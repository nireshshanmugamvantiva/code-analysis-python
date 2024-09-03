import time
import json
import logging
from ppadb.client import Client as AdbClient
from ppadb.utils.logger import AdbLogging
from uiautomator import Device
import logger
from logging.handlers import RotatingFileHandler
from logging import handlers
import subprocess
import os, sys
import time as t
import pytest
from pytest_html import extras
from pathlib import Path
from datetime import datetime
from tabulate import tabulate
import matplotlib.pyplot as plt
import re
import errno, sys
import pandas as pd
import numpy as np
import inspect
import conftest

repo_path = os.path.join(os.getcwd(), "base")
sys.path.append(repo_path)

img_path = os.path.join(os.getcwd(), "logs")
img_path = img_path + os.sep
sys.path.append(img_path)

cwd = str(os.getcwd()) + str(os.sep)
log_dir = cwd + "logs" + str(os.sep)
results_dir = cwd + "results" + str(os.sep)

old_log_files = log_dir
old_results_files = results_dir

try:
    if sys.platform.startswith('win'):
        os.chmod(old_log_files, 777)
        os.remove(old_log_files)
        os.chmod(old_results_files, 777)
        os.remove(old_results_files)
    else:    
        os.system("rm " + log_dir + "*.*")
        os.system("rm " + results_dir + "*.*")
except:
    pass
class TestClassAPIFunctions:
    """_summary_"""

    def __init__(
        self,
    ):
        self.mycfg = self.parse_cfg()
        self.cfg_dut = self.mycfg["DUT"]
        self.dut_ip = self.cfg_dut['BOX_IP']
        # self.cfg_pkg = self.mycfg["app_packages"]
        self.cfg_gui = self.mycfg["gui"]
        self.cfg_avstats = self.mycfg["av_decode_stats"]
        self.cfg_perfkpi = self.mycfg["performance_kpi"]
        self.cfg_appplybck = self.mycfg["app_playback"]

        self.adblogger = logger.adb_logger_init("ppadb.logger")
        self.mylogger = logger.logger_init(__name__)
        self.device_adb = self.get_device_adb(self.cfg_dut["BOX_IP"])
        if self.device_adb:
            self.device_ui = self.get_device_ui(self.cfg_dut["BOX_IP"])

    def parse_cfg(
        self,
    ):
        """_summary_

        Returns:
            _type_: _description_
        """
        with open("config.json", "r", encoding="UTF-8") as config:
            # self.mylogger.info("Parse Config File")
            return json.load(config)

    def get_device_adb(
        self,
        dut,
    ):
        """_summary_

        Returns:
            _type_: _description_
        """
        self.mylogger.info("Getting ADB device")
        self.mylogger.info("DUT IP = {}".format(dut))

        try:
            adb_device = self.adb_connection(dut)
            self.mylogger.debug("adb_device = {}".format(adb_device))
            return adb_device
        except Exception as exerror:  # pylint: disable=broad-except
            self.mylogger.exception("Exception Occured from adb connection", exc_info=True)
            data = ["Exception Occured from adb connection"]
            result = "Fail"
 
    def get_device_ui(self, dut):
        self.mylogger.info(f"Getting Device UI {dut}")
        d = Device(dut)
        self.mylogger.debug(d)
        return d

    def get_ui_screenshot(self, dut, filename):
        self.mylogger.info(f"Getting UI Screenshot for Device{dut}")
        d = Device(dut)
        return d.screenshot(filename)

    def dump_logcat(self, connection):
        self.adbloglist = []
        loglist_index = len(self.adbloglist)
        self.adblogger.debug(loglist_index)
        temp = []
        while True:
            data = connection.read(1024)
            if not data:
                break
            self.adblogger.info(data.decode("utf-8"))
            temp.append(str(data.decode("utf-8")))
        if len(temp) < 1:
            self.adbloglist.append("No console output available")
        else:
            lst_string = "".join(map(str, self.adbloglist))
            for items in temp:
                self.adbloglist.append(items)
        connection.close()

    def adb_connection(self, dut):
        """_summary_

        Args:
            dut (_type_): _description_
            retry (_type_): _description_
        """
        # Default is "127.0.0.1" and 5037
        client = AdbClient(host="127.0.0.1", port=5037)
        devices = client.devices()
        for device in devices:
            self.mylogger.debug(device.serial)
        if len(devices) == 0:
            self.mylogger.info("no device connected")
            quit()
        self.mylogger.debug(client)
        self.mylogger.debug(client.version())
        device = client.device(str(dut))
        self.mylogger.debug(device)
        return device

    def adb_shell(self, device, cmd, test_name):
        """_summary_"""
        if isinstance(cmd, list):
            data_list = []
            for items in cmd:
                device.shell(items, handler=self.dump_logcat)
                screenshot = device.screencap()
                screenshot_file = (
                    log_dir + test_name + "_" + str(cmd.index(items)) + ".png"
                )
                with open(screenshot_file, "wb") as fp:
                    fp.write(screenshot)
                    time.sleep(15)
            # return self.adbloglist[-1]
            return self.adbloglist

        elif isinstance(cmd, str):
            device.shell(cmd, handler=self.dump_logcat)
            screenshot = device.screencap()
            screenshot_file = log_dir + test_name + ".png"
            with open(screenshot_file, "wb") as fp:
                fp.write(screenshot)
                time.sleep(2)
            # return self.adbloglist[-1]
            return self.adbloglist

    def performance_kpi(self, test_name, cmd, kpi, iteration=2):
        """_summary_"""
        try:
            adb_cmd1 = cmd
            kpi_time = []
            adb_log_clean = "logcat -c"
            # adb_log_out = "logcat -d | grep 'ActivityTaskManager'"
            adb_log_out = "logcat -d | grep ' " + str(kpi) + "'"
            kpi_list = []
            for i in range(iteration):
                self.mylogger.info(
                    "Iteration : {} Started......\n".format(int(i) + 1)
                )
                data1 = self.adb_shell(
                    self.device_adb, adb_log_clean, test_name
                )
                # self.mylogger.info(data)
                t.sleep(2)
                data2 = self.adb_shell(self.device_adb, adb_cmd1, test_name)
                # self.mylogger.info(data)
                t.sleep(2)
                kpi_data = self.adb_shell(
                    self.device_adb, adb_log_out, test_name
                )
                t.sleep(5)
                kpi = "Displayed"
                for line in kpi_data:
                    # self.mylogger.info("KPI data - {}".format(line))
                    if kpi in line:
                        # self.mylogger.info("found {}".format(kpi_data))
                        kpi_time = str(line).split("+")[1]
                        self.mylogger.info(
                            "KPI Performance Time : {}".format(kpi_time)
                        )
                        kpi_time = self.convert_kpi_time(kpi_time)
                        kpi_list.append(kpi_time)
            # data = kpi_dict
            data = data2
            if iteration == (len(kpi_list)):
                kpi_dict = self.plt_graph(kpi_list, test_name)
                result = "Pass"
            else:
                result = "Fail"
        except Exception as exerror:  # pylint: disable=broad-except
            self.mylogger.exception("Exception Occured from performance kpi function", exc_info=True)
            data = ["Exception Occured from performance kpi function"]
            result = "Fail"
        finally:
            return result, data
        

    def convert_kpi_time(self, time):
        """_summary_

        Args:
            time (_type_): _description_

        Returns:
            _type_: _description_
        """
        try:
            # ms = re.search(r"s(.*?)ms", time).group(1)
            # sec = str(time).split(ms)[0].replace("s", "")
            # total_msec = (int(sec) * 1000) + int(ms)
            self.mylogger.info("Before converstion KPI Time : {}".format(time))
            total_msec = ''.join(i for i in time if i.isdigit())
            # total_msec = time
            # if "+" in total_msec:
            #     total_msec = str(time).replace("+", "")
            # elif "ms" in total_msec:
            #     total_msec = str(time).replace("ms", "")
            # elif "s" in total_msec:
            #     total_msec = str(time).replace("s", "")
            # elif "m" in total_msec:
            #     total_msec = str(time).replace("m", "")
            self.mylogger.info("After converstion KPI Time : {}".format(total_msec))
        except Exception as exerror:  # pylint: disable=broad-except
            self.mylogger.exception(
                "Exception Occured from convert kpi function", exc_info=True
            )
            total_msec = 0
        finally:
            return int(total_msec)

    def plt_graph(self, data, test_name):
        """_summary_

        Args:
            data (_type_): _description_
            test_name (_type_): _description_

        Returns:
            _type_: _description_
        """
        mydict = {}
        for i in range(1, len(data) + 1):
            mydict[i] = data[i - 1]

        # df = pd.DataFrame([mydict])
        df = pd.DataFrame(
            mydict.items(), columns=["Iteration", "Time in Milliseconds"]
        )
        # displaying the DataFrame
        print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))
        print(tabulate(pd.DataFrame(data).describe()))
        names = list(mydict.keys())
        values = list(mydict.values())

        bar_color = ["red" if int(i) > 1000 else "green" for i in mydict.values()]

        # bar_color = [{ p>1301: 'red', 1001>=p<=1300: 'orange', p<1000: 'green' }[True] for p in mydict.values()]
        plt.figure()
        plt.bar(
            names, values, tick_label=names, align="center", color=bar_color
        )
        # title = str(test_name).upper().split("_")[-1] + " - App Launch Performance Report"
        title = str(test_name).replace("test_", "").replace("_", " ")
        plt.title(title)
        plt.xlabel('Iteration')
        plt.ylabel("Time in Milliseconds")
        for i in range(len(values)):
            plt.annotate(str(values[i]), xy=(names[i],values[i]), ha='center', va='bottom')
        file_graph = results_dir + test_name + "_graph.png"

        #add horizontal line at mean value of y
        plt.axhline(y=np.nanmean(df.values), color='orange', linestyle='--', linewidth=3, label='Avg')

        plt.savefig(file_graph)
        # plt.show()
        # plt.clf()
        return mydict

    def func_app_launch(self, test_name, cmd, ref_str, iteration=1):
        """_summary_

        Args:
            test_name (_type_): _description_
            cmd (_type_): _description_
            ref_str (_type_): _description_
            iteration (int, optional): _description_. Defaults to 1.

        Returns:
            _type_: _description_
        """
        try:
            adb_cmd = cmd
            adb_log_clean = "logcat -c"
            ref_str = "Displayed"
            adb_log_out = "logcat -d | grep ' " + str(ref_str) + "'"
            for i in range(iteration):
                self.mylogger.info(
                    "Iteration : {} Started......\n".format(int(i) + 1)
                )
                log_clean = self.adb_shell(
                    self.device_adb, adb_log_clean, test_name
                )
                t.sleep(2)
                cmd_exec = self.adb_shell(self.device_adb, adb_cmd, test_name)
                # self.mylogger.info(cmd_exec)
                t.sleep(2)
                cmd_out = self.adb_shell(
                    self.device_adb, adb_log_out, test_name
                )
                t.sleep(5)
                # self.mylogger.info(cmd_out)                
                for line in cmd_out:
                    if ref_str in line:
                        result = "Pass"
                    else:
                        result = "Fail"
                data = cmd_out        
        except Exception as exerror:  # pylint: disable=broad-except
            self.mylogger.exception("Exception Occured from performance kpi function", exc_info=True)
            data = ["Exception Occured from performance kpi function"]
            result = "Fail"
        finally:
            func_name = inspect.stack()[0][3][5:]
            self.mylogger.info("Test : {} - {} - {}".format(test_name, func_name, result))
            return result, data            

    def func_exec_cmd(self, test_name, cmd, iteration=1):
        """_summary_

        Args:
            test_name (_type_): _description_
            cmd (_type_): _description_
            kpi (_type_): _description_
            iteration (int, optional): _description_. Defaults to 1.

        Returns:
            _type_: _description_
        """
        try:
            adb_cmd = cmd
            for i in range(iteration):
                self.mylogger.info(
                    "Iteration : {} Started......\n".format(int(i) + 1)
                )
                t.sleep(2)
                cmd_exec = self.adb_shell(self.device_adb, adb_cmd, test_name)
                # self.mylogger.info(cmd_exec)
                t.sleep(2)
                result = "Pass"
        except Exception as exerror:  # pylint: disable=broad-except
            self.mylogger.exception("Exception Occured from performance kpi function", exc_info=True)
            data = ["Exception Occured from performance kpi function"]
            result = "Fail"
        finally:
            return result, cmd_exec

    def func_videoplayback_stats(self, test_name):
        """_summary_

        Args:
            test_name (_type_): _description_

        Returns:
            _type_: _description_
        """
        try:
            adb_cmd1 = self.cfg_avstats["video_stats_cmd"]
            data = self.adb_shell(self.device_adb, adb_cmd1, test_name)
            # self.mylogger.info(data)

            if isinstance(data, list):
                data = ''.join(str(x) for x in data)

            for items in self.cfg_avstats["video_stats_pass"]:
                if items in data:
                    # self.mylogger.info("Video stats - {} found".format(items))
                    result = "Pass"
                else:
                    result = "Fail"
                    self.mylogger.error("Video stats - {} not found".format(items))
                    break
            for items in self.cfg_avstats["video_stats_stop"]:
                if items not in data:
                    # self.mylogger.info("Video stats - {} not found".format(items))
                    result = "Pass"
                else:
                    result = "Fail"
                    self.mylogger.error("Video stats - {} found".format(items))
                    break
        except:
            self.mylogger.exception("Exception occured from function : {}".format(__name__))
            result = "Fail"
            data = ["Exception Error occurred"]
        finally:
            func_name = inspect.stack()[0][3][5:]
            self.mylogger.info("Test : {} - {} - {}".format(test_name, func_name, result))
            return result, data            

    def func_extra(self, extra, result, data, test_name):
        """_summary_

        Args:
            extra (_type_): _description_
            result (_type_): _description_
            data (_type_): _description_
            test_name (_type_): _description_
        """
        extra.append(extras.text(result, name="Test Status"))
        extra.append(extras.text(data, name="Result Summary"))
        extra.append(extras.text(str(datetime.now()), name="Test End Time"))

        screenshots = [
            fileName
            for fileName in os.listdir("logs/")
            if fileName.startswith(test_name)
        ]
        # self.mylogger.info(screenshots)
        if len(screenshots) > 0:
            if isinstance(screenshots, list):
                screenshot = img_path + screenshots[-1]
            elif isinstance(screenshots, str):
                screenshot = img_path + screenshots
            extra.append(extras.image(screenshot, name="Screenshot"))
        else:
            extra.append(extras.image("No Image available", name="Screenshot"))
        assert result == "Pass", (
            "Test status: {}, Result Summary: {}",
            result,
            data,
        )

    def depends_tests(self, test_name):
        """_summary_

        Args:
            test_name (_type_): _description_

        Returns:
            _type_: _description_
        """
        test_status = "NA"
        test_report = conftest.test_report
        for key in test_report.keys():
            if test_name in test_report[key]['test_name']:
                self.mylogger.info("Test Case found")
                if test_report[key]['test_status'] == "passed":
                    test_status = "Pass"
                elif test_report[key]['test_status'] == "failed":
                    test_status = "Fail"
        return test_status


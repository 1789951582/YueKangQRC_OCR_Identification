import paddlehub as hub
import cv2
import os
import re
import zxing
import json
import time
import pymysql
import mysql.connector
import pyzbar.pyzbar as pyzbar
from PIL import Image,ImageEnhance

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

def get_QRC_data(img_path_list):
    print("正在解析二维码，默认使用zxing模块")
    QRC_data_list=[]
    reader = zxing.BarCodeReader()
    for img_path in img_path_list:
        QRC_data = reader.decode(img_path).parsed
        if len(QRC_data):
            print(img_path+"识别成功")
        else:
            print("由于zxing模块无法识别"+img_path+"，正在转到pyzbar模块执行")
            img = Image.open(img_path)
            while (1):#循环执行直到pyzbar识别成功
                barcodes = pyzbar.decode(img, symbols=[pyzbar.ZBarSymbol.QRCODE])
                if barcodes == []:
                    img = img.crop((0 + 10, 0 + 50, img.size[0] - 10, img.size[1] - 100))
                    img = ImageEnhance.Brightness(img).enhance(1.5)
                    # img = ImageEnhance.Color(img).enhance(1.5)
                    img = ImageEnhance.Contrast(img).enhance(1.5)
                    img.show()
                else:
                    for barcode in barcodes:
                        QRC_data = barcode.data.decode('UTF-8')
                        # print(barcodesData)
                    print(img_path + "识别成功")
                    break
        QRC_data_list.append(json.loads(QRC_data))
        print(QRC_data)
    return QRC_data_list

def file_process(file_path):
    print("正在获取图片路径")
    img_path_list=[]
    for _, _, files in os.walk(file_path, topdown=False):
        for img_name in files:
            img_path_list.append(f"{file_path}/{img_name}")
    return img_path_list

def get_ocr_data(img_path_list):
    print("正在读取图片文字")
    #加载预训练模型
    ocr = hub.Module(name="chinese_ocr_db_crnn_server")
    #读取照片路径
    np_images =[cv2.imread(image_path) for image_path in img_path_list]
    results = ocr.recognize_text(
                        images=np_images,         # 图片数据，ndarray.shape 为 [H, W, C]，BGR格式；
                        use_gpu=True,            # 是否使用 GPU；若使用GPU，请先设置CUDA_VISIBLE_DEVICES环境变量
                        output_dir='ocr_result',  # 图片的保存路径，默认设为 ocr_result；
                        visualization=True,       # 是否将识别结果保存为图片文件；
                        box_thresh=0.7,           # 检测文本框置信度的阈值；
                        text_thresh=0.5)          # 识别中文文本置信度的阈值；
    print(results)
    return results
def analyse(QRC_data_list,results):
    user_data = []
    time_re = re.compile('([\d]+)', re.S)
    # is_72=False #是否有72小时核酸证明
    # name_reg=re.compile('(.*?)管理')
    # btn_bobao_reg=re.compile(".*?播报")

    for idx, result in enumerate(results):
        temp_data_list = {}
        data = result['data']
        # begin_id = 0
        for info_idx, infomation in enumerate(data):
            # print(infomation['text'])
            #     print(QRC_data_list[idx]["name"])
            #     if re.search(QRC_data_list[idx]["name"]+".*?",infomation['text']):
            #         print(infomation)
            #         continue
            if re.search(".*?播报", infomation['text']):  # 找到参照点
                # print(infomation)
                # 名字
                for i in range(info_idx - 1, 0, -1):
                    if (re.search(QRC_data_list[idx]["name"] + ".*?", data[i]['text']) != None):  # 判断name是否与二维码一致
                        temp_data_list["name"] = QRC_data_list[idx]['name']
                        break
                else:  # 没找到返回错误并结束循环
                    print("error")
                    break
                # 时间
                for t in range(info_idx+1,info_idx+3,1):
                    if len(data[t]["text"])>=10:
                        # 格式化识别时间
                        time_temp1=""
                        time_text=""
                        time_text_list = time_re.findall(data[t]["text"])
                        for i in time_text_list:
                            time_temp1 += i
                        for i in range(0, len(time_temp1), 2):
                            time_text += time_temp1[i:i + 2] + "-"
                        # print(time_text)
                        # print(QRC_data_list[idx]["t"])
                        # 开始
                        # if QRC_data_list[idx]["t"] <= time.mktime(time.strptime(time.strftime("%Y") + "-" + time_text,"%Y-%m-%d-%H-%M-%S-")) and QRC_data_list[idx]["t"] + 600 >= time.mktime(time.strptime(time.strftime("%Y") + "-" + time_text, "%Y-%m-%d-%H-%M-%S-")):
                        if QRC_data_list[idx]["t"] <= time.mktime(
                                time.strptime("2022" + "-" + time_text, "%Y-%m-%d-%H-%M-%S-")) and \
                                QRC_data_list[idx]["t"] + 600 >= time.mktime(
                                time.strptime("2022" + "-" + time_text, "%Y-%m-%d-%H-%M-%S-")):
                            temp_data_list["time"] = QRC_data_list[idx]["t"]
                        else:
                            print("error")
                            # break
                        break
                continue
            if re.search(".*?健康信息", infomation['text']):
                for i in range(info_idx - 1, info_idx - 3, -1):
                    if re.search(".*?码", data[i]['text']) != None:
                        temp_data_list["QRC_Color"] = data[i]['text']
                        break
                else:
                    print("error")
                    break
                for i in range(info_idx + 2, info_idx + 6, 1):
                    if data[i]['text'] == "24" or data[i]['text'] == "48" or data[i]['text'] == "72":
                        temp_data_list["check_time"] = data[i]['text']
                        break
                    if data[i]['text'] == "阴性":
                        temp_data_list['check_time'] = 0
                        break
                    if data[i]['text'] == "阳性":
                        temp_data_list['check_time'] = -1
                        break
                for i in range(info_idx + 4, info_idx + 7, 1):
                    # print(data[i]['text'])
                    if data[i]['text'] == "已完成全程接种":
                        temp_data_list['vaccine'] = 1
                        break
                else:
                    temp_data_list["vaccine"] = 0
                break
        try:
            temp_data_list['id'] = QRC_data_list[idx]['cid']
            temp_data_list['idtype'] = QRC_data_list[idx]["cidtype"]
            temp_data_list["phone_num"] = QRC_data_list[idx]['phone']
        except KeyError as phone:
            print("注意:"+QRC_data_list[idx]['name']+"上传的粤康码不含手机号码")
            temp_data_list["phone_num"] = 0
        # print(temp_data_list)
        user_data.append(temp_data_list)
    return user_data

def write(user_data_list):
    print("执行写入数据库操作")
    host='127.0.0.1'
    user='root'
    passwd='123qwe'
    database='yuekangma'
    try:
        db = pymysql.connect(host=host, user=user, passwd=passwd, database=database, charset='utf8')
        cursor = db.cursor()
    except pymysql.err.OperationalError:
        print("检测到未创建数据库,自动创建")

        mydb = mysql.connector.connect(
            host=host,
            user=user,
            passwd=passwd
        )
        mycursor = mydb.cursor()
        mycursor.execute("CREATE DATABASE yuekangma")
        db = pymysql.connect(host=host, user=user, passwd=passwd, database=database, charset='utf8')

        # 使用 cursor() 方法创建一个游标对象 cursor
        cursor = db.cursor()
        # 使用 execute() 方法执行 SQL，如果表存在则删除
        # cursor.execute("DROP TABLE IF EXISTS USER_DATA_TABLE")
        # 使用预处理语句创建表
        sql = """CREATE TABLE employee (
             name  TEXT NOT NULL,
             time  LONG NOT NULL,
             qrccolor TEXT NOT NULL,  
             checktime TEXT NOT NULL ,
             vaccine int NOT NULL,
              id TEXT NOT NULL,
              idtype TEXT NOT NULL, 
              phonenum TEXT NOT NULL )"""
        cursor.execute(sql)

    for user_data in user_data_list:
        # print(user_data)
        search =f"select name,id from employee where name = '{user_data['name']}' and id ='{user_data['id']}'"
        if cursor.execute(search):
            sql = f"UPDATE employee SET time = '{user_data['time']}',qrccolor = '{user_data['QRC_Color']}',checktime = '{user_data['check_time']}',vaccine='{user_data['vaccine']}' where name = '{user_data['name']}' and id ='{user_data['id']}'"
        else:
            sql = f"insert into employee values ('{user_data['name']}','{user_data['time']}','{user_data['QRC_Color']}','{user_data['check_time']}','{user_data['vaccine']}','{user_data['id']}','{user_data['idtype']}','{user_data['phone_num']}') "
        cursor.execute(sql)
    db.commit()
    cursor.close()
    db.close()

if __name__ == '__main__':
    img_path_list=file_process("./image")
    QRC_data_list =get_QRC_data(img_path_list)
    results = get_ocr_data(img_path_list)
    user_data_list=analyse(QRC_data_list,results)
    write(user_data_list)


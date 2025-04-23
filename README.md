# 粤康码识别校验归档脚本

### 简介

此脚本是我在口罩时期编写的，目的是帮助辅导员识别粤康码的数据，并归档到数据库

脚本会先扫描图片二维码信息，再比较图片上的文字，无异常的会写进数据库，有异常的报错。

### 使用前准备

请根据[官方文档](https://www.paddlepaddle.org.cn/install/quick?docurl=/documentation/docs/zh/install/pip/windows-pip.html)安装paddlepaddle

安装[PaddleHub](https://www.paddlepaddle.org.cn/tutorials/projectdetail/520792)

安装图像识别模型[chinese_ocr_db_crnn_server](https://www.paddlepaddle.org.cn/hubdetail?name=chinese_ocr_db_crnn_server&en_category=TextRecognition)

```shell
hub install chinese_ocr_db_crnn_server==1.2.0
```

python包

```shell
pip install paddlehub paddlepaddle opencv-python zxing pymysql mysql-connector-python pyzbar pillow
```

### 使用方法

把粤康码截图放到image文件夹然后运行脚本即可

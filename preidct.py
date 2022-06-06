import os
import pymysql
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle

from datetime import date
from sklearn.preprocessing import MinMaxScaler
from keras import layers
from keras import models

model_dir = "D:\\models"
db = pymysql.connect(host='localhost',user='root',password='123456',database='stock_info')
cursor = db.cursor()


def model_define():
    model = models.Sequential()
    model.add(layers.GRU(50,return_sequences=True))
    model.add(layers.Dropout(0.1))
    model.add(layers.GRU(50,return_sequences=True))
    #model.add(layers.Dropout(0.2))
    model.add(layers.GRU(50))
    model.add(layers.Dropout(0.3))
    model.add(layers.Dense(units=1))
    return model


def one_dataset_prepare(one_stock_price_list,step):
    # 先把元组格式拆分
    stock_code = one_stock_price_list[0][0]
    stock_price_list = [stock[2] for stock in one_stock_price_list]
    # 划分训练集和数据集
    train_set = np.asarray(stock_price_list[:]).reshape(-1,1)

    # 归一化
    sc = MinMaxScaler(feature_range=[0,1])
    train_set_scaled = sc.fit_transform(train_set)
    
    # 存储sc，以便预测时使用
    with open(os.path.join(model_dir,stock_code+'.sc'),'w') as f:
        f.write(pickle.dumps(sc))

    # 按照步长转换训练集和测试集
    x_train = []
    y_train = []
    for i in range(step,train_set_scaled.shape[0]):
        x_train.append(train_set_scaled[i-step:i])
        y_train.append(train_set_scaled[i,0])
    x_train,y_train = np.array(x_train),np.array(y_train)

    
    return x_train,y_train #,x_test,y_test

def dataset_prepare(one_stock_price_list,test_radio,step):
    # 先把元组格式拆分
    stock_code = one_stock_price_list[0][0]
    stock_price_list = [stock[2] for stock in one_stock_price_list]
    # 划分训练集和数据集
    label = int((1-test_radio)*len(stock_price_list))
    train_set = np.asarray(stock_price_list[:label]).reshape(-1,1)
    test_set = np.asarray(stock_price_list[label-30:]) .reshape(-1,1)

    # 归一化
    sc = MinMaxScaler(feature_range=[0,1])
    train_set_scaled = sc.fit_transform(train_set)
    test_set_scaled = sc.transform(test_set)

    # 存储sc，以便预测时使用
    with open(os.path.join(model_dir,stock_code+'.sc'),'w') as f:
        f.write(pickle.dumps(sc))

    # 按照步长转换训练集和测试集
    x_train = []
    y_train = []
    for i in range(step,train_set_scaled.shape[0]):
        x_train.append(train_set_scaled[i-step:i])
        y_train.append(train_set_scaled[i,0])

    x_test = []
    y_test = []
    for i in range(step,test_set_scaled.shape[0]):
        x_test.append(test_set_scaled[i-step:i,0])
        y_test.append(test_set_scaled[i,0])

    x_train,y_train = np.array(x_train),np.array(y_train)
    x_test,y_test = np.array(x_test),np.array(y_test)
    x_test = np.reshape(x_test,(x_test.shape[0],x_test.shape[1],1))
    
    return x_train,y_train,x_test,y_test

def fit_model(model,x_train,y_train):
    # 模型编译
    model.compile(optimizer='rmsprop',loss='mae',metrics=['accuracy'])
    # 模型训练
    history = model.fit(x_train,y_train,epochs=60,batch_size=64)
    return model,history

def get_sc(stock_code):
    with open(os.path.join(model_dir,stock_code+'.sc'),'w') as f:
        sc = pickle.load(f.read())
    return sc

def show_info(history):
    '''
    绘制损失图像
    '''
    loss = history.history['loss']
    epochs = range(1,len(loss)+1)
    plt.plot(epochs,loss,'bo',label='Training loss')
    plt.title('Training and validation loss')
    plt.legend()
    plt.show()

def show_predict(model,x_test,y_test,train_data_list):
    '''
    通过传入的测试集，进行测试图像的绘制以便用于展示
    '''
    # TODO 添加一个把绘制图像保存的功能
    predict_price = model.predict(x_test)
    stock_code = train_data_list[0][0]
    sc = get_sc(stock_code)
    predict_price = sc.inverse_transform(predict_price)
    true_price = sc.inverse_transform(y_test.reshape(-1,1))
    stock_name = train_data_list[0][1]
    date_list = [x[1] for x in train_data_list]
    true_pd = pd.DataFrame(data = true_price, index=date_list[len(date_list) - len(true_price):])
    predict_pd = pd.DataFrame(data=predict_price, index=date_list[len(date_list) - len(true_price):])
    plt.figure(figsize=(25, 9))
    plt.plot(true_pd, color='red',label="{} predict stock_price".format(stock_name))
    plt.plot(predict_pd ,color='blue',label='{} true stock price'.format(stock_name))
    plt.title("{} stock price".format(stock_name))
    plt.xlabel("Time")
    plt.ylabel("Stock Price")
    plt.legend()
    plt.show()

def train_and_show(train_data_list):
    '''
    train_data_list：股票历史数据列表,每个数据的格式为(code,name,close)元组
    '''
    x_train,y_train,x_test,y_test = dataset_prepare(train_data_list,0.2,30)
    model = model_define()
    model,history = fit_model(model,x_train,y_train)
    show_info(history)
    show_predict(model,x_test,y_test,train_data_list)
    model.save(os.path.join(model_dir,train_data_list[0][0]+'.h5'))


def one_predict(code,history):
    '''
    传入前30个交易日的股价信息，获取下一个交易日的股价预测值

    '''
    sc = get_sc(code)
    model = models.load_model(os.path.join(model_dir,code+'.h5'))
    history = np.array(history).reshape(-1,1)
    history = sc.transform(history)
    history = np.reshape(history,(1,30,1))
    predict_value = model.predict(history)
    predict_value = sc.inverse_transform(predict_value.reshape(-1,1))
    return predict_value[0][0]

def train_total(train_data_list):
    '''
    train_data_list：股票历史数据列表,每个数据的格式为(code,name,close)元组
    '''
    x_train,y_train = one_dataset_prepare(train_data_list,30)
    model = model_define()
    model,history = fit_model(model,x_train,y_train)
    show_info(history)
    model.save(os.path.join(model_dir,train_data_list[0][0]+'.h5'))



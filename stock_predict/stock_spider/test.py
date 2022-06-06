from spider import stock_histroy_info
#from keras.models import load_model
# import pickle
# import numpy as np
import json

# model_hs300 = load_model(r'C:\Users\12554\Desktop\models\510300.XSHG.h5')
# with open(r'D:\models\510300.XSHG.sc','rb') as f:
#     sc_hs300 = pickle.loads(f.read())

history = stock_histroy_info('1.510300','20220506',30)["klines"]
# #print(history)
close_pirce = [float(str(x).split(',')[2]) for x in history]
# # print(len(close_pirce))
import requests
post_data = {
    "history_list":close_pirce,
    "stock_code":"510300.XSHG"
}
# data = json.dumps(post_data)



# history = close_pirce
# print(history)
from time import time
start = time()
# history = np.array(history).reshape(-1,1)
# history = sc_hs300.transform(history)
# history = np.reshape(history,(1,30,1))
# predict_value = model_hs300.predict(history)
# predict_value = sc_hs300.inverse_transform(predict_value.reshape(-1,1))
# my_value = predict_value[0][0]
# print(my_value)

res = requests.post("http://49.233.19.128:8080/index/",data=post_data)
print(res.content.decode())
d = json.loads(res.content.decode())
print(d["predict_value"])
print(type(d["predict_value"]))
end = time()
print(end-start)
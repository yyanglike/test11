import numpy as np
import pandas as pd
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from keras.layers import RepeatVector, TimeDistributed
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

# 加载数据
data = pd.read_csv('stock_data.csv')  # 假设你的股票数据在这个文件中

# 如果股票文件中有多个股票的数据存在，可以通过循环来训练每个股票的模型
for stock in data['stock_code'].unique():
    stock_data = data[data['stock_code'] == stock]
    stock_data = stock_data['close'].values  # 我们只使用收盘价
    stock_data = stock_data.astype('float32')

    # 数据归一化
    scaler = MinMaxScaler(feature_range=(0, 1))
    stock_data = scaler.fit_transform(stock_data.reshape(-1, 1))

    # 划分训练集和测试集
    train_size = int(len(stock_data) * 0.80)
    test_size = len(stock_data) - train_size
    train, test = stock_data[0:train_size, :], stock_data[train_size:len(stock_data), :]

    # 转换数据为LSTM所需的格式
    def create_dataset(dataset, look_back=1):
        dataX, dataY = [], []
        for i in range(len(dataset) - look_back - 1):
            a = dataset[i:(i + look_back), 0]
            dataX.append(a)
            dataY.append(dataset[i + look_back, 0])
        return np.array(dataX), np.array(dataY)

    look_back = 1
    trainX, trainY = create_dataset(train, look_back)
    testX, testY = create_dataset(test, look_back)

    # LSTM需要输入为[samples, time steps, features]的格式
    trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
    testX = np.reshape(testX, (testX.shape[0], 1, testX.shape[1]))

    # 定义Autoencoder模型
    model = Sequential()
    model.add(LSTM(100, activation='relu', input_shape=(1,look_back)))
    model.add(RepeatVector(1))
    model.add(LSTM(100, activation='relu', return_sequences=True))
    model.add(TimeDistributed(Dense(1)))
    model.compile(optimizer='adam', loss='mse')

    # 训练Autoencoder模型
    model.fit(trainX, trainX, epochs=300, verbose=0)

    # 使用Autoencoder提取特征
    trainX_encoded = model.predict(trainX)
    testX_encoded = model.predict(testX)

    # 使用提取的特征训练LSTM模型
    model = Sequential()
    model.add(LSTM(50, activation='relu', input_shape=(1, look_back)))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')

    model.fit(trainX_encoded, trainY, epochs=300, verbose=0)

    # 预测
    trainPredict = model.predict(trainX_encoded)
    testPredict = model.predict(testX_encoded)

    # 反归一化
    trainPredict = scaler.inverse_transform(trainPredict)
    trainY = scaler.inverse_transform([trainY])
    testPredict = scaler.inverse_transform(testPredict)
    testY = scaler.inverse_transform([testY])

    # 绘制原始数据和预测结果
    plt.plot(scaler.inverse_transform(stock_data))
    plt.plot(np.concatenate((trainPredict,testPredict),axis=0))
    plt.show()


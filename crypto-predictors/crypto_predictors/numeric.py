import pandas as pd
import numpy as np
from sklearn import linear_model
from typing import List


def simple_linear_regression(
    x_learn: List[int], y_learn: List[float], x_predict: List[int]
) -> pd.Series:
    model = linear_model.LinearRegression()
    fitted = model.fit(x_learn.reshape(-1, 1), y_learn.reshape(-1, 1))
    return fitted.predict(x_predict.reshape(-1, 1)).reshape(1, -1)[0]


def arima():
    pass


def knn():
    pass


if __name__ == "__main__":
    idx = [1, 2, 3, 4, 5]
    df = pd.DataFrame(columns=["0"])
    df.loc[1, 0] = 1
    print(type(df.index.values))
    xl = np.array([1, 2, 3, 4, 5])
    yl = np.array([1, 2, 3, 4, 5])
    xp = np.array([6, 7, 8, 9, 10])
    # reg = simple_linear_regression(xl, yl, xp)
    # for r in reg:
    #     print(f"1. {r}")
    # print(reg)

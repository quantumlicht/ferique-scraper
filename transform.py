class Transform:
    @staticmethod
    def transpose2d(arr):
        new_arr = []
        for i in range(0, len(arr[0])):
            tmp = []
            for j in range(0, len(arr)):
                tmp.append(arr[j][i])
            new_arr.append(tmp)

        return new_arr

    @staticmethod
    def prepend_col(data_arr, col):
        data_arr.append(col)
        for i, data in enumerate(data_arr):
            data.insert(0, col[i])

    @staticmethod
    def append_col(data_arr, col):
        for data, i in enumerate(data_arr):
            data.append(col[i])

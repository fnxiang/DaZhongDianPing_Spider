import csv


def check_shop(shop_id):
    with open('data/save_shop_id_03', 'r+') as file:
        lines = file.readlines()
        return lines.__contains__(shop_id)


def save_shop(shop_id):
    with open('data/save_shop_id_03', 'a+') as file:
        file.write(shop_id)


class Config():

    def __init__(self):
        self.cookie = None
        self.shop_id_list = []
        self.get_cookie()
        self.get_shop_list_from_excel()

    def get_cookie(self):
        with open('cookie') as file:
            self.cookie = file.read()

    def get_shop_list_from_excel(self, ):
        with open('data/shop_list_03.csv') as csv_file:
            reader = csv.reader(csv_file)
            header = next(reader)
            for row in reader:
                self.shop_id_list.append(row)

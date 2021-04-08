import requests
import re
import time
from lxml import etree
import random
import csv

class DaZhongDianPing():
    def __init__(self, url, csv_name):
        self.url = url + "/review_all"
        # 输出文件
        self.csv_name = csv_name
        # 页面 html
        self.html = None
        # 页面字体大小
        self.font_size = 14
        # 页面引用的 css 文件
        self.css = None
        # 商家地址使用的 svg 文件
        self.address_svg = None
        # 商家电话使用的 svg 文件
        self.tell_svg = None
        # 商家评论使用的 svg 文件
        self.review_svg = None
        # 记录csv文件写入
        self.write_flag = False

        # 字体码表，key 为 class 名称，value 为对应的汉字
        self.address_font_map = dict()
        self.tell_font_map = dict()
        self.review_font_map = dict()

        # 商家评论的最大页码数
        self.max_pages = None
        self.referer = self.url.replace('/review_all', '')
        self.timeout = 10
        self.headers = {
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': self.referer,
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cookie': 'Hm_lpvt_602b80cf8079ae6591966cc70a3940e7=1617856942; Hm_lvt_602b80cf8079ae6591966cc70a3940e7=1617856083; _lxsdk_s=178afbcb3ff-3d1-bc0-a58%7C%7C564; s_ViewType=10; ctu=e5076001f755d904667123b8be8cee8faa9c7bbada359dff6c94d43cb0796491; cy=2; cye=beijing; dper=8d717ffecfdbe496e0634b9f7596221e92a8bdeb8ec4cf2a0b93577e28ca30b0357318c2ccb37f6c3827d937e4f6e179826a2deec8c0cd01238abc7a652f9b28b3f9efcd9856f47cb90bb6d0b393c17fa872fda36741c6c18544fb1a06bc2452; dplet=92cab7e909546170543a80882bbdabca; ll=7fd06e815b796be3df069dec7836c3df; ua=dpuser_0547868996; _hc.v=c4064581-534b-a7f0-33e8-f6abfd867542.1617856083; _lx_utm=utm_source%3Dgoogle%26utm_medium%3Dorganic; _lxsdk=178afbcb3fec8-08ee321369e40d8-48183301-1aeaa0-178afbcb3fec8; _lxsdk_cuid=178afbcb3fec8-08ee321369e40d8-48183301-1aeaa0-178afbcb3fec8; fspop=test'
        }

    def get_max_pages(self):
        tree = etree.HTML(self.html)
        # print(tree.xpath('//div[@class="reviews-pages"]/a/text()'))
        self.max_pages = int(tree.xpath('//div[@class="reviews-pages"]/a/text()')[-2])

    def get_svg_html(self):
        # 获取商家评论页内容
        index_res = requests.get(self.url, headers=self.headers, timeout=self.timeout)
        time.sleep(2)
        self.html = index_res.text

        # 正则匹配 css 文件
        result = re.search('<link rel="stylesheet" type="text/css" href="//s3plus(.*?)">', self.html, re.S)
        if result:
            css_url = 'http://s3plus' + result.group(1)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'
            }
            css_res = requests.get(css_url, headers=headers)
            print(f'css_url:{css_url}')
            self.css = css_res.text

            # 正则匹配商家地址使用的 svg 文件 url
            result = re.search('bb\[class.*?background-image: url\((.*?)\);', self.css, re.S)
            address_svg_url = 'http:' + result.group(1)
            self.address_svg = requests.get(address_svg_url, headers=headers).text
            print(f'address_svg_url:{address_svg_url}')

            # 正则匹配商家电话号码使用的 svg 文件 url
            result = re.search('cc\[class.*?background-image: url\((.*?)\);', self.css, re.S)
            tell_svg_url = 'http:' + result.group(1)
            self.tell_svg = requests.get(tell_svg_url, headers=headers).text
            print(f'tell_svg_url:{tell_svg_url}')

            # 正则匹配评论使用的 svg 文件 url
            result = re.search('svgmtsi\[class.*?background-image: url\((.*?)\);', self.css, re.S)
            review_svg_url = 'http:' + result.group(1)
            self.review_svg = requests.get(review_svg_url, headers=headers).text
            print(review_svg_url)

    def get_font_map(self):
        # <bb class="xxx.*?"></bb>              地址
        # <cc class="xxx.*?"></cc>              电话
        # <svgmtsi class="xxx.*?"></svgmtsi>    评论
        # xxx 每天都会发生变化，所以动态匹配对应的前缀

        result = re.search('<bb class="(.*?)"></bb>', self.html, re.S)
        address_prefix = result.group(1)[:2]

        result = re.search('<cc class="(.*?)"></cc>', self.html, re.S)
        tell_prefix = result.group(1)[:2]

        result = re.search('<svgmtsi class="(.*?)"></svgmtsi>', self.html, re.S)
        review_prefix = result.group(1)[:2]


        """
        匹配 css 文件中格式为 '.' + self.prefix + (.*?){background:(.*?)px (.*?)px;} 的 css 样式

        匹配 svg 文件中格式为 <path id="(\d+)" d="M0 (\d+) H600"/> 的字段，其中 id 的值对应 xlink:href="#(\d+)" 的值，
        d="M0 (\d+) H600" 的值对应 background中 y轴的偏移量

        匹配 svg 文件中格式为 <textPath xlink:href="#(\d+)" textLength=".*?">(.*?)</textPath> 的字段，(.*?) 对应一串中文字符串，
        最终的字符 = 中文字符串[x轴偏移量 / 字体大小]
        :return:
        """


        address_class_list = re.findall('\.%s(.*?){background:(.*?)px (.*?)px;}' % address_prefix, self.css, re.S)
        tell_class_list = re.findall('\.%s(.*?){background:(.*?)px (.*?)px;}' % tell_prefix, self.css, re.S)
        review_class_list = re.findall('\.%s(.*?){background:(.*?)px (.*?)px;}' % review_prefix, self.css, re.S)

        address_svg_y_list = re.findall('<path id="(\d+)" d="M0 (\d+) H600"/>', self.address_svg, re.S)
        review_svg_y_words = re.findall('<text x=".*?" y="(.*?)">(.*?)</text>', self.review_svg, re.S)
        if not review_svg_y_words:
            review_svg_y_list = re.findall('<path id="(\d+)" d="M0 (\d+) H600"/>', self.review_svg, re.S)
            review_result = re.findall('<textPath xlink:href="#(\d+)" textLength=".*?">(.*?)</textPath>',
                                       self.review_svg, re.S)
            review_words_dc = dict(review_result)
            self.review_font_map = self.address_class_to_font(review_class_list, review_svg_y_list, review_words_dc, review_prefix)
        else:
            self.review_font_map = self.review_class_to_font(review_class_list, review_svg_y_words, review_prefix)

        address_result = re.findall('<textPath xlink:href="#(\d+)" textLength=".*?">(.*?)</textPath>', self.address_svg, re.S)
        tell_result = re.search('<text x="(.*?)" y=".*?">(.*?)</text>', self.tell_svg, re.S)
        tell_x_list = tell_result.group(1).split(' ')
        tell_words_str = tell_result.group(2)

        address_words_dc = dict(address_result)
        self.address_font_map = self.address_class_to_font(address_class_list, address_svg_y_list, address_words_dc, address_prefix)
        self.tell_font_map = self.tell_class_to_num(tell_class_list, tell_x_list, tell_words_str, tell_prefix)
        print(self.address_font_map)
        print(self.review_font_map)
        print(self.tell_font_map)

    def review_class_to_font(self, class_list, y_words, prefix):
        tmp_dc = dict()
        tmp = None
        for cname, x, y in class_list:
            for text_y, text in y_words:
                if int(text_y) >= abs(int(float(y))):
                    index = abs(int(float(x))) // self.font_size
                    tmp = text[index]
                    break
            tmp_dc[prefix + cname] = tmp
        return tmp_dc


    def address_class_to_font(self, class_list, y_list, words_dc, prefix):
        tmp_dc = dict()
        # 核心算法，将 css 转换为对应的字符
        for i in class_list:
            x_id = None
            for j in y_list:
                if int(j[1]) >= abs(int(float(i[2]))):
                    x_id = j[0]
                    break
            index = abs(int(float(i[1]))) // self.font_size
            if x_id is not None:
                tmp = words_dc[x_id][int(index)]
                tmp_dc[prefix + i[0]] = tmp
        return tmp_dc

    def tell_class_to_num(self, class_list, x_list, words_str, prefix):
        tmp_dc = dict()
        for i in class_list:
            x_index = None
            for index, num in enumerate(x_list):
                if int(num) >= abs(int(float(i[1]))):
                    x_index = index
                    break
            tmp = words_str[x_index]
            tmp_dc[prefix + i[0]] = tmp
        return tmp_dc

    def get_shop_info(self):
        # 将 self.html 商铺地址加密的 class 样式替换成对应的中文字符
        address_class_set = re.findall('<bb class="(.*?)"></bb>', self.html, re.S)
        for class_name in address_class_set:
            if class_name in self.address_font_map.keys():
                self.html = re.sub('<bb class="{}"></bb>'.format(class_name), self.address_font_map[class_name], self.html)

        # 将 self.html 电话号码加密的 class 样式替换成对应的数字
        tell_class_set = re.findall('<cc class="(.*?)"></cc>', self.html, re.S)
        for class_name in tell_class_set:
            self.html = re.sub('<cc class="{}"></cc>'.format(class_name), self.tell_font_map[class_name], self.html)

        tree = etree.HTML(self.html)
        shop_address = tree.xpath('//div[@class="address-info"]/text()')[0].replace('&nbsp;','').replace('\n','').replace(' ', '')
        shop_tell = tree.xpath('//div[@class="phone-info"]/text()')[0].replace('&nbsp;','').replace('\n','').replace(' ', '')

        print(f'地址：{shop_address}\n电话：{shop_tell}')


    def get_user_info(self):
        # 将 self.html 评论区域加密的 class 样式替换成对应的中文字符
        review_class_set = re.findall('<svgmtsi class="(.*?)"></svgmtsi>', self.html, re.S)
        for class_name in review_class_set:
            self.html = re.sub('<svgmtsi class="{}"></svgmtsi>'.format(class_name), self.review_font_map[class_name],
                               self.html)

        xhtml = etree.HTML(self.html)
        # 获取用户昵称
        user_name = xhtml.xpath('//div[@class="reviews-items"]/ul/li/div/div[1]/a/text()')
        user_name = [i.strip() for i in user_name]


        # 获取用户评论
        user_review = xhtml.xpath('//div[@class="review-words Hide"]')
        user_review_not_hide = xhtml.xpath('//div[@class="review-words"]')

        # 获取用户评论时间
        # comment_time = xhtml.xpath('//span[@class="time"]')

        review_list = [i.xpath('string(.)').replace(' ', '').replace('⃣', '.').replace('\n', '').replace('收起评价', '') for
                       i in user_review]
        review_list_not_hide = [i.xpath('string(.)').replace(' ', '').replace('⃣', '.').replace('\n', '').replace('收起评价', '').replace('\t', '').replace('[\'', '').replace('\']', '') for
                       i in user_review_not_hide]
        for comment in review_list_not_hide:
            review_list.append(comment);
        print(len(user_name), len(review_list))
        for i in review_list:
            print(i)
            print('-------------------------------------')
        count = 1;
        with open(self.csv_name, "a+", encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            if self.write_flag is False:
                writer.writerow(["用户名", "评论"])
                self.write_flag = True
            for j in range(0, len(review_list)):
                writer.writerow([user_name[j], review_list[j]])
                count = count+1;
            with open("continue.log", "w") as file:
                file.write(str(count+1))

    def run(self):
        self.get_svg_html()
        self.get_max_pages()
        self.get_font_map()
        self.get_shop_info()
        self.get_user_info()
        url = self.url;
        for i in range(0, self.max_pages+1):
            time.sleep(7)
            self.url = url+"/p"+str(i)
            self.get_svg_html()
            self.get_font_map()
            self.get_shop_info()
            self.get_user_info()


if __name__ == '__main__':
    url = "http://www.dianping.com/shop/issxn96WYmSEbdJv"
    csv_name = "shiqiaoshidi.csv"
    dz = DaZhongDianPing(url, csv_name)
    dz.run()

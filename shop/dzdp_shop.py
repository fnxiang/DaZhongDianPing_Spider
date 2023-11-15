import requests
import re
import time
from lxml import etree
import progressbar
import csv

address_prefix = ""
review_prefix = ""

class DaZhongDianPing():
    def __init__(self, url, csv_name, continue_flag, cookies):
        self.url = url
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
        # 断点续传标志位
        self.continue_flag = int(continue_flag)

        # 字体码表，key 为 class 名称，value 为对应的汉字
        self.address_font_map = dict()
        self.tell_font_map = dict()
        self.review_font_map = dict()

        # 商家评论的最大页码数
        self.max_pages = None
        self.referer = self.url.replace('/review_more#start=10', '')
        self.timeout = 10
        self.headers = {
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': self.referer,
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cookie': cookies
        }

    def get_max_pages(self):
        tree = etree.HTML(self.html)
        # print(tree.xpath('//div[@class="reviews-pages"]/a/text()'))
        try:
            page_index_xpath_content = tree.xpath('//div[@class="page"]/a/text()')
            if len(page_index_xpath_content) == 0:
                self.max_pages = 0
            else:
                self.max_pages = int(page_index_xpath_content[-2])
        except IndexError:
            print("Error: 现有Cookie无法访问到该网页或页面访问受限")
            raise IndexError

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
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15'
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
        try:
            global address_prefix
            global review_prefix
            result = re.search('<bb class="(.*?)"></bb>', self.html, re.S)
            address_prefix = result.group(1)[:2]

            result = re.search('<cc class="(.*?)"></cc>', self.html, re.S)
            tell_prefix = result.group(1)[:2]

            result = re.search('<svgmtsi class="shopNum">(.*?)</svgmtsi>', self.html, re.S)
            review_prefix = result.group(1)[:2]
        except AttributeError:
            print("Error: 未能获取到result，请重试")


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
        if tell_result is None:
            print("Error: 验证失效，请尝试手动验证")
            raise TypeError;
        tell_x_list = tell_result.group(1).split(' ')
        tell_words_str = tell_result.group(2)

        address_words_dc = dict(address_result)
        self.address_font_map = self.address_class_to_font(address_class_list, address_svg_y_list, address_words_dc, address_prefix)
        self.tell_font_map = self.tell_class_to_num(tell_class_list, tell_x_list, tell_words_str, tell_prefix)
        print(self.address_font_map)
        print(self.review_font_map)
        # print(self.tell_font_map)

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
        review_class_set = re.findall('<svgmtsi class="(.*?)"></svgmtsi>', self.html, re.S)
        for class_name in review_class_set:
            self.html = re.sub('<svgmtsi class="{}"></svgmtsi>'.format(class_name), self.review_font_map[class_name],
                               self.html)

        tree = etree.HTML(self.html)
        shop_name = tree.xpath('//div[@class="tit"]/a/h4')[0].replace('&nbsp;','').replace('\n','').replace(' ', '')
        # shop_tell = tree.xpath('//div[@class="phone-info"]/text()')[0].replace('&nbsp;','').replace('\n','').replace(' ', '')

        print(f'店铺名称：{shop_name}\n')

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

        # 获取评分
        rank_star_list = xhtml.xpath('//span[contains(@class, "sml")]')
        star_list = []
        for content in rank_star_list:
            star = content.attrib["class"].replace("sml-rank-stars sml-str", "").replace(" star", "")
            star_list.append(star)
            print(star)

        # 获取用户评论时间
        comment_time = xhtml.xpath('//span[@class="time"]')
        comment_list = [i.xpath('string(.)').replace(' ', '').replace('⃣', '.').replace('\n', '').replace('收起评价', '') for
                       i in comment_time]

        review_list = [i.xpath('string(.)').replace(' ', '').replace('⃣', '.').replace('\n', '').replace('收起评价', '') for
                       i in user_review]
        review_list_not_hide = [i.xpath('string(.)').replace(' ', '').replace('⃣', '.').replace('\n', '').replace('收起评价', '').replace('\t', '').replace('[\'', '').replace('\']', '') for
                       i in user_review_not_hide]
        for comment in review_list_not_hide:
            review_list.append(comment);
        print(len(user_name), len(review_list), len(comment_time))
        for i in review_list:
            print(i)
            print('-------------------------------------')

        with open(self.csv_name, "a+", encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            if self.write_flag is False:
                writer.writerow(["用户名", "评论", "评论时间", "评分"])
                self.write_flag = True
            for j in range(0, len(review_list)):
                star = 0
                if j < len(star_list):
                    star = star_list[j]
                writer.writerow([user_name[j], review_list[j], comment_list[j][0:10], star])
            self.continue_flag += 1
            with open("continue.log", "w") as log:
                log.write(str(self.continue_flag))

    def run(self):
        self.get_svg_html()
        self.get_max_pages()
        if self.continue_flag is 0:
            self.get_font_map()
            self.get_shop_info()
            self.get_user_info()
            self.continue_flag = 2
        else:
            self.write_flag = True
        url = self.url
        for i in range(self.continue_flag, self.max_pages+1):
            time.sleep(10)
            self.url = url+"/p"+str(i)
            print("正在获取："+url)
            self.get_svg_html()
            self.get_font_map()
            self.get_shop_info()
            self.get_user_info()


if __name__ == '__main__':
    with open("continue.log", "r+") as file:
        flag = file.read()
        cookies = '__mta=143563274.1618560794757.1618560794757.1618560794757.1; _lxsdk_cuid=178b09891a9c8-0d31520f0ac4f8-10114659-1aeaa0-178b09891a9c8; _lxsdk=178b09891a9c8-0d31520f0ac4f8-10114659-1aeaa0-178b09891a9c8; s_ViewType=10; ua=dpuser_0547868996; _hc.v=cbbd2ae0-2f4f-7e08-0fd1-4a5a3e36217e.1657027310; ctu=e5076001f755d904667123b8be8cee8f5a8f59ece63a5fbe8c36c8d5e4e4e71b; WEBDFPID=yyvx1u85638656u5113x511wu40vv73u816y1802vy797958zy529903-1980601020322-1665241015085OMSMOUG75613c134b6a252faa6802015be905513526; aburl=1; Hm_lvt_dbeeb675516927da776beeb1d9802bd4=1666789218; fspop=test; _lx_utm=utm_source%3Dgoogle%26utm_medium%3Dorganic; Hm_lvt_602b80cf8079ae6591966cc70a3940e7=1674186151; qruuid=42d0b541-0e0a-4879-a6cb-1aaba343ab1c; dplet=eda9c218a9636b24197fe4b43444527e; dper=854a0f81bc6dc23f3cda18d620ba32a79f8eb6eeabe5c651749862a57966f9173b67606ddddf6aaaf60b730b34abff0bf5f78e0d67a488726e75397a44c823a5; ll=7fd06e815b796be3df069dec7836c3df; cy=2; cye=beijing; Hm_lpvt_602b80cf8079ae6591966cc70a3940e7=1674186293; _lxsdk_s=185cd454eca-0d1-4-a31%7C%7C383'
        # '__mta=143563274.1618560794757.1618560794757.1618560794757.1; _lxsdk_cuid=178b09891a9c8-0d31520f0ac4f8-10114659-1aeaa0-178b09891a9c8; _lxsdk=178b09891a9c8-0d31520f0ac4f8-10114659-1aeaa0-178b09891a9c8; _hc.v=36bf09fa-1721-47b3-e058-3e04d3bafd89.1617870493; s_ViewType=10; ua=dpuser_0547868996; ctu=e5076001f755d904667123b8be8cee8f5d7331069b788974081b0fdf4b55b913; ll=7fd06e815b796be3df069dec7836c3df; fspop=test; Hm_lvt_602b80cf8079ae6591966cc70a3940e7=1645966602; dplet=a886f8d42e24365009ba648295361a37; dper=01a9994371ca7f6be4ea95373f1bcca2c6d9d2ef1b073dab42a6b89f1d3cb28d2ce4254b56e40abb908fc669193e44ca9848a460d077122b85833f64a3cdd66ed09458b9a1a635f35e3c5758dcf1e2b5a5f497a234613a146231ccbfb4dbfa9e; cy=2; cye=beijing; _lx_utm=utm_source%3Dbing%26utm_medium%3Dorganic; Hm_lpvt_602b80cf8079ae6591966cc70a3940e7=1645975981; _lxsdk_s=17f3bd02f4e-5f3-353-011%7C%7C21'
        cookies.encode("utf-8").decode("latin1")
        url = "https://www.dianping.com/shop/H3Fb3IoigP9Ky3bl"
        csv_name = "test.csv"
        dz = DaZhongDianPing(url, csv_name, flag, cookies)
        dz.run()
        file.truncate()
    with open("continue.log", "w") as file:
        file.write("0")
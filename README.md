# 大众点评商家店铺评论信息爬取

### 声明：

**项目基于 naiveliberty/DaZhongDianPing 改进，仅作为学习参考，不得用于商业用途。**
`dzdp_css_map_V1.1.py`等 文件来自于 https://github.com/naiveliberty/DaZhongDianPing

------

## 以下为原作者1.1版本相关信息
### 版本更新：

#### 2020-5-8

- 商户评论详情页面如果没有携带 cookies 访问，response 源码中电话号码后两位为 **；
- 商户评论详情页用户评论区域 svg 文件结构发生变化，新增了匹配规则;
- 美食分类页面（`http://www.dianping.com/shenzhen/ch10/g117`）,为携带 cookies 访问，返回的 html 源码为空;
- ~~dzdp_css_map_V1.0.py~~已失效，新增 `dzdp_css_map_V1.1.py`;
- 使用前请自行添加 Cookies。



| 作者    | 邮箱                 |
| ------- | -------------------- |
| liberty | fthemuse@foxmail.com |

##	1.2版本信息

### 改进

#### 2021-4-8

- 过滤address_font_map与words_dc  KeyError问题
- 新增div[@class="review-words"]`的评论获取(用户与评论信息可能不匹配问题)
- 可直接输出至CSV文件
- 解决Mac打开CSV文件乱码问题
- ~~增加简单的断点续传问题~~（已完善该功能，只针对当前店铺）
- 新增``dzdp_css_map_V1.2.py``
- 新增爬取商家所有评论信息**

### ⚠️注意

- 需自行添加cookies
- 页面爬取信息注意间隔
- 如遇到`self.max_pages`数组越界，请尝试刷新页面手动验证
- 抓取一个新的店铺前，请保证`continue.log`里面值为0
- PERMISSION ERROR 需要重新登录刷新cookie(cookie维度封锁，没找到解法)

| 作者    | 邮箱                 |
| ------- | -------------------- |
| fring | fnxiang@bjtu.edu.cn |


## 环境依赖

```
pip3 install -r requirements.txt
```



## 分析过程

详见：`https://blog.csdn.net/saberqqq/article/details/105977645`
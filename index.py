from bs4 import BeautifulSoup
from selenium import webdriver
import json
import os
import sys
import time
from selenium.webdriver.common.by import By
import requests
from functools import cmp_to_key

# 用于存储只处理一次的规则的规则名
parsed_rule = []
def init_parse(html,rules):
    global parsed_rule,sort_rule,log_level
    global page_num
    datas = {} # 最终接受爬取到数据的列表
    # 遍历爬虫规则
    for i in rules:
        # 如果为已执行一次的规则且已执行过则跳过
        if(i in parsed_rule):
            continue;
        rule = rules[i]
        # 判断是否只执行一次的规则
        if('only_one' in rule):
            parsed_rule.append(i);
        # 判断是否需排序的规则
        if('sort' in rule and not(i in sort_rule)):
            sort_rule[i] = rule['sort']
        # 判断规则类型
        if(rule['type'] == 'list'):
            # 根据规则css选择器获取元素列表
            conts = html.select(rule['css'])
            if(log_level == 'debug'):
                print(conts)
            print("共"+str(len(conts))+"条数据")
            # 根据规则索引截取元素列表
            if(rule['start']):
                print("==========")
                if(rule['end']):
                    conts = conts[rule['start']:len(conts) + rule['end']]
                else:
                    conts = conts[rule['start']:len(conts)]
            list_data = []
            index = 1
            # 根据规则目标对象进行爬取数据
            for j in conts:
                print("正在处理第"+ str(page_num)+"页，第" + str(index)+"条数据")
                index+=1
                # 单条数据
                data = {}
                for k in rule['targets']:
                    # 获取元素
                    if(log_level == 'debug'):
                        print(k['css'])
                        print(j.select_one(k['css']))
                        print(k)
                    ele=j.select_one(k['css'])
                    data[k['kw']] = parse_data_item(ele,k)
                    
                list_data.append(data)
            datas[i] = list_data;
            # print(datas)
        else:
            one_data = {}
            for k in rule['targets']:
                    if(log_level == 'debug'):
                        print(k)
                    # 获取元素
                    ele=html.select_one(k['css'])
                    one_data[k['kw']] = parse_data_item(ele,k)
            datas[i] = one_data;
    return datas
_id_ = ''
def parse_data_item(ele,conf):
    global _id_
    data = {}
    # 判断要获取的是文字还是属性
    if('loc' in conf):
        if(conf['loc'] == 'txt' and ele):
            txt = ele.get_text();
            txt = txt.strip()
            if("parse" in conf):
                parse = conf['parse'];
                if(parse['type'] == 'slice'):
                    if('start' in parse and 'end' in parse):
                        txt = txt[parse['start']:len(txt) + parse['end']]
                    elif('start' in parse):
                        txt = txt[parse['start']:len(txt)]
                    elif('end' in parse):
                        txt = txt[0:len(txt) + parse['end']]
                    if('id' in conf):
                        _id_ = txt
                    return txt
                else:
                    if('id' in conf):
                        _id_ = txt
                    return txt
            else:
                if('id' in conf):
                    _id_ = txt
                return txt
        elif(conf['loc'] == 'ele_num'):
            if('id' in conf):
                _id_ = len(ele.findChildren())
            return len(ele.findChildren())
        elif(conf['loc'] == 'attr'):
            for a in conf['attrs']:
                if(a['type'] == 'txt'):
                    txt = ele[a['kw']];
                    if("parse" in a):
                        parse = a['parse'];
                        if(parse['type'] == 'slice'):
                            if('start' in parse and 'end' in parse):
                                txt = txt[parse['start']:len(txt) + parse['end']]
                                if('id' in conf and 'id' in a):
                                    _id_ = txt;
                            elif('start' in parse):
                                txt = txt[parse['start']:len(txt)]
                                if('id' in conf and 'id' in a):
                                    _id_ = txt;
                            elif('end' in parse):
                                txt = txt[0:len(txt) + parse['end']]
                                if('id' in conf and 'id' in a):
                                    _id_ = txt;
                            data[a['kw']] = txt
                        else:
                            if('id' in conf and 'id' in a):
                                _id_ = txt;
                            data[a['kw']] = txt
                    else:
                        if('id' in conf and 'id' in a):
                            _id_ = txt;
                        data[a['kw']] = txt
                elif(a['type'] == 'byte'):
                    data[a['kw']] = ele[a['kw']];
                    if ('save_type' in a):
                        # 发送GET请求获取图片内容
                        try:
                            url = ele[a['kw']]
                            if('pre' in a):
                                url = a['pre'] + url
                            if('parse' in a and a['parse']['type'] == 'replace'):
                                url = url.replace(a['parse']['bf'],a['parse']['af'])
                            if(log_level == 'debug'):
                                print(out_path+conf['kw'] + '/'+ _id_+'.'+a['save_type'])
                                print(url)
                            response = requests.get(url)
                            os.makedirs(out_path+conf['kw'], exist_ok=True)
                            # 将图片内容写入本地文件
                            with open(out_path+conf['kw'] + '/'+ _id_+'.'+a['save_type'], 'wb') as file:
                                file.write(response.content)
                        except:
                            continue;
                else:
                    data[a['kw']] = ele[a['kw']];
            return data
    else:
        txt = ele.get_text();
        txt = txt.strip()
        if("parse" in conf):
            parse = conf['parse'];
            if(parse['type'] == 'slice'):
                if('start' in parse and 'end' in parse):
                    txt = txt[parse['start']:len(txt) + parse['end']]
                elif('start' in parse):
                    txt = txt[parse['start']:len(txt)]
                elif('end' in parse):
                    txt = txt[0:len(txt) + parse['end']]
                return txt
        else:
            return txt


# 输出的总数据
op_data = {'data':{}}
# 当前处理的页码
page_num = 1
pre_url = ''
def parse_page(driver,html,rules,opconf,pageconf):
    global sort_rule
    global page_num
    global op_data
    global pre_url
    # 处理当前页面
    print("正在处理第" + str(page_num)+"页")
    temp = init_parse(html,rules)
    for i in temp:
        if(i in op_data['data']):
            for item in temp[i]:
                op_data['data'][i].append(item)
        else:
            op_data['data'][i] = temp[i]
    page_num+=1
    # 根据规则获取下页的按钮元素
    button = driver.find_element(By.CSS_SELECTOR, pageconf['css'])
    if('max' in pageconf and pageconf['max'] and page_num > pageconf['max']):
        driver.quit()
        save2File(op_data,opconf)
        return
    if(button):
        pre_url = driver.current_url
        button.click()
        if(pre_url == driver.current_url and not 'sample_url' in pageconf):
            driver.quit()
            save2File(op_data,opconf)
            return
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html5lib")
        parse_page(driver,soup,rules,opconf,pageconf)
    else:
        driver.quit()
        save2File(op_data,opconf)
        return

sort_rule = {}
sort_kw = ''
def sort_op_data():
    global sort_rule,sort_kw
    global op_data
    for i in sort_rule:
        sort_item = sort_rule[i]
        if('type' in sort_item):
            sort_kw = sort_item['kw']
            if(sort_item['type'] == 'desc'):
                op_data['data'][i].sort(key=cmp_to_key(compare),reverse=True)
            else:
                op_data['data'][i].sort(key=cmp_to_key(compare))
        else:
            op_data['data'][i].sort(key=cmp_to_key(compare))
def compare(s1,s2):
    global sort_kw
    return int(s1[sort_kw]) - int(s2[sort_kw])


def save2File(data,config):
    sort_op_data()
    encoding = 'utf-8'
    if('encoding' in config):
        encoding = config['encoding']
    if('format' in config):
        format = config['format'];
        if(format == 'json'):
            with open(out_path+'/'+config['name']+".json", 'w', encoding=encoding) as file:
                json.dump(data, file, ensure_ascii=False)
        elif(format == 'xlsx'):
            print("暂不支持输出为xlsx格式")
            with open(out_path+'/'+config['name']+".json", 'w', encoding=encoding) as file:
                json.dump(data, file, ensure_ascii=False)
        else:
            with open(out_path+config['name']+".json", 'w', encoding=encoding) as file:
                json.dump(data, file, ensure_ascii=False)


                    
                
            
log_level = 'default'
out_path = ''
def main():
    global log_level,out_path
    # 配置文件
    conf = {}
    try:
        if len(sys.argv) > 1:
            for i, arg in enumerate(sys.argv[1:], 1):
                # print(f"参数 {i}: {arg}")
                with open( arg, 'r', encoding='utf-8') as f:
                    conf = json.load(f)
        else:
            # 读取配置文件
            with open('config.json', 'r', encoding='utf-8') as f:
                conf = json.load(f)
    except:
        print("配置文件不存在")
        return

    
    # 待爬链接
    url = conf['url']
    if('log-level' in conf):
        log_level = conf['log-level']

    # 输出相关初始化
    out_path = 'output/'+conf['name']+'/';
    os.makedirs(out_path, exist_ok=True)
    # 初始化浏览器驱动
    driver
    try:
        if('driver' in conf):
            if(conf['driver' == 'chrome']):
                driver = webdriver.Chrome()
            else:
                driver = webdriver.Edge()
    except:
        print("浏览器驱动初始化失败")
        return;
    driver.get(url)
    time.sleep(3)
    # 判断是否需预操作
    if('preop' in conf):
        button = driver.find_element(By.CSS_SELECTOR, conf['preop']['css'])
        button.click()
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html5lib")
    else:
        soup = BeautifulSoup(driver.page_source, "html5lib")
    # 判断爬取单页还是多页
    if('page' in conf):
        parse_page(driver,soup,conf['rules'],conf['output'],conf['page'])
    else:
        driver.quit()
        save2File(init_parse(soup,conf['rules']),conf['output'])



if __name__ == "__main__":
    main()
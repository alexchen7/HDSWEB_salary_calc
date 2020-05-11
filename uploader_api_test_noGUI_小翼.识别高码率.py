# -*- coding: utf-8 -*-
"""
Created on Tue Dec 10 10:44:30 2019

@author: asus
"""

import requests
import json
from bs4 import BeautifulSoup
import re
from datetime import datetime
import csv
from tqdm import tqdm
import os.path
import pandas as pd
import pathlib
#from tkinter import *

#root = Tk()
#root.title("HDSWeb组统计v0.01beta")
#
#select_time_lable = Label(root, text="若处理其他月份的数据请按照YYYY-XX输入日期, 留空则默认处理本月数据")
#select_time_entry = Entry(root)
#
#select_time_lable.grid(row = 0, sticky = W)
#select_time_entry.grid(row = 1, columnspan = 15)



cate_lib = {'401':"电影",'402':'电视剧分集', "403":"综艺", '404':'纪录片', \
            '405':'动漫', '406':'音乐MV', '407':'体育', '408':'无损音乐', \
            '409':'其他', '410':'iPad影视', '411':'剧集（合集）'}

valid_team_lib = {'31': 'HDSWEB', '35': 'HDSWEB合集专用'}

resolution_lib = {'1':"2K/1080p", '2':'1080i', '3':'720p', '4':'SD', '5':"4k/2160p"}

# set time for now
now = datetime.now()
def uploader_api(now = now):
    

    
    # create global variable for loaded_id
    loaded_id = set()
    
    # convert date in text format
    yr_mo = now.strftime("%Y-%m")
    
    # in case not collecting data for this month
    select_time = str(input('若处理其他月份的数据请按照YYYY-MM输入日期,\
                            按Enter键则默认处理本月数据'))
    # if there is an input
    if select_time:
        select_time = datetime.strptime(select_time, "%Y-%m")
        now = select_time
        yr_mo = select_time.strftime("%Y-%m")
        
    file_name_salary_report = 'salary_report_' + yr_mo.replace('-','_') + '.csv'
    
    # get finished progress
    if os.path.exists(file_name_salary_report):
        loaded_id = load_salary_report(now)
        print ('上次进度已完成', len(loaded_id), '人')
    
    # get all uids
    all_uploaders = load_uploaders()
    
    # num of user being processed
    to_be_done = len(all_uploaders) - len(loaded_id)
    print ('还剩', to_be_done, '人')
    
    # process the unfinshed uids
    for this_uploader in tqdm(all_uploaders):
        if this_uploader not in loaded_id:
            uid = this_uploader
    
            # create a dict for return
            uploader_dict = {'user_name':'', 'uid': uid, 'uploads':{}}
            
            # POST information to aquire adoption information of an uploader
            data = {'mod': 'USER', 'action': 'PUBLISH_INFO', 'uid': uid, 'date': yr_mo}
            
            # cookies
            cookies = {"__cfduid": "dd365ed8b4ba03783bea831bcb17c369d1586834432","UM_distinctid": "17176b5557c63a-0651bd910f42d7-87f133f-1fa400-17176b5557d1f4","c_secure_login": "bm9wZQ%3D%3D","c_secure_pass": "c6b94cef7e6da1397a60c914c51b6d42","c_secure_ssl": "eWVhaA%3D%3D","c_secure_tracker_ssl": "eWVhaA%3D%3D","c_secure_uid": "ODUzMjk%3D","CNZZDATA5476511": "cnzz_eid%3D1166175672-1586832819-https%253A%252F%252Fhdsky.me%252F%26ntime%3D1589202515"}
            
            # POST to aquire adoption information of a keeper
            r = requests.post("https://hdsky.me/addons.php",cookies = cookies, data = data)
            user_profile = BeautifulSoup(r.text, features = 'lxml')
            
            # convert html format to text format
            stats_str = user_profile.p.text
            
            """以下为错误的尝试，请无视"""
        #    # convert to dictionary format
        #    position_of_true = stats_str.find('true')
        #    # in case failed to grab the correct information
        #    if position_of_true == -1:
        #        print ('Error aquiring the data')
        #        return
        #    # change the small t to cap T, so dict can be built
        #    stats_str_formatted = stats_str[ : position_of_true] + 'T' + \
        #                            stats_str[position_of_true + 1 :]
            
            # convert to dictionary format
        
            #stats_dict = ast.literal_eval(stats_str_formatted)
            """错误的尝试结束"""
            
            # convert to dict format
            stats_dict = json.loads(stats_str)
            
            # put information in desired format
            if stats_dict['success']:
                
                # in case the uploader published 0 torrent!
                if stats_dict['data']['uploads']:
                    # iterate the torrents
                    for torrent in stats_dict['data']['uploads']:
                        # load basic information                
                        uploader_dict['uploads'][torrent['torrent']] = {'体积' : round(int(torrent['size'])/(1024**3), 2), \
                                    '发布时间' : torrent['added'], \
                                   '发布组' : torrent['team'], '分类' : torrent['category'], \
                                   'medium':torrent['medium'], '分辨率':torrent['standard'], \
                                   'codec':torrent['codec'], 'audiocodec':torrent['audiocodec'],\
                                   'options':torrent['options'], '标题':torrent['name'], \
                                   '小标题':torrent['small_descr'], 'NF':'', '高码率':'',\
                                   'numfiles':torrent['numfiles'],\
                                   '多集':'', \
                                   '旧合集':'', '新合集':'', '双语':'','备注':'', \
                                   '更新时间':str(datetime.now())}
                        
                        # analyze name
                        name_info = name_analyzer(torrent['name'])
                        
                        # copying result 
                        for this_info in name_info:
                            uploader_dict['uploads'][torrent['torrent']][this_info]= \
                            name_info[this_info]

                        # analyze small description
                        small_descr_info = \
                        small_descr_analyzer(torrent['small_descr'], \
                                             int(torrent['numfiles']))
                        
                        # copying result
                        for this_info in small_descr_info:
                            uploader_dict['uploads'][torrent['torrent']][this_info]= \
                            small_descr_info[this_info]
                else:
                    uploader_dict['uploads'][-1] = {'体积' : '1', '发布时间' : '1970-01-01 00:00:00', \
                   '发布组' : '0', '分类' : '0', 'medium': '0', '分辨率': '0', \
                   'codec':'0', 'audiocodec': '0', 'options': '0', '标题': '0', \
                   '小标题':'0' , 'NF':'', '多集':'','旧合集':'', '新合集':'', \
                   '双语':'', 'numfiles':'0', '高码率':'',\
                   '备注':'','更新时间':str(datetime.now())}
                
                # add user name
                uploader_dict['user_name'] = stats_dict['data']['username']
                uploader_dict['uid'] = uid
            else:
                print ("用户uid", uid, "信息获取失败!")
            
            # calculate the salary
            uploader_dict = salary_calc(uploader_dict)
            
            # write salary report
            write_salary_report(uploader_dict, now)
                    
    print ('开始转换csv到易读的excel...')
    
    csv_to_excel(file_name_salary_report)
    
    print ('转换完毕，全部完成!')
    
def name_analyzer(name):
    """read name and return if NF"""
    # create a dict to tell if it's NF
    name_info = {'NF' : ''}
    
    NF_reg = re.compile(" NF ")
    
    name_info['NF'] = bool(re.search(NF_reg, name))
    
    return name_info

def small_descr_analyzer(small_descr, numfiles):
    """takes the small description and output a dictionary for telling new/old 
    package, number of series or bilingual"""
    
    # create a dict for retrning result
    small_descr_info = {'多集':'','旧合集':'', '新合集':'', '双语':'', '高码率':''}
    
    # condition for old package also can be id
    old_package_reg = re.compile("全\d{1,5}[集期]")
    # condition for new package
    new_package_reg = re.compile("全\d{1,5}[集期]打包")
    
    # condition for series
    series_reg = re.compile("第[0-9]{1,5}-[0-9]{1,5}[集期]")
    
    # condition for high bitrate
    highbit_reg = re.compile(".?\[高码率.*\].?")
    
    # if its high bitrate
    if bool(re.search(highbit_reg, small_descr)):
        small_descr_info['高码率'] = '是'
    # condition for bilingual, must contain 双语 or [英中... or 中英...]
    #bilingual_reg = re.compile("(.?双语.?|.?^\[.?([简中繁]英|英[简中繁]).?$\].?)")
    bilingual_reg = re.compile("(.?双语.*|\[.*([简中繁]英|英[简中繁]).*\])")
    #bilingual_reg = re.compile("\[.+\]")
    
    small_descr_info['双语'] = bool(re.search(bilingual_reg, small_descr))
    
    # incase of multiple series
    match = re.search(series_reg, small_descr)
    # prevent none type err
    if match:
        """replaced by numfile"""
#        match = match.span()
#
#        # find the position of '第xx-xx集'
#        str_series_range = small_descr[match[0]: match[1]]
#        series_range = str_series_range[1:-1]
#        series_range = series_range.split('-')
#        series_num = int(series_range[1]) - int(series_range[0]) + 1
        small_descr_info['多集'] =  numfiles
        #print ('是剧集,共', series_num,'集')
        return small_descr_info
    
    # result of package decision
    match = re.search(old_package_reg, small_descr)
    
    # in case it's package
    if match:
        match = match.span()
#        
        # in case it's an new package
        match_new_package = re.search(new_package_reg, small_descr)
        if match_new_package:
            """replaced by numfile"""
#            match_new_package = match_new_package.span()
#            series_range = int(small_descr[match_new_package[0]: match_new_package[1]][1:-3])
            small_descr_info['新合集'] = numfiles
            #print('新包共,',series_range,'集')
            
        # in case it's old package
        else:
            """replaced by numfile"""
#            series_range = int(small_descr[match[0]: match[1]][1:-1])
            small_descr_info['旧合集'] = numfiles
            #print ('老包共,',series_range,'集')
        return small_descr_info
    
    # incase it's ongoing series that was not recognized
    if numfiles!= 1:
        small_descr_info['多集'] = numfiles

    return small_descr_info

def salary_calc(uploader_dict):
    
    # initialize total salary
    total_salary = 0
    for torrent in uploader_dict['uploads']:
        
        # get series_num
        series_num = int(uploader_dict['uploads'][torrent]['numfiles'])
        
        # if it's movie, regardless of new or old, NF, and regardless of num_files
        if uploader_dict['uploads'][torrent]['分类'] == '401' and \
        (uploader_dict['uploads'][torrent]['发布组'] == '31' or \
         uploader_dict['uploads'][torrent]['发布组'] == '35'):
            
            if uploader_dict['uploads'][torrent]['体积'] <= 10:
                uploader_dict['uploads'][torrent]['单种工资'] = 2000
            elif uploader_dict['uploads'][torrent]['体积'] <= 20:
                uploader_dict['uploads'][torrent]['单种工资'] = 3000
            elif uploader_dict['uploads'][torrent]['体积'] > 20:
                uploader_dict['uploads'][torrent]['单种工资'] = 4000
                
            total_salary += uploader_dict['uploads'][torrent]['单种工资']
            continue
        
        # if it's NF
        if uploader_dict['uploads'][torrent]['NF'] and \
        (uploader_dict['uploads'][torrent]['发布组'] == '31' or \
         uploader_dict['uploads'][torrent]['发布组'] == '35'):
                    
            uploader_dict['uploads'][torrent]['单种工资'] = 2000 * series_num
            total_salary += uploader_dict['uploads'][torrent]['单种工资']
            continue
            
            

        # no salary (filter) for new packages or other groups
        if (not uploader_dict['uploads'][torrent]['新合集']) and \
        (uploader_dict['uploads'][torrent]['发布组'] == '31' or \
         uploader_dict['uploads'][torrent]['发布组'] == '35'):

            # salary per torrent, default value for ongoing single torrent or series
            salary_per_torrent = 2000

            # in case it's high bitrate and bilingual
            if uploader_dict['uploads'][torrent]['高码率'] == \
            '是' and uploader_dict['uploads'][torrent]['双语']:
                salary_per_torrent = 4000
            # in case it's high bitrate only
            elif uploader_dict['uploads'][torrent]['高码率'] == \
            '是':
                salary_per_torrent = 3000
            # in case it's bilingual only
            elif uploader_dict['uploads'][torrent]['双语']:
                salary_per_torrent = 2000
            # in case it's neither bilingual nor bitrate
            elif uploader_dict['uploads'][torrent]['旧合集']:
                if uploader_dict['uploads'][torrent]['分辨率'] == '5':
                    salary_per_torrent = 1500
                else:
                    salary_per_torrent = 1000
                    
            # in case it's new single torrent or ongoing series        
            elif uploader_dict['uploads'][torrent]['标题'] != '0' \
            or uploader_dict['uploads'][torrent]['多集']:
                salary_per_torrent = 2000
            # incase no torrent
            else:
                salary_per_torrent = 0
                uploader_dict['uploads'][torrent]['备注'] = '超级大咸鱼!!'
            
            # record salary_per_torrent, and total salary
            uploader_dict['uploads'][torrent]['单种工资'] = salary_per_torrent * series_num
            total_salary += uploader_dict['uploads'][torrent]['单种工资']

                
        elif uploader_dict['uploads'][torrent]['新合集']:
            uploader_dict['uploads'][torrent]['备注'] = '打包新资源无魔力'
            uploader_dict['uploads'][torrent]['单种工资'] = 0
        elif uploader_dict['uploads'][torrent]['发布组'] != '31' or \
            uploader_dict['uploads'][torrent]['发布组'] != '35':
            uploader_dict['uploads'][torrent]['备注'] = '非web-dl组'
            uploader_dict['uploads'][torrent]['单种工资'] = 0
        else:
            uploader_dict['uploads'][torrent]['备注'] = '其他原因不达标'
            uploader_dict['uploads'][torrent]['单种工资'] = 0
    
    uploader_dict['总魔力'] = total_salary
    return uploader_dict

def write_salary_report(uploader_dict, now):
    """take the uploader_dict and write a csv"""
    
    user_name = uploader_dict['user_name']
    uid = uploader_dict['uid']
    # takes a torrent dict of a uploader and write in csv
    print ('开始写入发布员', user_name, '用户id', uid, '的本月报告')
    
    # get the time in str format
    yy_mm = now.strftime("%Y_%m")
    
    filename = 'salary_report_' + yy_mm + '.csv'
    #mini_filename = 'miniSR' + yy_mm
    
    with open(filename, 'a', newline = '', encoding = 'utf-8') as f:
        fieldnames = ['用户id', '用户名', '种子id', '标题','小标题','体积', \
                          '发布组', '分类', '分辨率', '多集','新合集','旧合集', \
                          '双语', '高码率','NF', \
                          '发布时间', '单种工资', '备注', '总魔力', '更新时间']
        thewriter = csv.DictWriter(f, fieldnames = fieldnames)
        
        # wrtie header if it's empty file
        if not (f.tell()):
            thewriter.writeheader() 
           
        # iterate thru the dict
        for torrent in uploader_dict['uploads']:
            
            # define 3 strs for translation
            team, resolution, cate = '', '', ''
            # translating code to name
            if uploader_dict['uploads'][torrent]['发布组'] in valid_team_lib:
                
                team = valid_team_lib[uploader_dict['uploads'][torrent]['发布组']]
            else:
                team = '非webdl组'
            
            if uploader_dict['uploads'][torrent]['分辨率'] in resolution_lib:
                resolution = resolution_lib[uploader_dict['uploads'][torrent]['分辨率']]
            else:
                resolution = '什么鬼？'
            if uploader_dict['uploads'][torrent]['分类'] in cate_lib:
                cate = cate_lib[uploader_dict['uploads'][torrent]['分类']]
            else:
                cate = '什么鬼？'
                
            if uploader_dict['uploads'][torrent]['双语']:
                bilingual = '是'
            else:
                bilingual = ''
                
            if uploader_dict['uploads'][torrent]['NF']:
                NF = '是'
            else:
                NF = ''
            
            
            
            thewriter.writerow({'用户id': uid, '用户名': user_name, \
                                '种子id': torrent, \
                                '标题':uploader_dict['uploads'][torrent]['标题'], \
                                '小标题':uploader_dict['uploads'][torrent]['小标题'], \
                                '体积':str(uploader_dict['uploads'][torrent]['体积']) + 'GB', \
                          '发布组':team, \
                          '分类':cate, \
                          '分辨率':resolution, \
                          '多集':uploader_dict['uploads'][torrent]['多集'], \
                          '新合集':uploader_dict['uploads'][torrent]['新合集'], \
                          '旧合集':uploader_dict['uploads'][torrent]['旧合集'], \
                          '双语': bilingual, \
                          '高码率': uploader_dict['uploads'][torrent]['高码率'], \
                          'NF': NF, \
                          '发布时间':uploader_dict['uploads'][torrent]['发布时间'], \
                          '单种工资':uploader_dict['uploads'][torrent]['单种工资'], \
                          '备注':uploader_dict['uploads'][torrent]['备注'], \
                          '更新时间':uploader_dict['uploads'][torrent]['更新时间']})
                        
        # write total salary
        thewriter.writerow({'用户id': uid, '用户名': user_name, \
                            '总魔力' : uploader_dict['总魔力']})
        
"""暂时不需要miniSR"""        
#        with open(mini_filename, 'a', newline = '', encoding = 'utf-8') as minif:
#            fieldnames = ['用户id', '用户名', '总魔力','生成时间']
#            
#            mini_writer = csv.DictWriter(minif, fieldnames = fieldnames)
#            
#            # write header if it's empty file
#            if not (minif.tell()):
#                mini_writer.writeheader()
#            
#            mini_writer.writerow({'用户id': uid, '用户名':user_name, \
#                                  '总魔力': uploader_dict['总魔力'], \
#                                  '生成时间': str(datetime.now())})

def load_salary_report(now):
    # load keepers to a set and return to prevent repeated scanning
    uid_loaded = set()
    
    yy_mm = now.strftime("%Y_%m")
    
    filename = 'salary_report_' + yy_mm + '.csv'
    
    
    
    fieldnames = ['用户id', '用户名', '种子id', '标题','小标题','体积', \
                          '发布组', '分类', '分辨率', '多集','新合集','旧合集', \
                          '发布时间', '单种工资', '备注', '总魔力', '更新时间']
    
    f = csv.DictReader(open(filename, encoding="utf-8"))
    
#    thewriter = csv.DictReader(f, fieldnames = fieldnames)
    
    for i in f:
        # add to set
        uid_loaded.add(i['用户id'])
        
    return uid_loaded

def load_uploaders():
    """takes a file called 发布员名单.txt and return a list of uids"""
    # create pattern for uid
    uid_reg = re.compile("\s+\d+")
    
    # create set of uid for return
    uid_set = set()
    
    # check the progress and record in loaded_sent_salary
    file = open('发布员名单.txt', encoding='utf-8')
    lines = file.readlines()
    
    for line in lines:
    
    
        # get position of uid
        uid_match = re.search(uid_reg, line).span()
        # create a blank uid str
        uid = ''
        uid_raw_str = line[uid_match[0]:uid_match[1]]
        uid = uid_raw_str.replace(' ','')
        
        uid_set.add(uid)
    return uid_set

def csv_to_excel(filename):
    
    # return salary_file_path
    salary_file_path = str(pathlib.Path(filename).absolute())
    print (salary_file_path)
    # create excel file path
    excel_file_path = str(pathlib.Path(filename).absolute()).replace('.csv', '.xlsx')
    print (excel_file_path)
    
    read_file = pd.read_csv (salary_file_path)
    
    read_file.to_excel (excel_file_path, index = None, header=True)
    
#start_button = Button(root, text="Start",fg = 'red', command = uploader_api)
#start_button.grid(row = 2)        
#root.mainloop() 
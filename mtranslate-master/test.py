#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mtranslate import translate
import pandas as pd
import numpy as np 




def main():
    df=pd.read_excel('00.00.xlsx')
    df=df.fillna('nan')
    
    T1=[]
    for i in range(len(df)):
        if df.iloc[i]['每日句子1'] != 'nan':
            T1.append(translate(df.iloc[i]['每日句子1'],'zh-TW'))
        else:
            T1.append('')
    T2=[]
    for i in range(len(df)):
        if df.iloc[i]['每日句子2'] != 'nan':
            T2.append(translate(df.iloc[i]['每日句子2'],'zh-TW'))
        else:
            T2.append('')
    T3=[]
    for i in range(len(df)):
        if df.iloc[i]['每日句子3'] != 'nan':
            T3.append(translate(df.iloc[i]['每日句子3'],'zh-TW'))
        else:
            T3.append('')
    T4=[]
    for i in range(len(df)):
        if df.iloc[i]['每日句子4'] != 'nan':
            T4.append(translate(df.iloc[i]['每日句子4'],'zh-TW'))
        else:
            T4.append('')
    T5=[]
    for i in range(len(df)):
        if df.iloc[i]['每日句子5'] != 'nan':
            T5.append(translate(df.iloc[i]['每日句子5'],'zh-TW'))
        else:
            T5.append('')
    df['翻譯句子1']=T1
    df['翻譯句子2']=T2
    df['翻譯句子3']=T3
    df['翻譯句子4']=T4
    df['翻譯句子5']=T5
    df.to_excel('新增 Microsoft Excel 工作表.xlsx')
    print('done')
if __name__ == '__main__':
    main()

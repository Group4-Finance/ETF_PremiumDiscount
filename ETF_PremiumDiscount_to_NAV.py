import urllib.request as req
import requests
import pandas as pd
import bs4 as bs # BeautifulSoup 4
import tabulate
import datetime


#台灣證交所ETF清單
url = "https://www.twse.com.tw/zh/ETFortune/ajaxProductsResult"
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://www.twse.com.tw/zh/ETFortune'
}
response = requests.get(url, headers=headers)
data = response.json()
records = data.get('data', [])
df = pd.DataFrame(records)

df['stockNo'] = df['stockNo'].astype(str).str.zfill(4)
df['stockNo'] = df['stockNo'].apply(lambda x: f"{x}")
df = df[['stockNo', 'stockName', 'listingDate', 'indexName', 'totalAv']]
df.columns = ['股票代號', 'ETF名稱', '上市日期', '標的指數', '資產規模(億元)']
df['資產規模(億元)'] = df['資產規模(億元)'].astype(str).str.replace(',', '').str.strip()
df['上市日期'] = pd.to_datetime(df['上市日期'], format='%Y.%m.%d', errors='coerce')
df['資產規模(億元)'] = pd.to_numeric(df['資產規模(億元)'], errors='coerce')

#篩選2020年前上市&規模>50億
df_filtered = df[
    (df['上市日期'].dt.year < 2020) &
    (df['資產規模(億元)'] > 50)
][['股票代號']]

# ETF代號
etf_list = df_filtered['股票代號']


#抓取每一個ETF的折溢價
for etf in etf_list:
    # 設定起始日期
    start_date = '2020-1-1'

    # 取得今天日期並轉為字串
    end_date = datetime.date.today().strftime('%Y-%m-%d')

    # MoneyDJ
    base_url_MoneyDJ = "https://www.moneydj.com/ETF/X/xdjbcd/Basic0003BCD.xdjbcd?etfid={}.TW&b={}&c={}"

    #url_MoneyDJ
    url_MoneyDJ = base_url_MoneyDJ.format(etf, start_date, end_date)

    response_MoneyDJ = req.urlopen(url_MoneyDJ)
    content_MoneyDJ = response_MoneyDJ.read().decode('utf-8')

    # 將內容按行分割
    lines = content_MoneyDJ.strip().split(' ')  # 分成 3 行
    dates = lines[0].split(',')
    navs = lines[1].split(',')
    prices = lines[2].split(',')

    # 組成表格資料
    records = []
    for date, nav, price in zip(dates, navs, prices ):
        records.append([date, float(nav), float(price)])

    # 建立 DataFrame
    df_MoneyDJ = pd.DataFrame(records, columns=['交易日期', '淨值', '市價'])
    df_MoneyDJ['交易日期'] = pd.to_datetime(df_MoneyDJ['交易日期'], format='%Y%m%d')

    # 計算折溢價利率（公式： (市價 - 淨值) / 淨值 ）
    df_MoneyDJ['折溢價利率(%)'] = ((df_MoneyDJ['市價'] - df_MoneyDJ['淨值']) / df_MoneyDJ['淨值'] * 100).map(lambda x: f"{x:.2f}%")

    #轉成csv檔案
    df_MoneyDJ.to_csv("MoneyDJ_ETF_PremiumDiscount_{}.csv".format(etf), index=False, encoding='utf-8-sig')




# response_MoneyDJ = req.urlopen(url_MoneyDJ)
# content = response_MoneyDJ.read()
# html = bs.BeautifulSoup(content, features="html.parser")
# rows = html.find_all("tr", class_=["even", "odd"]) #要一次抓取多個class時的用法
# table = []
# for r in rows:
#     tds = r.find_all('td')
#     code = tds[3].text.strip() # 代碼
#     name = tds[4].text.strip() # 名稱
#     premium_discount = tds[10].text.strip() # 折溢價
#     data = {
#         '代碼': code,
#         'ETF名稱': name,
#         '折溢價': premium_discount
#     }
#     table.append(data)
#
# df_MoneyDJ = pd.json_normalize(table)
#
# # 取得要比對的代碼清單
# filtered_codes = df_filtered['股票代號'].tolist()
#
# # 篩選 df_MoneyDJ 中代碼符合者
# df_result = df_MoneyDJ[df_MoneyDJ['代碼'].isin(filtered_codes)]
#
# # 轉成csv檔案
# df_result.to_csv("MoneyDJ_ETF_PremiumDiscount.csv", index=False, encoding='utf-8-sig')




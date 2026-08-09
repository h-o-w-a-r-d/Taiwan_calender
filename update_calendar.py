import os
import requests
import pandas as pd
from datetime import datetime, date
from icalendar import Calendar, Event
import pytz

CSV_URL = "https://data.ntpc.gov.tw/api/datasets/308dcd75-6434-45bc-a95f-584da4fed251/csv/file"
RAW_CSV_NAME = "政府行政機關辦公日曆表.csv"
OUTPUT_ICS_FULL = "taiwan_holidays_full.ics"
OUTPUT_ICS_CURRENT = "taiwan_holidays.ics"

def generate_ics(df_filtered, output_ics_path):
    # 建立日曆物件並設定屬性
    cal = Calendar()
    cal.add('prodid', '-//Taiwan Executive Yuan//Government Holiday Calendar//ZH')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'PUBLISH')
    cal.add('X-WR-CALNAME', '中華民國政府行政機關辦公日曆表')
    cal.add('X-WR-TIMEZONE', 'Asia/Taipei')
    
    now = datetime.utcnow().replace(tzinfo=pytz.utc)

    for idx, row in df_filtered.iterrows():
        # 建立事件物件
        event = Event()
        
        date_str = str(int(row['date']))
        # 使用 datetime.date 來建立「全天事件 (All-day event)」
        start_date = datetime.strptime(date_str, "%Y%m%d").date()
        
        name = str(row['name']) if pd.notna(row['name']) and str(row['name']).strip() != '' else str(row['holidaycategory'])
        is_holiday = str(row['isholiday']).strip() == '是'
        
        summary = name if is_holiday else f"【補班】{name}"
        desc = str(row['description']) if pd.notna(row['description']) else str(row['holidaycategory'])
        uid = f"{date_str}-{idx}@calendar.gov.tw"
        
        # 加入事件屬性
        event.add('uid', uid)
        event.add('dtstamp', now)
        event.add('dtstart', start_date)
        # 對於全天事件，iCalendar 規範沒有強制必須加上 dtend，
        # 如果要加，通常是加隔天，但直接設定 dtstart 就足夠代表當天全天事件了。
        
        event.add('summary', summary)
        event.add('description', desc)
        event.add('status', 'CONFIRMED')
        event.add('transp', 'TRANSPARENT' if is_holiday else 'OPAQUE')
        
        # 將事件加入日曆
        cal.add_component(event)
        
    # 將日曆物件寫入檔案，icalendar 會自動處理 CRLF 與格式規範
    with open(output_ics_path, 'wb') as f:
        f.write(cal.to_ical())

def convert_csv_to_ics(csv_file_path):
    df = pd.read_csv(csv_file_path)
    
    # 剔除普通週末，僅保留國定假日、補假、調整放假與補班日
    df_filtered = df[df['holidaycategory'] != '星期六、星期日'].copy()
    
    # 1. 產生完整版的 ICS
    generate_ics(df_filtered, OUTPUT_ICS_FULL)
    
    # 2. 篩選「今年與明年」的資料並產生標準版 ICS
    current_year = datetime.now().year
    target_years = [current_year, current_year + 1]
    
    df_current_next = df_filtered[df_filtered['year'].isin(target_years)].copy()
    generate_ics(df_current_next, OUTPUT_ICS_CURRENT)

def main():
    print("Downloading raw CSV...")
    response = requests.get(CSV_URL)
    response.raise_for_status()
    
    with open(RAW_CSV_NAME, "wb") as f:
        f.write(response.content)
        
    print("Converting to ICS using icalendar library...")
    convert_csv_to_ics(RAW_CSV_NAME)
    
    print("Successfully generated ICS files!")

if __name__ == "__main__":
    main()

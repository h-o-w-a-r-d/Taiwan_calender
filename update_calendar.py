import os
import requests
import pandas as pd
from datetime import datetime, timedelta

CSV_URL = "https://data.ntpc.gov.tw/api/datasets/308dcd75-6434-45bc-a95f-584da4fed251/csv/file"
RAW_CSV_NAME = "政府行政機關辦公日曆表.csv"
OUTPUT_ICS_FULL = "taiwan_holidays_full.ics"
OUTPUT_ICS_CURRENT = "taiwan_holidays.ics"

def generate_ics(df_filtered, output_ics_path, now_str):
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Taiwan Executive Yuan//Government Holiday Calendar//ZH",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:中華民國政府行政機關辦公日曆表",
        "X-WR-TIMEZONE:Asia/Taipei"
    ]
    
    for idx, row in df_filtered.iterrows():
        date_str = str(int(row['date']))
        dt_start = datetime.strptime(date_str, "%Y%m%d")
        dt_end = dt_start + timedelta(days=1)
        
        start_fmt = dt_start.strftime("%Y%m%d")
        end_fmt = dt_end.strftime("%Y%m%d")
        
        name = str(row['name']) if pd.notna(row['name']) and str(row['name']).strip() != '' else str(row['holidaycategory'])
        is_holiday = str(row['isholiday']).strip() == '是'
        
        summary = name if is_holiday else f"【補班】{name}"
        desc = str(row['description']) if pd.notna(row['description']) else str(row['holidaycategory'])
        uid = f"{date_str}-{idx}@calendar.gov.tw"
        
        ics_lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now_str}",
            f"DTSTART;VALUE=DATE:{start_fmt}",
            f"DTEND;VALUE=DATE:{end_fmt}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{desc}",
            "STATUS:CONFIRMED",
            f"TRANSP:{'TRANSPARENT' if is_holiday else 'OPAQUE'}",
            "END:VEVENT"
        ])
        
    ics_lines.append("END:VCALENDAR")
    
    # 修正重點：使用 CRLF (\r\n) 換行以符合 RFC 5545 規範
    with open(output_ics_path, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write("\r\n".join(ics_lines) + "\r\n")

def convert_csv_to_ics(csv_file_path):
    df = pd.read_csv(csv_file_path)
    
    # 剔除普通週末，僅保留國定假日、補假、調整放假與補班日
    df_filtered = df[df['holidaycategory'] != '星期六、星期日'].copy()
    
    now = datetime.utcnow()
    now_str = now.strftime("%Y%m%dT%H%M%SZ")
    
    # 1. 產生完整版的 ICS
    generate_ics(df_filtered, OUTPUT_ICS_FULL, now_str)
    
    # 2. 篩選「今年與明年」的資料並產生標準版 ICS
    current_year = now.year
    target_years = [current_year, current_year + 1]
    
    df_current_next = df_filtered[df_filtered['year'].isin(target_years)].copy()
    generate_ics(df_current_next, OUTPUT_ICS_CURRENT, now_str)

def main():
    print("Downloading raw CSV...")
    response = requests.get(CSV_URL)
    response.raise_for_status()
    
    # 保存原始 CSV
    with open(RAW_CSV_NAME, "wb") as f:
        f.write(response.content)
        
    print("Converting to ICS with CRLF line endings...")
    convert_csv_to_ics(RAW_CSV_NAME)
    
    print("Successfully updated ICS files with standard CRLF format!")

if __name__ == "__main__":
    main()

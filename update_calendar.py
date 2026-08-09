import os
import requests
import pandas as pd
from datetime import datetime, timedelta

CSV_URL = "https://data.ntpc.gov.tw/api/datasets/308dcd75-6434-45bc-a95f-584da4fed251/csv/file"
RAW_CSV_NAME = "政府行政機關辦公日曆表.csv"
OUTPUT_ICS = "taiwan_holidays.ics"

def convert_csv_to_ics(csv_file_path, output_ics_path):
    df = pd.read_csv(csv_file_path)
    
    # 剔除普通週末，僅保留國定假日、補假、調整放假與補班日
    df_filtered = df[df['holidaycategory'] != '星期六、星期日'].copy()
    
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Taiwan Executive Yuan//Government Holiday Calendar//ZH",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:中華民國政府行政機關辦公日曆表",
        "X-WR-TIMEZONE:Asia/Taipei"
    ]
    
    now_str = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    
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
    
    with open(output_ics_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(ics_lines))

def main():
    print("Downloading raw CSV...")
    response = requests.get(CSV_URL)
    response.raise_for_status()
    
    # 保存原始 CSV
    with open(RAW_CSV_NAME, "wb") as f:
        f.write(response.content)
        
    print("Converting to ICS...")
    convert_csv_to_ics(RAW_CSV_NAME, OUTPUT_ICS)
    
    print("Saved raw CSV and generated ICS successfully!")

if __name__ == "__main__":
    main()

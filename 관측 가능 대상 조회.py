# 작성자: 정재영 (Jeong Jaeyoung)
# 이메일: shaula0@naver.com
# 작성일: 2025-03-10
# 설명: 천체 관측 가능한 대상을 계산하는 코드

# 변수: 검색 시작 날짜, 끝 날짜, 관측 종료 시간, 관측 종료 시간, 관측 위치 경·위도, 관측 대상 고도, 조회 천체 목록
# 요약: 일몰 시간 + 30m 부터 관측을 시작하며, 관측 종료 시간 까지 1시간 단위로 천체 목록을 조회하여, 설정 고도보다 높은 위치에 있을 경우 관측 가능 대상에 저장한다.

from astropy.coordinates import EarthLocation, AltAz, get_body
from astropy.time import Time
from astroplan import Observer
from tabulate import tabulate
from tqdm import tqdm
import pandas as pd
import datetime

# pandas 한글 출력 깨지는 현상 방지
tabulate.WIDE_CHARS_MODE = False

# 날짜 범위 설정
start_date = datetime.date(2025, 1, 1)
end_date = datetime.date(2025, 12, 31)

# 관측 종료 시간 설정(시, 분)
end_hour = 20
end_min = 30

# 관측 위치 설정
loc = EarthLocation(lat=33.444558, lon=126.549283, height=394)  # 별빛누리 경도, 위도

# 관측 대상 고도 설정 (이상)
target_altitude = 25

# 조회 천체 목록 설정
planets = ["moon", "venus", "mars", "jupiter", "saturn"]

# 관측자 설정 (UTC 기준)
observer = Observer(location=loc)

# 데이터프레임 초기화
df = pd.DataFrame(columns=["날짜", "일몰시간", "관측가능 대상"])

def deg_to_dms(degrees):
    """십진수 도(deg)를 도(D) 분(M) 초(S) 형태로 변환"""
    d = int(degrees)
    m = int((degrees - d) * 60)
    s = (degrees - d - m / 60) * 3600
    return f"{d}° {m}' {s:.2f}\""

# 설정한 날짜 범위 for문
for single_date in tqdm(range((end_date - start_date).days + 1)):
    #검색 날짜
    current_date = start_date + datetime.timedelta(days=single_date)

    # 해당 날짜의 일몰 시간 계산 (UTC 기준)
    sunset_time_utc = observer.sun_set_time(Time(current_date.strftime("%Y-%m-%d")), which="nearest")

    # UTC → KST 변환 (UTC + 9시간)
    sunset_time_kst = sunset_time_utc + datetime.timedelta(hours=9)
    
    # 조건에 맞는 관측 대상 담을 list 초기화
    observable_list = []

    # 관측 종료 시간 KST → UTC 변환 (KST - 9시간)
    end_time_utc = Time(datetime.datetime.combine(current_date, datetime.time(end_hour, end_min)) + datetime.timedelta(hours=-9))
    
    # 행성 list 반복문
    for planet in planets:
        # 관측 시작 시간 = 일몰 시간 + 30분
        current_time_utc = sunset_time_utc + datetime.timedelta(minutes=30)
        
        # 관측 끝 시간 - 관측 시작 시간
        difference_time = end_time_utc - current_time_utc

        # 분 단위로 변환
        difference_time_to_min = difference_time.to_value('min')

        # 관측 시작 시간 + 1h > 관측 끝 시간 만큼 반복문
        for a in range(int(difference_time_to_min//60) + 2):
            # 관측 마지막 시간 보다 크다면 마지막 설정 시간으로 계산
            if current_time_utc >= end_time_utc:
                current_time_utc = end_time_utc
                
            # 좌표계 생성
            altaz = AltAz(location=loc, obstime=current_time_utc)
            
            # 고도 계산
            altitude = get_body(planet, current_time_utc, loc).transform_to(altaz).alt.deg
             
            # 설정 고도 이상일 경우 행성 이름 추가 후 종료
            if altitude >= target_altitude:
                observable_list.append(planet)
                break

            # 시간 +1h
            current_time_utc += datetime.timedelta(hours=1)

    # 현재 날짜에 관측 가능한 대상 리스트를 DataFrame 형태로 변환
    df_observable_list = pd.DataFrame([[current_date.strftime("%Y-%m-%d"), sunset_time_kst.strftime("%H:%M"), observable_list]], columns=["날짜", "일몰시간", "관측가능 대상"])
    
    # df에 추가
    df = pd.concat([df, df_observable_list])

# print(tabulate(df, headers='keys', tablefmt='psql', showindex=True))
    
# excel 저장
df.to_excel(start_date.strftime("%y%m%d") + "-" + end_date.strftime("%y%m%d") + "_Sunset+30m-" + str(end_hour).zfill(2) + "h" + str(end_min).zfill(2) + "m_Alt" + str(target_altitude) + "deg+" + ".xlsx", index=False)
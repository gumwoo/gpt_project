"""
데이터 스토리텔러 애플리케이션의 유틸리티 함수를 제공하는 모듈입니다.
"""

import pandas as pd
import numpy as np
import json
import re

def format_number(value, precision=2):
    """
    숫자 값을 읽기 쉬운 형식으로 포맷팅합니다.
    
    Args:
        value (float): 포맷팅할 숫자
        precision (int): 소수점 자릿수
    
    Returns:
        str: 포맷팅된 숫자 문자열
    """
    if pd.isna(value):
        return "N/A"
    
    if isinstance(value, (int, float)):
        # 1000 단위 구분자 추가
        if abs(value) >= 1000000:
            return f"{value / 1000000:.{precision}f}M"
        elif abs(value) >= 1000:
            return f"{value / 1000:.{precision}f}K"
        elif abs(value) < 0.01 and value != 0:
            return f"{value:.6f}"
        else:
            return f"{value:,.{precision}f}"
    
    return str(value)

def get_column_description(column_name):
    """
    일반적인 열 이름에 대한 설명을 제공합니다.
    
    Args:
        column_name (str): 열 이름
    
    Returns:
        str: 열에 대한 설명
    """
    column_descriptions = {
        "date": "날짜",
        "region": "지역",
        "product_category": "제품 카테고리",
        "sales_amount": "판매액",
        "units_sold": "판매량",
        "customer_type": "고객 유형",
        "promotion_active": "프로모션 활성 여부",
        "campaign_id": "캠페인 ID",
        "channel": "마케팅 채널",
        "cost": "비용",
        "impressions": "노출 수",
        "clicks": "클릭 수",
        "conversions": "전환 수",
        "conversion_value": "전환 가치",
        "target_audience": "타겟 고객층",
        "survey_id": "설문 ID",
        "customer_id": "고객 ID",
        "age_group": "연령대",
        "gender": "성별",
        "purchase_frequency": "구매 빈도",
        "product_quality_rating": "제품 품질 평가",
        "customer_service_rating": "고객 서비스 평가",
        "price_satisfaction": "가격 만족도",
        "recommendation_likelihood": "추천 가능성",
        "overall_satisfaction": "전반적인 만족도",
        "feedback_text": "피드백 텍스트"
    }
    
    # 정확한 일치 확인
    if column_name in column_descriptions:
        return column_descriptions[column_name]
    
    # 부분 일치 확인
    for key, value in column_descriptions.items():
        if key in column_name.lower():
            return value
    
    # 일치하는 설명이 없는 경우
    return column_name

def extract_key_metrics(df, column_map=None):
    """
    데이터프레임에서 주요 지표를 추출합니다.
    
    Args:
        df (pandas.DataFrame): 데이터프레임
        column_map (dict, optional): 열 이름 매핑 (예: {"sales": "sales_amount"})
    
    Returns:
        dict: 주요 지표
    """
    if column_map is None:
        column_map = {}
    
    metrics = {}
    
    # 일반적인 지표 추출
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    
    for col in numeric_cols:
        metrics[col] = {
            "mean": float(df[col].mean()),
            "median": float(df[col].median()),
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "sum": float(df[col].sum())
        }
    
    # 특정 열에 대한 지표 추출
    # 판매액
    sales_col = column_map.get("sales", "sales_amount") if "sales_amount" in df.columns else None
    if sales_col:
        metrics["total_sales"] = float(df[sales_col].sum())
        
        # 날짜 열이 있는 경우 월별/주별 판매액 추가
        date_col = next((col for col in df.columns if "date" in col.lower()), None)
        if date_col and pd.api.types.is_datetime64_any_dtype(df[date_col]):
            # 월별 판매액
            monthly_sales = df.groupby(df[date_col].dt.strftime('%Y-%m')).agg({sales_col: 'sum'})
            metrics["monthly_sales"] = monthly_sales[sales_col].to_dict()
            
            # 성장률 계산
            if len(monthly_sales) > 1:
                first_month = monthly_sales.iloc[0][sales_col]
                last_month = monthly_sales.iloc[-1][sales_col]
                metrics["growth_rate"] = ((last_month / first_month) - 1) * 100
    
    # 전환율 (마케팅 데이터)
    if "clicks" in df.columns and "conversions" in df.columns:
        metrics["conversion_rate"] = float((df["conversions"].sum() / df["clicks"].sum()) * 100) if df["clicks"].sum() > 0 else 0
    
    # 만족도 평균 (고객 만족도 데이터)
    satisfaction_cols = [col for col in df.columns if "satisfaction" in col.lower() or "rating" in col.lower()]
    if satisfaction_cols:
        metrics["avg_satisfaction"] = {col: float(df[col].mean()) for col in satisfaction_cols}
    
    return metrics

def identify_correlations(df, threshold=0.5):
    """
    데이터프레임에서 강한 상관관계가 있는 변수 쌍을 식별합니다.
    
    Args:
        df (pandas.DataFrame): 데이터프레임
        threshold (float): 상관계수 임계값
    
    Returns:
        list: (변수1, 변수2, 상관계수) 튜플의 리스트
    """
    # 수치형 열만 선택
    numeric_df = df.select_dtypes(include=['int64', 'float64'])
    
    if numeric_df.shape[1] < 2:
        return []
    
    # 상관관계 계산
    corr_matrix = numeric_df.corr()
    
    # 상관계수가 임계값을 초과하는 변수 쌍 찾기
    strong_correlations = []
    
    for i in range(corr_matrix.shape[0]):
        for j in range(i+1, corr_matrix.shape[0]):  # 대각선 아래쪽만 확인 (중복 방지)
            if abs(corr_matrix.iloc[i, j]) >= threshold:
                strong_correlations.append((
                    corr_matrix.index[i],
                    corr_matrix.columns[j],
                    corr_matrix.iloc[i, j]
                ))
    
    # 상관계수의 절대값 기준으로 내림차순 정렬
    strong_correlations.sort(key=lambda x: abs(x[2]), reverse=True)
    
    return strong_correlations

def identify_trends(df, date_column, value_column):
    """
    시계열 데이터에서 트렌드를 식별합니다.
    
    Args:
        df (pandas.DataFrame): 데이터프레임
        date_column (str): 날짜 열 이름
        value_column (str): 값 열 이름
    
    Returns:
        dict: 식별된 트렌드
    """
    # 날짜 열이 datetime 타입인지 확인, 아니면 변환
    if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
        try:
            df[date_column] = pd.to_datetime(df[date_column])
        except:
            return {"error": "날짜 열을 날짜 형식으로 변환할 수 없습니다."}
    
    # 날짜 기준으로 정렬
    df_sorted = df.sort_values(by=date_column)
    
    # 결과 저장
    trends = {}
    
    # 데이터가 충분한지 확인
    if len(df_sorted) < 3:
        return {"error": "트렌드 분석을 위한 충분한 데이터가 없습니다."}
    
    # 전체 기간에 대한 선형 추세
    try:
        import scipy.stats as stats
        
        # 날짜를 숫자로 변환 (선형 회귀를 위해)
        df_sorted['date_numeric'] = (df_sorted[date_column] - df_sorted[date_column].min()).dt.days
        
        # 선형 회귀 계산
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            df_sorted['date_numeric'],
            df_sorted[value_column]
        )
        
        # 추세 해석
        if p_value < 0.05:  # 통계적으로 유의미한 추세
            if slope > 0:
                trend_direction = "상승"
            else:
                trend_direction = "하락"
            
            # 추세의 강도
            if abs(r_value) > 0.7:
                trend_strength = "강한"
            elif abs(r_value) > 0.4:
                trend_strength = "중간"
            else:
                trend_strength = "약한"
            
            trends["overall_trend"] = {
                "direction": trend_direction,
                "strength": trend_strength,
                "slope": slope,
                "r_squared": r_value**2,
                "p_value": p_value
            }
        else:
            trends["overall_trend"] = {
                "direction": "불명확",
                "strength": "무의미",
                "slope": slope,
                "r_squared": r_value**2,
                "p_value": p_value
            }
    except:
        # scipy가 없거나 오류 발생시
        # 간단한 추세 계산 (첫 값과 마지막 값 비교)
        first_value = df_sorted[value_column].iloc[0]
        last_value = df_sorted[value_column].iloc[-1]
        
        if last_value > first_value:
            trend_direction = "상승"
            percent_change = ((last_value / first_value) - 1) * 100
        else:
            trend_direction = "하락"
            percent_change = ((first_value / last_value) - 1) * 100
        
        trends["overall_trend"] = {
            "direction": trend_direction,
            "percent_change": percent_change
        }
    
    # 계절성 또는 주기성 확인 (충분한 데이터가 있을 경우)
    if len(df_sorted) >= 12:
        # 월별 집계 (계절성 확인용)
        try:
            monthly_data = df_sorted.groupby(df_sorted[date_column].dt.month)[value_column].mean()
            max_month = monthly_data.idxmax()
            min_month = monthly_data.idxmin()
            
            month_names = {
                1: '1월', 2: '2월', 3: '3월', 4: '4월', 5: '5월', 6: '6월',
                7: '7월', 8: '8월', 9: '9월', 10: '10월', 11: '11월', 12: '12월'
            }
            
            max_diff = monthly_data.max() - monthly_data.min()
            avg_value = monthly_data.mean()
            
            # 변동성이 평균의 20% 이상인 경우 계절성이 있다고 판단
            if max_diff > avg_value * 0.2:
                trends["seasonality"] = {
                    "exists": True,
                    "peak_month": month_names[max_month],
                    "lowest_month": month_names[min_month],
                    "variation_percent": (max_diff / avg_value) * 100
                }
            else:
                trends["seasonality"] = {"exists": False}
        except:
            trends["seasonality"] = {"exists": "unknown"}
    
    return trends

def detect_anomalies(df, column, method='iqr', threshold=1.5):
    """
    데이터에서 이상치 감지
    
    Args:
        df (pandas.DataFrame): 데이터프레임
        column (str): 분석할 열 이름
        method (str): 'iqr' 또는 'zscore'
        threshold (float): 이상치 판단 임계값
        
    Returns:
        dict: 감지된 이상치 정보
    """
    if column not in df.columns:
        return {"error": f"열 '{column}'이 데이터프레임에 존재하지 않습니다."}
    
    if not pd.api.types.is_numeric_dtype(df[column]):
        return {"error": f"열 '{column}'이 수치형 데이터가 아닙니다."}
    
    result = {
        "method": method,
        "threshold": threshold,
        "anomalies": []
    }
    
    if method == 'iqr':
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        
        anomalies = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
        
        result.update({
            "lower_bound": float(lower_bound),
            "upper_bound": float(upper_bound),
            "anomaly_count": len(anomalies),
            "anomaly_percent": (len(anomalies) / len(df)) * 100,
            "anomalies": anomalies.to_dict(orient='records') if len(anomalies) <= 10 else None
        })
        
        if result["anomaly_count"] > 10:
            result["note"] = "10개 이상의 이상치가 발견되어 전체 목록은 생략됩니다."
    
    elif method == 'zscore':
        from scipy import stats
        z_scores = np.abs(stats.zscore(df[column]))
        anomalies = df[z_scores > threshold]
        
        result.update({
            "anomaly_count": len(anomalies),
            "anomaly_percent": (len(anomalies) / len(df)) * 100,
            "anomalies": anomalies.to_dict(orient='records') if len(anomalies) <= 10 else None
        })
        
        if result["anomaly_count"] > 10:
            result["note"] = "10개 이상의 이상치가 발견되어 전체 목록은 생략됩니다."
    
    return result

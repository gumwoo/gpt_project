"""
데이터 스토리텔러 애플리케이션의 데이터 로딩 및 기본 처리를 담당하는 모듈입니다.
"""

import pandas as pd
import numpy as np
import os
import chardet
import streamlit as st

def detect_encoding(file_path):
    """
    파일의 인코딩을 감지합니다.
    
    Args:
        file_path (str): 파일 경로
    
    Returns:
        str: 감지된 인코딩
    """
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def load_csv_with_encoding(file_path):
    """
    다양한 인코딩을 시도하여 CSV 파일을 로드합니다.
    
    Args:
        file_path (str): CSV 파일 경로
    
    Returns:
        pandas.DataFrame: 로드된 데이터프레임
    """
    # 인코딩 감지 시도
    try:
        encoding = detect_encoding(file_path)
        df = pd.read_csv(file_path, encoding=encoding)
        return df
    except:
        # 인코딩 감지 실패시 일반적인 인코딩 시도
        encodings = ['utf-8', 'cp949', 'euc-kr', 'latin1']
        for enc in encodings:
            try:
                df = pd.read_csv(file_path, encoding=enc)
                return df
            except:
                continue
        
        # 모든 인코딩 시도 실패시 예외 발생
        raise ValueError("지원되는 인코딩으로 파일을 읽을 수 없습니다.")

def load_sample_data(sample_name):
    """
    샘플 데이터를 로드합니다.
    
    Args:
        sample_name (str): 샘플 데이터 이름
    
    Returns:
        pandas.DataFrame: 로드된 데이터프레임
    """
    sample_data_path = os.path.join("sample_data", f"{sample_name}.csv")
    
    try:
        df = load_csv_with_encoding(sample_data_path)
        return df
    except Exception as e:
        raise Exception(f"샘플 데이터 로드 중 오류 발생: {e}")

def get_sample_data_info():
    """
    사용 가능한 샘플 데이터와 설명을 반환합니다.
    
    Returns:
        dict: 샘플 데이터 이름과 설명
    """
    return {
        "sales_data": {
            "title": "판매 데이터",
            "description": "날짜, 지역, 제품 카테고리, 판매액, 판매량 등이 포함된 판매 데이터입니다.",
            "columns": ["date", "region", "product_category", "sales_amount", "units_sold", "customer_type", "promotion_active"]
        },
        "marketing_campaign": {
            "title": "마케팅 캠페인 데이터",
            "description": "여러 마케팅 채널의 비용, 노출, 클릭, 전환 등 캠페인 성과 데이터입니다.",
            "columns": ["campaign_id", "date", "channel", "cost", "impressions", "clicks", "conversions", "conversion_value", "target_audience"]
        },
        "customer_satisfaction": {
            "title": "고객 만족도 조사",
            "description": "제품 품질, 고객 서비스, 가격 만족도 등에 대한 고객 설문 결과입니다.",
            "columns": ["survey_id", "date", "customer_id", "age_group", "gender", "purchase_frequency", "product_quality_rating", "customer_service_rating", "price_satisfaction", "recommendation_likelihood", "overall_satisfaction", "feedback_text"]
        }
    }

def clean_data(df, params=None):
    """
    기본적인 데이터 정제를 수행합니다.
    
    Args:
        df (pandas.DataFrame): 정제할 데이터프레임
        params (dict, optional): 정제 매개변수
    
    Returns:
        pandas.DataFrame: 정제된 데이터프레임
    """
    if params is None:
        params = {}
    
    # 복사본 생성
    cleaned_df = df.copy()
    
    # 날짜 열 변환
    date_columns = [col for col in cleaned_df.columns if 'date' in col.lower()]
    for col in date_columns:
        try:
            cleaned_df[col] = pd.to_datetime(cleaned_df[col])
        except:
            pass
    
    # 결측치 처리 (선택적)
    if params.get('handle_missing', False):
        numeric_cols = cleaned_df.select_dtypes(include=['int64', 'float64']).columns
        categorical_cols = cleaned_df.select_dtypes(include=['object', 'category']).columns
        
        # 수치형 열 - 평균으로 대체
        for col in numeric_cols:
            cleaned_df[col].fillna(cleaned_df[col].mean(), inplace=True)
        
        # 범주형 열 - 최빈값으로 대체
        for col in categorical_cols:
            if not cleaned_df[col].isna().any():
                continue
            try:
                cleaned_df[col].fillna(cleaned_df[col].mode()[0], inplace=True)
            except:
                pass
    
    # 이상치 처리 (선택적)
    if params.get('handle_outliers', False):
        numeric_cols = cleaned_df.select_dtypes(include=['int64', 'float64']).columns
        for col in numeric_cols:
            Q1 = cleaned_df[col].quantile(0.25)
            Q3 = cleaned_df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # 이상치를 경계값으로 대체
            cleaned_df[col] = cleaned_df[col].clip(lower=lower_bound, upper=upper_bound)
    
    return cleaned_df

def load_uploaded_file(uploaded_file):
    """
    Streamlit에서 업로드된 파일을 처리합니다.
    
    Args:
        uploaded_file: Streamlit의 업로드된 파일 객체
        
    Returns:
        pandas.DataFrame: 로드된 데이터프레임
    """
    try:
        # 파일을 임시 디렉토리에 저장
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # 인코딩 감지 및 파일 읽기
        df = load_csv_with_encoding(temp_path)
        
        # 임시 파일 삭제
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return df
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise Exception(f"파일 처리 중 오류가 발생했습니다: {str(e)}")

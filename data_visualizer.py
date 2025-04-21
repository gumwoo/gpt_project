"""
데이터 스토리텔러 애플리케이션의 데이터 시각화를 담당하는 모듈입니다.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.font_manager as fm
import platform
import os

# 한글 폰트 설정
def set_matplotlib_korean_font():
    """
    Matplotlib에 한글 폰트 설정을 적용합니다.
    """
    system_name = platform.system()
    
    # 기본 폰트 설정
    default_font = 'NanumGothic'
    
    try:
        if system_name == 'Windows':
            # Windows 시스템 폰트 목록
            font_list = ['Malgun Gothic', 'NanumGothic', 'NanumBarunGothic', 'Gulim']
            for font in font_list:
                if any([font in f.name for f in fm.fontManager.ttflist]):
                    plt.rcParams['font.family'] = font
                    plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 표시 설정
                    return
                    
        elif system_name == 'Darwin':  # macOS
            # macOS 시스템 폰트 목록
            font_list = ['AppleGothic', 'NanumGothic', 'NanumBarunGothic']
            for font in font_list:
                if any([font in f.name for f in fm.fontManager.ttflist]):
                    plt.rcParams['font.family'] = font
                    plt.rcParams['axes.unicode_minus'] = False
                    return
                    
        elif system_name == 'Linux':
            # Linux 시스템 폰트 목록
            font_list = ['NanumGothic', 'NanumBarunGothic', 'UnDotum']
            for font in font_list:
                if any([font in f.name for f in fm.fontManager.ttflist]):
                    plt.rcParams['font.family'] = font
                    plt.rcParams['axes.unicode_minus'] = False
                    return
                    
        # 폰트를 찾지 못한 경우, 자주 사용되는 폰트 파일 경로 확인
        font_paths = []
        
        if system_name == 'Windows':
            font_paths.append('C:/Windows/Fonts/malgun.ttf')  # 맑은 고딕
        elif system_name == 'Darwin':
            font_paths.append('/Library/Fonts/AppleGothic.ttf')  # 애플고딕
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                fm.fontManager.addfont(font_path)
                plt.rcParams['font.family'] = fm.FontProperties(fname=font_path).get_name()
                plt.rcParams['axes.unicode_minus'] = False
                return
        
        # 모든 시도 실패시 기본값 사용
        plt.rcParams['font.family'] = 'sans-serif'  
        plt.rcParams['axes.unicode_minus'] = False
        st.warning("한글 폰트를 찾을 수 없습니다. 한글이 깨져 보일 수 있습니다.")
        
    except Exception as e:
        st.warning(f"폰트 설정 중 오류 발생: {e}")
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['axes.unicode_minus'] = False

# 시각화 함수 호출 전에 한글 폰트 설정
set_matplotlib_korean_font()

def create_chart(df, chart_info):
    """
    차트 정보에 기반하여 적절한 시각화를 생성합니다.
    
    Args:
        df (pandas.DataFrame): 데이터프레임
        chart_info (dict): 차트 정보 및 매개변수
    
    Returns:
        matplotlib.figure.Figure 또는 plotly.graph_objects.Figure: 생성된 차트
    """
    chart_type = chart_info.get("type", "").lower()
    x_column = chart_info.get("x_column")
    y_column = chart_info.get("y_column")
    title = chart_info.get("title", "")
    
    if not x_column or not y_column:
        st.warning("차트 생성에 필요한 열 정보가 부족합니다.")
        return None
    
    # x_column과 y_column이 실제 데이터프레임에 존재하는지 확인
    if x_column not in df.columns or y_column not in df.columns:
        st.warning(f"지정된 열({x_column} 또는 {y_column})이 데이터프레임에 존재하지 않습니다.")
        return None
    
    # 차트 유형에 따라 적절한 시각화 생성
    try:
        if chart_type == "bar":
            fig = create_bar_chart(df, x_column, y_column, title)
        elif chart_type == "line":
            fig = create_line_chart(df, x_column, y_column, title)
        elif chart_type == "scatter":
            fig = create_scatter_chart(df, x_column, y_column, title)
        elif chart_type == "pie":
            fig = create_pie_chart(df, x_column, y_column, title)
        elif chart_type == "heatmap":
            fig = create_heatmap(df, chart_info)
        else:
            st.warning(f"지원하지 않는 차트 유형입니다: {chart_type}")
            return None
        
        return fig
    
    except Exception as e:
        st.error(f"차트 생성 중 오류 발생: {e}")
        return None

def create_bar_chart(df, x_column, y_column, title=""):
    """
    막대 차트를 생성합니다.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 한글 폰트 재확인
    set_matplotlib_korean_font()
    
    # 열의 데이터 타입에 따라 집계 여부 결정
    if df[x_column].dtype == 'object' or df[x_column].dtype.name == 'category':
        # 범주형 데이터의 경우 집계
        agg_data = df.groupby(x_column)[y_column].sum().reset_index()
        sns.barplot(x=x_column, y=y_column, data=agg_data, ax=ax)
    else:
        # 수치형 데이터의 경우 직접 플롯
        sns.barplot(x=x_column, y=y_column, data=df, ax=ax)
    
    ax.set_title(title)
    ax.set_xlabel(x_column)
    ax.set_ylabel(y_column)
    
    # x축 레이블이 길 경우 회전
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    return fig

def create_line_chart(df, x_column, y_column, title=""):
    """
    선 차트를 생성합니다.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 한글 폰트 재확인
    set_matplotlib_korean_font()
    
    # 날짜 열인 경우 정렬
    if pd.api.types.is_datetime64_any_dtype(df[x_column]):
        df = df.sort_values(by=x_column)
    
    # 열의 데이터 타입에 따라 집계 여부 결정
    if df[x_column].dtype == 'object' or df[x_column].dtype.name == 'category':
        # 범주형 데이터의 경우 집계
        agg_data = df.groupby(x_column)[y_column].mean().reset_index()
        ax.plot(agg_data[x_column], agg_data[y_column], marker='o')
    else:
        # 수치형 데이터의 경우 직접 플롯
        ax.plot(df[x_column], df[y_column], marker='o')
    
    ax.set_title(title)
    ax.set_xlabel(x_column)
    ax.set_ylabel(y_column)
    
    # x축 레이블이 길 경우 회전
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    return fig

def create_scatter_chart(df, x_column, y_column, title=""):
    """
    산점도를 생성합니다.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 한글 폰트 재확인
    set_matplotlib_korean_font()
    
    # 산점도 생성
    sns.scatterplot(x=x_column, y=y_column, data=df, ax=ax)
    
    # 추세선 추가
    try:
        # 두 변수가 모두 수치형인 경우에만 추세선 추가
        if pd.api.types.is_numeric_dtype(df[x_column]) and pd.api.types.is_numeric_dtype(df[y_column]):
            sns.regplot(x=x_column, y=y_column, data=df, scatter=False, ax=ax)
    except:
        pass
    
    ax.set_title(title)
    ax.set_xlabel(x_column)
    ax.set_ylabel(y_column)
    
    plt.tight_layout()
    return fig

def create_pie_chart(df, x_column, y_column, title=""):
    """
    파이 차트를 생성합니다.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 한글 폰트 재확인
    set_matplotlib_korean_font()
    
    # 범주형 변수에 대한 집계
    agg_data = df.groupby(x_column)[y_column].sum().reset_index()
    
    # 파이 차트 생성
    ax.pie(agg_data[y_column], labels=agg_data[x_column], autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # 원형 파이 차트를 위한 설정
    
    ax.set_title(title)
    
    plt.tight_layout()
    return fig

def create_heatmap(df, chart_info):
    """
    히트맵을 생성합니다.
    """
    # 한글 폰트 재확인
    set_matplotlib_korean_font()
    
    # 수치형 열만 선택
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    
    if len(numeric_cols) < 2:
        st.warning("히트맵을 생성하기 위한 충분한 수치형 열이 없습니다.")
        return None
    
    # 상관관계 계산
    corr_matrix = df[numeric_cols].corr()
    
    # 히트맵 생성
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', ax=ax)
    
    title = chart_info.get("title", "변수 간 상관관계 히트맵")
    ax.set_title(title)
    
    plt.tight_layout()
    return fig

def auto_generate_charts(df, max_charts=3):
    """
    데이터프레임을 분석하여 자동으로 의미 있는 차트를 생성합니다.
    
    Args:
        df (pandas.DataFrame): 데이터프레임
        max_charts (int): 생성할 최대 차트 수
    
    Returns:
        list: (차트 제목, matplotlib.figure.Figure) 튜플의 리스트
    """
    # 한글 폰트 재확인
    set_matplotlib_korean_font()
    
    charts = []
    
    # 데이터 타입 파악
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    date_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
    
    # 1. 시계열 데이터가 있는 경우 시계열 차트
    if date_cols and numeric_cols:
        date_col = date_cols[0]
        for i, num_col in enumerate(numeric_cols[:2]):  # 최대 2개의 수치형 열에 대해
            title = f"{date_col} 기준 {num_col} 추이"
            chart_info = {
                "type": "line",
                "x_column": date_col,
                "y_column": num_col,
                "title": title
            }
            fig = create_chart(df, chart_info)
            if fig:
                charts.append((title, fig))
                if len(charts) >= max_charts:
                    return charts
    
    # 2. 범주별 합계 또는 평균 (막대 차트)
    if categorical_cols and numeric_cols:
        cat_col = categorical_cols[0]  # 첫 번째 범주형 열
        num_col = numeric_cols[0]  # 첫 번째 수치형 열
        
        title = f"{cat_col}별 {num_col} 합계"
        chart_info = {
            "type": "bar",
            "x_column": cat_col,
            "y_column": num_col,
            "title": title
        }
        fig = create_chart(df, chart_info)
        if fig:
            charts.append((title, fig))
            if len(charts) >= max_charts:
                return charts
    
    # 3. 두 수치형 변수 간의 관계 (산점도)
    if len(numeric_cols) >= 2:
        x_col = numeric_cols[0]
        y_col = numeric_cols[1]
        
        title = f"{x_col}와 {y_col} 간의 관계"
        chart_info = {
            "type": "scatter",
            "x_column": x_col,
            "y_column": y_col,
            "title": title
        }
        fig = create_chart(df, chart_info)
        if fig:
            charts.append((title, fig))
            if len(charts) >= max_charts:
                return charts
    
    # 4. 변수 간 상관관계 (히트맵)
    if len(numeric_cols) >= 3:
        title = "변수 간 상관관계 히트맵"
        chart_info = {
            "type": "heatmap",
            "title": title
        }
        fig = create_heatmap(df, chart_info)
        if fig:
            charts.append((title, fig))
            if len(charts) >= max_charts:
                return charts
    
    return charts

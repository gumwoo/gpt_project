import streamlit as st
import pandas as pd
import numpy as np
import json
import requests
import os
from io import StringIO
import matplotlib.pyplot as plt
import seaborn as sns
from prompts import generate_data_story_prompt
from data_loader import load_sample_data, get_sample_data_info, load_uploaded_file
from data_visualizer import create_chart, auto_generate_charts, set_matplotlib_korean_font

# 환경 변수 로드 시도 (로컬 개발 환경용)
try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass

# 페이지 설정
st.set_page_config(
    page_title="데이터 스토리텔러",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API 키 설정 - Streamlit Cloud의 secrets 또는 환경 변수에서 로드
if 'OPENAI_API_KEY' in st.secrets:
    API_KEY = st.secrets['OPENAI_API_KEY']
else:
    API_KEY = os.getenv("OPENAI_API_KEY")

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# API 키가 없는 경우 경고
if not API_KEY:
    st.warning("OpenAI API 키가 설정되지 않았습니다. Streamlit Cloud의 secrets 또는 .env 파일을 확인하세요.")

# 한글 폰트 설정 시도 (오류가 발생해도 앱은 계속 작동)
try:
    set_matplotlib_korean_font()
except Exception as e:
    st.warning(f"한글 폰트 설정 중 오류가 발생했습니다: {e}. 한글이 깨져 보일 수 있습니다.")

# GPT API 호출 함수
def generate_data_story(prompt, model="gpt-3.5-turbo"):
    if not API_KEY:
        st.error("API 키가 설정되지 않았습니다.")
        return None
        
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    # response_format 추가 (일부 모델만 지원)
    try:
        # 최신 모델에만 적용
        if "gpt-4" in model or "-turbo" in model:
            payload["response_format"] = {"type": "json_object"}
    except:
        # 오류 발생시 무시
        pass
    
    try:
        response = requests.post(OPENAI_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # 오류 발생시 예외 발생
        
        # 응답 디버깅
        st.write("API 응답:", response.status_code)
        
        # 응답 형식 확인
        response_json = response.json()
        if "choices" in response_json and len(response_json["choices"]) > 0:
            content = response_json["choices"][0]["message"]["content"]
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                st.error("API 응답이 유효한 JSON 형식이 아닙니다.")
                st.write("원본 응답:", content)
                return None
        else:
            st.error(f"API 응답 형식 오류: {response_json}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 오류: {e}")
        if hasattr(e, 'response') and e.response is not None:
            st.error(f"응답 내용: {e.response.text}")
        return None
    except (KeyError, json.JSONDecodeError) as e:
        st.error(f"응답 파싱 오류: {e}")
        return None

# 기본 통계 분석 함수
def analyze_dataframe(df):
    analysis = {}
    
    # 기본 정보
    analysis["basic_info"] = {
        "rows": df.shape[0],
        "columns": df.shape[1],
        "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
    }
    
    # 수치형 열에 대한 기본 통계
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    if numeric_cols:
        analysis["numeric_stats"] = {}
        for col in numeric_cols:
            analysis["numeric_stats"][col] = {
                "mean": float(df[col].mean()),
                "median": float(df[col].median()),
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "std": float(df[col].std())
            }
        
        # 상관관계 매트릭스
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr().to_dict()
            analysis["correlation"] = corr_matrix
    
    # 범주형 열에 대한 기본 통계
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    if categorical_cols:
        analysis["categorical_stats"] = {}
        for col in categorical_cols:
            # 상위 5개 카테고리만 포함
            counts = df[col].value_counts().head(5).to_dict()
            analysis["categorical_stats"][col] = counts
    
    # 결측치 정보
    analysis["missing_values"] = df.isnull().sum().to_dict()
    
    return analysis

# 애플리케이션 UI
def main():
    st.title("📊 데이터 스토리텔러")
    st.markdown("#### 데이터를 업로드하고 AI가 분석한 스토리를 확인하세요!")
    
    with st.sidebar:
        st.header("설정")
        audience = st.selectbox(
            "대상 청중",
            ["경영진", "마케팅팀", "기술팀", "일반 대중"]
        )
        
        story_focus = st.selectbox(
            "스토리 중점",
            ["주요 트렌드", "이상치 및 특이점", "상관관계 분석", "종합 인사이트"]
        )
        
        story_length = st.select_slider(
            "스토리 길이",
            options=["간결", "보통", "상세"],
            value="보통"
        )
        
        # matplotlib 스타일 목록 수정 - 최신 버전 호환성을 위해
        available_styles = ['default', 'classic', 'ggplot', 'bmh', 'dark_background']
        
        chart_style = st.selectbox(
            "차트 스타일",
            available_styles
        )
        
        # 스타일 적용 시도, 실패하면 기본 스타일 사용
        try:
            plt.style.use(chart_style)
        except Exception as e:
            st.warning(f"스타일 '{chart_style}'을 적용할 수 없습니다. 기본 스타일을 사용합니다.")
            plt.style.use('default')
    
    # 파일 업로드
    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type=['csv'])
    
    df = None
    
    if uploaded_file is not None:
        try:
            # 업로드된 파일 처리
            try:
                # 먼저 기본 방식으로 시도
                df = pd.read_csv(uploaded_file)
            except UnicodeDecodeError:
                # 인코딩 오류 발생 시 사용자 정의 함수 사용
                uploaded_file.seek(0)  # 파일 포인터 초기화
                df = load_uploaded_file(uploaded_file)
            
            # 기본 데이터 미리보기
            st.subheader("데이터 미리보기")
            st.dataframe(df.head())
            
            # 기본 정보 표시
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("행 수", df.shape[0])
            with col2:
                st.metric("열 수", df.shape[1])
            with col3:
                st.metric("결측치", df.isnull().sum().sum())
            
        except Exception as e:
            st.error(f"파일 처리 중 오류가 발생했습니다: {str(e)}")
    
    else:
        # 샘플 데이터 옵션
        st.markdown("### 또는 샘플 데이터로 시작하세요")
        sample_data_info = get_sample_data_info()
        sample_options = ["선택하세요..."] + [info["title"] for info in sample_data_info.values()]
        
        sample_option = st.selectbox(
            "샘플 데이터 선택",
            sample_options
        )
        
        if sample_option != "선택하세요...":
            # 샘플 데이터 로드
            sample_name = next((name for name, info in sample_data_info.items() 
                              if info["title"] == sample_option), None)
            if sample_name:
                try:
                    df = load_sample_data(sample_name)
                    
                    # 기본 데이터 미리보기
                    st.subheader("데이터 미리보기")
                    st.dataframe(df.head())
                    
                    # 기본 정보 표시
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("행 수", df.shape[0])
                    with col2:
                        st.metric("열 수", df.shape[1])
                    with col3:
                        st.metric("결측치", df.isnull().sum().sum())
                    
                    st.success(f"{sample_option} 데이터가 로드되었습니다. '데이터 스토리 생성' 버튼을 눌러 계속하세요.")
                except Exception as e:
                    st.error(f"샘플 데이터 로드 중 오류 발생: {e}")
    
    # 데이터 분석 버튼
    if df is not None and st.button("데이터 스토리 생성"):
        with st.spinner("데이터를 분석하고 스토리를 생성 중입니다..."):
            # 데이터 분석
            analysis_result = analyze_dataframe(df)
            
            # 분석 결과 디버깅 (개발 중에만 사용)
            with st.expander("데이터 분석 결과 (디버깅용)"):
                st.json(analysis_result)
            
            # 사용자 설정에 맞는 프롬프트 생성
            prompt = generate_data_story_prompt(
                dataframe_info=analysis_result,
                audience=audience,
                focus=story_focus,
                length=story_length,
                sample_data=df.head(10).to_dict()
            )
            
            # 프롬프트 디버깅 (개발 중에만 사용)
            with st.expander("생성된 프롬프트 (디버깅용)"):
                st.text(prompt)
            
            # GPT API 호출 전 더미 데이터 준비 (API 오류 시 사용)
            dummy_data = {
                "key_insights": [
                    {
                        "title": "샘플 인사이트 1",
                        "description": "이것은 API 호출 실패 시 표시되는 샘플 인사이트입니다.",
                        "chart_recommendation": {
                            "type": "bar",
                            "x_column": df.columns[0] if len(df.columns) > 0 else "",
                            "y_column": df.select_dtypes(include=['int64', 'float64']).columns[0] if len(df.select_dtypes(include=['int64', 'float64']).columns) > 0 else "",
                            "title": "샘플 차트",
                            "description": "샘플 차트 설명"
                        }
                    }
                ],
                "narrative": "이것은 API 호출 실패 시 표시되는 샘플 내러티브입니다. 실제 API가 성공적으로 호출되면 이 텍스트는 대체됩니다.",
                "recommended_actions": [
                    {
                        "title": "샘플 액션",
                        "description": "이것은 샘플 추천 액션입니다."
                    }
                ]
            }
            
            # GPT API 호출
            story_result = generate_data_story(prompt)
            
            # API 호출 실패 시 더미 데이터 사용
            if story_result is None:
                st.warning("GPT API 호출이 실패했습니다. 샘플 데이터를 표시합니다.")
                story_result = dummy_data
            
            # 결과 표시
            st.subheader("📝 데이터 스토리")
            
            # 주요 인사이트 표시
            st.markdown("### 주요 인사이트")
            
            if "key_insights" in story_result and isinstance(story_result["key_insights"], list):
                for i, insight in enumerate(story_result["key_insights"]):
                    if not isinstance(insight, dict):
                        continue
                        
                    title = insight.get("title", f"인사이트 {i+1}")
                    with st.expander(f"인사이트 {i+1}: {title}"):
                        st.markdown(insight.get("description", ""))
                        
                        # 차트 추천이 있는 경우
                        if "chart_recommendation" in insight and isinstance(insight["chart_recommendation"], dict):
                            chart_info = insight["chart_recommendation"]
                            st.markdown(f"**추천 차트**: {chart_info.get('type', '')}")
                            
                            # 차트 생성 시도
                            try:
                                if all(k in chart_info for k in ["type", "x_column", "y_column"]):
                                    if chart_info["x_column"] in df.columns and chart_info["y_column"] in df.columns:
                                        fig = create_chart(df, chart_info)
                                        if fig:
                                            st.pyplot(fig)
                                        else:
                                            st.warning("차트를 생성할 수 없습니다.")
                                    else:
                                        st.warning(f"차트 생성에 필요한 열({chart_info['x_column']} 또는 {chart_info['y_column']})이 데이터에 없습니다.")
                            except Exception as e:
                                st.error(f"차트 생성 중 오류 발생: {e}")
            else:
                st.warning("인사이트를 찾을 수 없습니다.")
            
            # 종합 스토리 표시
            st.markdown("### 종합 데이터 스토리")
            st.markdown(story_result.get("narrative", "내러티브 내용이 없습니다."))
            
            # 추천 액션 표시
            if "recommended_actions" in story_result and isinstance(story_result["recommended_actions"], list):
                st.markdown("### 추천 액션")
                for action in story_result["recommended_actions"]:
                    if isinstance(action, dict):
                        st.markdown(f"- **{action.get('title', '')}**: {action.get('description', '')}")
            
            # 원본 JSON 데이터 보기 (디버깅용)
            with st.expander("원본 JSON 데이터"):
                st.json(story_result)
    
    # 필수 패키지 정보
    with st.expander("필요한 패키지 정보"):
        st.markdown("""
        이 애플리케이션을 실행하기 위해 필요한 Python 패키지:
        - streamlit
        - pandas
        - numpy
        - matplotlib
        - seaborn
        - requests
        - chardet (한글 인코딩 감지용)
        
        로컬 개발 환경에서 실행할 경우:
        - python-dotenv (환경 변수 로드용)
        
        API 키 설정 방법:
        - Streamlit Cloud에서는 앱 설정의 Secrets 메뉴에서 OPENAI_API_KEY 설정
        - 로컬 개발 환경에서는 .env 파일에 OPENAI_API_KEY=your_api_key_here 추가
        """)
    
    # 푸터
    st.markdown("---")
    st.markdown("데이터 스토리텔러 | GPT API 기반 데이터 분석 및 스토리텔링 도구")

if __name__ == "__main__":
    main()

import pandas as pd
import streamlit as st
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import plotly.express as px
import traceback

def prepare_features(df):
    """Enhanced feature preparation with validation and debugging"""
    try:
        # Initial data validation with correct PRAZO column names
        required_columns = ['DATA', 'RESOLUÇÃO', 'SITUAÇÃO', 'BANCO', 'PRAZO 7', 'PRAZO B']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Convert dates with validation
        date_columns = ['DATA', 'RESOLUÇÃO', 'ENTRADA', 'ÚLTIMO PAGAMENTO']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', dayfirst=True, errors='coerce')
                null_dates = df[col].isna().sum()
                if null_dates > 0:
                    print(f"Warning: {null_dates} null values in {col}")

        # Calculate DIAS_RESOLUCAO with validation
        df['DIAS_RESOLUCAO'] = np.where(
            df['DATA'].notna() & df['RESOLUÇÃO'].notna(),
            (df['RESOLUÇÃO'] - df['DATA']).dt.days,
            np.nan
        )

        # Process PRAZO columns safely using actual column names
        df['PRAZO_7'] = pd.to_numeric(df['PRAZO 7'].fillna(0), errors='coerce')
        df['PRAZO_B'] = pd.to_numeric(df['PRAZO B'].fillna(0), errors='coerce')
        df['PRAZO_TOTAL'] = df['PRAZO_7'] + df['PRAZO_B']

        # Add status flags
        status_flags = {
            'IS_APROVADO': df['SITUAÇÃO'] == 'APROVADO',
            'IS_QUITADO': df['SITUAÇÃO'] == 'QUITADO',
            'IS_PENDENTE': df['SITUAÇÃO'] == 'PENDENTE',
            'IS_ANALISE': df['SITUAÇÃO'] == 'ANÁLISE'
        }
        for flag_name, flag_value in status_flags.items():
            df[flag_name] = flag_value.astype(int)

        # Debug information
        print("\nProcessed Features:")
        print(f"PRAZO_7 range: {df['PRAZO_7'].min()} to {df['PRAZO_7'].max()}")
        print(f"PRAZO_B range: {df['PRAZO_B'].min()} to {df['PRAZO_B'].max()}")
        print(f"PRAZO_TOTAL range: {df['PRAZO_TOTAL'].min()} to {df['PRAZO_TOTAL'].max()}")

        return df

    except Exception as e:
        print(f"Error in prepare_features: {str(e)}")
        print(f"Available columns: {df.columns.tolist()}")
        return None

def train_model(df):
    """Train RandomForest model"""
    try:
        # Prepare features
        features = ['MONTH', 'WEEKDAY', 'BANCO_ENCODED', 'ESCRITÓRIO_ENCODED']
        X = df[features]
        y = df['SUCCESS']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Get feature importance
        importance = pd.DataFrame({
            'feature': features,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        # Get predictions
        y_pred = model.predict(X_test)
        
        return model, importance, classification_report(y_test, y_pred)
    except Exception as e:
        st.error(f"Error training model: {str(e)}")
        return None, None, None

def load_and_process_data():
    """Load and preprocess the data with proper date handling"""
    try:
        # Load data file with explicit encoding
        df = pd.read_csv('(JULIO) LISTAS INDIVIDUAIS - IGOR.csv', 
                        encoding='utf-8')
        
        # Clean column names
        df.columns = df.columns.str.strip()
        print("Columns after cleaning:", df.columns.tolist())

        # Convert date columns with proper format
        date_columns = ['DATA', 'RESOLUÇÃO', 'ENTRADA', 'ÚLTIMO PAGAMENTO']
        for col in date_columns:
            if col in df.columns:
                # Convert to datetime with proper format
                df[col] = pd.to_datetime(df[col], 
                                       format='%d/%m/%Y',
                                       dayfirst=True,
                                       errors='coerce')
                print(f"\nConverted {col} to datetime. Sample values:")
                print(df[col].head())

        return df

    except Exception as e:
        st.error(f"Error in load_and_process_data: {str(e)}")
        return None

def analyze_patterns(df):
    """Enhanced pattern analysis with safe defaults"""
    try:
        if df is None:
            raise ValueError("DataFrame is None")

        # Initialize metrics dictionary with safe defaults
        metrics = {
            'time_metrics': {
                'avg_dias_resolucao': 0,
                'max_dias_resolucao': 0,
                'min_dias_resolucao': 0,
                'avg_prazo_total': 0
            },
            'status_counts': pd.Series(dtype='int64'),
            'bank_performance': pd.DataFrame(),
            'monthly_stats': pd.DataFrame()
        }

        # Status analysis
        metrics['status_counts'] = df['SITUAÇÃO'].value_counts()
        print("\nStatus distribution:", metrics['status_counts'])

        # Time metrics with validation
        if 'DIAS_RESOLUCAO' in df.columns:
            valid_dias = df['DIAS_RESOLUCAO'].dropna()
            if not valid_dias.empty:
                metrics['time_metrics'].update({
                    'avg_dias_resolucao': valid_dias.mean(),
                    'max_dias_resolucao': valid_dias.max(),
                    'min_dias_resolucao': valid_dias.min()
                })

        if 'PRAZO_TOTAL' in df.columns:
            valid_prazo = df['PRAZO_TOTAL'].dropna()
            if not valid_prazo.empty:
                metrics['time_metrics']['avg_prazo_total'] = valid_prazo.mean()

        # Bank performance
        bank_metrics = df.groupby('BANCO').agg({
            'IS_APROVADO': 'sum',
            'IS_QUITADO': 'sum',
            'PRAZO_TOTAL': 'mean'
        }).round(2)
        metrics['bank_performance'] = bank_metrics

        # Monthly analysis
        df['MES'] = df['DATA'].dt.month
        monthly_data = df.groupby('MES').agg({
            'IS_APROVADO': 'sum',
            'IS_QUITADO': 'sum'
        }).fillna(0)
        metrics['monthly_stats'] = monthly_data

        return metrics

    except Exception as e:
        print(f"Error in analyze_patterns: {str(e)}")
        return None

def analyze_status_statistics(df):
    """Analyze SITUAÇÃO statistics with enhanced null handling"""
    try:
        # Basic status counts with null check
        status_counts = df['SITUAÇÃO'].value_counts()
        total_records = len(df)
        status_percentages = {
            status: round((count / total_records * 100), 2)
            for status, count in status_counts.items()
        }
        
        # Status metrics with safe calculations
        status_metrics = {}
        for status in df['SITUAÇÃO'].unique():
            status_data = df[df['SITUAÇÃO'] == status]
            
            # Safe calculations for averages
            avg_dias_resolucao = status_data['DIAS_RESOLUCAO'].mean()
            avg_dias_resolucao = round(float(avg_dias_resolucao), 2) if pd.notnull(avg_dias_resolucao) else 0
            
            avg_prazo_total = status_data['PRAZO_TOTAL'].mean()
            avg_prazo_total = round(float(avg_prazo_total), 2) if pd.notnull(avg_prazo_total) else 0
            
            # Safe processing time calculation
            valid_dates = status_data[status_data['DATA'].notna() & status_data['RESOLUÇÃO'].notna()]
            avg_processing_time = (valid_dates['RESOLUÇÃO'] - valid_dates['DATA']).dt.days.mean()
            avg_processing_time = round(float(avg_processing_time), 2) if pd.notnull(avg_processing_time) else 0
            
            metrics = {
                'count': int(len(status_data)),
                'percentage': round(float(len(status_data) / total_records * 100), 2),
                'avg_dias_resolucao': avg_dias_resolucao,
                'avg_prazo_total': avg_prazo_total,
                'banks_count': int(status_data['BANCO'].nunique()),
                'top_banks': status_data['BANCO'].value_counts().head(3).to_dict(),
                'avg_processing_time': avg_processing_time,
                'null_counts': {
                    'DATA': int(status_data['DATA'].isna().sum()),
                    'RESOLUÇÃO': int(status_data['RESOLUÇÃO'].isna().sum()),
                    'ENTRADA': int(status_data['ENTRADA'].isna().sum()),
                    'ÚLTIMO PAGAMENTO': int(status_data['ÚLTIMO PAGAMENTO'].isna().sum())
                }
            }
            
            # Monthly distribution with null handling
            valid_dates = status_data[status_data['DATA'].notna()]
            monthly_dist = valid_dates.groupby(valid_dates['DATA'].dt.month).size()
            metrics['monthly_distribution'] = monthly_dist.to_dict()
            
            status_metrics[status] = metrics
        
        # Calculate overall statistics
        avg_resolution_time = df['DIAS_RESOLUCAO'].mean()
        avg_resolution_time = round(float(avg_resolution_time), 2) if pd.notnull(avg_resolution_time) else 0
        
        status_volatility = status_counts.std() / status_counts.mean()
        status_volatility = round(float(status_volatility), 2) if pd.notnull(status_volatility) else 0
        
        insights = {
            'main_findings': {
                'most_common_status': str(status_counts.index[0]),
                'least_common_status': str(status_counts.index[-1]),
                'avg_resolution_time': avg_resolution_time,
                'status_volatility': status_volatility,
                'status_distribution': status_percentages
            },
            'status_details': status_metrics,
            'data_quality': {
                'total_null_dates': {
                    'DATA': int(df['DATA'].isna().sum()),
                    'RESOLUÇÃO': int(df['RESOLUÇÃO'].isna().sum()),
                    'ENTRADA': int(df['ENTRADA'].isna().sum()),
                    'ÚLTIMO PAGAMENTO': int(df['ÚLTIMO PAGAMENTO'].isna().sum())
                },
                'completeness_score': round(
                    (1 - df[['DATA', 'RESOLUÇÃO', 'ENTRADA', 'ÚLTIMO PAGAMENTO']].isna().sum().mean() / len(df)) * 100,
                    2
                )
            }
        }
        
        return insights

    except Exception as e:
        print(f"Error in status analysis: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return None

def create_summary(df):
    """Create summary statistics"""
    try:
        summary = {
            'total_registros': len(df),
            'total_bancos': df['BANCO'].nunique(),
            'media_prazo': df['PRAZO_TOTAL'].mean(),
            'status_distribution': df['SITUAÇÃO'].value_counts().to_dict(),
            'bank_counts': df['BANCO'].value_counts().to_dict()
        }

        return pd.DataFrame([summary])

    except Exception as e:
        print(f"Error creating summary: {str(e)}")
        return None

def create_status_dashboard():
    """Enhanced dashboard with status analysis"""
    try:
        st.title("📊 Dashboard de Análise de Status")
        
        # Load and process data
        df = load_and_process_data()
        if df is None:
            st.error("Erro ao carregar dados")
            return
            
        df = prepare_features(df)
        if df is None:
            st.error("Erro ao preparar features")
            return
        
        # Get status insights
        insights = analyze_status_statistics(df)
        if insights is None:
            st.error("Erro na análise de status")
            return
            
        # Display insights
        display_status_insights(insights)
        
        # Additional analysis
        analysis = analyze_patterns(df)
        if analysis:
            st.header("📈 Métricas Adicionais")
            display_additional_metrics(analysis, df)

    except Exception as e:
        st.error(f"Dashboard error: {str(e)}")

def display_status_insights(insights):
    """Display status insights with data quality information"""
    try:
        st.header("📊 Análise Detalhada por Status")
        
        # Data quality metrics
        st.subheader("Qualidade dos Dados")
        quality_score = insights['data_quality']['completeness_score']
        st.metric("Score de Completude dos Dados", f"{quality_score}%")
        
        # Null values summary
        with st.expander("📋 Detalhes de Dados Nulos"):
            null_df = pd.DataFrame.from_dict(
                insights['data_quality']['total_null_dates'],
                orient='index',
                columns=['Quantidade de Nulos']
            )
            st.dataframe(null_df)
        
        # Main metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Status Mais Comum", 
                     insights['main_findings']['most_common_status'])
        with col2:
            st.metric("Tempo Médio de Resolução", 
                     f"{insights['main_findings']['avg_resolution_time']:.1f} dias")
        with col3:
            st.metric("Volatilidade dos Status", 
                     f"{insights['main_findings']['status_volatility']:.2f}")
        
        # Status distribution
        st.subheader("Distribuição dos Status")
        status_dist = pd.DataFrame.from_dict(
            insights['main_findings']['status_distribution'], 
            orient='index', 
            columns=['Percentual']
        )
        fig = px.bar(status_dist, 
                    title="Distribuição Percentual dos Status",
                    labels={'value': 'Percentual (%)', 'index': 'Status'})
        st.plotly_chart(fig)
        
        # Detailed status analysis
        st.subheader("Análise por Status")
        for status, metrics in insights['status_details'].items():
            with st.expander(f"📌 {status}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Quantidade", metrics['count'])
                    st.metric("Percentual", f"{metrics['percentage']:.2f}%")
                with col2:
                    st.metric("Bancos Únicos", metrics['banks_count'])
                    st.metric("Tempo Médio de Resolução", 
                             f"{metrics['avg_dias_resolucao']:.1f} dias")
                with col3:
                    st.metric("Prazo Médio", 
                             f"{metrics['avg_prazo_total']:.1f}")
                    st.metric("Dados Nulos", 
                             metrics['null_counts']['DATA'])
                
                # Top banks
                st.write("Top 3 Bancos:")
                st.write(metrics['top_banks'])
                
                # Monthly trend
                if metrics['monthly_distribution']:
                    monthly_data = pd.Series(metrics['monthly_distribution'])
                    fig = px.line(monthly_data, 
                                title=f"Distribuição Mensal - {status}")
                    st.plotly_chart(fig)
                else:
                    st.warning("Sem dados mensais disponíveis para este status")

    except Exception as e:
        st.error(f"Error displaying insights: {str(e)}")
        st.error(f"Traceback: {traceback.format_exc()}")

def display_additional_metrics(analysis, df):
    """Display additional metrics focusing on contracts and negotiations"""
    try:
        st.subheader("📑 Análise de Contratos e Negociações")
        
        # Create columns for key metrics
        col1, col2 = st.columns(2)
        
        with col1:
            # CTT Analysis
            st.write("### Análise por CTT")
            ctt_analysis = df.groupby(['BANCO', 'SITUAÇÃO']).size().unstack(fill_value=0)
            st.dataframe(ctt_analysis)
            
            # Visualization
            fig = px.bar(ctt_analysis, 
                        title="Distribuição de Status por Banco",
                        labels={'value': 'Quantidade', 'variable': 'Status'})
            st.plotly_chart(fig)
        
        with col2:
            # Negotiation Analysis
            st.write("### Análise de Negociações")
            neg_status = df.groupby(['NEGOCIAÇÃO', 'SITUAÇÃO']).size().unstack(fill_value=0)
            st.dataframe(neg_status)
            
            # Visualization
            fig = px.bar(neg_status,
                        title="Status por Tipo de Negociação",
                        labels={'value': 'Quantidade', 'variable': 'Status'})
            st.plotly_chart(fig)
        
        # Resolution Timeline Analysis
        st.subheader("📅 Timeline de Resoluções")
        
        # Group by resolution date and status
        timeline = df.groupby([df['RESOLUÇÃO'].dt.to_period('M'), 'SITUAÇÃO']).size().unstack(fill_value=0)
        
        # Convert period index to datetime for plotting
        timeline.index = timeline.index.astype(str)
        
        fig = px.line(timeline,
                     title="Evolução Temporal de Resoluções",
                     labels={'value': 'Quantidade', 'variable': 'Status', 'index': 'Período'})
        st.plotly_chart(fig)
        
        # Contract Analysis
        st.subheader("📊 Análise de Contratos")
        
        # Create contract metrics
        contract_metrics = pd.DataFrame({
            'Total_Contratos': len(df['CONTRATO'].unique()),
            'Media_Prazo': df['PRAZO_TOTAL'].mean(),
            'Contratos_Em_Analise': len(df[df['SITUAÇÃO'] == 'ANÁLISE']),
            'Contratos_Pendentes': len(df[df['SITUAÇÃO'] == 'PENDENTE']),
            'Contratos_Prioritarios': len(df[df['SITUAÇÃO'] == 'PRIORIDADE'])
        }, index=[0])
        
        # Display contract metrics
        st.dataframe(contract_metrics)
        
        # Contract Status Timeline
        contract_timeline = df.groupby([df['DATA'].dt.to_period('M'), 'SITUAÇÃO'])['CONTRATO'].count().unstack(fill_value=0)
        contract_timeline.index = contract_timeline.index.astype(str)
        
        fig = px.line(contract_timeline,
                     title="Evolução de Contratos por Status",
                     labels={'value': 'Quantidade de Contratos', 'variable': 'Status', 'index': 'Período'})
        st.plotly_chart(fig)
        
        # Update create_status_dashboard function to include the new metrics
        additional_insights = {
            'contract_metrics': contract_metrics.to_dict('records')[0],
            'negotiation_summary': neg_status.sum().to_dict(),
            'bank_distribution': ctt_analysis.sum().to_dict()
        }
        
        return additional_insights

    except Exception as e:
        st.error(f"Error displaying additional metrics: {str(e)}")
        st.error(f"Traceback: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    st.set_page_config(page_title="Análise de Aprovados/Quitados", layout="wide")
    create_status_dashboard()
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Tuple
import logging
import os

class QuitadosAnalyzer:
    def __init__(self):
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    @staticmethod
    @st.cache_data
    def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load and preprocess all datasets with Streamlit caching"""
        try:
            # Load main dataset
            main_df = pd.read_csv(
                r"C:\Users\igor de jesus\zaptest\(JULIO) LISTAS INDIVIDUAIS - IGOR.csv",
                encoding='utf-8',
                decimal=',',
                thousands='.'
            )
            
            # Clean column names and convert to uppercase for consistency
            main_df.columns = main_df.columns.str.strip().str.upper()
            
            # Convert monetary values with enhanced error handling
            if 'VALOR DO CLIENTE' in main_df.columns:
                main_df['VALOR_CLEANED'] = (
                    main_df['VALOR DO CLIENTE']
                    .str.replace('R$', '')
                    .str.replace('.', '')
                    .str.replace(',', '.')
                    .str.extract(r'(\d+\.?\d*)')
                )
                main_df['VALOR_CLEANED'] = pd.to_numeric(main_df['VALOR_CLEANED'], errors='coerce')
            
            # Load supporting datasets
            aprovados_df = pd.read_csv(
                r"C:\Users\igor de jesus\zaptest\DEMANDAS DE ABRIL_2025 - APROVADOS.csv",
                encoding='utf-8'
            )
            aprovados_df.columns = aprovados_df.columns.str.strip().str.upper()
            
            quitados_df = pd.read_csv(
                r"C:\Users\igor de jesus\zaptest\DEMANDAS DE ABRIL_2025 - QUITADOS.csv",
                encoding='utf-8'
            )
            quitados_df.columns = quitados_df.columns.str.strip().str.upper()
            
            # Process dates
            date_cols = ['DATA', 'RESOLUÇÃO']
            for df in [main_df, aprovados_df, quitados_df]:
                for col in date_cols:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
            
            return main_df, aprovados_df, quitados_df
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            raise

    def analyze_bank_performance(self, df: pd.DataFrame) -> pd.DataFrame:
        """Analyze success rates and metrics by bank"""
        try:
            # Basic bank statistics
            bank_stats = df.groupby('BANCO').agg({
                'SITUAÇÃO': 'count',
                'VALOR_CLEANED': 'mean'
            }).reset_index()
            
            # Calculate quitados
            quitados = df[df['SITUAÇÃO'] == 'QUITADO'].groupby('BANCO').size()
            bank_stats['QUITADOS'] = bank_stats['BANCO'].map(quitados).fillna(0)
            bank_stats['SUCCESS_RATE'] = (bank_stats['QUITADOS'] / bank_stats['SITUAÇÃO'] * 100).round(2)
            
            return bank_stats.sort_values('SUCCESS_RATE', ascending=False)
            
        except Exception as e:
            st.error(f"Error in bank analysis: {str(e)}")
            return pd.DataFrame()

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and validate features for analysis"""
        try:
            df = df.copy()
            
            # Debug column names
            st.sidebar.expander("Available Columns").write(df.columns.tolist())
            
            # Handle PRAZO columns
            prazo_columns = [col for col in df.columns if 'PRAZO' in col.upper()]
            st.sidebar.expander("PRAZO Columns Found").write(prazo_columns)
            
            # Convert PRAZO columns to numeric
            for col in prazo_columns:
                df[f"{col.replace(' ', '_')}"] = pd.to_numeric(
                    df[col].astype(str)
                    .str.strip()
                    .str.replace(',', '.')
                    .str.replace('R$', '')
                    .str.replace('%', ''),
                    errors='coerce'
                )
            
            # Create resolution time feature
            df['DIAS_RESOLUCAO'] = (df['RESOLUÇÃO'] - df['DATA']).dt.days
            
            # Create payment delay feature
            df['DIAS_ULTIMO_PAGAMENTO'] = (df['DATA'] - df['ÚLTIMO PAGAMENTO']).dt.days
            
            # Create entrada delay feature
            df['DIAS_ATE_ENTRADA'] = (df['ENTRADA'] - df['DATA']).dt.days
            
            # Convert VALOR DO CLIENTE to numeric
            df['VALOR_CLIENTE'] = pd.to_numeric(
                df['VALOR DO CLIENTE'].astype(str)
                .str.replace('R$', '')
                .str.replace('.', '')
                .str.replace(',', '.'),
                errors='coerce'
            )
            
            # Create features DataFrame
            features = pd.DataFrame()
            
            # Add numeric features
            numeric_features = [
                'DIAS_RESOLUCAO',
                'DIAS_ULTIMO_PAGAMENTO',
                'DIAS_ATE_ENTRADA',
                'VALOR_CLIENTE'
            ] + [f"{col.replace(' ', '_')}" for col in prazo_columns]
            
            for feature in numeric_features:
                if feature in df.columns:
                    features[feature] = df[feature]
            
            # Add categorical features
            categorical_features = ['BANCO', 'SITUAÇÃO']
            for feature in categorical_features:
                if feature in df.columns:
                    dummies = pd.get_dummies(df[feature], prefix=feature)
                    features = pd.concat([features, dummies], axis=1)
            
            # Fill missing values
            features = features.fillna(-999)
            
            # Log feature creation
            st.sidebar.expander("Created Features").write({
                "Numeric Features": numeric_features,
                "Categorical Features": categorical_features,
                "Total Features": len(features.columns)
            })
            
            return features
            
        except Exception as e:
            st.error(f"Error in prepare_features: {str(e)}")
            st.error(f"Available columns: {df.columns.tolist()}")
            raise

    def analyze_resolution_time(self, df: pd.DataFrame) -> pd.DataFrame:
        """Analyze resolution times and patterns with enhanced features"""
        try:
            # Prepare features
            features = self.prepare_features(df)
            
            # Calculate resolution metrics
            resolution_stats = df.groupby('BANCO').agg({
                'DIAS_RESOLUCAO': {
                    'média_dias': 'mean',
                    'mediana_dias': 'median',
                    'desvio_padrão': 'std',
                    'total_casos': 'count',
                    'min_dias': 'min',
                    'max_dias': 'max'
                }
            }).round(2)
            
            resolution_stats.columns = ['AVG_DAYS', 'MEDIAN_DAYS', 'STD_DAYS', 'TOTAL_CASES', 'MIN_DAYS', 'MAX_DAYS']
            return resolution_stats.sort_values('AVG_DAYS')
            
        except Exception as e:
            st.error(f"Error in resolution analysis: {str(e)}")
            return pd.DataFrame()

    def analyze_responsible_performance(self, df: pd.DataFrame) -> pd.DataFrame:
        """Analyze performance metrics by responsible person"""
        try:
            # Ensure RESPONSAVEL column exists and is clean
            if 'RESPONSAVEL' not in df.columns:
                st.warning("Coluna 'RESPONSAVEL' não encontrada. Verificando alternativas...")
                possible_columns = [col for col in df.columns if 'RESP' in col.upper()]
                if possible_columns:
                    df['RESPONSAVEL'] = df[possible_columns[0]]
                else:
                    return pd.DataFrame()

            # Ensure VALOR_CLEANED is numeric
            if 'VALOR_CLEANED' not in df.columns:
                df['VALOR_CLEANED'] = pd.to_numeric(
                    df['VALOR DO CLIENTE'].str.replace('R$', '')
                    .str.replace('.', '')
                    .str.replace(',', '.')
                    .str.extract(r'(\d+\.?\d*)'),
                    errors='coerce'
                )

            # Calculate metrics by responsible person with safe numeric handling
            responsible_stats = df.groupby('RESPONSAVEL').agg({
                'SITUAÇÃO': 'count',
                'VALOR_CLEANED': lambda x: pd.to_numeric(x, errors='coerce').mean(),
                'BANCO': 'nunique'
            }).reset_index()

            # Calculate quitados count
            quitados = df[df['SITUAÇÃO'].str.upper() == 'QUITADO'].groupby('RESPONSAVEL').size()
            responsible_stats['QUITADOS'] = responsible_stats['RESPONSAVEL'].map(quitados).fillna(0)
            
            # Calculate success rate and metrics (ensure numeric operations)
            responsible_stats['SUCCESS_RATE'] = (responsible_stats['QUITADOS'].astype(float) / 
                                               responsible_stats['SITUAÇÃO'].astype(float) * 100).round(2)
            responsible_stats['MEDIA_VALOR'] = pd.to_numeric(responsible_stats['VALOR_CLEANED'], errors='coerce').round(2)
            responsible_stats['BANCOS_ATENDIDOS'] = responsible_stats['BANCO']
            
            # Rename columns for better presentation
            responsible_stats.columns = [
                'RESPONSÁVEL', 'TOTAL_CASOS', 'MÉDIA_VALOR', 'BANCOS_ATENDIDOS',
                'QUITADOS', 'TAXA_SUCESSO(%)'
            ]
            
            # Sort and handle any remaining non-numeric values
            result = responsible_stats.sort_values('TAXA_SUCESSO(%)', ascending=False)
            result = result.fillna(0)  # Replace any remaining NaN with 0
            
            # Add debug information
            st.sidebar.expander("Debug Info").write({
                "Total Responsáveis": len(result),
                "Colunas Numéricas": result.select_dtypes(include=[np.number]).columns.tolist()
            })
            
            return result
            
        except Exception as e:
            st.error(f"Erro na análise de responsáveis: {str(e)}")
            st.error(f"Tipos de dados: {df.dtypes}")
            return pd.DataFrame()

def main():
    st.set_page_config(page_title="Quitados Analysis", layout="wide")
    
    st.title("Análise de Quitados e Desempenho Bancário")
    
    analyzer = QuitadosAnalyzer()
    
    try:
        # Load data with progress indicator
        with st.spinner('Carregando dados...'):
            main_df, aprovados_df, quitados_df = analyzer.load_data()
        
        # Sidebar filters
        st.sidebar.header("Filtros")
        selected_banks = st.sidebar.multiselect(
            "Selecione os Bancos",
            options=sorted(main_df['BANCO'].unique()),
            default=sorted(main_df['BANCO'].unique())
        )
        
        # Filter data
        filtered_df = main_df[main_df['BANCO'].isin(selected_banks)]
        
        # Bank Performance Analysis
        st.header("Análise de Desempenho por Banco")
        bank_stats = analyzer.analyze_bank_performance(filtered_df)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Taxa de Sucesso por Banco")
            if not bank_stats.empty:
                fig = px.bar(
                    bank_stats,
                    x='BANCO',
                    y='SUCCESS_RATE',
                    title='Taxa de Quitação por Banco (%)',
                    color='SUCCESS_RATE',
                    labels={'SUCCESS_RATE': 'Taxa de Quitação (%)'}
                )
                st.plotly_chart(fig)
        
        with col2:
            st.subheader("Valor Médio por Banco")
            if not bank_stats.empty:
                fig = px.bar(
                    bank_stats,
                    x='BANCO',
                    y='VALOR_CLEANED',
                    title='Valor Médio por Banco',
                    color='BANCO'
                )
                st.plotly_chart(fig)
        
        # Resolution Time Analysis
        st.header("Análise de Tempo de Resolução")
        resolution_stats = analyzer.analyze_resolution_time(filtered_df)
        
        if not resolution_stats.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=resolution_stats.index,
                y=resolution_stats['AVG_DAYS'],
                name='Média de Dias',
                error_y=dict(
                    type='data',
                    array=resolution_stats['STD_DAYS'],
                    visible=True
                )
            ))
            fig.update_layout(title='Tempo Médio de Resolução por Banco (dias)')
            st.plotly_chart(fig)
        
        # Detailed Statistics
        st.header("Estatísticas Detalhadas")
        st.dataframe(resolution_stats)
        
        # Responsible Analysis
        st.header("Análise por Responsável")
        responsible_stats = analyzer.analyze_responsible_performance(filtered_df)
        
        if not responsible_stats.empty:
            col3, col4 = st.columns(2)
            
            with col3:
                st.subheader("Top Responsáveis por Taxa de Sucesso")
                fig = px.bar(
                    responsible_stats.head(10),
                    x='RESPONSÁVEL',
                    y='TAXA_SUCESSO(%)',
                    title='Top 10 Responsáveis - Taxa de Sucesso',
                    color='TAXA_SUCESSO(%)',
                    labels={'TAXA_SUCESSO(%)': 'Taxa de Quitação (%)'}
                )
                st.plotly_chart(fig)
            
            with col4:
                st.subheader("Volume de Casos por Responsável")
                fig = px.bar(
                    responsible_stats.head(10),
                    x='RESPONSÁVEL',
                    y='TOTAL_CASOS',
                    title='Top 10 Responsáveis - Volume de Casos',
                    color='BANCOS_ATENDIDOS',
                    labels={'TOTAL_CASOS': 'Total de Casos'}
                )
                st.plotly_chart(fig)
            
            # Add detailed metrics table
            st.subheader("Métricas Detalhadas por Responsável")
            st.dataframe(
                responsible_stats.style.highlight_max(subset=['TAXA_SUCESSO(%)', 'TOTAL_CASOS'])
                                      .format({
                                          'MÉDIA_VALOR': 'R$ {:,.2f}',
                                          'TAXA_SUCESSO(%)': '{:.1f}%'
                                      })
            )
        
    except Exception as e:
        st.error(f"Erro na análise: {str(e)}")

if __name__ == "__main__":
    main()
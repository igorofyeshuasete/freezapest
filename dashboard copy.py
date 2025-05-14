import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

class DashboardData:
    def __init__(self):
        self.df = pd.read_csv("(JULIO) LISTAS INDIVIDUAIS - IGOR.csv", encoding='utf-8')
        self.process_dates()
    
    def process_dates(self):
        for col in ['DATA', 'NEGOCIAÇÃO']:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(self.df[col], format='%d/%m/%Y', errors='coerce')
    
    def get_summary_stats(self):
        valores = self.df['VALOR DO CLIENTE'].str.extract(r'(\d+(?:\.\d+)?)', expand=False).astype(float)
        return {
            'total_contracts': len(self.df),
            'total_banks': self.df['BANCO'].nunique(),
            'approved': len(self.df[self.df['SITUAÇÃO'] == 'APROVADO']),
            'pending': len(self.df[self.df['SITUAÇÃO'] == 'PENDENTE']),
            'total_value': valores.sum(),
            'avg_value': valores.mean()
        }

def main():
    st.set_page_config(page_title="Dashboard Financeiro", layout="wide")
    
    # Initialize data
    data = DashboardData()
    stats = data.get_summary_stats()
    
    # Header
    st.title("📊 Dashboard Financeiro")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Contratos", f"{stats['total_contracts']:,}")
    with col2:
        st.metric("Aprovados", f"{stats['approved']:,}")
    with col3:
        st.metric("Valor Total", f"R$ {stats['total_value']:,.2f}")
    with col4:
        st.metric("Bancos", f"{stats['total_banks']:,}")
    
    # Charts
    st.subheader("Análise por Status")
    col1, col2 = st.columns(2)
    
    with col1:
        fig_pie = px.pie(data.df, names='SITUAÇÃO', title='Distribuição por Status')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        fig_bar = px.histogram(data.df, x='BANCO', color='SITUAÇÃO', 
                             title='Contratos por Banco')
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Data Analysis
    st.subheader("Análise Detalhada")
    tabs = st.tabs(["Dados", "Financeiro", "Status"])
    
    with tabs[0]:
        st.dataframe(data.df[['DATA', 'CONTRATO', 'BANCO', 'SITUAÇÃO']])
    
    with tabs[1]:
        st.dataframe(data.df[['BANCO', 'VALOR DO CLIENTE', 'CÓD']])
    
    with tabs[2]:
        st.dataframe(data.df.groupby('SITUAÇÃO').agg({
            'CONTRATO': 'count',
            'VALOR DO CLIENTE': lambda x: x.str.extract(r'(\d+(?:\.\d+)?)', expand=False).astype(float).sum()
        }).rename(columns={'CONTRATO': 'Quantidade', 'VALOR DO CLIENTE': 'Valor Total'}))

if __name__ == "__main__":
    main()
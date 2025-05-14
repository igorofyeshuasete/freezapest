import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import re

def analyze_contract_patterns(filepath: str) -> None:
    """Analyze contract number patterns with focus on legacy contracts"""
    try:
        # Read data
        df = pd.read_csv(filepath, encoding='utf-8')
        df.columns = df.columns.str.strip()
        
        # Create pattern matching function
        def is_legacy_contract(contract):
            if pd.isna(contract):
                return False
            contract_str = str(contract).strip()
            return bool(re.match(r'^1\d{4,5}$', contract_str))
        
        # Add analysis columns
        df['IS_LEGACY'] = df['CONTRATO'].apply(is_legacy_contract)
        df['CONTRACT_LENGTH'] = df['CONTRATO'].astype(str).str.len()
        
        # Create analysis summary
        analysis = pd.DataFrame({
            'Total_Registros': [len(df)],
            'Contratos_Legacy': [(df['IS_LEGACY'] == True).sum()],
            'Porcentagem_Legacy': [(df['IS_LEGACY'] == True).mean() * 100],
        })
        
        # Create detailed legacy analysis
        legacy_df = df[df['IS_LEGACY']].copy()
        legacy_df['ANO'] = pd.to_datetime(legacy_df['DATA']).dt.year
        legacy_df['MES'] = pd.to_datetime(legacy_df['DATA']).dt.month
        
        # Create visualizations
        fig1 = px.histogram(
            df,
            x='CONTRACT_LENGTH',
            title='Distribuição do Tamanho dos Contratos',
            labels={'CONTRACT_LENGTH': 'Número de Dígitos', 'count': 'Quantidade'}
        )
        
        fig2 = px.scatter(
            legacy_df,
            x='CONTRATO',
            y='DATA',
            color='BANCO',
            title='Contratos Legacy por Data',
            labels={'CONTRATO': 'Número do Contrato', 'DATA': 'Data'}
        )
        
        # Print analysis
        print("\n=== Análise de Padrões de Contrato ===")
        print("\nResumo Geral:")
        print(analysis.to_string(index=False))
        
        print("\nDistribuição de Contratos Legacy por Banco:")
        print(legacy_df['BANCO'].value_counts().to_frame())
        
        print("\nDetalhes dos Contratos Legacy:")
        legacy_details = legacy_df[['CONTRATO', 'DATA', 'BANCO', 'SITUAÇÃO']].sort_values('CONTRATO')
        print(legacy_details.to_string(index=False))
        
        # Save visualizations
        fig1.write_html("contract_length_distribution.html")
        fig2.write_html("legacy_contracts_scatter.html")
        
        # Export detailed analysis
        legacy_df.to_csv('legacy_contracts_analysis.csv', index=False)
        
    except Exception as e:
        print(f"Erro na análise: {str(e)}")

if __name__ == "__main__":
    filepath = r"C:\Users\igor de jesus\zaptest\(JULIO) LISTAS INDIVIDUAIS - IGOR.csv"
    analyze_contract_patterns(filepath)
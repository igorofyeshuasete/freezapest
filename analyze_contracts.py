import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import re
from typing import Dict, List, Tuple

class LegacyContractAnalyzer:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.success_states = ['QUITADO', 'APROVADO']
        
    def analyze_success_patterns(self) -> None:
        """Analyze success patterns in legacy contracts"""
        try:
            # Read and prepare data
            df = pd.read_csv(self.filepath, encoding='utf-8')
            df.columns = df.columns.str.strip()
            
            # Convert dates properly
            date_cols = ['DATA', 'ÚLTIMO PAGAMENTO', 'ENTRADA']
            for col in date_cols:
                df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', dayfirst=True)
            
            # Identify legacy contracts
            df['IS_LEGACY'] = df['CONTRATO'].apply(self._is_legacy_contract)
            legacy_df = df[df['IS_LEGACY']].copy()
            
            # Calculate success metrics
            bank_success = self._analyze_bank_success(legacy_df)
            time_patterns = self._analyze_time_patterns(legacy_df)
            value_patterns = self._analyze_value_patterns(legacy_df)
            
            # Create opportunity score
            legacy_df = self._calculate_opportunity_score(legacy_df)
            
            # Print enhanced analysis
            self._print_enhanced_analysis(legacy_df, bank_success, time_patterns, value_patterns)
            
            # Create enhanced visualizations
            self._create_enhanced_visualizations(legacy_df)
            
            # Export detailed analysis
            self._export_analysis(legacy_df)
            
        except Exception as e:
            print(f"Erro na análise: {str(e)}")
    
    def _is_legacy_contract(self, contract) -> bool:
        """Check if contract is legacy (5-6 digits starting with 1)"""
        if pd.isna(contract):
            return False
        contract_str = str(contract).strip()
        return bool(re.match(r'^1\d{4,5}$', contract_str))
    
    def _analyze_bank_success(self, df: pd.DataFrame) -> pd.DataFrame:
        """Analyze success patterns by bank"""
        bank_stats = df.groupby('BANCO').agg({
            'CONTRATO': 'count',
            'SITUAÇÃO': lambda x: (x.isin(self.success_states)).mean() * 100
        }).round(2)
        
        bank_stats.columns = ['Total_Contratos', 'Taxa_Sucesso']
        return bank_stats.sort_values('Taxa_Sucesso', ascending=False)
    
    def _analyze_time_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze time-based patterns"""
        df['DIAS_SEM_PAGAMENTO'] = (df['DATA'] - df['ÚLTIMO PAGAMENTO']).dt.days
        
        success_cases = df[df['SITUAÇÃO'].isin(self.success_states)]
        return {
            'media_dias_sem_pagamento': df['DIAS_SEM_PAGAMENTO'].mean(),
            'media_dias_sucesso': success_cases['DIAS_SEM_PAGAMENTO'].mean(),
            'melhor_periodo': df[df['SITUAÇÃO'].isin(self.success_states)]['MES'].mode().iloc[0]
        }
    
    def _analyze_value_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze value-based patterns"""
        df['VALOR'] = pd.to_numeric(
            df['VALOR DO CLIENTE'].str.replace('R$', '').str.replace('.', '')
            .str.replace(',', '.'), errors='coerce'
        )
        
        success_cases = df[df['SITUAÇÃO'].isin(self.success_states)]
        return {
            'valor_medio_total': df['VALOR'].mean(),
            'valor_medio_sucesso': success_cases['VALOR'].mean(),
            'faixa_valor_otima': f"R$ {success_cases['VALOR'].quantile(0.25):,.2f} - R$ {success_cases['VALOR'].quantile(0.75):,.2f}"
        }
    
    def _calculate_opportunity_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate opportunity score for each contract"""
        df['SCORE'] = 0
        
        # Value score (30%)
        df['VALOR'] = pd.to_numeric(df['VALOR DO CLIENTE'].str.replace('R$', '').str.replace('.', '').str.replace(',', '.'), errors='coerce')
        df['VALOR_SCORE'] = df['VALOR'].rank(pct=True) * 30
        
        # Time score (40%)
        df['DIAS_SEM_PAGAMENTO'] = (df['DATA'] - df['ÚLTIMO PAGAMENTO']).dt.days
        df['TEMPO_SCORE'] = (1 - df['DIAS_SEM_PAGAMENTO'].rank(pct=True)) * 40
        
        # Bank success score (30%)
        bank_success = self._analyze_bank_success(df)
        df['BANCO_SCORE'] = df['BANCO'].map(bank_success['Taxa_Sucesso']) * 0.3
        
        # Total score
        df['SCORE'] = df['VALOR_SCORE'] + df['TEMPO_SCORE'] + df['BANCO_SCORE']
        
        return df
    
    def _print_enhanced_analysis(self, df: pd.DataFrame, bank_success: pd.DataFrame, 
                               time_patterns: Dict, value_patterns: Dict) -> None:
        """Print enhanced analysis results"""
        print("\n=== Análise Avançada de Contratos Legacy ===")
        
        print("\nMelhores Oportunidades de Negociação:")
        top_opportunities = df.nlargest(10, 'SCORE')[
            ['CONTRATO', 'BANCO', 'VALOR', 'SCORE', 'SITUAÇÃO']
        ]
        print(top_opportunities.to_string(index=False))
        
        print("\nPadrões de Sucesso por Banco:")
        print(bank_success)
        
        print("\nPadrões Temporais:")
        for key, value in time_patterns.items():
            print(f"{key}: {value}")
        
        print("\nPadrões de Valor:")
        for key, value in value_patterns.items():
            print(f"{key}: {value}")
    
    def _create_enhanced_visualizations(self, df: pd.DataFrame) -> None:
        """Create enhanced visualizations"""
        # Success probability by bank and value range
        fig1 = px.scatter(
            df,
            x='VALOR',
            y='SCORE',
            color='BANCO',
            size='DIAS_SEM_PAGAMENTO',
            hover_data=['CONTRATO', 'SITUAÇÃO'],
            title='Mapa de Oportunidades - Contratos Legacy'
        )
        
        # Time patterns
        fig2 = px.box(
            df,
            x='BANCO',
            y='DIAS_SEM_PAGAMENTO',
            color='SITUAÇÃO',
            title='Distribuição do Tempo sem Pagamento por Banco'
        )
        
        # Save visualizations
        fig1.write_html("legacy_opportunities.html")
        fig2.write_html("payment_patterns.html")
    
    def _export_analysis(self, df: pd.DataFrame) -> None:
        """Export detailed analysis results"""
        # Export full analysis
        df.sort_values('SCORE', ascending=False).to_csv('legacy_analysis_full.csv', index=False)
        
        # Export top opportunities
        df[df['SCORE'] > df['SCORE'].quantile(0.75)].to_csv('top_opportunities.csv', index=False)

if __name__ == "__main__":
    filepath = r"C:\Users\igor de jesus\zaptest\(JULIO) LISTAS INDIVIDUAIS - IGOR.csv"
    analyzer = LegacyContractAnalyzer(filepath)
    analyzer.analyze_success_patterns()
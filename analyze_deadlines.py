import pandas as pd
import numpy as np
from datetime import datetime

def prepare_features(df):
    """Prepare features with proper column name handling"""
    try:
        # Create copy and clean column names
        df = df.copy()
        
        # Show original column names for debugging
        print("Original columns:", df.columns.tolist())
        
        # Clean column names - remove trailing/leading spaces
        df.columns = df.columns.str.strip()
        
        # Handle PRAZO columns specifically
        prazo_b_col = [col for col in df.columns if 'PRAZO B' in col][0]
        prazo_7_col = [col for col in df.columns if 'PRAZO 7' in col][0]
        
        # Rename columns without spaces
        df = df.rename(columns={
            prazo_b_col: 'PRAZOB',
            prazo_7_col: 'PRAZO7'
        })
        
        # Convert PRAZO values to numeric
        df['PRAZOB'] = pd.to_numeric(df['PRAZOB'].astype(str).str.replace(',','.'), errors='coerce')
        df['PRAZO7'] = pd.to_numeric(df['PRAZO7'].astype(str).str.replace(',','.'), errors='coerce')
        
        # Convert dates safely
        date_cols = ['DATA', 'RESOLUÇÃO', 'ÚLTIMO PAGAMENTO', 'ENTRADA']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
        
        # Create temporal features
        current_date = pd.Timestamp.now()
        df['dias_desde_ultimo_pagamento'] = (current_date - df['ÚLTIMO PAGAMENTO']).dt.days
        df['dias_ate_resolucao'] = (df['RESOLUÇÃO'] - current_date).dt.days
        df['dias_ate_entrada'] = (df['ENTRADA'] - current_date).dt.days
        
        # Extract numeric values from monetary columns
        if 'VALOR DO CLIENTE' in df.columns:
            df['VALOR_CLIENTE'] = df['VALOR DO CLIENTE'].str.extract(r'R\$\s*([\d,.]+)', expand=False)
            df['VALOR_CLIENTE'] = pd.to_numeric(
                df['VALOR_CLIENTE'].str.replace('.','').str.replace(',','.'), 
                errors='coerce'
            )
        
        # Create derived features
        df['tem_contato'] = df['CONTATO'].notna().astype(int)
        df['tem_negociacao'] = df['NEGOCIAÇÃO'].notna().astype(int)
        df['tem_campanha'] = df['CAMPANHA'].fillna('NAO').map({'SIM': 1, 'NAO': 0})
        
        # Encode categorical variables
        for col in ['ESCRITÓRIO', 'BANCO', 'SITUAÇÃO']:
            if col in df.columns:
                df[f'{col}_encoded'] = pd.Categorical(df[col]).codes
        
        # Select final features
        feature_cols = [
            'PRAZOB', 'PRAZO7',
            'dias_desde_ultimo_pagamento', 'dias_ate_resolucao', 
            'dias_ate_entrada', 'tem_contato', 'tem_negociacao',
            'tem_campanha'
        ] + [col for col in df.columns if '_encoded' in col]
        
        print("\nProcessed features:", feature_cols)
        return df[feature_cols].fillna(-1)
        
    except Exception as e:
        print(f"Error in prepare_features: {str(e)}")
        print("Available columns:", df.columns.tolist())
        raise

def analyze_deadlines(df):
    """Analyze relationship between PRAZO 7 and PRAZO B"""
    try:
        # Clean and prepare data
        prazo_data = prepare_features(df)
        
        # Calculate correlations
        correlation = prazo_data[['PRAZOB', 'PRAZO7']].corr()
        
        # Analyze distributions
        prazo_stats = {
            'PRAZO B': prazo_data['PRAZOB'].describe(),
            'PRAZO 7': prazo_data['PRAZO7'].describe()
        }
        
        # Create priority categories
        prazo_data['prioridade'] = pd.cut(
            prazo_data['PRAZOB'],
            bins=[-np.inf, 0, 5, 10, 15, np.inf],
            labels=['VENCIDO', 'URGENTE', 'ALTA', 'MÉDIA', 'NORMAL']
        )
        
        print("\n=== Análise de Prazos ===")
        print("\nCorrelação entre PRAZO B e PRAZO 7:")
        print(correlation)
        
        print("\nEstatísticas PRAZO B:")
        print(prazo_stats['PRAZO B'])
        
        print("\nEstatísticas PRAZO 7:")
        print(prazo_stats['PRAZO 7'])
        
        print("\nDistribuição de Prioridades:")
        print(prazo_data['prioridade'].value_counts())
        
        return prazo_data
        
    except Exception as e:
        print(f"Error in analyze_deadlines: {str(e)}")
        raise

def analyze_quitado_journey(df):
    """Analyze the journey towards QUITADO status"""
    try:
        # Create copy and clean data
        df = df.copy()
        
        # Convert dates
        df['ENTRADA'] = pd.to_datetime(df['ENTRADA'], format='%d/%m/%Y', errors='coerce')
        df['RESOLUÇÃO'] = pd.to_datetime(df['RESOLUÇÃO'], format='%d/%m/%Y', errors='coerce')
        
        # Calculate days between ENTRADA and RESOLUÇÃO
        df['dias_processo'] = (df['RESOLUÇÃO'] - df['ENTRADA']).dt.days
        
        # Group by SITUAÇÃO and analyze
        situacao_analysis = df.groupby('SITUAÇÃO').agg({
            'dias_processo': ['count', 'mean', 'min', 'max'],
            'PRAZO B': 'mean',
            'PRAZO 7': 'mean'
        }).round(2)
        
        # Calculate conversion rates
        total_cases = len(df)
        status_flow = {
            'PENDENTE': len(df[df['SITUAÇÃO'] == 'PENDENTE']),
            'ANÁLISE': len(df[df['SITUAÇÃO'] == 'ANÁLISE']),
            'APROVADO': len(df[df['SITUAÇÃO'] == 'APROVADO']),
            'QUITADO': len(df[df['SITUAÇÃO'] == 'QUITADO'])
        }
        
        conversion_rates = {
            'pendente_to_analise': (status_flow['ANÁLISE'] / status_flow['PENDENTE'] * 100),
            'analise_to_aprovado': (status_flow['APROVADO'] / status_flow['ANÁLISE'] * 100),
            'aprovado_to_quitado': (status_flow['QUITADO'] / status_flow['APROVADO'] * 100) if status_flow['APROVADO'] > 0 else 0
        }
        
        print("\n=== Análise de Jornada para QUITADO ===")
        print("\nEstatísticas por Situação:")
        print(situacao_analysis)
        
        print("\nMétricas de Conversão:")
        print(f"Pendente → Análise: {conversion_rates['pendente_to_analise']:.1f}%")
        print(f"Análise → Aprovado: {conversion_rates['analise_to_aprovado']:.1f}%")
        print(f"Aprovado → Quitado: {conversion_rates['aprovado_to_quitado']:.1f}%")
        
        # Calculate goals and projections
        avg_days_to_quitado = df[df['SITUAÇÃO'].isin(['APROVADO', 'QUITADO'])]['dias_processo'].mean()
        success_rate = status_flow['QUITADO'] / total_cases * 100 if total_cases > 0 else 0
        
        print("\nMetas e Projeções:")
        print(f"Tempo Médio até Quitação: {avg_days_to_quitado:.1f} dias")
        print(f"Taxa de Sucesso Atual: {success_rate:.1f}%")
        
        # Identify high-potential cases
        high_potential = df[
            (df['SITUAÇÃO'] == 'ANÁLISE') & 
            (df['PRAZO B'] <= df['PRAZO B'].median()) &
            (df['dias_processo'] <= df['dias_processo'].median())
        ]
        
        print(f"\nCasos com Alto Potencial de Quitação: {len(high_potential)}")
        if len(high_potential) > 0:
            print("\nTop 5 Casos Prioritários:")
            priority_cols = ['CONTRATO', 'BANCO', 'PRAZO B', 'dias_processo']
            print(high_potential[priority_cols].head())
        
        return {
            'situacao_analysis': situacao_analysis,
            'conversion_rates': conversion_rates,
            'high_potential_cases': high_potential
        }
        
    except Exception as e:
        print(f"Error in analyze_quitado_journey: {str(e)}")
        raise

# Main execution
if __name__ == "__main__":
    try:
        file_path = r"C:\Users\igor de jesus\zaptest\(JULIO) LISTAS INDIVIDUAIS - IGOR.csv"
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # Run both analyses
        deadline_results = analyze_deadlines(df)
        journey_results = analyze_quitado_journey(df)
        
        # Export results
        pd.DataFrame(journey_results['high_potential_cases']).to_csv('priority_cases.csv', index=False)
        
    except Exception as e:
        print(f"Error: {str(e)}")
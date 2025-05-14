import pandas as pd
import numpy as np
from datetime import datetime
import os

def analyze_deadlines(df):
    """Analyze deadlines and negotiation periods"""
    try:
        # Clean and prepare data
        df = df.copy()
        
        # Clean column names by removing any leading/trailing spaces
        df.columns = df.columns.str.strip()
        
        # First check if PRAZO B exists
        if 'PRAZO B' not in df.columns:
            print("Available columns:", df.columns.tolist())
            raise ValueError("Column 'PRAZO B' not found in dataframe")
        
        # Convert 'PRAZO B' to numeric, with better error handling
        df['PRAZO B'] = df['PRAZO B'].astype(str).str.strip()
        df['PRAZO B'] = pd.to_numeric(df['PRAZO B'].str.replace(',', '.'), errors='coerce')
        
        # Convert dates to datetime with error handling
        date_columns = ['DATA', 'RESOLUÇÃO', 'ÚLTIMO PAGAMENTO', 'ENTRADA']
        for col in date_columns:
            df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
        
        # Calculate key metrics with null handling
        current_date = datetime.now()
        df['dias_ate_resolucao'] = (df['RESOLUÇÃO'] - df['DATA']).dt.days
        df['dias_sem_pagamento'] = (current_date - df['ÚLTIMO PAGAMENTO']).dt.days
        df['dias_ate_entrada'] = (df['ENTRADA'] - current_date).dt.days
        
        # Create deadline categories with proper null handling
        df['prioridade'] = pd.cut(
            df['PRAZO B'].fillna(-1),  # Handle null values
            bins=[-np.inf, 0, 5, 10, 15, np.inf],
            labels=['VENCIDO', 'URGENTE', 'ALTA', 'MÉDIA', 'NORMAL']
        )
        
        # Enhanced status analysis
        status_analysis = df.groupby('SITUAÇÃO', as_index=False).agg({
            'PRAZO B': lambda x: x.mean(skipna=True),
            'PRAZO 7': lambda x: x.mean(skipna=True),
            'dias_ate_resolucao': lambda x: x.mean(skipna=True),
            'CONTRATO': 'count'
        }).round(2)
        
        # Enhanced bank analysis
        bank_analysis = df.groupby('BANCO', as_index=False).agg({
            'PRAZO B': lambda x: x.mean(skipna=True),
            'CONTRATO': 'count',
            'SITUAÇÃO': lambda x: x.value_counts().index[0] if len(x) > 0 else 'N/A'
        })
        
        # Calculate deadline metrics
        deadline_metrics = {
            'avg_resolution_time': df['dias_ate_resolucao'].mean(skipna=True),
            'urgent_cases': len(df[df['prioridade'].isin(['URGENTE', 'VENCIDO'])]),
            'overdue_cases': len(df[df['PRAZO B'] <= 0]),
            'status_distribution': df['SITUAÇÃO'].value_counts().to_dict(),
            'priority_distribution': df['prioridade'].value_counts().to_dict()
        }
        
        # Print detailed analysis
        print("\n=== Análise de Prazos e Negociações ===")
        print(f"\nMétricas Gerais:")
        print(f"Tempo Médio de Resolução: {deadline_metrics['avg_resolution_time']:.1f} dias")
        print(f"Casos Urgentes: {deadline_metrics['urgent_cases']}")
        print(f"Casos Vencidos: {deadline_metrics['overdue_cases']}")
        
        print("\nDistribuição por Situação:")
        for status, count in deadline_metrics['status_distribution'].items():
            print(f"{status:15} : {count:3d}")
        
        print("\nDistribuição por Prioridade:")
        for priority, count in deadline_metrics['priority_distribution'].items():
            print(f"{priority:10} : {count:3d}")
            
        return {
            'status_analysis': status_analysis,
            'bank_analysis': bank_analysis,
            'deadline_metrics': deadline_metrics
        }
        
    except Exception as e:
        print(f"Erro na análise: {str(e)}")
        print("Traceback completo:")
        import traceback
        print(traceback.format_exc())
        return None

# Modified file reading section
try:
    # Get the full path using os.path
    file_path = os.path.join(os.getcwd(), "(JULIO) LISTAS INDIVIDUAIS - IGOR.csv")
    
    # Read CSV with explicit parameters
    df = pd.read_csv(
        file_path,
        encoding='utf-8',
        sep=',',
        decimal=',',
        thousands='.',
        parse_dates=['DATA', 'RESOLUÇÃO', 'ÚLTIMO PAGAMENTO', 'ENTRADA'],
        dayfirst=True  # Brazilian date format
    )
    
    # Print debug info
    print(f"File loaded successfully from: {file_path}")
    print(f"Columns found: {df.columns.tolist()}")
    print(f"Total rows: {len(df)}")
    
    # Run analysis
    results = analyze_deadlines(df)
    
except FileNotFoundError:
    print(f"Arquivo não encontrado: {file_path}")
    print("Diretório atual:", os.getcwd())
except Exception as e:
    print(f"Erro ao processar arquivo: {str(e)}")
    import traceback
    print(traceback.format_exc())
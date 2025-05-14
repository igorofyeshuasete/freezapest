import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_csv():
    try:
        # Read CSV file
        df = pd.read_csv('(JULIO) LISTAS INDIVIDUAIS - IGOR.csv', encoding='utf-8')
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Analysis by SITUAÇÃO
        print("\n=== Analysis by SITUAÇÃO ===")
        situacao_counts = df['SITUAÇÃO'].value_counts()
        print(situacao_counts)
        
        # Analysis by RESOLUÇÃO
        print("\n=== Analysis by RESOLUÇÃO ===")
        resolucao_counts = df['RESOLUÇÃO'].value_counts()
        print(resolucao_counts)
        
        # Analysis of CONTRATO column
        print("\n=== Analysis of CONTRATO ===")
        print(f"Total unique contracts: {df['CONTRATO'].nunique()}")
        
        # Group contracts by SITUAÇÃO
        contratos_por_situacao = df.groupby('SITUAÇÃO')['CONTRATO'].agg(['count', 'nunique'])
        print("\nContracts by Status:")
        print(contratos_por_situacao)
        
        # Group contracts by BANCO
        contratos_por_banco = df.groupby(['BANCO', 'SITUAÇÃO'])['CONTRATO'].count().unstack(fill_value=0)
        print("\nContracts by Bank and Status:")
        print(contratos_por_banco)
        
        # Create visualizations
        plt.figure(figsize=(15, 10))
        
        # Pie chart for SITUAÇÃO
        plt.subplot(2, 2, 1)
        situacao_counts.plot(kind='pie', autopct='%1.1f%%')
        plt.title('Distribution by SITUAÇÃO')
        
        # Bar chart for RESOLUÇÃO
        plt.subplot(2, 2, 2)
        resolucao_counts.plot(kind='bar')
        plt.title('Distribution by RESOLUÇÃO')
        plt.xticks(rotation=45)
        
        # Contracts by Bank
        plt.subplot(2, 2, 3)
        sns.countplot(data=df, x='BANCO', hue='SITUAÇÃO')
        plt.title('Contracts by Bank and Status')
        plt.xticks(rotation=45)
        
        # Contracts Distribution
        plt.subplot(2, 2, 4)
        df_counts = df['CONTRATO'].value_counts().reset_index()
        df_counts.columns = ['CONTRATO', 'Count']
        sns.barplot(data=df_counts.head(10), x='CONTRATO', y='Count')
        plt.title('Top 10 Contracts by Frequency')
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig('analysis_results.png')
        
        # Export summary to Excel
        summary = {
            'SITUAÇÃO Analysis': situacao_counts,
            'RESOLUÇÃO Analysis': resolucao_counts
        }
        
        with pd.ExcelWriter('analysis_summary.xlsx') as writer:
            for sheet_name, data in summary.items():
                data.to_frame().to_excel(writer, sheet_name=sheet_name)
        
        # Export detailed contract analysis
        with pd.ExcelWriter('contract_analysis.xlsx') as writer:
            contratos_por_situacao.to_excel(writer, sheet_name='By Status')
            contratos_por_banco.to_excel(writer, sheet_name='By Bank')
            
            # Detailed contract list
            df[['CONTRATO', 'BANCO', 'SITUAÇÃO', 'RESOLUÇÃO']].to_excel(
                writer, sheet_name='Detail', index=False
            )
        
        # Additional analysis
        print("\n=== Summary Statistics ===")
        print(f"Total Records: {len(df)}")
        print(f"Unique Status: {df['SITUAÇÃO'].nunique()}")
        
        # Filter by specific conditions
        pendentes = df[df['SITUAÇÃO'] == 'PENDENTE']
        aprovados = df[df['SITUAÇÃO'] == 'APROVADO']
        
        print(f"\nPending Cases: {len(pendentes)}")
        print(f"Approved Cases: {len(aprovados)}")
        
        print("\n=== Contract Statistics ===")
        print(f"Total contracts: {len(df)}")
        print(f"Unique contracts: {df['CONTRATO'].nunique()}")
        print(f"Contracts per bank (average): {len(df) / df['BANCO'].nunique():.2f}")
        
        return True
        
    except Exception as e:
        print(f"Error analyzing data: {str(e)}")
        return False

if __name__ == "__main__":
    analyze_csv()

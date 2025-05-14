import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def analyze_csv():
    try:
        # Read CSV file
        df = pd.read_csv('(JULIO) LISTAS INDIVIDUAIS - IGOR.csv', encoding='utf-8')
        
        # Clean column names (remove spaces and special characters)
        df.columns = df.columns.str.strip()
        
        # Analysis by SITUAÇÃO
        print("\n=== Analysis by SITUAÇÃO ===")
        situacao_counts = df['SITUAÇÃO'].value_counts()
        print(situacao_counts)
        
        # Analysis by RESOLUÇÃO
        print("\n=== Analysis by RESOLUÇÃO ===")
        resolucao_counts = df['RESOLUÇÃO'].value_counts()
        print(resolucao_counts)
        
        # Create visualizations
        plt.figure(figsize=(12, 6))
        
        # Pie chart for SITUAÇÃO
        plt.subplot(1, 2, 1)
        situacao_counts.plot(kind='pie', autopct='%1.1f%%')
        plt.title('Distribution by SITUAÇÃO')
        
        # Bar chart for RESOLUÇÃO
        plt.subplot(1, 2, 2)
        resolucao_counts.plot(kind='bar')
        plt.title('Distribution by RESOLUÇÃO')
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
        
        # Additional analysis
        print("\n=== Summary Statistics ===")
        print(f"Total Records: {len(df)}")
        print(f"Unique Status: {df['SITUAÇÃO'].nunique()}")
        
        # Filter by specific conditions
        pendentes = df[df['SITUAÇÃO'] == 'PENDENTE']
        aprovados = df[df['SITUAÇÃO'] == 'APROVADO']
        
        print(f"\nPending Cases: {len(pendentes)}")
        print(f"Approved Cases: {len(aprovados)}")
        
        return True
        
    except Exception as e:
        print(f"Error analyzing data: {str(e)}")
        return False

if __name__ == "__main__":
    analyze_csv()
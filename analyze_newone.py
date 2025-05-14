import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

class DataVisualizer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None
        self.output_dir = 'analysis_output'
        self.setup_environment()
        
    def setup_environment(self):
        """Setup the visualization environment"""
        try:
            # Get absolute path for output directory
            self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'analysis_output')
            
            # Create main output directory
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
                print(f"Created main directory: {self.output_dir}")
            
            # Create subdirectories
            folders = ['graphs', 'reports', 'clusters']
            for folder in folders:
                folder_path = os.path.join(self.output_dir, folder)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                    print(f"Created subdirectory: {folder_path}")
            
            # Set style for all plots
            plt.style.use('seaborn')
            sns.set_palette("husl")
            print("Visualization environment setup completed")
            
        except Exception as e:
            print(f"Error setting up environment: {str(e)}")
            raise
        
    def load_data(self):
        """Load and prepare the data"""
        self.df = pd.read_csv(self.file_path, encoding='utf-8')
        self.clean_data()
        
    def clean_data(self):
        """Clean and prepare data for visualization"""
        # Convert dates
        date_cols = ['DATA', 'ÚLTIMO PAGAMENTO', 'NEGOCIAÇÃO']
        for col in date_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(self.df[col], format='%d/%m/%Y', errors='coerce')
                
        # Clean currency values
        if 'VALOR DO CLIENTE' in self.df.columns:
            self.df['VALOR_NUMERIC'] = self.df['VALOR DO CLIENTE'].str.extract(r'(\d+(?:\.\d+)?)', expand=False).astype(float)
    
    def create_status_analysis(self):
        """Create detailed status analysis visualizations"""
        plt.figure(figsize=(15, 10))
        
        # Status distribution
        plt.subplot(2, 2, 1)
        status_counts = self.df['SITUAÇÃO'].value_counts()
        sns.barplot(x=status_counts.index, y=status_counts.values)
        plt.title('Status Distribution')
        plt.xticks(rotation=45)
        
        # Status by bank
        plt.subplot(2, 2, 2)
        status_by_bank = pd.crosstab(self.df['BANCO'], self.df['SITUAÇÃO'])
        sns.heatmap(status_by_bank, annot=True, fmt='d', cmap='YlGnBu')
        plt.title('Status by Bank')
        
        # Status over time
        plt.subplot(2, 2, (3, 4))
        status_time = self.df.pivot_table(
            index='DATA',
            columns='SITUAÇÃO',
            aggfunc='size',
            fill_value=0
        )
        status_time.plot(kind='area', stacked=True)
        plt.title('Status Evolution Over Time')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/graphs/status_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_financial_analysis(self):
        """Create financial analysis visualizations"""
        if 'VALOR_NUMERIC' in self.df.columns:
            plt.figure(figsize=(15, 10))
            
            # Value distribution
            plt.subplot(2, 2, 1)
            sns.histplot(data=self.df, x='VALOR_NUMERIC', bins=30)
            plt.title('Distribution of Contract Values')
            
            # Value by bank
            plt.subplot(2, 2, 2)
            sns.boxplot(data=self.df, x='BANCO', y='VALOR_NUMERIC')
            plt.xticks(rotation=45)
            plt.title('Contract Values by Bank')
            
            # Value by status
            plt.subplot(2, 2, (3, 4))
            sns.violinplot(data=self.df, x='SITUAÇÃO', y='VALOR_NUMERIC')
            plt.xticks(rotation=45)
            plt.title('Contract Values by Status')
            
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/graphs/financial_analysis.png', dpi=300, bbox_inches='tight')
            plt.close()
    
    def create_temporal_analysis(self):
        """Create temporal analysis visualizations"""
        plt.figure(figsize=(15, 10))
        
        # Contracts over time
        plt.subplot(2, 1, 1)
        self.df['DATA'].value_counts().sort_index().plot(kind='line', marker='o')
        plt.title('Number of Contracts Over Time')
        
        # Monthly distribution
        plt.subplot(2, 1, 2)
        self.df['DATA'].dt.month.value_counts().sort_index().plot(kind='bar')
        plt.title('Monthly Distribution of Contracts')
        plt.xlabel('Month')
        plt.ylabel('Number of Contracts')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/graphs/temporal_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_bank_analysis(self):
        """Create bank analysis visualizations"""
        plt.figure(figsize=(15, 10))
        
        # Bank distribution
        plt.subplot(2, 2, 1)
        bank_counts = self.df['BANCO'].value_counts()
        plt.pie(bank_counts.values, labels=bank_counts.index, autopct='%1.1f%%')
        plt.title('Distribution by Bank')
        
        # Bank success rate
        plt.subplot(2, 2, 2)
        success_rate = self.df.groupby('BANCO')['SITUAÇÃO'].apply(
            lambda x: (x == 'APROVADO').mean()
        ).sort_values(ascending=False)
        sns.barplot(x=success_rate.index, y=success_rate.values)
        plt.title('Approval Rate by Bank')
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/graphs/bank_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

def main():
    try:
        # Get current working directory
        current_dir = os.getcwd()
        csv_file = "(JULIO) LISTAS INDIVIDUAIS - IGOR.csv"
        csv_path = os.path.join(current_dir, csv_file)
        
        print(f"Working directory: {current_dir}")
        print(f"Looking for CSV at: {csv_path}")
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found at: {csv_path}")
        
        # Initialize visualizer
        visualizer = DataVisualizer(csv_path)
        
        # Create visualizations
        analyses = {
            'Status Analysis': {
                'func': visualizer.create_status_analysis,
                'output': 'graphs/status/status_analysis.png'
            },
            'Financial Analysis': {
                'func': visualizer.create_financial_analysis,
                'output': 'graphs/financial/financial_analysis.png'
            },
            'Temporal Analysis': {
                'func': visualizer.create_temporal_analysis,
                'output': 'graphs/temporal/temporal_analysis.png'
            },
            'Bank Analysis': {
                'func': visualizer.create_bank_analysis,
                'output': 'graphs/bank/bank_analysis.png'
            }
        }
        
        # Run analyses
        for name, info in analyses.items():
            print(f"\nGenerating {name}...")
            info['func']()
            output_path = os.path.join(visualizer.output_dir, info['output'])
            if os.path.exists(output_path):
                print(f"✓ Created: {info['output']}")
            else:
                print(f"❌ Failed to create: {info['output']}")
        
        print("\nAnalysis complete! Check the 'analysis_output' folder.")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
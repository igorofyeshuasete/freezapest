import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
from typing import Dict, List, Tuple
import logging

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

    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load and preprocess all datasets"""
        try:
            # Load main dataset
            main_df = pd.read_csv(
                r"C:\Users\igor de jesus\zaptest\(JULIO) LISTAS INDIVIDUAIS - IGOR.csv",
                encoding='utf-8'
            )
            
            # Load supporting datasets
            aprovados_df = pd.read_csv(
                r"C:\Users\igor de jesus\zaptest\DEMANDAS DE ABRIL_2025 - APROVADOS.csv",
                encoding='utf-8'
            )
            
            quitados_df = pd.read_csv(
                r"C:\Users\igor de jesus\zaptest\DEMANDAS DE ABRIL_2025 - QUITADOS.csv",
                encoding='utf-8'
            )
            
            # Clean and standardize date columns
            for df in [main_df, aprovados_df, quitados_df]:
                df['DATA'] = pd.to_datetime(df['DATA'], format='%d/%m/%Y', errors='coerce')
                if 'RESOLUÇÃO' in df.columns:
                    df['RESOLUÇÃO'] = pd.to_datetime(df['RESOLUÇÃO'], format='%d/%m/%Y', errors='coerce')
            
            return main_df, aprovados_df, quitados_df
            
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            raise

    def analyze_bank_performance(self, df: pd.DataFrame) -> pd.DataFrame:
        """Analyze success rates and metrics by bank"""
        try:
            bank_stats = df.groupby('BANCO').agg({
                'SITUAÇÃO': 'count',
                'VALOR DO CLIENTE': 'mean',
                'CTT': 'count'
            }).reset_index()
            
            # Calculate quitados per bank
            quitados = df[df['SITUAÇÃO'] == 'QUITADO'].groupby('BANCO').size()
            bank_stats['QUITADOS'] = bank_stats['BANCO'].map(quitados).fillna(0)
            bank_stats['SUCCESS_RATE'] = (bank_stats['QUITADOS'] / bank_stats['SITUAÇÃO'] * 100).round(2)
            
            return bank_stats.sort_values('SUCCESS_RATE', ascending=False)
            
        except Exception as e:
            self.logger.error(f"Error in bank analysis: {str(e)}")
            return pd.DataFrame()

    def analyze_resolution_time(self, df: pd.DataFrame) -> pd.DataFrame:
        """Analyze resolution times and patterns"""
        try:
            df['RESOLUTION_DAYS'] = (df['RESOLUÇÃO'] - df['DATA']).dt.days
            
            resolution_stats = df.groupby('BANCO').agg({
                'RESOLUTION_DAYS': ['mean', 'median', 'std']
            }).round(2)
            
            resolution_stats.columns = ['AVG_DAYS', 'MEDIAN_DAYS', 'STD_DAYS']
            return resolution_stats.sort_values('AVG_DAYS')
            
        except Exception as e:
            self.logger.error(f"Error in resolution analysis: {str(e)}")
            return pd.DataFrame()

    def create_visualizations(self, bank_stats: pd.DataFrame, resolution_stats: pd.DataFrame):
        """Create interactive visualizations"""
        try:
            # Success Rate by Bank
            fig1 = px.bar(
                bank_stats,
                x='BANCO',
                y='SUCCESS_RATE',
                title='Success Rate by Bank',
                color='SUCCESS_RATE',
                labels={'SUCCESS_RATE': 'Quitado Rate (%)'}
            )
            
            # Resolution Time Analysis
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=resolution_stats.index,
                y=resolution_stats['AVG_DAYS'],
                name='Average Days to Resolution'
            ))
            fig2.update_layout(title='Resolution Time by Bank')
            
            # Save visualizations
            fig1.write_html("bank_success_rates.html")
            fig2.write_html("resolution_times.html")
            
        except Exception as e:
            self.logger.error(f"Error creating visualizations: {str(e)}")

    def predict_success_probability(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate success probability based on historical patterns"""
        try:
            # Create features for prediction
            features = pd.get_dummies(df['BANCO'])
            features['VALOR'] = pd.to_numeric(
                df['VALOR DO CLIENTE'].str.replace('R$', '').str.replace('.', '').str.replace(',', '.'),
                errors='coerce'
            )
            
            # Calculate probability based on historical patterns
            success_patterns = df[df['SITUAÇÃO'] == 'QUITADO'].groupby('BANCO').size() / df.groupby('BANCO').size()
            
            return success_patterns.to_frame('PROBABILITY').sort_values('PROBABILITY', ascending=False)
            
        except Exception as e:
            self.logger.error(f"Error in probability calculation: {str(e)}")
            return pd.DataFrame()

def main():
    analyzer = QuitadosAnalyzer()
    
    try:
        # Load data
        main_df, aprovados_df, quitados_df = analyzer.load_data()
        
        # Analyze bank performance
        bank_stats = analyzer.analyze_bank_performance(main_df)
        print("\n=== Bank Performance Analysis ===")
        print(bank_stats)
        
        # Analyze resolution times
        resolution_stats = analyzer.analyze_resolution_time(main_df)
        print("\n=== Resolution Time Analysis ===")
        print(resolution_stats)
        
        # Calculate success probabilities
        success_prob = analyzer.predict_success_probability(main_df)
        print("\n=== Success Probability by Bank ===")
        print(success_prob)
        
        # Create visualizations
        analyzer.create_visualizations(bank_stats, resolution_stats)
        
        # Export results
        bank_stats.to_csv('bank_analysis.csv')
        resolution_stats.to_csv('resolution_analysis.csv')
        success_prob.to_csv('success_probabilities.csv')
        
        print("\nAnalysis complete. Results exported to CSV files and visualizations created.")
        
    except Exception as e:
        print(f"Error in analysis: {str(e)}")

if __name__ == "__main__":
    main()
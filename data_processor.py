import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
import logging

class DataPreprocessor:
    """Professional data preprocessing and validation class"""
    
    def __init__(self, logging_level: int = logging.INFO):
        """Initialize with configurable logging"""
        self.logger = self._setup_logger(logging_level)
        self.required_columns = {
            'priority': ['PRAZO B', 'PRAZO 7', 'BANCO', 'SITUAÇÃO'],
            'quitados': ['CTT', 'SALDO DEVEDOR', 'DESCONTO', 'BANCO', 'CONSULTOR'],
            'basic': ['DATA', 'RESOLUÇÃO', 'SITUAÇÃO']
        }
        
    def _setup_logger(self, level: int) -> logging.Logger:
        """Configure logging"""
        logger = logging.getLogger('DataPreprocessor')
        logger.setLevel(level)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def validate_columns(self, df: pd.DataFrame, column_set: str) -> bool:
        """Validate required columns exist"""
        missing = [col for col in self.required_columns[column_set] 
                  if col not in df.columns]
        if missing:
            self.logger.error(f"Missing required columns for {column_set}: {missing}")
            return False
        return True

    def clean_numeric(self, series: pd.Series) -> pd.Series:
        """Clean and convert numeric values"""
        try:
            if series.dtype == object:
                return pd.to_numeric(
                    series.astype(str)
                    .str.replace('R$', '')
                    .str.replace('%', '')
                    .str.replace('.', '')
                    .str.replace(',', '.')
                    .str.strip(),
                    errors='coerce'
                )
            return series
        except Exception as e:
            self.logger.error(f"Error cleaning numeric data: {str(e)}")
            return pd.Series([np.nan] * len(series))

    def process_dataframe(self, df: pd.DataFrame, analysis_type: str) -> pd.DataFrame:
        """Process dataframe based on analysis type"""
        try:
            df = df.copy()
            df.columns = df.columns.str.strip()
            
            if not self.validate_columns(df, analysis_type):
                raise ValueError(f"Missing required columns for {analysis_type}")
            
            # Common cleaning
            for col in df.columns:
                if 'PRAZO' in col or 'VALOR' in col or 'SALDO' in col:
                    df[col] = self.clean_numeric(df[col])
                    
            # Specific processing
            if analysis_type == 'priority':
                df = self._process_priority(df)
            elif analysis_type == 'quitados':
                df = self._process_quitados(df)
                
            return df
            
        except Exception as e:
            self.logger.error(f"Error processing dataframe: {str(e)}")
            raise

    def _process_priority(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process priority-specific data"""
        try:
            # Handle PRAZO columns
            if 'PRAZO B' not in df.columns and 'PRAZO 7' in df.columns:
                df['PRAZO B'] = df['PRAZO 7']
            
            # Convert dates
            date_cols = ['DATA', 'RESOLUÇÃO', 'ÚLTIMO PAGAMENTO', 'ENTRADA']
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error in priority processing: {str(e)}")
            raise

    def _process_quitados(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process quitados-specific data"""
        try:
            # Handle specific columns
            if 'DESCONTO' in df.columns:
                df['DESCONTO'] = self.clean_numeric(df['DESCONTO'])
            if 'SALDO DEVEDOR' in df.columns:
                df['SALDO_DEVEDOR'] = self.clean_numeric(df['SALDO DEVEDOR'])
                
            # Calculate derived metrics
            df['VALOR_DESCONTO'] = df['SALDO_DEVEDOR'] * (df['DESCONTO'] / 100)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error in quitados processing: {str(e)}")
            raise
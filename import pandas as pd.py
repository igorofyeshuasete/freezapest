import pandas as pd
import numpy as np
from datetime import datetime
import os
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
import lightgbm as lgb  # Proper LightGBM import
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Add typing imports at the top of the file
from typing import Dict, List, Optional, Union, Any
import logging
import traceback

# Verify NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

import plotly.express as px
import plotly.graph_objects as go
from prophet import Prophet
from data_processor import DataPreprocessor

# Initialize preprocessor
preprocessor = DataPreprocessor(logging_level=logging.INFO)

class EnhancedPatternAnalyzer:
    def __init__(self):
        self.tfidf = TfidfVectorizer(max_features=100)
        self.lgb_model = None
        self.scaler = StandardScaler()
        
    def preprocess_text(self, text_series):
        """Enhanced text preprocessing with NLTK"""
        stop_words = set(stopwords.words('portuguese'))
        processed_texts = []
        
        for text in text_series.dropna():
            tokens = word_tokenize(text.lower())
            tokens = [t for t in tokens if t not in stop_words]
            processed_texts.append(' '.join(tokens))
            
        return processed_texts

    def build_lgb_model(self):
        """Build LightGBM model for pattern detection"""
        params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9
        }
        return lgb.LGBMClassifier(**params)

    def analyze_patterns(self, df):
        """Enhanced pattern analysis with LightGBM"""
        try:
            # Text pattern analysis using TF-IDF instead of Word2Vec
            processed_texts = self.preprocess_text(df['OBSERVAÇÃO'])
            text_features = self.tfidf.fit_transform(processed_texts)
            
            # Time series analysis for campaigns
            campaign_ts = df.groupby('DATA')['has_campaign_related'].sum().reset_index()
            prophet_df = campaign_ts.rename(columns={'DATA': 'ds', 'has_campaign_related': 'y'})
            
            # Prophet model for forecasting
            m = Prophet(yearly_seasonality=True, weekly_seasonality=True)
            m.fit(prophet_df)
            future = m.make_future_dataframe(periods=30)
            forecast = m.predict(future)
            
            # Pattern detection using LightGBM
            X = self.prepare_features(df)
            y = df['SITUAÇÃO'].map({'QUITADO': 1, 'PENDENTE': 0}).fillna(0)
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
            self.lgb_model = self.build_lgb_model()
            self.lgb_model.fit(X_train, y_train)
            
            pattern_scores = self.lgb_model.predict_proba(X_test)[:,1]
            
            return {
                'text_features': text_features,
                'forecast': forecast,
                'pattern_scores': pattern_scores
            }
            
        except Exception as e:
            print(f"Error in pattern analysis: {str(e)}")
            return None

    def prepare_features(self, df):
        """Prepare features for LightGBM model"""
        numeric_features = ['PRAZO B', 'PRAZO 7']
        categorical_features = ['BANCO', 'SITUAÇÃO']
        
        X = pd.get_dummies(df[categorical_features])
        for col in numeric_features:
            if col in df.columns:
                X[col] = df[col]
        
        return X.fillna(-1)

def create_interactive_dashboard(analysis_results, df):
    """Create interactive dashboard using Plotly"""
    # Time series plot
    fig1 = px.line(
        analysis_results['forecast'], 
        x='ds', 
        y=['yhat', 'yhat_lower', 'yhat_upper'],
        title='Campaign Performance Forecast'
    )
    
    # Pattern distribution
    fig2 = px.histogram(
        df, 
        x='OBSERVAÇÃO', 
        color='SITUAÇÃO',
        title='Pattern Distribution by Status'
    )
    
    # Anomaly detection
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        y=analysis_results['anomaly_scores'].flatten(),
        mode='lines',
        name='Anomaly Score'
    ))
    
    # Save plots
    fig1.write_html("campaign_forecast.html")
    fig2.write_html("pattern_distribution.html")
    fig3.write_html("anomaly_detection.html")

def enhanced_analyze_quitados_patterns(df):
    """Enhanced analysis with ML/DL features"""
    try:
        analyzer = EnhancedPatternAnalyzer()
        
        # Original pattern analysis
        base_analysis = analyze_quitados_patterns(df)
        
        # Enhanced pattern analysis
        ml_analysis = analyzer.analyze_patterns(df)
        
        # Create interactive dashboard
        create_interactive_dashboard(ml_analysis, df)
        
        # Combine results
        enhanced_results = {
            **base_analysis,
            'ml_analysis': ml_analysis,
            'visualization_files': [
                'campaign_forecast.html',
                'pattern_distribution.html',
                'anomaly_detection.html'
            ]
        }
        
        # Export enhanced results
        pd.DataFrame({
            'metric': list(enhanced_results['conversion_metrics'].keys()),
            'value': list(enhanced_results['conversion_metrics'].values()),
            'anomaly_score': ml_analysis['anomaly_scores'].flatten()[:len(enhanced_results['conversion_metrics'])]
        }).to_csv('enhanced_quitados_analysis.csv', index=False)
        
        return enhanced_results
        
    except Exception as e:
        print(f"Error in enhanced analysis: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

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

def safe_numeric_conversion(series: pd.Series) -> pd.Series:
    """
    Safely convert series to numeric with enhanced error handling
    """
    try:
        if pd.api.types.is_string_dtype(series):
            # Clean string values first
            cleaned = (series.astype(str)
                     .str.strip()
                     .str.replace(',', '.')
                     .str.replace('R$', '')
                     .str.replace('%', ''))
            return pd.to_numeric(cleaned, errors='coerce')
        elif pd.api.types.is_numeric_dtype(series):
            return series
        else:
            # Convert to string first, then to numeric
            return pd.to_numeric(series.astype(str), errors='coerce')
    except Exception as e:
        logging.warning(f"Error converting series: {str(e)}")
        return pd.Series([np.nan] * len(series))

def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare features with enhanced error handling and type validation
    """
    try:
        df = df.copy()
        
        # Debug logging
        logging.info("Starting feature preparation")
        logging.info(f"Input columns: {df.columns.tolist()}")
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Validate PRAZO columns
        prazo_columns = [col for col in df.columns if 'PRAZO' in col]
        logging.info(f"Found PRAZO columns: {prazo_columns}")
        
        # Safe conversion of PRAZO columns
        for col in prazo_columns:
            df[f"{col.replace(' ', '_')}"] = safe_numeric_conversion(df[col])
            logging.info(f"Converted {col} to numeric")
        
        # Create the feature matrix with error handling
        numeric_features = ['PRAZOB', 'PRAZO7']
        categorical_features = ['BANCO', 'SITUAÇÃO']
        
        X = pd.DataFrame()
        
        # Add numeric features safely
        for feature in numeric_features:
            source_col = feature.upper().replace('_', ' ')
            if source_col in df.columns:
                X[feature] = safe_numeric_conversion(df[source_col])
        
        # Add categorical features with validation
        try:
            cat_df = pd.get_dummies(df[categorical_features], dummy_na=True)
            X = pd.concat([X, cat_df], axis=1)
        except Exception as e:
            logging.error(f"Error creating categorical features: {str(e)}")
            # Create minimal features if dummies fail
            for col in categorical_features:
                if col in df.columns:
                    X[f"{col}_OTHER"] = 1
        
        # Validate output
        if X.empty:
            raise ValueError("No features were created")
            
        # Fill missing values
        X = X.fillna(-999)
        
        logging.info(f"Created features: {X.columns.tolist()}")
        return X
        
    except Exception as e:
        logging.error(f"Error in feature preparation: {str(e)}")
        logging.error(traceback.format_exc())
        raise

def train_advanced_model(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Train model with enhanced error handling and validation
    """
    try:
        logging.info("Starting model training")
        
        # Prepare features with validation
        X = prepare_features(df)
        
        # Validate target variable
        if 'SITUAÇÃO' not in df.columns:
            raise ValueError("Target variable 'SITUAÇÃO' not found")
            
        # Create target with validation
        positive_status = ['PRIORIDADE', 'APROVADO', 'QUITADO']
        y = df['SITUAÇÃO'].isin(positive_status).astype(int)
        
        if len(y.unique()) < 2:
            raise ValueError("Target variable has insufficient classes")
        
        # Continue with existing training code...
        
    except Exception as e:
        logging.error(f"Error in model training: {str(e)}")
        logging.error(traceback.format_exc())
        return None

# Update main execution
if __name__ == "__main__":
    try:
        # Configure logging with more detail
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        
        # Load data with validation
        file_path = r"C:\Users\igor de jesus\zaptest\(JULIO) LISTAS INDIVIDUAIS - IGOR.csv"
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found: {file_path}")
        
        df = pd.read_csv(
            file_path,
            encoding='utf-8',
            sep=',',
            decimal=',',
            thousands='.'
        )
        
        logging.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
        
        # Process and validate data
        df_priority = preprocessor.process_dataframe(df, 'priority')
        
        # Train model with enhanced error handling
        model_results = train_advanced_model(df_priority)
        
        if model_results:
            logging.info("Analysis completed successfully")
        else:
            logging.warning("Analysis completed with warnings")
            
    except Exception as e:
        logging.error(f"Critical error in main execution: {str(e)}")
        logging.error(traceback.format_exc())
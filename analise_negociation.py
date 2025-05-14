import pandas as pd
import numpy as np
from datetime import datetime
import os
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import LabelEncoder, StandardScaler
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

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

def prepare_features(df):
    """Prepare features for ML model with enhanced error handling"""
    df = df.copy()
    
    # Clean column names - remove spaces and special characters
    df.columns = df.columns.str.strip().str.replace(' ', '')
    
    # Handle PRAZO B column name with space
    if 'PRAZO B ' in df.columns:
        df['PRAZOB'] = df['PRAZO B '].astype(str).str.strip()
    elif 'PRAZO B' in df.columns:
        df['PRAZOB'] = df['PRAZO B'].astype(str).str.strip()
    else:
        raise ValueError("PRAZO B column not found")
    
    # Convert dates safely
    date_cols = ['DATA', 'RESOLUÇÃO', 'ÚLTIMO PAGAMENTO', 'ENTRADA']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
    
    # Create temporal features
    current_date = pd.Timestamp.now()
    df['dias_desde_ultimo_pagamento'] = (current_date - df['ÚLTIMO PAGAMENTO']).dt.days
    df['dias_ate_resolucao'] = (df['RESOLUÇÃO'] - current_date).dt.days
    df['dias_ate_entrada'] = (df['ENTRADA'] - current_date).dt.days
    
    # Convert PRAZO columns safely
    df['PRAZOB'] = pd.to_numeric(df['PRAZOB'].str.replace(',','.'), errors='coerce')
    df['PRAZO7'] = pd.to_numeric(df['PRAZO 7 '].astype(str).str.replace(',','.'), errors='coerce')
    
    # Extract numeric values from monetary columns
    df['VALOR_CLIENTE'] = df['VALOR DO CLIENTE'].str.extract(r'R\$\s*([\d,.]+)', expand=False)
    df['VALOR_CLIENTE'] = pd.to_numeric(df['VALOR_CLIENTE'].str.replace('.','').str.replace(',','.'), errors='coerce')
    
    # Enhanced feature engineering
    df['tem_contato'] = df['CONTATO'].notna().astype(int)
    df['tem_negociacao'] = df['NEGOCIAÇÃO'].notna().astype(int)
    df['tem_campanha'] = df['CAMPANHA'].fillna('NAO').map({'SIM': 1, 'NAO': 0})
    
    # Encode categorical variables
    le = LabelEncoder()
    cat_cols = ['ESCRITÓRIO', 'BANCO', 'SITUAÇÃO']
    for col in cat_cols:
        df[f'{col}_encoded'] = le.fit_transform(df[col].fillna('MISSING'))
    
    # Select and prepare final features
    feature_cols = [
        'PRAZOB', 'PRAZO7',
        'dias_desde_ultimo_pagamento', 'dias_ate_resolucao', 'dias_ate_entrada',
        'VALOR_CLIENTE', 'tem_contato', 'tem_negociacao', 'tem_campanha',
        'ESCRITÓRIO_encoded', 'BANCO_encoded', 'SITUAÇÃO_encoded'
    ]
    
    return df[feature_cols].fillna(-1)

def train_advanced_model(df):
    """Train enhanced XGBoost model with hyperparameter tuning"""
    X = prepare_features(df)
    y = (df['SITUAÇÃO'].isin(['PRIORIDADE', 'APROVADO', 'QUITADO'])).astype(int)
    
    # Split data with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Define hyperparameter grid
    param_grid = {
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.1],
        'n_estimators': [100, 200],
        'min_child_weight': [1, 3],
        'subsample': [0.8, 1.0]
    }
    
    # Initialize model
    model = XGBClassifier(objective='binary:logistic', random_state=42)
    
    # Perform grid search - Fixed: Assign GridSearchCV to grid_search variable
    grid_search = GridSearchCV(
        model, param_grid, cv=5, scoring='f1', n_jobs=-1
    )
    grid_search.fit(X_train_scaled, y_train)
    
    # Get best model and continue with existing code
    best_model = grid_search.best_estimator_
    y_pred = best_model.predict(X_test_scaled)
    y_prob = best_model.predict_proba(X_test_scaled)[:,1]
    
    # Feature importance
    importance = pd.DataFrame({
        'feature': X.columns,
        'importance': best_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    return {
        'model': best_model,
        'scaler': scaler,
        'feature_importance': importance,
        'metrics': classification_report(y_test, y_pred),
        'confusion_matrix': confusion_matrix(y_test, y_pred),
        'best_params': grid_search.best_params_,
        'probabilities': y_prob
    }

def predict_priorities(df, model_results):
    """Predict priorities for all contracts"""
    X = prepare_features(df)
    X_scaled = model_results['scaler'].transform(X)
    
    # Get predictions and probabilities
    priorities = model_results['model'].predict_proba(X_scaled)[:,1]
    
    # Add predictions to dataframe
    df['priority_score'] = priorities
    df['priority_rank'] = df['priority_score'].rank(ascending=False)
    
    return df.sort_values('priority_score', ascending=False)

def analyze_quitados_patterns(df):
    """Analyze patterns and probabilities for QUITADO status"""
    try:
        # Clean and prepare data
        df = df.copy()
        df.columns = df.columns.str.strip()

        # Convert observation patterns to categorical features
        observation_patterns = {
            'HIGH_PRIORITY': ['BOLETO SOLICITADO', 'CONTRATO EM TRANSFERENCIA'],
            'PROCESS_BLOCKERS': ['AGUARDANDO PROCURAÇÃO', 'PROCURAÇÃO ENVIADA'],
            'STATUS_INDICATORS': ['INADIMPLENTE', 'CLIENTE INADIMPLENTE'],
            'CAMPAIGN_RELATED': ['SEM CAMPANHA', 'CAMPANHA DE 70,66%', 'CAMPANHA DE 69,04%']
        }

        # Create new features based on observations
        for category, patterns in observation_patterns.items():
            df[f'has_{category.lower()}'] = df['OBSERVAÇÃO'].str.contains('|'.join(patterns), case=False, na=False)

        # Analyze bank distribution for QUITADO status
        bank_quitado = df[df['SITUAÇÃO'] == 'QUITADO'].groupby('BANCO').agg({
            'CONTRATO': 'count',
            'VALOR DO CLIENTE': 'mean',
            'OBSERVAÇÃO': lambda x: x.value_counts().index[0] if len(x) > 0 else 'N/A'
        }).reset_index()

        bank_quitado['success_rate'] = bank_quitado['CONTRATO'] / len(df) * 100

        # Calculate conversion metrics
        conversion_metrics = {
            'overall_conversion': len(df[df['SITUAÇÃO'] == 'QUITADO']) / len(df) * 100,
            'with_campaign': len(df[(df['SITUAÇÃO'] == 'QUITADO') & (df['has_campaign_related'])]) / len(df[df['has_campaign_related']]) * 100,
            'without_campaign': len(df[(df['SITUAÇÃO'] == 'QUITADO') & (~df['has_campaign_related'])]) / len(df[~df['has_campaign_related']]) * 100,
            'with_boleto': len(df[(df['SITUAÇÃO'] == 'QUITADO') & (df['OBSERVAÇÃO'].str.contains('BOLETO SOLICITADO', na=False))]) / len(df[df['OBSERVAÇÃO'].str.contains('BOLETO SOLICITADO', na=False)]) * 100
        }

        # Calculate processing times
        df['processing_time'] = (pd.to_datetime(df['RESOLUÇÃO']) - pd.to_datetime(df['DATA'])).dt.days

        processing_times = {
            'boleto_solicitado': df[df['OBSERVAÇÃO'].str.contains('BOLETO SOLICITADO', na=False)]['processing_time'].mean(),
            'contrato_transferencia': df[df['OBSERVAÇÃO'].str.contains('CONTRATO EM TRANSFERENCIA', na=False)]['processing_time'].mean(),
            'standard': df['processing_time'].mean()
        }

        # Print analysis results
        print("\n=== Análise de Padrões de Quitação ===")
        print("\nDistribuição por Banco:")
        print(bank_quitado[['BANCO', 'CONTRATO', 'success_rate']].round(2))

        print("\nMétricas de Conversão:")
        for metric, value in conversion_metrics.items():
            print(f"{metric}: {value:.2f}%")

        print("\nTempos de Processamento (dias):")
        for process, days in processing_times.items():
            print(f"{process}: {days:.1f}")

        return {
            'bank_distribution': bank_quitado,
            'conversion_metrics': conversion_metrics,
            'processing_times': processing_times,
            'observation_patterns': df.filter(like='has_').sum().to_dict()
        }

    except Exception as e:
        print(f"Erro na análise de quitados: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

# Main execution
if __name__ == "__main__":
    try:
        # Load data
        file_path = r"C:\Users\igor de jesus\zaptest\(JULIO) LISTAS INDIVIDUAIS - IGOR.csv"
        df = pd.read_csv(file_path, encoding='utf-8')
        
        print("\n=== Training Advanced Priority Prediction Model ===")
        model_results = train_advanced_model(df)
        
        print("\nBest Model Parameters:")
        print(model_results['best_params'])
        
        print("\nFeature Importance:")
        print(model_results['feature_importance'])
        
        print("\nModel Performance:")
        print(model_results['metrics'])
        
        print("\nConfusion Matrix:")
        print(model_results['confusion_matrix'])
        
        # Get and display predictions
        predictions = predict_priorities(df, model_results)
        
        print("\nTop 10 Priority Contracts:")
        cols = ['CONTRATO', 'BANCO', 'SITUAÇÃO', 'priority_score', 'VALOR DO CLIENTE']
        print(predictions[cols].head(10))
        
        # Export results
        predictions.to_csv('priority_predictions.csv', index=False)
        print("\nDetailed results exported to 'priority_predictions.csv'")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())

    try:
        # Load QUITADOS data
        quitados_file = r"C:\Users\igor de jesus\zaptest\DEMANDAS DE ABRIL_2025 - QUITADOS.csv"
        df_quitados = pd.read_csv(quitados_file, encoding='utf-8')
        
        print("\n=== Analyzing QUITADOS Patterns ===")
        quitados_analysis = analyze_quitados_patterns(df_quitados)
        
        if quitados_analysis:
            # Export results
            results_df = pd.DataFrame({
                'metric': list(quitados_analysis['conversion_metrics'].keys()),
                'value': list(quitados_analysis['conversion_metrics'].values())
            })
            results_df.to_csv('quitados_analysis.csv', index=False)
            print("\nDetailed results exported to 'quitados_analysis.csv'")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())

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
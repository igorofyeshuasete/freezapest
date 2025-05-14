from flask import Flask, render_template
import pandas as pd
import json
import plotly
import plotly.express as px
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for Flask sessions

class DashboardData:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path, encoding='utf-8')
        self.df['DATA'] = pd.to_datetime(self.df['DATA'], format='%d/%m/%Y')
        
    def get_summary_stats(self):
        return {
            'total_contracts': len(self.df),
            'approved': len(self.df[self.df['SITUAÇÃO'] == 'APROVADO']),
            'pending': len(self.df[self.df['SITUAÇÃO'] == 'PENDENTE']),
            'total_value': self.df['VALOR DO CLIENTE'].str.extract(r'(\d+(?:\.\d+)?)', expand=False).astype(float).sum()
        }
    
    def create_charts(self):
        # Status distribution with custom colors
        fig1 = px.pie(self.df, names='SITUAÇÃO', title='Status Distribution',
                      color_discrete_sequence=px.colors.qualitative.Set3)
        
        # Bank analysis with improved styling
        bank_data = self.df.groupby('BANCO').size().reset_index()
        bank_data.columns = ['BANCO', 'Count']
        fig2 = px.bar(bank_data, x='BANCO', y='Count', 
                     title='Contracts by Bank',
                     color='Count',
                     color_continuous_scale='Viridis')
        
        # Timeline with better formatting
        timeline_data = self.df.groupby('DATA').size().reset_index()
        timeline_data.columns = ['DATA', 'Count']
        fig3 = px.line(timeline_data, x='DATA', y='Count', 
                      title='Contracts Timeline',
                      line_shape='spline')
        
        # Update layout for all charts
        for fig in [fig1, fig2, fig3]:
            fig.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(size=12)
            )
        
        return {
            'status_chart': json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder),
            'bank_chart': json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder),
            'timeline_chart': json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder)
        }

@app.route('/')
def dashboard():
    data = DashboardData('(JULIO) LISTAS INDIVIDUAIS - IGOR.csv')
    stats = data.get_summary_stats()
    charts = data.create_charts()
    return render_template('dashboard.html', stats=stats, charts=charts)

if __name__ == '__main__':
    # Ensure templates directory exists
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Set Flask environment variables
    os.environ['FLASK_APP'] = 'dashboard.py'
    os.environ['FLASK_ENV'] = 'development'
    
    # Run the app
    app.run(debug=True, port=5000)
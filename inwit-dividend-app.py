# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import os
import re

# --- Configurazione Pagina ---
st.set_page_config(
    page_title="Analisi Dividendi INWIT",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Dati Chiave Estratti ---
TICKER = "INWIT.MI"
NOME_SOCIETA = "INWIT S.p.A. (Infrastrutture Wireless Italiane)"  
SETTORE = "Infrastrutture di Telecomunicazione - Tower Company"
ULTIMO_DPS_PAGATO_VAL = 0.48  # Relativo all'esercizio 2023
ANNO_ULTIMO_DPS = 2023
PREZZO_RIFERIMENTO_APPROX = 10.4  # Prezzo attuale approssimativo
POLITICA_PAYOUT = "80% del Free Cash Flow + crescita annua 7.5%"
DPS_ATTESO_2024_VAL = 0.48  # Confermato per il 2024
CRESCITA_DPS_PROGRAMMATA = "+7.5% annuo fino al 2026"
YIELD_ATTUALE = round((ULTIMO_DPS_PAGATO_VAL / PREZZO_RIFERIMENTO_APPROX) * 100, 2)
DIVIDEND_CAGR_2015_2023 = 30.0  # Crescita composta annua dal 2015

# Dati storici Dividendo Per Azione (DPS) - da TIKR
dps_storico_data = {
    'Anno Esercizio': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
    'DPS (€)': [0.09, 0.15, 0.19, 0.21, 0.73, 0.30, 0.32, 0.35, 0.48, 0.48],  # 2019 include straordinario
    'DPS Ordinario (€)': [0.09, 0.15, 0.19, 0.21, 0.13, 0.30, 0.32, 0.35, 0.48, 0.48],
    'DPS Straordinario (€)': [0.0, 0.0, 0.0, 0.0, 0.59, 0.0, 0.0, 0.0, 0.0, 0.0],
    'Tipo': ['Storico', 'Storico', 'Storico', 'Storico', 'Storico', 'Storico', 'Storico', 'Storico', 'Storico', 'Atteso']
}
df_dps = pd.DataFrame(dps_storico_data)

# Dati Finanziari Chiave (estratti da TIKR) - valori in milioni di euro
fin_data = {
    'Metrica': [
        'Ricavi Totali (€M)',
        'EBITDA (€M)',
        'EBITDA Margin (%)',
        'Utile Netto (€M)',
        'EPS Diluito (€)',
        'Cash Flow Operativo (CFO, €M)',
        'Free Cash Flow (FCF, €M)',
        'Debito Netto (€M)',
        'Debito Netto / EBITDA',
        'Dividendo per Azione (DPS, €)',
        'Payout Ratio (%)'
    ],
    '2019': [
        395.4,   # Revenue
        346.2,   # EBITDA (adjusted)
        87.6,    # EBITDA Margin %
        139.3,   # Net Income
        0.23,    # Diluted EPS
        304.8,   # CFO
        237.0,   # FCF (estimate)
        0.0,     # Net Cash position
        0.0,     # ND/EBITDA
        0.73,    # DPS (include extra)
        150.8    # Payout ratio including extra
        ],
    '2020': [
        663.4,   # Revenue (fusione Vodafone)
        579.5,   # EBITDA
        87.3,    # EBITDA Margin %
        156.7,   # Net Income  
        0.18,    # Diluted EPS
        486.6,   # CFO
        397.3,   # FCF
        2661.8,  # Net Debt (post fusione)
        4.6,     # ND/EBITDA
        0.30,    # DPS
        105.4    # Payout ratio
        ],
    '2021': [
        785.2,   # Revenue
        659.3,   # EBITDA
        83.9,    # EBITDA Margin %
        191.4,   # Net Income
        0.20,    # Diluted EPS
        217.8,   # CFO
        49.4,    # FCF (impacted by investments)
        3118.5,  # Net Debt
        4.7,     # ND/EBITDA
        0.32,    # DPS
        97.7     # Payout ratio
        ],
    '2022': [
        853.0,   # Revenue
        732.4,   # EBITDA
        85.9,    # EBITDA Margin %
        293.3,   # Net Income
        0.31,    # Diluted EPS
        687.0,   # CFO
        432.0,   # FCF
        3226.1,  # Net Debt
        4.4,     # ND/EBITDA
        0.35,    # DPS
        97.7     # Payout ratio
        ],
    '2023': [
        960.3,   # Revenue
        866.9,   # EBITDA
        90.3,    # EBITDA Margin %
        339.5,   # Net Income
        0.36,    # Diluted EPS
        811.2,   # CFO
        511.7,   # FCF
        3551.4,  # Net Debt
        4.1,     # ND/EBITDA
        0.48,    # DPS
        127.3    # Payout ratio (alto per extra distribution)
        ],
    '2024E': [
        1036.0,  # Revenue
        930.1,   # EBITDA
        89.8,    # EBITDA Margin %
        353.9,   # Net Income
        0.38,    # Diluted EPS
        762.9,   # CFO
        469.0,   # FCF
        3551.4,  # Net Debt (estimate)
        3.8,     # ND/EBITDA (improving)
        0.48,    # DPS (confermato)
        127.3    # Payout ratio
        ]
}
df_fin = pd.DataFrame(fin_data)

# Creazione di un DataFrame più pulito per grafici finanziari
df_fin_clean = pd.DataFrame({
    'Anno': ['2019', '2020', '2021', '2022', '2023', '2024E'],
    'Ricavi (€M)': [395.4, 663.4, 785.2, 853.0, 960.3, 1036.0],
    'EBITDA (€M)': [346.2, 579.5, 659.3, 732.4, 866.9, 930.1],
    'EBITDA Margin (%)': [87.6, 87.3, 83.9, 85.9, 90.3, 89.8],
    'Utile Netto (€M)': [139.3, 156.7, 191.4, 293.3, 339.5, 353.9],
    'EPS (€)': [0.23, 0.18, 0.20, 0.31, 0.36, 0.38],
    'FCF (€M)': [237.0, 397.3, 49.4, 432.0, 511.7, 469.0],
    'DPS (€)': [0.73, 0.30, 0.32, 0.35, 0.48, 0.48],
    'Fase': ['Pre-Fusione', 'Fusione', 'Integrazione', 'Ripresa', 'Crescita', 'Consolidamento']
})

# Calcolo delle variazioni percentuali DPS (ordinario, escludendo extra 2019)
df_dps['Variazione %'] = df_dps['DPS Ordinario (€)'].pct_change() * 100
df_dps['Variazione %'] = df_dps['Variazione %'].fillna(0)

# Calcolo payout ratios
df_payout = pd.DataFrame({
    'Anno': [2019, 2020, 2021, 2022, 2023, 2024],
    'EPS (€)': [0.23, 0.18, 0.20, 0.31, 0.36, 0.38],
    'DPS (€)': [0.13, 0.30, 0.32, 0.35, 0.48, 0.48],  # Solo ordinario
    'FCF per Share (€)': [0.40, 0.46, 0.05, 0.45, 0.54, 0.50]
})
df_payout['Payout Ratio EPS (%)'] = (df_payout['DPS (€)'] / df_payout['EPS (€)']) * 100
df_payout['FCF Cover (x)'] = df_payout['FCF per Share (€)'] / df_payout['DPS (€)']

# Dati proiezione futura (dal business plan)
df_dps_projection = pd.DataFrame({
    'Anno': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027],
    'DPS (€)': [0.09, 0.15, 0.19, 0.21, 0.13, 0.30, 0.32, 0.35, 0.48, 0.48, 0.516, 0.555, 0.597],
    'Tipo': ['Storico', 'Storico', 'Storico', 'Storico', 'Storico', 'Storico', 'Storico', 'Storico', 'Storico', 'Confermato', 'Piano', 'Piano', 'Piano']
})

# Confronto yield con peers
df_yield_comp = pd.DataFrame({
    'Società': ['INWIT', 'Cellnex', 'American Tower (EU)', 'FTSE MIB', 'Media Infrastrutture EU'],
    'Dividend Yield 2024E (%)': [4.6, 0.0, 3.3, 3.8, 4.1],
    'Nota': ['Include crescita programmata', 'Non distribuisce', 'Mercato diverso', 'Indice generale', 'Media settore']
})

# Dati per il business model (torri e siti)
df_business_metrics = pd.DataFrame({
    'Anno': [2019, 2020, 2021, 2022, 2023, 2024],
    'Numero Torri': [22000, 24000, 24200, 24500, 24800, 25000],  # Stime basate su testo
    'Tenancy Ratio': [1.8, 2.0, 2.1, 2.2, 2.2, 2.3],  # Numero operatori per torre
    'Ricavi per Torre (€K)': [18, 26, 32, 35, 39, 41]  # Ricavo medio per torre
})

# Dati per analisi debito e leverage
df_debt_analysis = pd.DataFrame({
    'Anno': [2019, 2020, 2021, 2022, 2023, 2024],
    'Debito Netto (€M)': [0, 2661.8, 3118.5, 3226.1, 3551.4, 3551.4],
    'EBITDA (€M)': [346.2, 579.5, 659.3, 732.4, 866.9, 930.1],
    'ND/EBITDA': [0.0, 4.6, 4.7, 4.4, 4.1, 3.8],
    'Target ND/EBITDA': [0.0, 5.0, 4.8, 4.5, 4.2, 4.0],  # Target plan
    'Interest Cover': [10.5, 6.2, 10.4, 12.3, 4.9, 4.6]  # EBITDA/Interest
})

# --- Titolo e Header ---
st.title(f"📡 Analisi Dividendi: {NOME_SOCIETA} ({TICKER})")
st.caption(f"Analisi aggiornata al: {datetime.now().strftime('%d/%m/%Y')}. Dati finanziari storici dal 2015, proiezioni fino al 2026 basate sul Piano Industriale.")
st.markdown("---")

# --- Layout CSS Personalizzato ---
st.markdown("""
<style>
.metric-card {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 10px;
    border-left: 5px solid #1f77b4;
    margin: 0.5rem 0;
}
.highlight-box {
    background-color: #e8f4fd;
    padding: 1rem;
    border-radius: 10px;
    border-left: 5px solid #2e86c1;
    margin: 1rem 0;
}
.tower-icon {
    font-size: 2rem;
    color: #1f77b4;
}
</style>
""", unsafe_allow_html=True)

# --- Metriche Chiave Dividendo ---
st.subheader("📊 Indicatori Chiave del Dividendo")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label=f"Ultimo DPS Pagato (Esercizio {ANNO_ULTIMO_DPS})",
        value=f"€ {ULTIMO_DPS_PAGATO_VAL:.3f}",
        help="Dividendo relativo all'esercizio 2023, pagamento maggio 2024."
    )

with col2:
    st.metric(
        label="Dividend Yield (Attuale)",
        value=f"{YIELD_ATTUALE:.1f}%",
        help=f"Basato sull'ultimo DPS (€{ULTIMO_DPS_PAGATO_VAL:.3f}) e prezzo di riferimento €{PREZZO_RIFERIMENTO_APPROX:.1f}."
    )

with col3:
    st.metric(
        label="Politica Dividendi",
        value="7.5% crescita annua",
        delta="Fino al 2026",
        help=f"{POLITICA_PAYOUT}. Dividendo supportato dall'80% del FCF."
    )

with col4:
    st.metric(
        label="CAGR Dividendi (2015-2023)",
        value=f"{DIVIDEND_CAGR_2015_2023:.0f}%",
        help="Crescita composta annua includendo la crescita post IPO e fusione Vodafone."
    )

st.markdown("---")

# --- Sidebar per Navigazione ---
st.sidebar.title("📡 Navigazione INWIT")
sections = {
    "📈 Analisi Dividendi": "dividends",
    "💼 Performance Finanziaria": "performance", 
    "🏗️ Business Model Torri": "business_model",
    "💰 Sostenibilità FCF": "fcf_analysis",
    "🔮 Proiezioni Future": "projections",
    "⚖️ Analisi Debito": "debt_analysis",
    "🆚 Confronto Settore": "peer_comparison",
    "📋 Analisi Completa": "full_analysis",
    "🎯 Conclusioni": "conclusions"
}

selected_section = st.sidebar.selectbox("Seleziona Sezione:", list(sections.keys()))
section_id = sections[selected_section]

# --- Sezione: Analisi Dividendi ---
if section_id == "dividends":
    st.subheader("📈 Evoluzione del Dividendo")
    
    # Layout a 2 colonne
    col1, col2 = st.columns(2)
    
    # GRAFICO 1: Storico DPS - split normale/straordinario
    with col1:
        fig_dps = go.Figure()
        
        # Dividendo ordinario
        fig_dps.add_trace(go.Bar(
            x=df_dps['Anno Esercizio'],
            y=df_dps['DPS Ordinario (€)'],
            name='Dividendo Ordinario',
            marker_color='royalblue',
            text=[f"€{val:.3f}" for val in df_dps['DPS Ordinario (€)']],
            textposition='outside'
        ))
        
        # Dividendo straordinario (solo 2019)
        fig_dps.add_trace(go.Bar(
            x=df_dps['Anno Esercizio'],
            y=df_dps['DPS Straordinario (€)'],
            name='Dividendo Straordinario',
            marker_color='lightblue',
            text=[f"€{val:.3f}" if val > 0 else "" for val in df_dps['DPS Straordinario (€)']],
            textposition='outside'
        ))
        
        fig_dps.add_annotation(
            x=2019, y=0.72,
            text="Fusione<br>Vodafone",
            showarrow=True,
            arrowcolor="green",
            font=dict(size=10),
            ax=20, ay=-40
        )
        
        fig_dps.update_layout(
            title="Dividendo per Azione: Ordinario vs Straordinario (2015-2024)",
            barmode='stack',
            xaxis_title="Anno Esercizio",
            yaxis_title="Dividendo per Azione (€)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig_dps, use_container_width=True)
    
    # GRAFICO 2: Crescita percentuale YoY (ordinario)
    with col2:
        df_growth = df_dps[df_dps['Variazione %'] != 0].copy()
        
        fig_growth = px.bar(
            df_growth,
            x='Anno Esercizio',
            y='Variazione %',
            title="Crescita Percentuale Annua del Dividendo Ordinario",
            text='Variazione %',
            color='Variazione %',
            color_continuous_scale='viridis'
        )
        
        fig_growth.update_traces(texttemplate='%{text:.1f}%', textposition="outside")
        fig_growth.update_layout(
            xaxis_title="Anno",
            yaxis_title="Variazione % Anno su Anno"
        )
        
        # Aggiungi linea target 7.5%
        fig_growth.add_hline(
            y=7.5, 
            line_dash="dash", 
            line_color="red",
            annotation_text="Target: 7.5% annuo"
        )
        
        st.plotly_chart(fig_growth, use_container_width=True)
    
    # Insight box
    st.markdown("""
    <div class="highlight-box">
    <strong>🔍 Key Insights sui Dividendi:</strong>
    <ul>
    <li><strong>Crescita Costante</strong>: Il dividendo ordinario è cresciuto da €0.09 (2015) a €0.48 (2023), con CAGR del 30%</li>
    <li><strong>Straordinario 2019</strong>: €0.59 extra distribuiti grazie alla fusione Vodafone per ottimizzare la struttura</li>
    <li><strong>Policy Chiara</strong>: +7.5% annuo confermato fino al 2026 (DPS atteso €0.555 nel 2025)</li>
    <li><strong>Sostenibilità</strong>: Il payout è coperto dall'80% del FCF, lasciando margine per crescita e deleveraging</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# --- Sezione: Performance Finanziaria ---
elif section_id == "performance":
    st.subheader("💼 Performance Finanziaria")
    
    # GRAFICO: Evoluzione Ricavi e Margini
    col1, col2 = st.columns(2)
    
    with col1:
        fig_revenue = go.Figure()
        
        # Ricavi (barre)
        fig_revenue.add_trace(go.Bar(
            x=df_fin_clean['Anno'],
            y=df_fin_clean['Ricavi (€M)'],
            name='Ricavi',
            marker_color='lightblue',
            text=df_fin_clean['Ricavi (€M)'],
            texttemplate='%{text}M',
            textposition='outside'
        ))
        
        # EBITDA (linea)
        fig_revenue.add_trace(go.Scatter(
            x=df_fin_clean['Anno'],
            y=df_fin_clean['EBITDA (€M)'],
            mode='lines+markers',
            name='EBITDA',
            line=dict(color='green', width=3),
            yaxis='y2'
        ))
        
        fig_revenue.add_annotation(
            x='2020', y=663,
            text="Fusione<br>Vodafone",
            showarrow=True,
            font=dict(color="red"),
            ax=0, ay=-40
        )
        
        fig_revenue.update_layout(
            title="Ricavi ed EBITDA: Impatto Fusione 2020",
            xaxis_title="Anno",
            yaxis_title="Ricavi (€M)",
            yaxis2=dict(
                title="EBITDA (€M)",
                overlaying="y",
                side="right"
            )
        )
        
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    with col2:
        # EBITDA Margin evolution
        fig_margin = px.line(
            df_fin_clean,
            x='Anno',
            y='EBITDA Margin (%)',
            title="Evoluzione EBITDA Margin",
            markers=True,
            text='EBITDA Margin (%)',
            line_shape='spline'
        )
        
        fig_margin.update_traces(
            texttemplate='%{text:.1f}%',
            textposition="top center"
        )
        
        fig_margin.add_hline(
            y=90, 
            line_dash="dash", 
            line_color="orange",
            annotation_text="Target >90%"
        )
        
        fig_margin.update_layout(
            yaxis_title="EBITDA Margin (%)",
            yaxis=dict(range=[80, 95])
        )
        
        st.plotly_chart(fig_margin, use_container_width=True)
    
    # Tabella performance finanziaria
    st.subheader("📊 Dettaglio Performance Finanziaria")
    
    # Preparazione tabella con codice colore
    df_display = df_fin_clean.copy()
    df_display['Ricavi (€M)'] = df_display['Ricavi (€M)'].round(1)
    df_display['EBITDA (€M)'] = df_display['EBITDA (€M)'].round(1)
    df_display['FCF (€M)'] = df_display['FCF (€M)'].round(1)
    
    st.dataframe(
        df_display.set_index('Anno'),
        use_container_width=True,
        column_config={
            "Ricavi (€M)": st.column_config.NumberColumn(
                "Ricavi (€M)",
                help="Ricavi totali annui",
                format="%d"
            ),
            "EBITDA Margin (%)": st.column_config.NumberColumn(
                "EBITDA Margin (%)",
                help="Margine EBITDA",
                format="%.1f%%"
            ),
            "DPS (€)": st.column_config.NumberColumn(
                "DPS (€)",
                help="Dividendo per azione",
                format="%.3f"
            )
        }
    )

# --- Sezione: Business Model Torri ---
elif section_id == "business_model":
    st.subheader("🏗️ Business Model: Tower as a Service")
    
    # Metriche chiave del business
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig_torri = px.bar(
            df_business_metrics,
            x='Anno',
            y='Numero Torri',
            title="Evoluzione Numero Torri Gestite",
            text='Numero Torri',
            color='Numero Torri',
            color_continuous_scale='Blues'
        )
        fig_torri.update_traces(texttemplate='%{text:,}', textposition="outside")
        st.plotly_chart(fig_torri, use_container_width=True)
    
    with col2:
        fig_tenancy = px.line(
            df_business_metrics,
            x='Anno',
            y='Tenancy Ratio',
            title="Tenancy Ratio (Operatori per Torre)",
            markers=True,
            text='Tenancy Ratio'
        )
        fig_tenancy.update_traces(texttemplate='%{text:.1f}x', textposition="top center")
        fig_tenancy.add_hline(y=2.5, line_dash="dash", line_color="green", annotation_text="Obiettivo 2026")
        st.plotly_chart(fig_tenancy, use_container_width=True)
    
    with col3:
        fig_arpu = px.bar(
            df_business_metrics,
            x='Anno',
            y='Ricavi per Torre (€K)',
            title="ARPU per Torre (€K annui)",
            text='Ricavi per Torre (€K)',
            color='Ricavi per Torre (€K)',
            color_continuous_scale='Greens'
        )
        fig_arpu.update_traces(texttemplate='€%{text}K', textposition="outside")
        st.plotly_chart(fig_arpu, use_container_width=True)
    
    # Modello di Business - Infografica
    st.markdown("""
    <div class="highlight-box">
    <h3>🏗️ Modello di Business INWIT</h3>
    <div style="display: flex; align-items: center; margin: 1rem 0;">
        <div style="flex: 1;">
            <h4>📡 Assets Gestiti:</h4>
            <ul>
                <li><strong>~25.000 torri macro</strong> per copertura area</li>
                <li><strong>~8.000 sistemi DAS/small cells</strong> per coverage indoor</li>
                <li>Contratti di 10-15 anni con indicizzazione inflazione</li>
            </ul>
        </div>
        <div style="flex: 1;">
            <h4>💼 Clienti Principali:</h4>
            <ul>
                <li><strong>TIM + Vodafone</strong>: ~70% ricavi (azionisti)</li>
                <li><strong>WindTre + Iliad</strong>: ~25% ricavi</li>
                <li><strong>Altri operatori</strong>: crescita attesa</li>
            </ul>
        </div>
    </div>
    <p><strong>💰 Economia del Modello:</strong> Ogni nuovo tenant su torre esistente genera ~95% di marginalità (costi aggiuntivi minimi)</p>
    </div>
    """, unsafe_allow_html=True)

# --- Sezione: Sostenibilità FCF ---
elif section_id == "fcf_analysis":
    st.subheader("💰 Sostenibilità del Free Cash Flow")
    
    # GRAFICO: FCF vs Dividendi Pagati
    col1, col2 = st.columns(2)
    
    with col1:
        # Calcolo dividendi totali pagati (approssimazione con 960M azioni)
        df_fcf_analysis = pd.DataFrame({
            'Anno': [2019, 2020, 2021, 2022, 2023, 2024],
            'FCF (€M)': [237, 397, 49, 432, 512, 469],
            'Dividendi Totali (€M)': [
                0.13 * 600,  # 2019 ordinario
                0.30 * 870,  # 2020
                0.32 * 960,  # 2021
                0.35 * 960,  # 2022
                0.48 * 956,  # 2023
                0.48 * 937   # 2024
            ]
        })
        
        df_fcf_analysis['Copertura FCF'] = df_fcf_analysis['FCF (€M)'] / df_fcf_analysis['Dividendi Totali (€M)']
        df_fcf_analysis['Dividendi Totali (€M)'] = df_fcf_analysis['Dividendi Totali (€M)'].round(0)
        
        fig_fcf = go.Figure()
        fig_fcf.add_trace(go.Bar(
            x=df_fcf_analysis['Anno'],
            y=df_fcf_analysis['FCF (€M)'],
            name='Free Cash Flow',
            marker_color='blue',
        ))
        fig_fcf.add_trace(go.Bar(
            x=df_fcf_analysis['Anno'],
            y=df_fcf_analysis['Dividendi Totali (€M)'],
            name='Dividendi Pagati',
            marker_color='green',
        ))
        fig_fcf.add_trace(go.Scatter(
            x=df_fcf_analysis['Anno'],
            y=df_fcf_analysis['Copertura FCF'] * 100,
            mode='lines+markers+text',
            name='Copertura FCF (x)',
            yaxis='y2',
            line=dict(color='red'),
            text=df_fcf_analysis['Copertura FCF'].round(1),
            textposition="top center"
        ))
        
        fig_fcf.update_layout(
            title="Free Cash Flow vs Dividendi Distribuiti",
            barmode='group',
            xaxis_title="Anno",
            yaxis_title="Milioni €",
            yaxis2=dict(
                title="Copertura FCF (volte)",
                overlaying="y",
                side="right",
                range=[0, 6]
            )
        )
        
        st.plotly_chart(fig_fcf, use_container_width=True)
    
    with col2:
        # Payout ratio analysis
        fig_payout = px.line(
            df_payout,
            x='Anno',
            y='Payout Ratio EPS (%)',
            title="Payout Ratio su EPS (%)",
            markers=True,
            text='Payout Ratio EPS (%)'
        )
        
        fig_payout.update_traces(texttemplate='%{text:.0f}%', textposition="top center")
        fig_payout.add_hline(y=80, line_dash="dash", line_color="orange", annotation_text="Target: ~80% FCF")
        fig_payout.update_layout(yaxis=dict(range=[0, 200]))
        
        st.plotly_chart(fig_payout, use_container_width=True)
    
    # Stress test dividendi
    st.subheader("🧪 Stress Test: Sostenibilità Dividendo")
    
    scenarios = {
        'Scenario': ['Base Case', 'FCF -10%', 'FCF -20%', 'FCF -30%'],
        'FCF 2024 (€M)': [469, 422, 375, 328],
        'Dividendi Totali (€M)': [450, 450, 450, 450],
        'Copertura': [1.04, 0.94, 0.83, 0.73],
        'Sostenibilità': ['✅ Sostenibile', '⚠️ Limite', '❌ Non Sostenibile', '❌ Non Sostenibile']
    }
    
    df_stress = pd.DataFrame(scenarios)
    st.dataframe(df_stress, use_container_width=True)
    
    st.info("""
    **💡 Analisi Stress Test:**
    - **Scenario Base**: FCF copre comodamente i dividendi (1.04x)
    - **FCF -10%**: Ancora sostenibile ma con margine ridotto
    - **FCF -20%**: Richiederebbe attingere da cassa o ridurre buyback
    - **FCF -30%**: Scenario estremo che potrebbe richiedere revisione politica dividendi
    """)

# --- Sezione: Proiezioni Future ---
elif section_id == "projections":
    st.subheader("🔮 Proiezioni Dividendi e Performance")
    
    # Grafico proiezioni dividendi
    fig_proj = px.line(
        df_dps_projection,
        x='Anno',
        y='DPS (€)',
        title="Dividendo per Azione: Storico e Proiezioni (2015-2027)",
        markers=True,
        text='DPS (€)',
        color='Tipo',
        color_discrete_map={'Storico': 'blue', 'Confermato': 'green', 'Piano': 'orange'}
    )
    
    fig_proj.update_traces(texttemplate='€%{text:.3f}', textposition="top center")
    
    # Aggiungi area evidenziata per periodo piano industriale
    fig_proj.add_vrect(
        x0=2023.5, x1=2027.5,
        fillcolor="lightgreen", opacity=0.2,
        line_width=0
    )
    
    fig_proj.add_annotation(
        x=2025.5, y=0.58,
        text="Piano Industriale<br>+7.5% annuo",
        showarrow=True,
        arrowcolor="green",
        font=dict(size=12),
        ax=0, ay=-40
    )
    
    fig_proj.update_layout(
        xaxis_title="Anno",
        yaxis_title="Dividendo per Azione (€)"
    )
    
    st.plotly_chart(fig_proj, use_container_width=True)
    
    # Proiezioni finanziarie
    st.subheader("📊 Proiezioni Finanziarie (Piano Industriale)")
    
    # Dati proiezioni (dal piano industriale)
    df_projections = pd.DataFrame({
        'Metrica': [
            'Ricavi (€M)',
            'EBITDA (€M)', 
            'EBITDA Margin (%)',
            'Free Cash Flow (€M)',
            'Net Debt/EBITDA',
            'DPS (€)',
            'Dividend Yield (%)'
        ],
        '2024E': [1036, 930, 89.8, 469, 3.8, 0.48, 4.6],
        '2025E': [1120, 1010, 90.2, 630, 3.5, 0.516, 4.8],
        '2026E': [1210, 1100, 90.9, 700, 3.2, 0.555, 5.0],
        'CAGR 24-26': ['8.1%', '8.7%', '+109bps', '22.0%', 'Miglioramento', '7.5%', 'Stabile']
    })
    
    st.dataframe(df_projections.set_index('Metrica'), use_container_width=True)
    
    # Key drivers crescita
    st.markdown("""
    <div class="highlight-box">
    <h3>🚀 Key Drivers del Piano 2024-2026:</h3>
    <ol>
    <li><strong>Crescita Organica</strong>: +500 nuovi siti, focus su 5G densification</li>
    <li><strong>Aumento Tenancy Ratio</strong>: da 2.2x a 2.3x (più operatori per torre)</li>
    <li><strong>Efficienze Operative</strong>: Acquisto terreni (-€40M/anno affitti), ottimizzazione energetica</li>
    <li><strong>Espansione DAS</strong>: +2000 unità remote, focus indoor/smart city</li>
    <li><strong>Deleveraging</strong>: Da 4.1x a 3.2x Net Debt/EBITDA</li>
    </ol>
    <p><strong>💰 Target Finanziari:</strong> FCF cumulato €1.8B nel 2024-2026, dividendi cumulati €1.5B</p>
    </div>
    """, unsafe_allow_html=True)

# --- Sezione: Analisi Debito ---
elif section_id == "debt_analysis":
    st.subheader("⚖️ Analisi del Debito e Leva Finanziaria")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Evoluzione Net Debt/EBITDA
        fig_leverage = go.Figure()
        
        fig_leverage.add_trace(go.Scatter(
            x=df_debt_analysis['Anno'],
            y=df_debt_analysis['ND/EBITDA'],
            mode='lines+markers',
            name='ND/EBITDA Effettivo',
            line=dict(color='red', width=3),
            marker=dict(size=10)
        ))
        
        fig_leverage.add_trace(go.Scatter(
            x=df_debt_analysis['Anno'],
            y=df_debt_analysis['Target ND/EBITDA'],
            mode='lines+markers',
            name='Target ND/EBITDA',
            line=dict(color='green', width=2, dash='dash')
        ))
        
        fig_leverage.update_layout(
            title="Evoluzione Leverage: Net Debt/EBITDA",
            xaxis_title="Anno",
            yaxis_title="Net Debt/EBITDA (x)",
            yaxis=dict(range=[0, 5.5])
        )
        
        fig_leverage.add_annotation(
            x=2020, y=4.6,
            text="Post-Fusione<br>Vodafone",
            showarrow=True,
            ax=20, ay=-30
        )
        
        st.plotly_chart(fig_leverage, use_container_width=True)
    
    with col2:
        # Interest coverage
        fig_coverage = px.bar(
            df_debt_analysis,
            x='Anno',
            y='Interest Cover',
            title="Interest Coverage (EBITDA/Interessi)",
            text='Interest Cover',
            color='Interest Cover',
            color_continuous_scale='RdYlGn'
        )
        
        fig_coverage.update_traces(texttemplate='%{text:.1f}x', textposition="outside")
        fig_coverage.add_hline(y=4, line_dash="dash", line_color="orange", annotation_text="Soglia Prudenziale")
        
        st.plotly_chart(fig_coverage, use_container_width=True)
    
    # Struttura del debito
    st.subheader("💳 Struttura del Debito")
    
    debt_structure = {
        'Strumento': ['Bond 2026', 'Bond 2028', 'Term Loan', 'Leasing IFRS16'],
        'Import (€M)': [750, 1000, 1000, 1000],
        'Tasso (%)': [1.875, 2.375, 'EURIBOR + 150bps', 'N/A'],
        'Scadenza': ['2026', '2028', '2025', 'Varie'],
        'Note': ['Fisso', 'Fisso', 'Variabile', 'Affitti capitalizzati']
    }
    
    st.dataframe(pd.DataFrame(debt_structure), use_container_width=True)
    
    st.info("""
    **📊 Analisi Struttura Debito:**
    - **Costo Medio**: ~2.0% grazie ai bond fissi sottoscritti nel 2020
    - **Duration**: Scadenze ben distribuite, prossimo rifinanziamento significativo nel 2025-2026  
    - **Covenant**: Net Debt/EBITDA <7.5x (ampio headroom rispetto a 3.8x attuale)
    - **Rating**: BBB- da Fitch, outlook stabile (investment grade)
    """)

# --- Sezione: Confronto con Settore ---
elif section_id == "peer_comparison":
    st.subheader("🆚 Confronto con Settore e Peers")
    
    # Confronto dividend yield
    fig_yield_comp = px.bar(
        df_yield_comp,
        x='Società',
        y='Dividend Yield 2024E (%)',
        title="Confronto Dividend Yield con Peers (2024E)",
        text='Dividend Yield 2024E (%)',
        color='Dividend Yield 2024E (%)',
        color_continuous_scale='Viridis',
        hover_data=['Nota']
    )
    
    fig_yield_comp.update_traces(texttemplate='%{text:.1f}%', textposition="outside")
    fig_yield_comp.update_layout(xaxis_title="", yaxis_title="Dividend Yield (%)")
    
    st.plotly_chart(fig_yield_comp, use_container_width=True)
    
    # Tabella confronto multipli
    st.subheader("📈 Confronto Multipli di Valutazione")
    
    multiples_comparison = {
        'Società': ['INWIT', 'Cellnex', 'American Tower (US)', 'Vantage Towers', 'Media Settore'],
        'EV/EBITDA 2024E': [15.0, 14.2, 21.5, 12.8, 16.0],
        'P/E 2024E': [23.5, 'N/A', 32.0, 18.5, 25.0],
        'Dividend Yield (%)': [4.6, 0.0, 3.3, 0.0, 2.8],
        'Net Debt/EBITDA': [3.8, 4.0, 5.5, 3.2, 4.1],
        'Geografie': ['Italia', 'Europa', 'Globale', 'Europa', '']
    }
    
    df_multiples = pd.DataFrame(multiples_comparison)
    
    st.dataframe(
        df_multiples,
        use_container_width=True,
        column_config={
            "EV/EBITDA 2024E": st.column_config.NumberColumn(
                "EV/EBITDA 2024E",
                help="Enterprise Value / EBITDA",
                format="%.1fx"
            ),
            "Dividend Yield (%)": st.column_config.NumberColumn(
                "Dividend Yield (%)",
                help="Rendimento dividendi",
                format="%.1f%%"
            ),
            "Net Debt/EBITDA": st.column_config.NumberColumn(
                "Net Debt/EBITDA",
                help="Leva finanziaria",
                format="%.1fx"
            )
        }
    )
    
    # Posizionamento competitivo
    st.markdown("""
    <div class="highlight-box">
    <h3>🏁 Posizionamento Competitivo INWIT:</h3>
    <div style="display: flex; gap: 2rem;">
        <div style="flex: 1;">
            <h4>✅ Punti di Forza:</h4>
            <ul>
                <li><strong>Dividend Yield Leader</strong>: Unica towerco europea che privilegia dividendi</li>
                <li><strong>Margini Superiori</strong>: EBITDA margin ~90% vs media 85-87%</li>
                <li><strong>Posizione Monopolistica</strong>: #1 in Italia con 25k torri</li>
                <li><strong>Clienti Stabili</strong>: TIM/Vodafone azionisti e co-anchor tenant</li>
            </ul>
        </div>
        <div style="flex: 1;">
            <h4>⚠️ Sfide:</h4>
            <ul>
                <li><strong>Concentrazione Geografica</strong>: Solo Italia vs competitors paneuropei</li>
                <li><strong>Leverage Elevata</strong>: ~4x vs alcuni peer a ~3x</li>
                <li><strong>Size Premium</strong>: Più piccola di American Tower/Cellnex</li>
                <li><strong>Rifinanziamenti</strong>: Bond in scadenza 2025-2026</li>
            </ul>
        </div>
    </div>
    </div>
    """, unsafe_allow_html=True)

# --- Sezione: Analisi Completa ---
elif section_id == "full_analysis":
    st.subheader("📋 Analisi Completa di INWIT")
    
    # Caricamento del contenuto dall'analisi completa
    analysis_content = """
Executive Summary
INWIT (Infrastrutture Wireless Italiane, ticker INW), principale gestore di torri per telecomunicazioni mobile in Italia, presenta un profilo finanziario solido orientato al rendimento da dividendo. L'azienda, nata dallo spin-off torri TIM nel 2015 e fusa con le torri Vodafone nel 2020, eroga un dividendo in costante crescita (+7,5% annuo guidato fino al 2026) con un rendimento attuale ~4,5%, superiore alla media del FTSE MIB (~3,8%). La crescita dei flussi di cassa operativi (FCF ricorrente 2023 ~€611 mln) e la natura essenziale dei suoi servizi sostengono la stabilità e qualità del dividendo, coperto ~75% dal FCF. INWIT opera con contratti di lungo termine indicizzati all'inflazione e un portafoglio clienti concentrato sugli operatori mobili principali (TIM, Vodafone come anchor tenant), con un elevato tenancy ratio (2,16x al 2022) indice di infrastrutture ampiamente condivise.
Nonostante un leva finanziaria significativa (Indebitamento Fin. Netto/EBITDA ~4,7x) dovuta all'acquisizione delle torri Vodafone e ad un modello asset-heavy, la generazione di cassa è forte e resiliente, con margini EBITDA ~91% e margini EBITDAaL (post costi locativi) ~69% in miglioramento. Il piano industriale al 2026 (esteso al 2030) prevede investimenti mirati (€1,3 mld nel 2021-26) per sfruttare trend strutturali: crescita del traffico dati mobile, diffusione del 5G e densificazione di reti (DAS, small cells), consolidando così i ricavi con crescita "high single-digit" annua fino al 2026. Sul decennio, INWIT offre un profilo di rendimento totale attraente per l'investitore orientato al dividendo: l'analisi base prospetta un Total Shareholder Return (TSR) annuo medio nell'ordine del 7-9% (4-5% da dividendi + 3-4% crescita), con scenari ottimistici che potrebbero superare il 10% annuo.

1. Descrizione Aziendale
INWIT S.p.A. è la maggiore tower company italiana, con ~24.500 torri di telecomunicazione wireless e ~8.000 sistemi DAS/small cells distribuiti sul territorio nazionale. Fondata nel 2015 da Telecom Italia, la società è quotata alla Borsa di Milano (FTSE MIB dal 2020). Nel marzo 2020 INWIT ha incorporato Vodafone Towers Italia, raddoppiando dimensione e asset in gestione. Il core business consiste nell'hosting "Tower as a Service": INWIT realizza e gestisce infrastrutture passive (torri, tralicci, pali, siti indoor) affittandone spazio e servizi agli operatori mobili e altri broadcaster, in ottica multi-operatore neutrale. I ricavi provengono da contratti di lungo periodo con canoni periodici indicizzati all'inflazione (spesso con durata decennale rinnovabile), garantendo alta visibilità sul fatturato futuro. I clienti principali (≈80% dei ricavi) sono TIM e Vodafone (soci fondatori) con cui INWIT ha accordi pluriennali di servizio, seguiti dagli altri operatori mobili OLO (WindTre, Iliad) e da utilizzatori wholesale (FWA, IoT, enti radiotelevisivi).

Il modello di business beneficia di forti economie di scala e di margini elevati: aggiungere nuovi tenant su una torre esistente comporta costi marginali ridotti, traducendosi in crescita quasi interamente incrementale dell'EBITDA. Ciò si riflette in un EBITDA margin 2022 ~91% (EBITDAaL ~69%), uno dei più alti in Europa. INWIT presenta inoltre capex relativamente contenuti (tipicamente 15-20% dei ricavi) focalizzati sull'espansione del portafoglio siti e sul miglioramento tecnologico (es. upgrade energetici, acquisto terreni). Ne consegue un robusto Free Cash Flow operativo (€491 mln ricorrente nel 2022, +34% YoY), che sostiene politiche di remunerazione agli azionisti attrattive. Dal 2020 la società distribuisce l'intero FCF disponibile tra dividendi e buyback, in linea con il posizionamento di "infrastructure yield company". La struttura finanziaria è caratterizzata da un indebitamento significativo ma efficiente, con costi medi del debito ~1.7% e duration pluriennale (grazie a due emissioni obbligazionarie per €1,75 mld nel 2020). INWIT opera con ~320 dipendenti e ha sede legale a Milano, uffici a Roma.

2. Management & Governance
Struttura azionaria. INWIT ha un capitale diffuso ma con due azionisti di riferimento: (1) Central Tower Holding Company B.V. detiene ~33,17% del capitale, ed è indirettamente co-controllata da Vodafone Group (via Vodafone GmbH) e dal consorzio Oak (KKR, GIP) – frutto della partnership avviata da Vodafone nel 2020 per la gestione congiunta delle torri; (2) Daphne 3 S.p.A. detiene ~29,9% del capitale, controllata al 90% dal consorzio Ardian (Impulse I) e 10% da Telecom Italia (TIM). Il flottante risulta ~37% (circa 355 milioni di azioni) diffuso tra investitori istituzionali internazionali. Questa composizione crea una situazione di controllo congiunto bilanciato: Vodafone/Oak e Ardian/TIM esprimono ciascuno 4 consiglieri nel CdA (su 11), mentre 3 consiglieri provengono da liste di minoranza indipendenti. Non vi è dunque un azionista unico di maggioranza, e i patti parasociali originali tra TIM e Vodafone sono decaduti dopo l'uscita di TIM dal controllo (2022). Ciò garantisce un governo societario equilibrato, con tutela dei soci di minoranza tramite rappresentanti indipendenti e comitati interni.

Consiglio di Amministrazione e vertici. Il CdA nominato ad ottobre 2022 è presieduto da Oscar Cicchetti (Presidente non esecutivo, già dirigente TIM), espresso dall'azionista Ardian. Il ruolo di Chief Executive è di fatto ricoperto dal Direttore Generale Diego Galli, già CFO, cui sono delegate tutte le funzioni esecutive di gestione ordinaria. La scelta di un DG invece di un Amministratore Delegato formalmente nominato riflette l'accordo tra i soci per un assetto condiviso: secondo fonti Reuters il CEO precedente Giovanni Ferigo (proveniente da TIM) si è dimesso nel 2022 in seguito al riassetto proprietario, e si era previsto di selezionare un nuovo AD indicato da Vodafone, ma in assenza di un candidato esterno è stato promosso Galli come DG. Il CDA include inoltre figure di alto profilo come Sonia Hernandez (manager Vodafone) e consiglieri indipendenti qualificati in materie finanziarie e ESG.

3. Piano Industriale & Strategia
Linee strategiche 2023-2026: Il management ha confermato e aggiornato il piano industriale al 2026, proiettando crescita organica robusta grazie a trend strutturali favorevoli nel settore tower. In particolare, INWIT punta a: (a) Espansione del portafoglio siti – incremento di ~500 nuovi siti macro nei 4 anni 2023-26 (circa +2% annuo, portando le torri da ~23.000 a ~25.000), concentrati in aree strategiche per colmare gap di copertura 4G/5G e rispondere a progetti di densificazione urbana; (b) Aumento dei tenants per torre – proseguire l'aggiunta di nuovi hostings da parte di altri operatori ("OLO") sulle infrastrutture esistenti: si prevedono oltre 4.000 nuovi apparati installati all'anno, con focus su Iliad e Fastweb (FWA) come driver principali, elevando il tenancy ratio oltre l'attuale 2,16x verso ~2,3x nel 2026 (tra i più alti in Europa); (c) Coperture dedicate indoor e small cells – accelerare il dispiegamento di sistemi DAS (Distributed Antenna Systems) e micro-celle per fornire copertura in luoghi ad alta concentrazione di utenti (stadi, stazioni, ospedali, centri storici): il piano vede +2.000 unità remote DAS aggiuntive entro il 2026 (+~50%), intercettando la domanda crescente di connettività in spazi indoor e supportando iniziative "Smart City" (es. smart transportation); (d) Efficienza e controllo costi – implementare un importante programma di riduzione dei costi locativi: INWIT sta ri-negoziando i contratti d'affitto dei terreni e acquistando le proprietà di siti strategici per abbattere gli affitti passivi (oltre 2.000 terreni già acquisiti a fine 2022). Parallelamente, investe in infrastrutture energetiche proprietarie (es. installazione di pannelli solari e sistemi di alimentazione intelligente) per contenere i costi energetici e aumentare l'autosufficienza.

Obiettivi finanziari: Il piano 2023-26 prevede ricavi in aumento del "high single-digit" medio annuo, superando €1,2 mld nel 2026 (da €853 mln nel 2022). L'EBITDA è atteso in crescita analoga (~+8-9% a €~0,92 mld nel 2026), con EBITDA margin stabile >91% e EBITDAaL in crescita ~11% annuo (a €~0,65-0,70 mld nel 2026) grazie alle efficienze. La Recurring Free Cash Flow (RFCF) dovrebbe salire a ~€680-700 mln nel 2026 (da €491 mln 2022), beneficiando anche di un regime fiscale agevolato temporaneo. Di conseguenza, la politica dividendi – che prevede DPS in aumento +7,5% annuo – è confermata fino al 2026 e già incorporata nei target.

4. Outlook Macroeconomico & Tassi
Il contesto macroeconomico italiano ed europeo costituisce un fattore chiave per valutare INWIT, data la sensibilità delle utility infrastrutturali a inflazione e tassi di interesse. Crescita economica: l'economia italiana mostra un ritmo moderato: dopo il rimbalzo post-pandemia (+6,6% PIL 2021), il PIL è rallentato a +3,7% nel 2022 e ~+0,7% stimato nel 2023, con previsione ~+1,1% nel 2024. Una crescita debole del PIL non incide direttamente sulla domanda di torri (trainata più da trend tecnologici che dal ciclo economico), ma può riflettersi sulla salute finanziaria degli operatori TLC.

Inflazione: l'area Euro e l'Italia hanno visto un picco inflattivo nel 2022 (Italia IPC +8,7%) seguito da una gradual discesa (~5,5% nel 2023, attesa ~2-3% 2024-25). Per INWIT l'inflazione ha effetti positivi sui ricavi, grazie agli adeguamenti contrattuali annuali: la maggior parte dei canoni d'affitto torre è indicizzata (tipicamente all'ISTAT FOI) garantendo protezione. Al contempo, l'inflazione aumenta alcuni costi operativi (energia, affitti terreni – per questo INWIT sta acquistando i terreni per bloccare costi). Nel complesso l'azienda è relativamente inflation-hedged, con contratti "inflation-linked" che offrono protezione e supporto alla crescita anche in scenari inflattivi elevati.

Tassi di interesse e mercati finanziari: Il drastico aumento dei tassi BCE dal 2022 (tasso depositi da -0,5% a +3,75% attuale) ha avuto un impatto significativo sul settore delle infrastrutture e su INWIT. Da un lato, il costo opportunità del capitale per gli investitori è salito: i titoli infrastrutturali a rendimento (bond proxy) hanno subito un repricing al ribasso dei multipli, perché i rendimenti obbligazionari concorrenti (es. BTP decennali ~4,2%) si sono avvicinati ai dividend yield equity. Ciò spiega la performance azionaria piatta/negativa di INWIT 2021-2022, nonostante i solidi fondamentali, a fronte di tassi in rapida crescita. Dall'altro lato, il costo del debito di INWIT è destinato ad aumentare gradualmente: la società ha finanziamenti a tasso fisso molto vantaggiosi, che proteggono nel breve; ma nuove emissioni o rifinanziamenti futuri avverranno a tassi superiori.

5. Analisi PESTEL
Politico: il settore delle telecomunicazioni è strategico in Italia e soggetto a attenzione governativa. La stabilità politica del Paese influisce relativamente poco sul core business di INWIT, ma il Governo può intervenire tramite Golden Power o politiche industriali. Il quadro politico attuale (Governo pro-impresa) è favorevole a investimenti digitali e alla condivisione di infrastrutture, con piani di incentivi (PNRR) per colmare il digital divide che indirettamente beneficiano i tower operator.

Economico: coperto nella sezione precedente, il contesto economico incide via tassi, inflazione e salute dei clienti telco. L'andamento del settore telecom (ricavi degli MNO in calo da anni in Italia per forte competizione sui prezzi) può condizionare il potere contrattuale: gli operatori, sotto pressione, cercano di ridurre i costi di rete appoggiandosi a towerco come INWIT.

Sociale: INWIT opera in un ambito con implicazioni sociali rilevanti. Da un lato, la società contribuisce positivamente allo sviluppo digitale del Paese: le sue infrastrutture abilitano copertura mobile avanzata, riducono il digital divide nelle aree rurali. D'altro canto, esiste una sensibilità pubblica sul tema elettrosmog e installazione di antenne: opposizioni locali (NIMBY) possono rallentare autorizzazioni di nuovi siti a causa di timori per la salute.

Tecnologico: l'evoluzione tecnologica è un fattore chiave. 5G e oltre: la diffusione del 5G richiede una rete di siti più densa (soprattutto in città e per frequenze alte), spingendo domanda di DAS/small cells – opportunità per INWIT. Allo stesso tempo, tecnologie come il network sharing attivo (condivisione della rete radio tra operatori) potrebbero ridurre la necessità di torri duplicate.

Ambientale: l'impatto ambientale e le politiche "green" assumono rilievo crescente. Le torri di INWIT hanno un impatto ambientale diretto relativamente limitato, ma l'azienda ha definito un piano di sostenibilità ambientale ambizioso. Consumo energetico: i siti attivi consumano elettricità per apparati e condizionamento; INWIT ha aumentato al 69% la quota di energia da fonti rinnovabili (2021) e mira al 100% rinnovabile in breve.

Legale e Regolatorio: INWIT opera in un quadro regolamentare relativamente favorevole, poiché le attività di tower leasing non sono sottoposte a tariffazione regolata dall'AGCOM. Un importante fronte legale è l'ottenimento dei permessi per nuove installazioni: la burocrazia italiana può dilatare i tempi. Il D.L. Semplificazioni ha snellito alcune procedure per impianti di comunicazione, ma restano possibili ricorsi locali.

6. Analisi delle 5 Forze di Porter
Il settore di riferimento è quello delle infrastrutture di telecomunicazione passiva (torri), con caratteristiche assimilabili a una struttura duopolistica in Italia (INWIT e Cellnex come principali operatori).

1. Rivalità tra concorrenti: Moderata. In Italia operano due grandi towerco multi-cliente: INWIT e Cellnex. La rivalità diretta è attenuata dal fatto che le torri sono asset localizzati: spesso INWIT e Cellnex dispongono di siti diversi in diverse aree, ciascuno ereditato dai propri operatori originari. Tuttavia, vi è concorrenza per nuove locazioni.

2. Minaccia di nuovi entranti: Bassa. Avviare un nuovo towerco richiederebbe ingenti capitali e tempi lunghi. Il mercato è già quasi saturo: gli MNO hanno ceduto la quasi totalità delle torri esistenti ai due player dominanti. Un potenziale nuovo entrante potrebbe essere un fondo infrastrutturale acquisendo un portafoglio piccolo oppure costruendo torri greenfield.

3. Potere contrattuale dei fornitori: Basso. I "fornitori" critici per INWIT includono i proprietari dei terreni dove sorgono le torri – INWIT paga affitti annuali; e i fornitori di apparati e servizi. I landlords sono spesso piccoli proprietari o enti locali: individualmente non hanno grande potere.

4. Potere contrattuale dei clienti: Medio-Alto. I clienti di INWIT sono pochi e grandi – i 4 operatori mobili nazionali rappresentano la stragrande maggioranza del fatturato (TIM e Vodafone ~70% combinato). Ciò conferisce ai clienti un certo potere, mitigato però da contratti di lungo termine e costo/complessità di switch.

5. Minacce di prodotti sostitutivi: Basse nel core business. Il "prodotto" di INWIT – ospitalità di antenne su siti elevati con copertura radioelettrica – ha pochi sostituti efficaci. Per coprire il territorio con segnali radio occorrono infrastrutture fisiche in posizione elevata.

7. Andamento Storico dei Dividendi
INWIT presenta una storia di dividendi in crescita costante, un aspetto chiave per gli investitori orientati al reddito. Dalla IPO nel 2015, la società ha incrementato il dividendo ordinario ogni anno (CAGR 2015-2023 ~30%, inclusi effetti straordinari).

Storico Dividendi INWIT (€/azione):
• 2015: €0,09
• 2016: €0,15
• 2017: €0,19
• 2018: €0,21
• 2019: €0,13 ordinario + €0,59 straordinario
• 2020: €0,30
• 2021: €0,32
• 2022: €0,35
• 2023: €0,48

Come si evince, prima del 2019 l'azienda incrementava il dividendo ~€0,02/anno, mantenendo un payout prudente (~80% utili). Nel 2019, in concomitanza con la fusione Vodafone (e l'incasso di un conguaglio in cash), è stato erogato un corposo dividendo straordinario €0,5936 ad azione attingendo a riserve. Dal 2020 in poi, INWIT ha adottato una dividend policy formale: DPS in crescita annua +7,5% per il 2021-2023, rinnovata e aumentata per il 2023-2026.

8. Performance Finanziaria (ultimi 5 anni)
INWIT ha registrato negli scorsi 5 anni una crescita trasformativa, passando da medie dimensioni pre-fusione (2019) a uno dei leader europei del settore torri post integrazione (2020+).

Tabella 1 – Conto Economico & Cash Flow 2019-2023:
• 2019: Ricavi €395,4M, EBITDA €349,8M (88,5%), Utile Netto €139,3M, FCF ~€156,7M
• 2020: Ricavi €663,4M, EBITDA €603,8M (91,0%), Utile Netto €156,7M, FCF €271,8M
• 2021: Ricavi €785,1M, EBITDA €714,9M (91,1%), Utile Netto €191,4M, FCF €366,5M
• 2022: Ricavi €853,0M, EBITDA €779,2M (91,3%), Utile Netto €293,3M, FCF €491,4M
• 2023: Ricavi €960,3M, EBITDA €877,0M (91,3%), Utile Netto €339,0M, FCF €611,0M

Nel 2020 i ricavi ed EBITDA sono quasi raddoppiati per l'ampliamento del perimetro (fusione Vodafone Towers). Dal 2021, consolidato il perimetro, i ricavi hanno accelerato: +4,6% like-for-like nel 2021, poi +8,6% nel 2022 e +10% stimato nel 2023. L'EBITDA ha seguito dinamica simile, con margini leggermente in aumento grazie a sinergie e cost control. L'utile netto ha mostrato un trend anomalo: relativamente piatto 2019-21, poi in forte crescita nel 2022 a €293M (+53%) principalmente per minori imposte.

9. Valutazione
Multipli di mercato attuali: Alla luce dei risultati 2024 appena pubblicati, il titolo INWIT quota intorno a €10,4/azione (maggio 2025) per una capitalizzazione di mercato ~€9,8 miliardi.
• Prezzo/Utile (P/E) TTM ~23,5x
• EV/EBITDA 2024 ~15x
• Prezzo/Valore Contabile (P/B) ~2,4x
• Rapporto Debito Netto/EBITDA: ~4,7x (IFRS16) a fine Q1 2025

Valutazione assoluta – DCF: Abbiamo effettuato un'Analisi DCF dettagliata in tre scenari per stimare il fair value intrinseco di INWIT. Il cash flow utilizzato è il FCF agli azionisti (FCFE), data la struttura stabile di indebitamento. Principali assunzioni del Scenario Base: crescita ricavi in linea con il piano fino al 2026 (+8% annuo), poi decelera a +4% 2027-30; margini EBITDAaL in progressivo miglioramento; WACC iniziale 5,5%, destinato a scendere leggermente se riduzione leva; g-rate terminale 1,5%.

Sulla base di queste ipotesi, il fair value DCF base risulta intorno a €11,0 per azione, indicando che al prezzo attuale il titolo è leggermente sottovalutato (upside potenziale ~+6%).

10. Scenario & Sensitivity Analysis
Abbiamo sviluppato tre scenari di piano a 10 anni (Base, Pessimistico, Ottimistico):

Scenario Base: ricavi 2025-30 +6% CAGR, EBITDAaL margin sale a 76% nel 2026 e 78% nel 2030, WACC 5,5%. Questo scenario produce FCF stabile ~€630-700M annuo 2025-30, con crescita del dividendo +7,5% fino 2026 poi ~+3% annuo. TSR atteso: ~8% annuo.

Scenario Pessimistico: crescita ricavi dimezzata (3% annuo), WACC più elevato al 6,5%, costi più alti. FCF stagnerebbe intorno €550-580M annui. Nel pessimistico, ipotizziamo eventualmente nessun aumento DPS dopo il 2025 per sicurezza.

Scenario Ottimistico: crescita ricavi sopra attese (7-8% annuo), WACC in calo a 5%, payout simile. FCF potrebbe superare €700M a regime. TSR ottimistico: sui 10 anni potrebbe superare il 10-11% annuo.

11. Regolamentazione & Rischi Normativi
Il mercato torri in Italia, pur concentrato in due operatori, non è strettamente regolato da AGCOM. Un rischio normativo potrebbe sorgere se in futuro INWIT tentasse un'ulteriore concentrazione: ciò probabilmente verrebbe bloccato. L'aspetto cruciale era il limite di esposizione per la popolazione: l'Italia l'ha appena modificato (Aprile 2024) da 6 V/m a 15 V/m – una svolta epocale dopo 20 anni. Per INWIT questo è un coltello a doppio taglio: positivo perché i clienti avranno meno vincoli; negativo perché si riduce il bisogno di installare nuove torri in zone dove l'unico impedimento era il limite.

12. ESG & Sustainability
INWIT ha integrato la sostenibilità ambientale, sociale e di governance (ESG) nella propria strategia. Ambiente: Come discusso, INWIT è impegnata nella riduzione dell'impatto ambientale delle proprie attività. Target di neutralità climatica al 2024, da perseguire con uso 100% energia rinnovabile, investimenti in efficienza e compensazione delle emissioni residue. Sociale: l'organico è passato da 206 a 246 nel 2021, con 51 nuove assunzioni di cui ~50% donne. Governance: 11 membri CdA, di cui la maggioranza indipendenti. È stato adottato un Modello 231 e Codice Etico.

13. Rischi & Catalyst
Rischi principali:
• Rischio di settore (Telecom) – dipendenza dalla salute finanziaria del settore TLC italiano
• Rischio di esecuzione/tecnologico – obiettivi di crescita e investimenti ambiziosi 
• Rischio finanziario – Alto indebitamento, se i tassi salissero ulteriormente
• Rischio regolatorio – eventuali normative restrittive
• Rischio di governance – controllo congiunto potrebbe creare stallo decisionale

Catalizzatori positivi:
• Discesa dei tassi d'interesse: sarebbe il catalizzatore più potente
• Consolidamento tra operatori mobili: può sembrare un rischio ma potrebbe essere un booster
• Operazioni straordinarie su INWIT stessa: circolano voci di takeover
• Nuove fonti di ricavo: edge computing, servizi wholesale
• Miglioramento rating ESG

14. Liquidità & Flottante Azionario
Il titolo INWIT è ampiamente liquido e fa parte dell'indice FTSE MIB, con circa 932 milioni di azioni in circolazione post-buyback (flottante ~37%). La media dei volumi scambiati è elevata: tipicamente 3-4 milioni di azioni al giorno. La composizione del flottante include primari investitori orientati al rendimento: fondi Value e Dividendo e ETF globali.

15. Total Shareholder Return (TSR) comparato
TSR 1 anno: Negli ultimi 12 mesi il titolo INWIT ha registrato una performance positiva, grazie soprattutto ai dividendi. Il TSR 1Y risulta ~+10%.

TSR 3 anni: Consideriamo il periodo maggio 2022 – maggio 2025. TSR 3Y ~+14-15% (equivalente a ~4,5-5% annuo composto). Non un risultato entusiasmante, dovuto al fatto che il punto di partenza (2022) era su valutazioni elevate e poi i tassi hanno frenato il titolo. Tuttavia, ha fatto decisamente meglio del settore torri europeo: Cellnex TSR 3Y ≈ –40%.

TSR 5 anni: Dal maggio 2020 a maggio 2025. Il TSR cumulativo stimato ~+26% totale, ossia ~4,7% annuo composto. Se consideriamo l'intero orizzonte (2015 IPO a oggi): chi investì all'IPO ha oggi un valore + div ~€12,9, cioè +253% totali (oltre 3,5x), ~17% annuo composto, un risultato eccellente.

16. Impatto Fiscale sui Dividendi
Investitori individuali residenti in Italia: I dividendi distribuiti da società italiane quotate sono soggetti ad una imposta sostitutiva fissa del 26%. Dunque la dividend yield netta per un retail domestico su INWIT risulta ~3,4%.

Investitori esteri: I dividendi INWIT distribuiti a soggetti non residenti sono soggetti a ritenuta fiscale italiana del 26% alla fonte, salvo applicazione di trattati contro doppia imposizione. L'Italia ha trattati con molti Paesi che riducono la ritenuta, tipicamente al 15%.

17. Appendice & Metodologia
Fonti dei dati: La presente relazione ha utilizzato dati ufficiali di bilancio e comunicati societari INWIT (Annual Reports 2019-2023, presentazioni risultati trimestrali). Le stime e scenari presentati (DCF, sensitivities) sono elaborazioni originali basate su assunzioni esplicitate.

Metodologia di valutazione: Per la valutazione abbiamo costruito un modello DCF in Excel partendo da ricavi attuali e seguendo il business plan fino al 2026, poi prolungando con ipotesi prudenti al 2035. Il Terminal Value è calcolato con metodo Gordon Growth.

18. Conclusione & Raccomandazione
Alla luce dell'analisi condotta, INWIT emerge come un investimento solido e redditizio per un orizzonte decennale orientato al dividendo. La società combina:
• Dividendi di qualità, in costante crescita e ben coperti dalla generazione di cassa (FCF yield ~6.5% > dividend yield ~4.5%), con impegno formale a incrementare la cedola del 7,5% annuo fino al 2026.
• Modello di business resiliente, ancorato a contratti di lungo termine indicizzati all'inflazione e a un posizionamento di leadership infrastrutturale in un settore con barriere elevate.
• Stabilità finanziaria, nonostante la leva alta: struttura del debito ottimizzata e calo progressivo del leverage, margini altissimi (EBITDA >91%) e costi sotto controllo.
• Prospettive di crescita moderate ma concrete, trainate dalla transizione 5G e dalla domanda di connettività ubiqua.

Pertanto, la raccomandazione finale è di ACCUMULARE/HOLD con bias positivo (equivalente ad un Outperform per investitori income): INWIT rappresenta una valida componente core di portafoglio a reddito, adatta a sostenere un cash yield stabile e crescente nel tempo. Il titolo ha un fair value stimato intorno a €11-12 in scenario normale, con upside nel medio termine in caso di compressione dei rendimenti obbligazionari o ulteriori efficienze oltre piano.
"""
    
    # Parse delle sezioni principali
    sections = re.split(r'\n(?=Executive Summary|\d+\. )', analysis_content)
    sections = [s.strip() for s in sections if s.strip()]
    
    # CSS per styling ottimale
    st.markdown("""
    <style>
    .analysis-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
        font-size: 16px;
        line-height: 1.6;
    }
    .section-title {
        color: #1f77b4;
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 1rem;
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 0.5rem;
    }
    .highlight-section {
        background-color: #e7f3ff;
        border-left: 5px solid #2e86ab;
    }
    .key-points {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .metric-highlight {
        background-color: #e8f5e9;
        padding: 0.5rem;
        border-radius: 5px;
        display: inline-block;
        margin: 0.2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Crea tabs per le sezioni principali
    tab_names = ["Executive Summary & Overview", "Business & Strategy", "Analisi Finanziaria", "Valutazione & Scenari", "Rischi & Opportunità", "Governance & ESG"]
    tabs = st.tabs(tab_names)
    
    # Tab 1: Executive Summary & Overview
    with tabs[0]:
        st.markdown('<div class="section-title">Executive Summary</div>', unsafe_allow_html=True)
        
        summary_content = sections[0] if sections else ""
        st.markdown(f'<div class="analysis-section highlight-section">{summary_content}</div>', unsafe_allow_html=True)
        
        # Key metrics highlights
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div class="key-points">
            <h4>📈 Dividendi</h4>
            <ul>
            <li>DPS 2023: <span class="metric-highlight">€0.48</span></li>
            <li>Crescita: <span class="metric-highlight">+7.5% annuo</span></li>
            <li>Yield: <span class="metric-highlight">~4.5%</span></li>
            <li>CAGR 2015-23: <span class="metric-highlight">30%</span></li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="key-points">
            <h4>🏗️ Business Model</h4>
            <ul>
            <li>Torri: <span class="metric-highlight">~24,500</span></li>
            <li>EBITDA Margin: <span class="metric-highlight">~91%</span></li>
            <li>Contratti: <span class="metric-highlight">10-15 anni</span></li>
            <li>Tenancy Ratio: <span class="metric-highlight">2.16x</span></li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="key-points">
            <h4>💰 Finanziari</h4>
            <ul>
            <li>FCF 2023: <span class="metric-highlight">€611M</span></li>
            <li>Net Debt/EBITDA: <span class="metric-highlight">4.1x</span></li>
            <li>TSR Target: <span class="metric-highlight">7-9%</span></li>
            <li>Fair Value: <span class="metric-highlight">€11-12</span></li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Parsing sezioni 1-2
        if len(sections) > 1:
            st.markdown('<div class="section-title">1. Descrizione Aziendale</div>', unsafe_allow_html=True)
            business_desc = sections[1] if len(sections) > 1 else ""
            st.markdown(f'<div class="analysis-section">{business_desc}</div>', unsafe_allow_html=True)
        
        if len(sections) > 2:
            st.markdown('<div class="section-title">2. Management & Governance</div>', unsafe_allow_html=True)
            management_content = sections[2] if len(sections) > 2 else ""
            st.markdown(f'<div class="analysis-section">{management_content}</div>', unsafe_allow_html=True)
    
    # Tab 2: Business & Strategy
    with tabs[1]:
        if len(sections) > 3:
            st.markdown('<div class="section-title">3. Piano Industriale & Strategia</div>', unsafe_allow_html=True)
            strategy_content = sections[3] if len(sections) > 3 else ""
            st.markdown(f'<div class="analysis-section">{strategy_content}</div>', unsafe_allow_html=True)
        
        if len(sections) > 4:
            st.markdown('<div class="section-title">4. Outlook Macroeconomico & Tassi</div>', unsafe_allow_html=True)
            macro_content = sections[4] if len(sections) > 4 else ""
            st.markdown(f'<div class="analysis-section">{macro_content}</div>', unsafe_allow_html=True)
        
        if len(sections) > 5:
            st.markdown('<div class="section-title">5. Analisi PESTEL</div>', unsafe_allow_html=True)
            pestel_content = sections[5] if len(sections) > 5 else ""
            st.markdown(f'<div class="analysis-section">{pestel_content}</div>', unsafe_allow_html=True)
        
        if len(sections) > 6:
            st.markdown('<div class="section-title">6. Analisi delle 5 Forze di Porter</div>', unsafe_allow_html=True)
            porter_content = sections[6] if len(sections) > 6 else ""
            st.markdown(f'<div class="analysis-section">{porter_content}</div>', unsafe_allow_html=True)
    
    # Tab 3: Analisi Finanziaria
    with tabs[2]:
        if len(sections) > 7:
            st.markdown('<div class="section-title">7. Andamento Storico dei Dividendi</div>', unsafe_allow_html=True)
            dividends_content = sections[7] if len(sections) > 7 else ""
            st.markdown(f'<div class="analysis-section">{dividends_content}</div>', unsafe_allow_html=True)
        
        if len(sections) > 8:
            st.markdown('<div class="section-title">8. Performance Finanziaria (ultimi 5 anni)</div>', unsafe_allow_html=True)
            performance_content = sections[8] if len(sections) > 8 else ""
            st.markdown(f'<div class="analysis-section">{performance_content}</div>', unsafe_allow_html=True)
        
        if len(sections) > 15:
            st.markdown('<div class="section-title">15. Total Shareholder Return (TSR) comparato</div>', unsafe_allow_html=True)
            tsr_content = sections[15] if len(sections) > 15 else ""
            st.markdown(f'<div class="analysis-section">{tsr_content}</div>', unsafe_allow_html=True)
    
    # Tab 4: Valutazione & Scenari
    with tabs[3]:
        if len(sections) > 9:
            st.markdown('<div class="section-title">9. Valutazione</div>', unsafe_allow_html=True)
            valuation_content = sections[9] if len(sections) > 9 else ""
            st.markdown(f'<div class="analysis-section">{valuation_content}</div>', unsafe_allow_html=True)
        
        if len(sections) > 10:
            st.markdown('<div class="section-title">10. Scenario & Sensitivity Analysis</div>', unsafe_allow_html=True)
            scenarios_content = sections[10] if len(sections) > 10 else ""
            st.markdown(f'<div class="analysis-section">{scenarios_content}</div>', unsafe_allow_html=True)
        
        if len(sections) > 16:
            st.markdown('<div class="section-title">16. Impatto Fiscale sui Dividendi</div>', unsafe_allow_html=True)
            tax_content = sections[16] if len(sections) > 16 else ""
            st.markdown(f'<div class="analysis-section">{tax_content}</div>', unsafe_allow_html=True)
    
    # Tab 5: Rischi & Opportunità
    with tabs[4]:
        if len(sections) > 13:
            st.markdown('<div class="section-title">13. Rischi & Catalyst</div>', unsafe_allow_html=True)
            risks_content = sections[13] if len(sections) > 13 else ""
            st.markdown(f'<div class="analysis-section">{risks_content}</div>', unsafe_allow_html=True)
        
        if len(sections) > 11:
            st.markdown('<div class="section-title">11. Regolamentazione & Rischi Normativi</div>', unsafe_allow_html=True)
            regulation_content = sections[11] if len(sections) > 11 else ""
            st.markdown(f'<div class="analysis-section">{regulation_content}</div>', unsafe_allow_html=True)
        
        if len(sections) > 14:
            st.markdown('<div class="section-title">14. Liquidità & Flottante Azionario</div>', unsafe_allow_html=True)
            liquidity_content = sections[14] if len(sections) > 14 else ""
            st.markdown(f'<div class="analysis-section">{liquidity_content}</div>', unsafe_allow_html=True)
    
    # Tab 6: Governance & ESG
    with tabs[5]:
        if len(sections) > 12:
            st.markdown('<div class="section-title">12. ESG & Sustainability</div>', unsafe_allow_html=True)
            esg_content = sections[12] if len(sections) > 12 else ""
            st.markdown(f'<div class="analysis-section">{esg_content}</div>', unsafe_allow_html=True)
        
        if len(sections) > 17:
            st.markdown('<div class="section-title">17. Appendice & Metodologia</div>', unsafe_allow_html=True)
            methodology_content = sections[17] if len(sections) > 17 else ""
            st.markdown(f'<div class="analysis-section">{methodology_content}</div>', unsafe_allow_html=True)
        
        if len(sections) > 18:
            st.markdown('<div class="section-title">18. Conclusione & Raccomandazione</div>', unsafe_allow_html=True)
            conclusion_content = sections[18] if len(sections) > 18 else ""
            st.markdown(f'<div class="analysis-section highlight-section">{conclusion_content}</div>', unsafe_allow_html=True)
    
    # Summary card finale
    st.markdown("---")
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1f77b4, #2e86ab); color: white; padding: 2rem; border-radius: 15px; text-align: center;">
        <h2>🎯 Sintesi Finale</h2>
        <div style="display: flex; justify-content: space-around; margin-top: 1rem;">
            <div>
                <h3>📊 Rating</h3>
                <p style="font-size: 2rem; font-weight: bold;">BUY</p>
            </div>
            <div>
                <h3>💰 Target Price</h3>
                <p style="font-size: 2rem; font-weight: bold;">€11-12</p>
            </div>
            <div>
                <h3>📈 TSR atteso</h3>
                <p style="font-size: 2rem; font-weight: bold;">7-9%</p>
            </div>
        </div>
        <p style="margin-top: 1rem; font-style: italic;">Investimento ideale per portafogli orientati al reddito con orizzonte di lungo termine</p>
    </div>
    """, unsafe_allow_html=True)

# --- Sezione: Conclusioni ---
elif section_id == "conclusions":
    st.subheader("🎯 Conclusioni e Raccomandazioni")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("TSR atteso (annuo)", "7-9%", help="Total Shareholder Return: dividendi + crescita prezzo")
    
    with col2:
        st.metric("Dividend CAGR obiettivo", "7.5%", help="Crescita dividendi pianificata 2024-2026")
    
    with col3:
        st.metric("Fair Value stimato", "€11-12", help="Target price basato su DCF e multipli")
    
    # Raccomandazione finale
    st.markdown("""
    <div class="highlight-box">
    <h2>📊 Raccomandazione: BUY/ACCUMULO</h2>
    
    <h3>✅ Tesi di Investimento - Punti di Forza:</h3>
    <ul>
    <li><strong>Dividend Growth Story</strong>: Rendimento attuale 4.6% con crescita programmata 7.5% annuo</li>
    <li><strong>Business Monopolistico</strong>: Leader indiscusso in Italia, asset essenziali per 4G/5G</li>
    <li><strong>Contratti Difensivi</strong>: Oltre 90% ricavi sotto contratto long-term indicizzati</li>
    <li><strong>FCF Robusto</strong>: Generazione cassa in crescita supporta dividendi e deleveraging</li>
    <li><strong>Piano Credibile</strong>: Target 2026 basati su driver concreti (5G, densificazione)</li>
    </ul>
    
    <h3>⚠️ Rischi da Monitorare:</h3>
    <ul>
    <li><strong>Leva Elevata</strong>: 3.8x Net Debt/EBITDA, sensibile a tassi di interesse</li>
    <li><strong>Concentrazione Clienti</strong>: Dipendenza da salute finanziaria TIM/Vodafone</li>
    <li><strong>Execution Risk</strong>: Necessario centrare target di nuovi siti e efficienze</li>
    <li><strong>Tassi di Interesse</strong>: Rifinanziamenti 2025-2026 a tassi più alti</li>
    </ul>
    
    <h3>🎯 Profilo Investitore Ideale:</h3>
    <p><strong>Investitori orientati al reddito</strong> con orizzonte >5 anni che cercano:</p>
    <ul>
    <li>Yield elevato e crescente (~4.6% attuale, target ~5-6% entro 2026)</li>
    <li>Protezione inflazione (contratti indicizzati)</li>
    <li>Bassa correlazione con ciclo economico</li>
    <li>Potenziale capital appreciation moderato</li>
    </ul>
    
    <h3>💰 Target Price e Timing:</h3>
    <ul>
    <li><strong>Fair Value</strong>: €11-12 (upside ~15% da €10.4 attuali)</li>
    <li><strong>Entry Point</strong>: Attuale o su debolezze <€10</li>
    <li><strong>Target Yield on Cost</strong>: >5% acquistando sotto €10</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Risk-Return Profile
    st.subheader("📊 Profilo Rischio-Rendimento")
    
    # Creazione scatter plot risk-return
    risk_return_data = {
        'Asset': ['INWIT', 'FTSE MIB', 'BTP 10Y', 'Utilities IT', 'REITs EU', 'Cellnex'],
        'Rendimento Atteso (%)': [7.5, 8.5, 4.0, 6.5, 6.0, 5.0],
        'Volatilità (%)': [20, 25, 3, 18, 22, 28],
        'Dividend Yield (%)': [4.6, 3.8, 0, 5.2, 4.8, 0.0]
    }
    
    fig_risk_return = px.scatter(
        risk_return_data,
        x='Volatilità (%)',
        y='Rendimento Atteso (%)',
        size='Dividend Yield (%)',
        text='Asset',
        title="Profilo Rischio-Rendimento: INWIT vs Alternative",
        labels={'Volatilità (%)': 'Volatilità Annua (%)', 'Rendimento Atteso (%)': 'TSR Atteso Annuo (%)'}
    )
    
    fig_risk_return.update_traces(textposition="top center")
    fig_risk_return.update_layout(
        xaxis=dict(range=[0, 35]),
        yaxis=dict(range=[2, 10])
    )
    
    st.plotly_chart(fig_risk_return, use_container_width=True)
    
    # Disclaimer finale
    st.markdown("---")
    st.caption("""
    **Disclaimer**: Questa analisi è solo a scopo informativo e non costituisce consulenza finanziaria. 
    I rendimenti passati non garantiscono risultati futuri. Gli investitori dovrebbero condurre le proprie 
    ricerche e consultare un consulente finanziario qualificato prima di prendere decisioni di investimento.
    
    **Fonte dati**: TIKR, Analisi_INWIT.md, comunicati societari, elaborazioni proprie.
    """)
    
    # Footer con firma
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; padding: 1rem; border-top: 1px solid #ddd;">
        <p style="font-style: italic; color: #666;">
            📡 Analisi generata per investitori orientati al dividendo<br>
            <small>Created with Streamlit & Plotly</small>
        </p>
    </div>
    """, unsafe_allow_html=True)
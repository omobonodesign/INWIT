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

# --- Dati Chiave Estratti dal TIKR report ---
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

# Dati storici Dividendo Per Azione (DPS) - aggiornati dai dati TIKR
dps_storico_data = {
    'Anno Esercizio': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
    'DPS (€)': [0.09, 0.15, 0.19, 0.21, 0.73, 0.30, 0.32, 0.35, 0.48, 0.48],  # Dati correrti da TIKR
    'DPS Ordinario (€)': [0.09, 0.15, 0.19, 0.21, 0.13, 0.30, 0.32, 0.35, 0.48, 0.48],
    'DPS Straordinario (€)': [0.0, 0.0, 0.0, 0.0, 0.60, 0.0, 0.0, 0.0, 0.0, 0.0],
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
        150.8    # Payout ratio
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

# Disclaimer in alto
st.markdown("""
<div style="background-color: #f8f9fa; padding: 0.7rem; border-radius: 0.5rem; margin-bottom: 1rem; font-size: 0.8rem;">
<strong>DISCLAIMER</strong><br>
Le informazioni contenute in questa presentazione sono fornite esclusivamente a scopo informativo generale e/o educativo. Non costituiscono e non devono essere interpretate come consulenza finanziaria, legale, fiscale o di investimento.<br>
Investire nei mercati finanziari comporta rischi significativi, inclusa la possibilità di perdere l'intero capitale investito. Le performance passate non sono indicative né garanzia di risultati futuri.<br>
Si raccomanda vivamente di condurre la propria analisi approfondita (due diligence) e di consultare un consulente finanziario indipendente e qualificato prima di prendere qualsiasi decisione di investimento.<br><br>
<em>Realizzazione a cura della Barba Sparlante con l'utilizzo di tecnologie di intelligenza artificiale</em>
</div>
""", unsafe_allow_html=True)

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
    <li><strong>Straordinario 2019</strong>: €0.60 extra distribuiti grazie alla fusione Vodafone per ottimizzare la struttura</li>
    <li><strong>Policy Chiara</strong>: +7.5% annuo confermato fino al 2026 (DPS atteso €0.555 nel 2025)</li>
    <li><strong>Sostenibilità</strong>: Il payout è coperto dall'80% del FCF, lasciando margine per crescita e deleveraging</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer standard con disclaimer
    st.markdown("---")
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem; font-size: 0.8rem;">
    <strong>DISCLAIMER</strong><br>
    Le informazioni contenute in questa presentazione sono fornite esclusivamente a scopo informativo generale e/o educativo. Non costituiscono e non devono essere interpretate come consulenza finanziaria, legale, fiscale o di investimento.<br>
    Investire nei mercati finanziari comporta rischi significativi, inclusa la possibilità di perdere l'intero capitale investito. Le performance passate non sono indicative né garanzia di risultati futuri.<br>
    Si raccomanda vivamente di condurre la propria analisi approfondita (due diligence) e di consultare un consulente finanziario indipendente e qualificato prima di prendere qualsiasi decisione di investimento.<br><br>
    <em>Realizzazione a cura della Barba Sparlante con l'utilizzo di tecnologie di intelligenza artificiale</em>
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
            texttemplate='%{text:.1f}M',
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
            x='2020', y=663.4,
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
    
    # Tabella performance finanziaria - CORRETTO CON EXPANDER
    with st.expander("📊 Dettaglio Performance Finanziaria", expanded=True):
        # Preparazione tabella con codice colore
        df_display = df_fin_clean.copy()
        df_display['Ricavi (€M)'] = df_display['Ricavi (€M)'].round(1)
        df_display['EBITDA (€M)'] = df_display['EBITDA (€M)'].round(1)
        df_display['EBITDA Margin (%)'] = df_display['EBITDA Margin (%)'].round(1)
        df_display['Utile Netto (€M)'] = df_display['Utile Netto (€M)'].round(1)
        df_display['FCF (€M)'] = df_display['FCF (€M)'].round(1)
        df_display['EPS (€)'] = df_display['EPS (€)'].round(2)
        df_display['DPS (€)'] = df_display['DPS (€)'].round(3)
        
        st.dataframe(
            df_display.set_index('Anno'),
            use_container_width=True,
            hide_index=False,
            column_config={
                "Ricavi (€M)": st.column_config.NumberColumn(
                    "Ricavi (€M)",
                    help="Ricavi totali annui",
                    format="%.1f"
                ),
                "EBITDA (€M)": st.column_config.NumberColumn(
                    "EBITDA (€M)",
                    help="EBITDA annuale",
                    format="%.1f"
                ),
                "EBITDA Margin (%)": st.column_config.NumberColumn(
                    "EBITDA Margin (%)",
                    help="Margine EBITDA",
                    format="%.1f%%"
                ),
                "Utile Netto (€M)": st.column_config.NumberColumn(
                    "Utile Netto (€M)",
                    help="Utile netto annuale",
                    format="%.1f"
                ),
                "EPS (€)": st.column_config.NumberColumn(
                    "EPS (€)",
                    help="Utile per azione",
                    format="%.2f"
                ),
                "FCF (€M)": st.column_config.NumberColumn(
                    "FCF (€M)",
                    help="Free Cash Flow",
                    format="%.1f"
                ),
                "DPS (€)": st.column_config.NumberColumn(
                    "DPS (€)",
                    help="Dividendo per azione",
                    format="%.3f"
                ),
                "Fase": st.column_config.TextColumn(
                    "Fase",
                    help="Fase dell'azienda"
                )
            }
        )
    
    # Footer standard con disclaimer
    st.markdown("---")
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem; font-size: 0.8rem;">
    <strong>DISCLAIMER</strong><br>
    Le informazioni contenute in questa presentazione sono fornite esclusivamente a scopo informativo generale e/o educativo. Non costituiscono e non devono essere interpretate come consulenza finanziaria, legale, fiscale o di investimento.<br>
    Investire nei mercati finanziari comporta rischi significativi, inclusa la possibilità di perdere l'intero capitale investito. Le performance passate non sono indicative né garanzia di risultati futuri.<br>
    Si raccomanda vivamente di condurre la propria analisi approfondita (due diligence) e di consultare un consulente finanziario indipendente e qualificato prima di prendere qualsiasi decisione di investimento.<br><br>
    <em>Realizzazione a cura della Barba Sparlante con l'utilizzo di tecnologie di intelligenza artificiale</em>
    </div>
    """, unsafe_allow_html=True)

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
    
    # Stress test dividendi - CORRETTO CON EXPANDER
    with st.expander("🧪 Stress Test: Sostenibilità Dividendo", expanded=True):
        scenarios = {
            'Scenario': ['Base Case', 'FCF -10%', 'FCF -20%', 'FCF -30%'],
            'FCF 2024 (€M)': [469, 422, 375, 328],
            'Dividendi Totali (€M)': [450, 450, 450, 450],
            'Copertura': [1.04, 0.94, 0.83, 0.73],
            'Sostenibilità': ['✅ Sostenibile', '⚠️ Limite', '❌ Non Sostenibile', '❌ Non Sostenibile']
        }
        
        df_stress = pd.DataFrame(scenarios)
        
        # Formatta correttamente lo stress test
        st.dataframe(
            df_stress,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Scenario": st.column_config.TextColumn(
                    "Scenario",
                    help="Scenario di stress test"
                ),
                "FCF 2024 (€M)": st.column_config.NumberColumn(
                    "FCF 2024 (€M)",
                    help="Free Cash Flow stimato",
                    format="%.1f"
                ),
                "Dividendi Totali (€M)": st.column_config.NumberColumn(
                    "Dividendi Totali (€M)",
                    help="Totale dividendi distribuiti",
                    format="%.1f"
                ),
                "Copertura": st.column_config.NumberColumn(
                    "Copertura",
                    help="Rapporto FCF/Dividendi",
                    format="%.2f"
                ),
                "Sostenibilità": st.column_config.TextColumn(
                    "Sostenibilità",
                    help="Valutazione della sostenibilità del dividendo"
                )
            }
        )
    
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
    
    # Proiezioni finanziarie - CORRETTO CON EXPANDER
    with st.expander("📊 Proiezioni Finanziarie (Piano Industriale)", expanded=True):
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
        
        # Formattazione corretta delle proiezioni finanziarie
        st.dataframe(
            df_projections.set_index('Metrica'),
            use_container_width=True,
            hide_index=False,
            column_config={
                "2024E": st.column_config.Column(
                    "2024E",
                    help="Stima 2024"
                ),
                "2025E": st.column_config.Column(
                    "2025E",
                    help="Stima 2025"
                ),
                "2026E": st.column_config.Column(
                    "2026E",
                    help="Stima 2026"
                ),
                "CAGR 24-26": st.column_config.Column(
                    "CAGR 24-26",
                    help="Crescita annua composta 2024-2026"
                )
            }
        )
    
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
    
    # Struttura del debito - CORRETTO CON EXPANDER
    with st.expander("💳 Struttura del Debito", expanded=True):
        debt_structure = {
            'Strumento': ['Bond 2026', 'Bond 2028', 'Term Loan', 'Leasing IFRS16'],
            'Importo (€M)': [750, 1000, 1000, 1000],
            'Tasso (%)': [1.875, 2.375, 'EURIBOR + 150bps', 'N/A'],
            'Scadenza': ['2026', '2028', '2025', 'Varie'],
            'Note': ['Fisso', 'Fisso', 'Variabile', 'Affitti capitalizzati']
        }
        
        df_debt_structure = pd.DataFrame(debt_structure)
        
        # Formattazione corretta della struttura del debito
        st.dataframe(
            df_debt_structure,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Strumento": st.column_config.TextColumn(
                    "Strumento",
                    help="Tipologia di strumento di debito"
                ),
                "Importo (€M)": st.column_config.NumberColumn(
                    "Importo (€M)",
                    help="Importo in milioni di euro",
                    format="%.0f"
                ),
                "Tasso (%)": st.column_config.Column(
                    "Tasso (%)",
                    help="Tasso di interesse applicato"
                ),
                "Scadenza": st.column_config.TextColumn(
                    "Scadenza",
                    help="Anno di scadenza"
                ),
                "Note": st.column_config.TextColumn(
                    "Note",
                    help="Informazioni aggiuntive"
                )
            }
        )
    
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
    
    # Tabella confronto multipli - CORRETTO CON EXPANDER
    with st.expander("📈 Confronto Multipli di Valutazione", expanded=True):
        multiples_comparison = {
            'Società': ['INWIT', 'Cellnex', 'American Tower (US)', 'Vantage Towers', 'Media Settore'],
            'EV/EBITDA 2024E': [15.0, 14.2, 21.5, 12.8, 16.0],
            'P/E 2024E': [23.5, 'N/A', 32.0, 18.5, 25.0],
            'Dividend Yield (%)': [4.6, 0.0, 3.3, 0.0, 2.8],
            'Net Debt/EBITDA': [3.8, 4.0, 5.5, 3.2, 4.1],
            'Geografie': ['Italia', 'Europa', 'Globale', 'Europa', '']
        }
        
        df_multiples = pd.DataFrame(multiples_comparison)
        
        # Formattazione corretta dei multipli
        st.dataframe(
            df_multiples,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Società": st.column_config.TextColumn(
                    "Società",
                    help="Nome dell'azienda"
                ),
                "EV/EBITDA 2024E": st.column_config.Column(
                    "EV/EBITDA 2024E",
                    help="Enterprise Value / EBITDA"
                ),
                "P/E 2024E": st.column_config.Column(
                    "P/E 2024E",
                    help="Price / Earnings"
                ),
                "Dividend Yield (%)": st.column_config.NumberColumn(
                    "Dividend Yield (%)",
                    help="Rendimento dividendi",
                    format="%.1f%%"
                ),
                "Net Debt/EBITDA": st.column_config.NumberColumn(
                    "Net Debt/EBITDA",
                    help="Leva finanziaria",
                    format="%.1f"
                ),
                "Geografie": st.column_config.TextColumn(
                    "Geografie",
                    help="Mercati geografici principali"
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

    # Funzione per caricare il file di testo - qui legge l'intero contenuto
    def load_analysis_text(filename="Analisi_INWIT.md"):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            # Contenuto fallback in caso il file non sia disponibile
            return """
            # Analisi non disponibile
            
            Il file di analisi non è stato trovato. Assicurarsi che il file "Analisi_INWIT.md" sia nella stessa directory dell'applicazione.
            """
    
    # Carica l'analisi completa
    analysis_content = load_analysis_text()
    
    # Suddividi in sezioni principali usando i titoli numerati come "1. ", "2. " ecc.
    sections = re.split(r'\n(?=\d+\. )', analysis_content)
    
    # Separa l'Executive Summary
    if sections and not sections[0].startswith("1."):
        executive_summary = sections[0]
        sections = sections[1:]
    else:
        executive_summary = ""
    
    # Crea tabs per le sezioni principali
    tab_names = ["Executive Summary & Overview", "Business & Strategy", "Analisi Finanziaria", "Valutazione & Scenari", "Rischi & Opportunità", "Governance & ESG"]
    tabs = st.tabs(tab_names)
    
    # Tab 1: Executive Summary & Overview
    with tabs[0]:
        st.markdown('<div class="section-title">Executive Summary</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="analysis-section highlight-section">{executive_summary}</div>', unsafe_allow_html=True)
        
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
            <li>FCF 2023: <span class="metric-highlight">€511M</span></li>
            <li>Net Debt/EBITDA: <span class="metric-highlight">4.1x</span></li>
            <li>TSR Target: <span class="metric-highlight">7-9%</span></li>
            <li>Fair Value: <span class="metric-highlight">€11-12</span></li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Sections 1 & 2
        if len(sections) > 0:
            with st.expander("1. Descrizione Aziendale", expanded=True):
                st.markdown(f'<div class="analysis-section">{sections[0]}</div>', unsafe_allow_html=True)
        
        if len(sections) > 1:
            with st.expander("2. Management & Governance", expanded=True):
                st.markdown(f'<div class="analysis-section">{sections[1]}</div>', unsafe_allow_html=True)
        
        # Footer standard con disclaimer
        st.markdown("---")
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem; font-size: 0.8rem;">
        <strong>DISCLAIMER</strong><br>
        Le informazioni contenute in questa presentazione sono fornite esclusivamente a scopo informativo generale e/o educativo. Non costituiscono e non devono essere interpretate come consulenza finanziaria, legale, fiscale o di investimento.<br>
        Investire nei mercati finanziari comporta rischi significativi, inclusa la possibilità di perdere l'intero capitale investito. Le performance passate non sono indicative né garanzia di risultati futuri.<br>
        Si raccomanda vivamente di condurre la propria analisi approfondita (due diligence) e di consultare un consulente finanziario indipendente e qualificato prima di prendere qualsiasi decisione di investimento.<br><br>
        <em>Realizzazione a cura della Barba Sparlante con l'utilizzo di tecnologie di intelligenza artificiale</em>
        </div>
        """, unsafe_allow_html=True)
    
    # Tab 2: Business & Strategy
    with tabs[1]:
        if len(sections) > 2:
            with st.expander("3. Piano Industriale & Strategia", expanded=True):
                st.markdown(f'<div class="analysis-section">{sections[2]}</div>', unsafe_allow_html=True)
        
        if len(sections) > 3:
            with st.expander("4. Outlook Macroeconomico & Tassi", expanded=True):
                st.markdown(f'<div class="analysis-section">{sections[3]}</div>', unsafe_allow_html=True)
        
        if len(sections) > 4:
            with st.expander("5. Analisi PESTEL", expanded=True):
                st.markdown(f'<div class="analysis-section">{sections[4]}</div>', unsafe_allow_html=True)
        
        if len(sections) > 5:
            with st.expander("6. Analisi delle 5 Forze di Porter", expanded=True):
                st.markdown(f'<div class="analysis-section">{sections[5]}</div>', unsafe_allow_html=True)
        
        # Footer standard con disclaimer
        st.markdown("---")
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem; font-size: 0.8rem;">
        <strong>DISCLAIMER</strong><br>
        Le informazioni contenute in questa presentazione sono fornite esclusivamente a scopo informativo generale e/o educativo. Non costituiscono e non devono essere interpretate come consulenza finanziaria, legale, fiscale o di investimento.<br>
        Investire nei mercati finanziari comporta rischi significativi, inclusa la possibilità di perdere l'intero capitale investito. Le performance passate non sono indicative né garanzia di risultati futuri.<br>
        Si raccomanda vivamente di condurre la propria analisi approfondita (due diligence) e di consultare un consulente finanziario indipendente e qualificato prima di prendere qualsiasi decisione di investimento.<br><br>
        <em>Realizzazione a cura della Barba Sparlante con l'utilizzo di tecnologie di intelligenza artificiale</em>
        </div>
        """, unsafe_allow_html=True)
    
    # Tab 3: Analisi Finanziaria
    with tabs[2]:
        if len(sections) > 6:
            with st.expander("7. Andamento Storico dei Dividendi", expanded=True):
                st.markdown(f'<div class="analysis-section">{sections[6]}</div>', unsafe_allow_html=True)
        
        if len(sections) > 7:
            with st.expander("8. Performance Finanziaria (ultimi 5 anni)", expanded=True):
                st.markdown(f'<div class="analysis-section">{sections[7]}</div>', unsafe_allow_html=True)
        
        if len(sections) > 14:
            with st.expander("15. Total Shareholder Return (TSR) comparato", expanded=True):
                st.markdown(f'<div class="analysis-section">{sections[14]}</div>', unsafe_allow_html=True)
        
        # Footer standard con disclaimer
        st.markdown("---")
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem; font-size: 0.8rem;">
        <strong>DISCLAIMER</strong><br>
        Le informazioni contenute in questa presentazione sono fornite esclusivamente a scopo informativo generale e/o educativo. Non costituiscono e non devono essere interpretate come consulenza finanziaria, legale, fiscale o di investimento.<br>
        Investire nei mercati finanziari comporta rischi significativi, inclusa la possibilità di perdere l'intero capitale investito. Le performance passate non sono indicative né garanzia di risultati futuri.<br>
        Si raccomanda vivamente di condurre la propria analisi approfondita (due diligence) e di consultare un consulente finanziario indipendente e qualificato prima di prendere qualsiasi decisione di investimento.<br><br>
        <em>Realizzazione a cura della Barba Sparlante con l'utilizzo di tecnologie di intelligenza artificiale</em>
        </div>
        """, unsafe_allow_html=True)
    
    # Tab 4: Valutazione & Scenari
    with tabs[3]:
        if len(sections) > 8:
            with st.expander("9. Valutazione", expanded=True):
                st.markdown(f'<div class="analysis-section">{sections[8]}</div>', unsafe_allow_html=True)
        
        if len(sections) > 9:
            with st.expander("10. Scenario & Sensitivity Analysis", expanded=True):
                st.markdown(f'<div class="analysis-section">{sections[9]}</div>', unsafe_allow_html=True)
        
        if len(sections) > 15:
            with st.expander("16. Impatto Fiscale sui Dividendi", expanded=True):
                st.markdown(f'<div class="analysis-section">{sections[15]}</div>', unsafe_allow_html=True)
        
        # Footer standard con disclaimer
        st.markdown("---")
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem; font-size: 0.8rem;">
        <strong>DISCLAIMER</strong><br>
        Le informazioni contenute in questa presentazione sono fornite esclusivamente a scopo informativo generale e/o educativo. Non costituiscono e non devono essere interpretate come consulenza finanziaria, legale, fiscale o di investimento.<br>
        Investire nei mercati finanziari comporta rischi significativi, inclusa la possibilità di perdere l'intero capitale investito. Le performance passate non sono indicative né garanzia di risultati futuri.<br>
        Si raccomanda vivamente di condurre la propria analisi approfondita (due diligence) e di consultare un consulente finanziario indipendente e qualificato prima di prendere qualsiasi decisione di investimento.<br><br>
        <em>Realizzazione a cura della Barba Sparlante con l'utilizzo di tecnologie di intelligenza artificiale</em>
        </div>
        """, unsafe_allow_html=True)
    
    # Tab 5: Rischi & Opportunità
    with tabs[4]:
        if len(sections) > 12:
            with st.expander("13. Rischi & Catalyst", expanded=True):
                st.markdown(f'<div class="analysis-section">{sections[12]}</div>', unsafe_allow_html=True)
        
        if len(sections) > 10:
            with st.expander("11. Regolamentazione & Rischi Normativi", expanded=True):
                st.markdown(f'<div class="analysis-section">{sections[10]}</div>', unsafe_allow_html=True)
        
        if len(sections) > 13:
            with st.expander("14. Liquidità & Flottante Azionario", expanded=True):
                st.markdown(f'<div class="analysis-section">{sections[13]}</div>', unsafe_allow_html=True)
        
        # Footer standard con disclaimer
        st.markdown("---")
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem; font-size: 0.8rem;">
        <strong>DISCLAIMER</strong><br>
        Le informazioni contenute in questa presentazione sono fornite esclusivamente a scopo informativo generale e/o educativo. Non costituiscono e non devono essere interpretate come consulenza finanziaria, legale, fiscale o di investimento.<br>
        Investire nei mercati finanziari comporta rischi significativi, inclusa la possibilità di perdere l'intero capitale investito. Le performance passate non sono indicative né garanzia di risultati futuri.<br>
        Si raccomanda vivamente di condurre la propria analisi approfondita (due diligence) e di consultare un consulente finanziario indipendente e qualificato prima di prendere qualsiasi decisione di investimento.<br><br>
        <em>Realizzazione a cura della Barba Sparlante con l'utilizzo di tecnologie di intelligenza artificiale</em>
        </div>
        """, unsafe_allow_html=True)
    
    # Tab 6: Governance & ESG
    with tabs[5]:
        if len(sections) > 11:
            with st.expander("12. ESG & Sustainability", expanded=True):
                st.markdown(f'<div class="analysis-section">{sections[11]}</div>', unsafe_allow_html=True)
        
        if len(sections) > 16:
            with st.expander("17. Appendice & Metodologia", expanded=True):
                st.markdown(f'<div class="analysis-section">{sections[16]}</div>', unsafe_allow_html=True)
        
        if len(sections) > 17:
            with st.expander("18. Conclusione & Valutazione Finale", expanded=True):
                st.markdown(f'<div class="analysis-section highlight-section">{sections[17]}</div>', unsafe_allow_html=True)
        
        # Footer standard con disclaimer
        st.markdown("---")
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem; font-size: 0.8rem;">
        <strong>DISCLAIMER</strong><br>
        Le informazioni contenute in questa presentazione sono fornite esclusivamente a scopo informativo generale e/o educativo. Non costituiscono e non devono essere interpretate come consulenza finanziaria, legale, fiscale o di investimento.<br>
        Investire nei mercati finanziari comporta rischi significativi, inclusa la possibilità di perdere l'intero capitale investito. Le performance passate non sono indicative né garanzia di risultati futuri.<br>
        Si raccomanda vivamente di condurre la propria analisi approfondita (due diligence) e di consultare un consulente finanziario indipendente e qualificato prima di prendere qualsiasi decisione di investimento.<br><br>
        <em>Realizzazione a cura della Barba Sparlante con l'utilizzo di tecnologie di intelligenza artificiale</em>
        </div>
        """, unsafe_allow_html=True)
    
    # Summary card finale
    st.markdown("---")
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1f77b4, #2e86ab); color: white; padding: 2rem; border-radius: 15px; text-align: center;">
        <h2>🎯 Sintesi Finale</h2>
        <div style="display: flex; justify-content: space-around; margin-top: 1rem;">
            <div>
                <h3>📊 Valutazione</h3>
                <p style="font-size: 2rem; font-weight: bold;">Favorevole</p>
            </div>
            <div>
                <h3>💰 Fair Value Range</h3>
                <p style="font-size: 2rem; font-weight: bold;">€11-12</p>
            </div>
            <div>
                <h3>📈 TSR atteso</h3>
                <p style="font-size: 2rem; font-weight: bold;">7-9%</p>
            </div>
        </div>
        <p style="margin-top: 1rem; font-style: italic;">Profilo coerente con portafogli orientati al reddito con orizzonte di lungo termine</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer standard con disclaimer
    st.markdown("---")
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem; font-size: 0.8rem;">
    <strong>DISCLAIMER</strong><br>
    Le informazioni contenute in questa presentazione sono fornite esclusivamente a scopo informativo generale e/o educativo. Non costituiscono e non devono essere interpretate come consulenza finanziaria, legale, fiscale o di investimento.<br>
    Investire nei mercati finanziari comporta rischi significativi, inclusa la possibilità di perdere l'intero capitale investito. Le performance passate non sono indicative né garanzia di risultati futuri.<br>
    Si raccomanda vivamente di condurre la propria analisi approfondita (due diligence) e di consultare un consulente finanziario indipendente e qualificato prima di prendere qualsiasi decisione di investimento.<br><br>
    <em>Realizzazione a cura della Barba Sparlante con l'utilizzo di tecnologie di intelligenza artificiale</em>
    </div>
    """, unsafe_allow_html=True)

# --- Sezione: Conclusioni ---
elif section_id == "conclusions":
    st.subheader("🎯 Conclusioni e Considerazioni")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("TSR atteso (annuo)", "7-9%", help="Total Shareholder Return: dividendi + crescita prezzo")
    
    with col2:
        st.metric("Dividend CAGR obiettivo", "7.5%", help="Crescita dividendi pianificata 2024-2026")
    
    with col3:
        st.metric("Fair Value stimato", "€11-12", help="Target price basato su DCF e multipli")
    
    # Considerazioni sull'investimento
    st.markdown("""
    <div class="highlight-box">
    <h2>📊 Elementi di Analisi</h2>
    
    <h3>✅ Punti di Interesse per l'Investimento:</h3>
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
    
    <h3>🎯 Profilo Investitore Potenzialmente Interessato:</h3>
    <p><strong>Investitori orientati al reddito</strong> con orizzonte >5 anni che cercano:</p>
    <ul>
    <li>Yield elevato e crescente (~4.6% attuale, target ~5-6% entro 2026)</li>
    <li>Protezione inflazione (contratti indicizzati)</li>
    <li>Bassa correlazione con ciclo economico</li>
    <li>Potenziale capital appreciation moderato</li>
    </ul>
    
    <h3>💰 Elementi di Valutazione:</h3>
    <ul>
    <li><strong>Fair Value</strong>: €11-12 (upside ~15% da €10.4 attuali)</li>
    <li><strong>Livelli di Interesse</strong>: Attuali o <€10</li>
    <li><strong>Yield on Cost potenziale</strong>: >5% acquisendo sotto €10</li>
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
    
    # Footer standard con disclaimer
    st.markdown("---")
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem; font-size: 0.8rem;">
    <strong>DISCLAIMER</strong><br>
    Le informazioni contenute in questa presentazione sono fornite esclusivamente a scopo informativo generale e/o educativo. Non costituiscono e non devono essere interpretate come consulenza finanziaria, legale, fiscale o di investimento.<br>
    Investire nei mercati finanziari comporta rischi significativi, inclusa la possibilità di perdere l'intero capitale investito. Le performance passate non sono indicative né garanzia di risultati futuri.<br>
    Si raccomanda vivamente di condurre la propria analisi approfondita (due diligence) e di consultare un consulente finanziario indipendente e qualificato prima di prendere qualsiasi decisione di investimento.<br><br>
    <em>Realizzazione a cura della Barba Sparlante con l'utilizzo di tecnologie di intelligenza artificiale</em>
    </div>
    """, unsafe_allow_html=True)

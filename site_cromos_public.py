import streamlit as st
import pandas as pd
import sqlite3
import os
import base64
import urllib.parse

# 1. Configurar a página do website
st.set_page_config(page_title="Mundial 2026", layout="wide")

# --- O TRUQUE DE PROGRAMADOR: CAMINHOS DINÂMICOS ---
# 1. Descobre automaticamente qual é a pasta onde este ficheiro (.py) está guardado
PASTA_BASE = os.path.dirname(os.path.abspath(__file__))

# 2. Cola o nome da pasta de imagens e da base de dados ao caminho que descobriu
PASTA_IMAGENS = os.path.join(PASTA_BASE, 'imagens')
FICHEIRO_DB = os.path.join(PASTA_BASE, 'mundial2026.db')


def get_image_base64(caminho_imagem):
    with open(caminho_imagem, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return f"data:image/png;base64,{encoded_string}"

# --- INICIALIZAÇÃO DE ESTADO ---
if "modo_vista" not in st.session_state:
    st.session_state.modo_vista = "🌍 Seleção Nacional"
if "selecao_escolhida" not in st.session_state:
    st.session_state.selecao_escolhida = "Portugal"
if "clube_escolhido" not in st.session_state:
    st.session_state.clube_escolhido = ""

# --- CAPTURAR CLIQUES NOS LINKS MÁGICOS VIA URL ---
try:
    if "clube" in st.query_params:
        st.session_state.modo_vista = "⚽ Clube / Equipa"
        st.session_state.clube_escolhido = st.query_params["clube"]
        st.query_params.clear() 
    elif "selecao" in st.query_params:
        st.session_state.modo_vista = "🌍 Seleção Nacional"
        st.session_state.selecao_escolhida = st.query_params["selecao"]
        st.query_params.clear() 
except AttributeError:
    qp = st.experimental_get_query_params()
    if "clube" in qp:
        st.session_state.modo_vista = "⚽ Clube / Equipa"
        st.session_state.clube_escolhido = qp["clube"][0]
        st.experimental_set_query_params()
    elif "selecao" in qp:
        st.session_state.modo_vista = "🌍 Seleção Nacional"
        st.session_state.selecao_escolhida = qp["selecao"][0]
        st.experimental_set_query_params()


# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_dados():
    if os.path.exists(FICHEIRO_DB):
        conn = sqlite3.connect(FICHEIRO_DB)
        query = """
        SELECT 
            j.id_jogador as ID,
            j.nome as Nome,
            j.posicao as Posição,
            s.nome as Seleção,
            s.ficheiro as Emblema_Selecao,
            s.grupo as Grupo, 
            c.nome as Clube,
            c.ficheiro as Logotipo_Clube,
            j.data_nascimento as 'Data de Nascimento',
            j.idade as Idade,
            j.altura as Altura,
            j.peso as Peso,
            j.ficheiro as Ficheiro,
            j.internacionalizacoes as Internacionalizações,
            j.valor_mercado as 'Valor de Mercado',
            j.jogos_epoca as 'Jogos Época',
            j.estrela_equipa as 'Estrela da Equipa',
            j.surpresa as Surpresa
        FROM jogadores j
        LEFT JOIN selecoes s ON j.id_selecao = s.id_selecao
        LEFT JOIN clubes c ON j.id_clube = c.id_clube
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    return pd.DataFrame()

df = carregar_dados()

if df.empty:
    st.error(f"Erro: Não foi possível encontrar a base de dados em: {FICHEIRO_DB}")
else:
    # --- FUNÇÕES HELPER DE VALIDAÇÃO ---
    def limpar_posicao(p):
        if pd.isna(p): return 'Desconhecido'
        p = str(p).upper().strip()
        if p in ['GR', 'GUARDA-REDES', 'GOLEIRO']: return 'GR'
        if p in ['DEF', 'DEFESA', 'ZAGUEIRO', 'LATERAL']: return 'DEF'
        if p in ['MED', 'MÉDIO', 'MEDIO', 'MEIA', 'VOLANTE']: return 'MED'
        if p in ['AVA', 'AVANÇADO', 'AVANCADO', 'ATACANTE', 'PONTA']: return 'AVA'
        return 'Desconhecido'

    df['Posição'] = df['Posição'].apply(limpar_posicao)

    def tem_texto_valido(valor):
        if pd.isna(valor): return False
        texto = str(valor).strip().lower()
        if texto in ['', 'nan', 'none', 'null']: return False
        return True

    def imagem_existe(ficheiro):
        if tem_texto_valido(ficheiro):
            caminho = os.path.join(PASTA_IMAGENS, str(ficheiro).strip())
            return os.path.exists(caminho) and os.path.isfile(caminho)
        return False


    # -------------------------------------------------------------------
    # CSS GLOBAL E INJEÇÕES (Com design responsivo para telemóvel)
    # -------------------------------------------------------------------
    st.markdown("""
    <style>
    /* CSS DO EXPLORADOR */
    [data-testid="stButton"] { margin-bottom: -10px !important; }
    
    [data-testid="baseButton-tertiary"], [data-testid="stBaseButton-tertiary"], .stButton > button[kind="tertiary"] {
        padding: 0px 4px !important;
        min-height: 0px !important;
        height: 24px !important;
        line-height: 1 !important;
        justify-content: flex-start !important; 
        text-align: left !important;
        color: #334155 !important;
    }
    
    [data-testid="baseButton-tertiary"] div, [data-testid="stBaseButton-tertiary"] div, .stButton > button[kind="tertiary"] div {
        display: flex; justify-content: flex-start !important; width: 100%; text-align: left !important;
    }
    
    [data-testid="baseButton-tertiary"] p, [data-testid="stBaseButton-tertiary"] p, .stButton > button[kind="tertiary"] p {
        font-size: 0.9rem !important; margin: 0 !important; text-align: left !important; width: 100%;
    }
    
    [data-testid="baseButton-tertiary"]:hover, [data-testid="stBaseButton-tertiary"]:hover {
        color: #2563eb !important; text-decoration: underline;
    }
    
    .titulo-grupo-compacto {
        font-weight: bold; font-size: 0.95rem; color: #0f172a; margin-top: 12px; margin-bottom: 2px;
        border-bottom: 1px solid #cbd5e1; padding-bottom: 2px;
    }
    
    /* CSS LINKS MÁGICOS */
    .link-magico {
        color: inherit !important; text-decoration: none !important; font-weight: inherit !important; cursor: pointer;
    }
    .link-magico:hover { color: inherit !important; text-decoration: none !important; }
    </style>
    """, unsafe_allow_html=True)


    def navegar_para_pais(pais_escolhido):
        st.session_state.modo_vista = "🌍 Seleção Nacional"
        st.session_state.selecao_escolhida = pais_escolhido
        # st.rerun() REMOVIDO DAQUI PARA EVITAR O ERRO NA NUVEM!


    # ===================================================================
    # ESTRUTURA COLUNAS PRINCIPAIS DO TOPO
    # ===================================================================
    left_main_content, right_logo_section = st.columns([10, 6]) 

    with left_main_content:
        # 1. TÍTULO
        st.markdown(f"<h1 style='margin-top:5px; margin-bottom:20px;'>Mundial 2026</h1>", unsafe_allow_html=True)

        # 2. EXPLORADOR 
        df_grupos = df[['Grupo', 'Seleção']].drop_duplicates().dropna()
        df_grupos = df_grupos[df_grupos['Grupo'].str.startswith('Grupo')]
        grupos_unicos = sorted(df_grupos['Grupo'].unique())

        if grupos_unicos and st.session_state.modo_vista == "🌍 Seleção Nacional":
            with st.expander("🗺️ Explorar Grupos do Mundial", expanded=False):
                cols_exp = st.columns(6)
                for i, grp in enumerate(grupos_unicos):
                    col_idx = i % 6
                    paises_grupo = df_grupos[df_grupos['Grupo'] == grp]['Seleção'].tolist()
                    with cols_exp[col_idx]:
                        st.markdown(f"<div class='titulo-grupo-compacto'>{grp}</div>", unsafe_allow_html=True)
                        for pais in paises_grupo:
                            st.button(pais, key=f"btn_{grp}_{pais}", on_click=navegar_para_pais, args=(pais,), type="tertiary", use_container_width=True)

        # 3. PRIMEIRO SEPARADOR 
        st.markdown("---")

        # 4. CONTROLOS DE FILTRO 
        col_menu1, col_menu2 = st.columns([1.5, 2]) 
        
        with col_menu1:
            st.radio("Organizar a coleção por:", ["🌍 Seleção Nacional", "⚽ Clube / Equipa"], key="modo_vista")

        with col_menu2:
            if st.session_state.modo_vista == "🌍 Seleção Nacional":
                coluna_filtro = 'Seleção'
                label_dropdown = "Escolhe a Seleção:"
                opcoes_filtro = sorted(df[coluna_filtro].dropna().unique())
                
                if st.session_state.selecao_escolhida in opcoes_filtro:
                    idx_padrao = opcoes_filtro.index(st.session_state.selecao_escolhida)
                elif "Portugal" in opcoes_filtro:
                    idx_padrao = opcoes_filtro.index("Portugal")
                else:
                    idx_padrao = 0
                st.selectbox(label_dropdown, opcoes_filtro, index=idx_padrao, key="selecao_escolhida")
            else:
                coluna_filtro = 'Clube'
                label_dropdown = "Escolhe o Clube:"
                opcoes_filtro = df[coluna_filtro].value_counts().index.tolist()
                
                if st.session_state.clube_escolhido in opcoes_filtro:
                    idx_padrao_clube = opcoes_filtro.index(st.session_state.clube_escolhido)
                else:
                    idx_padrao_clube = 0
                st.selectbox(label_dropdown, opcoes_filtro, index=idx_padrao_clube, key="clube_escolhido")

        # 5. SEGUNDO SEPARADOR 
        st.markdown("---")

    with right_logo_section:
        # -------------------------------------------------------------------
        # IMAGEM 9.PNG
        # -------------------------------------------------------------------
        caminho_logo = os.path.join(PASTA_IMAGENS, '9.png')
        if os.path.exists(caminho_logo):
            logo_b64 = get_image_base64(caminho_logo)
            st.markdown(f"""
            <div style="
                display: flex; justify-content: flex-end; align-items: flex-start;
                height: 100%; margin-top: 15px; padding-right: 20px;
            ">
                <img src="{logo_b64}" style="max-height: 120px; width: auto; object-fit: contain;">
            </div>
            """, unsafe_allow_html=True)
    # ===================================================================


    # --- FILTRAGEM E ORDENAÇÃO ---
    escolha_principal = st.session_state.selecao_escolhida if st.session_state.modo_vista == "🌍 Seleção Nacional" else st.session_state.clube_escolhido
    df_filtrado = df[df[coluna_filtro] == escolha_principal].copy()

    df_filtrado['Tem_Imagem'] = df_filtrado['Ficheiro'].apply(imagem_existe)
    ordem_posicoes = ['GR', 'DEF', 'MED', 'AVA', 'Desconhecido']
    df_filtrado['Posição'] = pd.Categorical(df_filtrado['Posição'], categories=ordem_posicoes, ordered=True)
    df_filtrado = df_filtrado.sort_values(['Posição', 'Nome'], ascending=[True, True])

    jogadores_com_foto = df_filtrado[df_filtrado['Tem_Imagem'] == True].to_dict('records')
    jogadores_sem_foto = df_filtrado[df_filtrado['Tem_Imagem'] == False].to_dict('records')

    st.write(f"A mostrar **{len(df_filtrado)}** jogadores em **{escolha_principal}** ({len(jogadores_com_foto)} com foto, {len(jogadores_sem_foto)} em falta)")
    
    # -------------------------------------------------------------------
    # TÍTULO DA SELEÇÃO E INJEÇÕES
    # -------------------------------------------------------------------
    if st.session_state.modo_vista == "🌍 Seleção Nacional" and len(df_filtrado) > 0:
        grupo_emblema = df_filtrado['Grupo'].iloc[0] if tem_texto_valido(df_filtrado['Grupo'].iloc[0]) else ""
        ficheiro_emblema = df_filtrado['Emblema_Selecao'].iloc[0]
        
        if grupo_emblema:
            badge_topo = f"<span style='display:inline-block; background-color:#1e293b; color:white; padding:4px 14px; border-radius:14px; font-size:1.1rem; font-weight:bold; vertical-align:middle; margin-left:12px; margin-bottom:5px;'>{grupo_emblema}</span>"
            st.markdown(f"<h2 style='margin-top:5px; margin-bottom:20px; color:#0f172a;'>{escolha_principal} {badge_topo}</h2>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h2 style='margin-top:5px; margin-bottom:20px; color:#0f172a;'>{escolha_principal}</h2>", unsafe_allow_html=True)
        
        if tem_texto_valido(ficheiro_emblema) and imagem_existe(ficheiro_emblema):
            cromo_equipa = {'Nome': escolha_principal, 'Ficheiro': ficheiro_emblema, 'Tem_Imagem': True, 'É_Emblema': True}
            jogadores_com_foto.insert(0, cromo_equipa)
            
    elif st.session_state.modo_vista == "⚽ Clube / Equipa" and len(df_filtrado) > 0:
        logo_clube = df_filtrado['Logotipo_Clube'].iloc[0]
        if tem_texto_valido(logo_clube):
            cromo_clube = {'Nome': escolha_principal, 'Ficheiro': logo_clube, 'Tem_Imagem': True, 'É_Logo_Clube': True, 'Total_Jogadores': len(df_filtrado)}
            jogadores_com_foto.insert(0, cromo_clube)

    # -------------------------------------------------------------------
    # CSS DINÂMICO E GRELHA DE CROMOS (AGORA COM VERSÃO TELEMÓVEL!)
    # -------------------------------------------------------------------
    css_grid = """
    <style>
    /* COMPORTAMENTO BASE PARA COMPUTADOR (DESKTOP) */
    .grid-container {
        display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 25px; padding: 10px 0;
    }
    .cromo-card { display: flex; flex-direction: column; background: transparent; }
    .cromo-img-container { position: relative; width: 100%; }
    .cromo-img {
        width: 100%; aspect-ratio: 3/4; border-radius: 6px; box-shadow: 0px 4px 8px rgba(0,0,0,0.15);
    }
    .img-cover { object-fit: cover; object-position: top; }
    .img-contain { object-fit: contain; }

    .card-clube {
        width: 100%; aspect-ratio: 3/4; background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
        border: 2px solid #e2e8f0; border-radius: 6px; display: flex; flex-direction: column;
        align-items: center; justify-content: center; padding: 20px; box-sizing: border-box;
        box-shadow: 0px 4px 8px rgba(0,0,0,0.15); text-align: center;
    }
    .card-clube img { width: 120px; height: 120px; object-fit: contain; margin-bottom: 20px; }
    .card-clube-nome { font-size: 1.3rem; font-weight: bold; color: #1e293b; margin: 0 0 15px 0; line-height: 1.2; }
    .card-clube-stats { font-size: 0.95rem; color: #64748b; line-height: 1.2; }
    .card-clube-stats span { font-size: 2.2rem; font-weight: 900; color: #0f172a; display: block; margin-bottom: 4px; }

    .cromo-badge {
        position: absolute; right: 8px; top: 8px; font-size: 30px; background: rgba(255,255,255,0.85);
        border-radius: 50%; padding: 8px; line-height: 1; box-shadow: 0px 3px 6px rgba(0,0,0,0.5); z-index: 10;
    }
    .cromo-info { font-family: sans-serif; margin-top: 10px; }
    .cromo-info h4 { margin: 0 0 8px 0; font-size: 1.1rem; }
    .cromo-info p { margin: 2px 0; font-size: 0.9rem; line-height: 1.4; }
    
    /* COMPORTAMENTO RESPONSIVO PARA TELEMÓVEL (Ecrãs com menos de 600px) */
    @media (max-width: 600px) {
        .grid-container {
            grid-template-columns: repeat(2, 1fr); /* Força a grelha a ter exatamente 2 colunas */
            gap: 12px; /* Reduz o espaço morto entre os cromos */
        }
        .cromo-info h4 { font-size: 0.95rem; margin-bottom: 4px; }
        .cromo-info p { font-size: 0.75rem; margin: 1px 0; line-height: 1.2; }
        .cromo-badge { font-size: 20px; padding: 5px; right: 4px; top: 4px; }
        
        /* Ajusta o tamanho da carta de estatísticas do clube */
        .card-clube { padding: 10px; }
        .card-clube img { width: 70px; height: 70px; margin-bottom: 10px; }
        .card-clube-nome { font-size: 1rem; margin-bottom: 8px; }
        .card-clube-stats { font-size: 0.8rem; }
        .card-clube-stats span { font-size: 1.5rem; }
    }

    /* CSS DA TABELA */
    .tabela-faltantes {
        width: 100%; border-collapse: collapse; margin-top: 10px; font-family: sans-serif; font-size: 0.9rem;
    }
    .tabela-faltantes th {
        background-color: #f1f5f9; color: #1e293b; text-align: left; padding: 8px 12px;
        font-weight: bold; border-bottom: 2px solid #cbd5e1;
    }
    .tabela-faltantes td { padding: 8px 12px; border-bottom: 1px solid #e2e8f0; color: #334155; }
    .tabela-faltantes tr:hover { background-color: #f8fafc; }
    </style>
    """
    
    # RENDERIZAÇÃO DA GRELHA
    html_cards = '<div class="grid-container">'
    
    for row in jogadores_com_foto:
        html_cards += '<div class="cromo-card">'
        
        if row.get('É_Emblema'):
            caminho_imagem = os.path.join(PASTA_IMAGENS, str(row['Ficheiro']).strip())
            img_b64 = get_image_base64(caminho_imagem)
            html_cards += f"""<div class="cromo-img-container"><img src="{img_b64}" class="cromo-img img-contain"></div>"""
            
        elif row.get('É_Logo_Clube'):
            html_cards += f"""
            <div class="card-clube">
                <img src="{row['Ficheiro']}">
                <div class="card-clube-nome">{row['Nome']}</div>
                <div class="card-clube-stats"><span>{row.get('Total_Jogadores', 0)}</span>jogadores selecionados</div>
            </div>
            """
            
        else:
            is_estrela = tem_texto_valido(row.get('Estrela da Equipa'))
            is_surpresa = tem_texto_valido(row.get('Surpresa'))
            badge_html = f"<div class='cromo-badge' title='Estrela'>⭐</div>" if is_estrela else (f"<div class='cromo-badge' title='Surpresa'>⚡</div>" if is_surpresa else "")
            posicao_str = f" ({row['Posição']})" if pd.notna(row.get('Posição')) else ""
            
            caminho_imagem = os.path.join(PASTA_IMAGENS, str(row['Ficheiro']).strip())
            img_b64 = get_image_base64(caminho_imagem)
            
            html_cards += f'<div class="cromo-img-container"><img src="{img_b64}" class="cromo-img img-cover">{badge_html}</div>'
            html_cards += f'<div class="cromo-info"><h4>{row["Nome"]}{posicao_str}</h4>'
            
            if st.session_state.modo_vista == "🌍 Seleção Nacional":
                logo_clube = row.get('Logotipo_Clube')
                clube_url_enc = urllib.parse.quote(row['Clube'])
                link_html_clube = f"<a href='?clube={clube_url_enc}' target='_self' class='link-magico'>{row['Clube']}</a>"
                html_cards += f"<p><strong>Clube:</strong> {link_html_clube} <img src='{logo_clube}' width='18' style='vertical-align: middle; margin-left: 5px;'></p>" if tem_texto_valido(logo_clube) else f"<p><strong>Clube:</strong> {link_html_clube}</p>"
            else:
                selecao_url_enc = urllib.parse.quote(row['Seleção'])
                link_html_selecao = f"<a href='?selecao={selecao_url_enc}' target='_self' class='link-magico'>{row['Seleção']}</a>"
                html_cards += f"<p><strong>Seleção:</strong> {link_html_selecao}</p>"
                
            if tem_texto_valido(row.get('Idade')):
                try:
                    idade = int(float(row['Idade']))
                    html_cards += f"<p><strong>Idade:</strong> {idade} anos</p>"
                except: pass
            caps_txt = str(row['Internacionalizações']).replace('.0', '') if tem_texto_valido(row.get('Internacionalizações')) else "-"
            html_cards += f"<p><strong>Caps:</strong> {caps_txt}</p>"
            valor_txt = str(row['Valor de Mercado']) if tem_texto_valido(row.get('Valor de Mercado')) else "-"
            html_cards += f"<p><strong>Valor:</strong> {valor_txt}</p>"
            html_cards += '</div>' 
            
        html_cards += '</div>' 
        
    html_cards += '</div>' 
    st.markdown(css_grid + html_cards, unsafe_allow_html=True)
    
    # --- TABELA DOS FALTANTES ---
    if jogadores_sem_foto:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.subheader("📋 Restantes Jogadores Inscritos")
        
        col_contexto_label = "Clube" if st.session_state.modo_vista == "🌍 Seleção Nacional" else "Seleção"
        
        html_tabela = f"<div style='overflow-x:auto;'><table class='tabela-faltantes'><thead><tr><th>Posição</th><th>Nome do Jogador</th><th>{col_contexto_label}</th><th>Idade</th><th>Caps</th><th>Valor</th></tr></thead><tbody>"
        
        for p_row in jogadores_sem_foto:
            tag_nome = " ⭐" if tem_texto_valido(p_row.get('Estrela da Equipa')) else (" ⚡" if tem_texto_valido(p_row.get('Surpresa')) else "")
            nome_com_tag = f"{p_row['Nome']}{tag_nome}"
            try: idade_txt = f"{int(float(p_row['Idade']))} anos" if tem_texto_valido(p_row.get('Idade')) else "-"
            except: idade_txt = "-"
                
            if st.session_state.modo_vista == "🌍 Seleção Nacional":
                logo_clube = p_row.get('Logotipo_Clube')
                clube_url_enc = urllib.parse.quote(p_row['Clube'])
                link_html_clube = f"<a href='?clube={clube_url_enc}' target='_self' class='link-magico'>{p_row['Clube']}</a>"
                contexto_txt = f"{link_html_clube} <img src='{logo_clube}' width='14' style='vertical-align: middle; margin-left: 3px;'>" if tem_texto_valido(logo_clube) else link_html_clube
            else:
                selecao_url_enc = urllib.parse.quote(p_row['Seleção'])
                link_html_selecao = f"<a href='?selecao={selecao_url_enc}' target='_self' class='link-magico'>{p_row['Seleção']}</a>"
                contexto_txt = link_html_selecao
                
            caps_txt = str(p_row['Internacionalizações']).replace('.0', '') if tem_texto_valido(p_row.get('Internacionalizações')) else "-"
            valor_txt = str(p_row['Valor de Mercado']) if tem_texto_valido(p_row.get('Valor de Mercado')) else "-"
            
            html_tabela += f"<tr><td><strong>{p_row['Posição']}</strong></td><td>{nome_com_tag}</td><td>{contexto_txt}</td><td>{idade_txt}</td><td>{caps_txt}</td><td>{valor_txt}</td></tr>"
            
        html_tabela += "</tbody></table></div>"
        st.markdown(html_tabela, unsafe_allow_html=True)
        
    st.markdown("---")

    # --- SECÇÕES DE ANÁLISE ---
    st.header(f"📊 Relatório de Análise: {escolha_principal}")
    col_estrelas, col_surpresas = st.columns(2)
    
    with col_estrelas:
        st.subheader("⭐ Estrelas da Equipa")
        df_est = df_filtrado[df_filtrado['Estrela da Equipa'].apply(tem_texto_valido)]
        if not df_est.empty:
            for _, row in df_est.iterrows():
                st.success(f"**{row['Nome']}** ({row['Posição']}) \n\n {row['Estrela da Equipa']}")
        else:
            st.write("Sem estrelas destacadas.")
            
    with col_surpresas:
        st.subheader("⚡ Jogadores Surpresa")
        df_surp = df_filtrado[df_filtrado['Surpresa'].apply(tem_texto_valido)]
        if not df_surp.empty:
            for _, row in df_surp.iterrows():
                st.info(f"**{row['Nome']}** ({row['Posição']}) \n\n {row['Surpresa']}")
        else:
            st.write("Sem surpresas destacadas.")

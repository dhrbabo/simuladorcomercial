import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io

# Configuração da página
st.set_page_config(
    page_title="Sadio | Simulador Comercial",
    page_icon="🧮",
    layout="wide"
)

# Título da aplicação
st.title("🧮 Sadio | Simulador Comercial")
st.markdown("---")

# Função para processar arquivo XLSX
def processar_xlsx(uploaded_file):
    """
    Função para processar arquivo XLSX - estrutura específica do arquivo
    """
    try:
        # Ler o arquivo XLSX sem cabeçalho inicialmente
        df = pd.read_excel(uploaded_file, engine='openpyxl', header=None)
        
        # Exibir informações originais para debug
        st.sidebar.write(f"📊 Arquivo original: {len(df)} linhas, {len(df.columns)} colunas")
        
        # Verificar se temos pelo menos 4 linhas
        if len(df) < 4:
            st.error("❌ Arquivo muito pequeno. Necessário pelo menos 4 linhas.")
            return None
        
        # ESTRUTURA DO ARQUIVO:
        # Linha 0: Cabeçalho geral
        # Linha 1: (vazia ou com outros dados)
        # Linha 2: Cabeçalho real (EAN, NCM, Cod, Descrição, QTD, etc.)
        # Linha 3 em diante: Dados reais
        
        # Pegar o cabeçalho real da linha 2 (índice 2)
        cabecalho_real = df.iloc[2].values.tolist()
        st.sidebar.write("📝 Cabeçalho real encontrado na linha 3")
        
        # Pegar os dados a partir da linha 3 (índice 3)
        dados = df.iloc[3:]
        
        # Criar novo DataFrame com o cabeçalho correto
        df_processado = pd.DataFrame(dados.values, columns=cabecalho_real)
        
        # Excluir a última linha se tiver dados
        if len(df_processado) > 0:
            df_processado = df_processado.iloc[:-1].reset_index(drop=True)
            st.sidebar.write("✅ Última linha removida")
        
        # Limpar nomes de colunas
        df_processado.columns = df_processado.columns.astype(str).str.strip()
        
        # Limpar dados - remover linhas completamente vazias
        df_processado = df_processado.dropna(how='all')
        
        st.sidebar.write(f"📊 Arquivo processado: {len(df_processado)} linhas")
        st.sidebar.write("🔍 Colunas finais:", list(df_processado.columns))
        
        return df_processado
        
    except Exception as e:
        st.error(f"❌ Erro ao processar arquivo XLSX: {str(e)}")
        return None

# Função para mapear colunas automaticamente
def mapear_colunas(df):
    """
    Tenta mapear automaticamente as colunas disponíveis para as colunas esperadas
    """
    mapeamento = {}
    colunas_esperadas = ['EAN', 'Descrição', 'QTD', 'Preco CX', 'Preco UN', 'Grupo']
    colunas_disponiveis = [str(col).strip() for col in df.columns]
    
    st.sidebar.write("🔄 Tentando mapear colunas automaticamente...")
    
    # Mapeamento por padrões conhecidos
    padroes = {
        'EAN': ['ean', 'codigo barras', 'código barras', 'codigo de barras'],
        'Descrição': ['descrição', 'descricao', 'produto', 'nome', 'item'],
        'QTD': ['qtd', 'quantidade', 'qtde', 'qty', 'quant'],
        'Preco CX': ['preco cx', 'precocx', 'preço cx', 'preçocx', 'caixa'],
        'Preco UN': ['preco un', 'precoun', 'preço un', 'preçoun', 'unidade', 'unitário'],
        'Grupo': ['grupo', 'categoria', 'categ', 'familia', 'família']
    }
    
    for col_esperada, possiveis_nomes in padroes.items():
        for col_disponivel in colunas_disponiveis:
            col_lower = col_disponivel.lower()
            for padrao in possiveis_nomes:
                if padrao in col_lower:
                    mapeamento[col_esperada] = col_disponivel
                    st.sidebar.write(f"   ✅ '{col_disponivel}' → '{col_esperada}'")
                    break
            if col_esperada in mapeamento:
                break
    
    return mapeamento

# Função para renomear colunas
def renomear_colunas(df, mapeamento):
    """
    Renomeia as colunas do DataFrame baseado no mapeamento
    """
    return df.rename(columns=mapeamento)

# Função para carregar dados
def load_data(uploaded_file, file_type):
    """
    Função para carregar arquivo CSV ou XLSX com tratamento robusto de erros
    """
    try:
        if file_type == 'xlsx':
            # Processar arquivo XLSX
            df = processar_xlsx(uploaded_file)
            if df is None:
                return None
            
            # Tentar mapear colunas automaticamente
            mapeamento = mapear_colunas(df)
            
            if mapeamento:
                df = renomear_colunas(df, mapeamento)
                st.sidebar.success("✅ Colunas mapeadas automaticamente")
                
        else:
            # Processar arquivo CSV
            content = uploaded_file.getvalue().decode('utf-8')
            
            # Tentar diferentes delimitadores
            delimiters = [',', ';', '\t']
            df = None
            
            for delimiter in delimiters:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(
                        uploaded_file, 
                        delimiter=delimiter,
                        decimal=',', 
                        thousands='.',
                        encoding='utf-8'
                    )
                    
                    if len(df.columns) > 1:
                        st.sidebar.info(f"Delimitador detectado: '{delimiter}'")
                        break
                        
                except Exception:
                    continue
            
            # Se não conseguiu com delimitadores comuns, tentar leitura básica
            if df is None or len(df.columns) <= 1:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='utf-8')
        
        # Verificar se as colunas necessárias existem
        required_columns = ['EAN', 'Descrição', 'QTD', 'Preco CX', 'Preco UN', 'Grupo']
        
        # Mostrar colunas disponíveis
        st.sidebar.write("🔍 Colunas detectadas:", list(df.columns))
        
        # Verificar colunas faltando
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"❌ Colunas faltando: {missing_columns}")
            st.info("📋 Colunas disponíveis: " + ", ".join(df.columns))
            
            # Tentar encontrar colunas similares
            st.info("🔍 Tentando encontrar colunas similares...")
            for req_col in missing_columns:
                for col in df.columns:
                    if req_col.lower() in str(col).lower():
                        st.info(f"   • '{req_col}' pode ser: '{col}'")
                        break
            
            return None
        
        # Limpar e converter dados
        df_clean = df.copy()
        
        # Converter colunas numéricas
        numeric_columns = ['QTD', 'Preco CX', 'Preco UN']
        for col in numeric_columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str).str.replace(',', '.').str.strip()
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        # Converter EAN para string
        if 'EAN' in df_clean.columns:
            df_clean['EAN'] = df_clean['EAN'].astype(str)
        
        # Remover linhas com valores NaN críticos
        colunas_criticas = ['Descrição', 'Preco CX', 'Preco UN']
        for col in colunas_criticas:
            if col in df_clean.columns:
                df_clean = df_clean.dropna(subset=[col])
        
        st.sidebar.success(f"✅ Dados processados: {len(df_clean)} produtos válidos")
        return df_clean
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar o arquivo: {str(e)}")
        return None

# Função para calcular preços com desconto
def calcular_precos_com_desconto(preco_base, quantidade, desconto_percentual, tipo_preco='CX'):
    """
    Calcula preços com desconto aplicado
    """
    desconto_decimal = desconto_percentual / 100
    preco_com_desconto = preco_base * (1 - desconto_decimal)
    
    if tipo_preco == 'CX':
        total = preco_com_desconto * quantidade
        total_sem_desconto = preco_base * quantidade
    else:  # UN
        total = preco_com_desconto * quantidade
        total_sem_desconto = preco_base * quantidade
    
    desconto_total = total_sem_desconto - total
    
    return {
        'preco_unitario_com_desconto': preco_com_desconto,
        'total_com_desconto': total,
        'total_sem_desconto': total_sem_desconto,
        'desconto_total': desconto_total
    }

# Função para converter desconto em R$ para porcentagem
def converter_desconto_reais_para_percentual(desconto_reais, preco_base):
    """
    Converte desconto em R$ para porcentagem
    """
    if preco_base > 0:
        return (desconto_reais / preco_base) * 100
    return 0

# Função para calcular preço com desconto em R$
def calcular_preco_com_desconto_reais(preco_base, desconto_reais, quantidade):
    """
    Calcula preço com desconto direto em R$
    """
    preco_com_desconto = preco_base - desconto_reais
    total_com_desconto = preco_com_desconto * quantidade
    total_sem_desconto = preco_base * quantidade
    desconto_total = total_sem_desconto - total_com_desconto
    
    return {
        'preco_unitario_com_desconto': preco_com_desconto,
        'total_com_desconto': total_com_desconto,
        'total_sem_desconto': total_sem_desconto,
        'desconto_total': desconto_total
    }

# Sidebar para upload do arquivo
st.sidebar.header("📁 Importar Tabela de Preços")

uploaded_file = st.sidebar.file_uploader(
    "Carregue o arquivo com a tabela de preços",
    type=['csv', 'xlsx'],
    help="Suporte para CSV e XLSX. Para XLSX: linhas 1-2 serão excluídas, linha 3 será o cabeçalho, e última linha removida."
)

# Determinar o tipo de arquivo
file_type = None
if uploaded_file is not None:
    if uploaded_file.name.endswith('.xlsx'):
        file_type = 'xlsx'
        st.sidebar.info("📊 Arquivo XLSX detectado")
    else:
        file_type = 'csv'
        st.sidebar.info("📄 Arquivo CSV detectado")

# Inicializar session state
if 'produtos_selecionados' not in st.session_state:
    st.session_state.produtos_selecionados = []
if 'df_produtos' not in st.session_state:
    st.session_state.df_produtos = None
if 'sync_desconto' not in st.session_state:
    st.session_state.sync_desconto = None

# Processar arquivo carregado
if uploaded_file is not None and file_type:
    with st.spinner('Carregando e processando arquivo...'):
        df_loaded = load_data(uploaded_file, file_type)
        if df_loaded is not None:
            st.session_state.df_produtos = df_loaded
            st.sidebar.success(f"✅ Arquivo carregado: {len(df_loaded)} produtos")
            
            # Mostrar estatísticas rápidas
            col1, col2, col3, col4 = st.sidebar.columns(4)
            with col1:
                st.metric("Total Produtos", len(df_loaded))
            with col2:
                st.metric("Grupos", df_loaded['Grupo'].nunique())
            with col3:
                preco_medio_cx = df_loaded['Preco CX'].mean() 
                st.metric("Preço Médio CX", f"R$ {preco_medio_cx:.2f}")
            with col4:
                preco_medio_un = df_loaded['Preco UN'].mean()
                st.metric("Preço Médio UN", f"R$ {preco_medio_un:.2f}")

# Layout principal
if st.session_state.df_produtos is not None:
    df = st.session_state.df_produtos
    
    # Colunas para busca e filtros
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        busca = st.text_input("🔍 Buscar produto:", placeholder="Digite o nome, código ou EAN...")
    
    with col2:
        grupo_filter = st.selectbox(
            "Filtrar por grupo:",
            ["Todos"] + list(df['Grupo'].unique())
        )
    
    with col3:
        marca_options = ["Todos"]
        if 'Marca' in df.columns:
            marca_options.extend(list(df['Marca'].unique()))
        marca_filter = st.selectbox("Filtrar por marca:", marca_options)
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    if busca:
        mask = (df_filtrado['Descrição'].str.contains(busca, case=False, na=False)) | \
               (df_filtrado['Cod'].astype(str).str.contains(busca, na=False)) | \
               (df_filtrado['EAN'].astype(str).str.contains(busca, na=False))
        df_filtrado = df_filtrado[mask]
    
    if grupo_filter != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Grupo'] == grupo_filter]
    
    if marca_filter != "Todos" and 'Marca' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Marca'] == marca_filter]
    
    # Mostrar produtos filtrados
    st.subheader(f"📦 Produtos Disponíveis ({len(df_filtrado)})")
    
    # Selecionar colunas para exibição
    colunas_exibicao = ['Cod', 'Descrição', 'QTD', 'Preco CX', 'Preco UN', 'Grupo']
    if 'Marca' in df_filtrado.columns:
        colunas_exibicao.append('Marca')
    
    # Mostrar apenas as colunas que existem no DataFrame
    colunas_exibicao = [col for col in colunas_exibicao if col in df_filtrado.columns]
    
    st.dataframe(
        df_filtrado[colunas_exibicao].head(50),
        use_container_width=True,
        height=300
    )
    
    # Seção para adicionar produtos à simulação
    st.subheader("➕ Adicionar Produto à Simulação")
    
    if len(df_filtrado) > 0:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            produto_selecionado = st.selectbox(
                "Selecionar produto:",
                df_filtrado['Descrição'].values,
                key="produto_select"
            )
        
        if produto_selecionado:
            produto_info = df_filtrado[df_filtrado['Descrição'] == produto_selecionado].iloc[0]
            
            with col2:
                tipo_venda = st.radio("Tipo:", ["Caixa", "Unidade"], horizontal=True)
            
            with col3:
                quantidade = st.number_input("Quantidade:", min_value=1, value=1, step=1)
            
            with col4:
                st.write("Preços:")
                if tipo_venda == "Caixa":
                    preco_cx = produto_info['Preco CX']
                    st.write(f"**R$ {preco_cx:.2f}**/CX")
                    preco_base = preco_cx
                    preco_unitario = preco_cx
                else:
                    preco_un = produto_info['Preco UN']
                    st.write(f"**R$ {preco_un:.2f}**/UN")
                    preco_base = preco_un
                    preco_unitario = preco_un
            
            # Seção de desconto
            st.subheader("🎯 Configurar Desconto")
            
            col5, col6 = st.columns(2)
            
            with col5:
                st.markdown("**🔘 Desconto em Porcentagem**")
                
                slider_value = 0.0
                if st.session_state.sync_desconto == 'slider':
                    slider_value = st.session_state.get('last_slider_value', 0.0)
                
                desconto_slider = st.slider(
                    "Desconto (%)",
                    min_value=0.0,
                    max_value=50.0,
                    value=slider_value,
                    step=0.5,
                    key="desconto_slider"
                )
                
                desconto_equivalente_reais = preco_unitario * (desconto_slider / 100)
                
                calculo_slider = calcular_precos_com_desconto(
                    preco_unitario, quantidade, desconto_slider, 
                    'CX' if tipo_venda == 'Caixa' else 'UN'
                )
                
                st.metric(
                    "Preço com Desconto",
                    f"R$ {calculo_slider['preco_unitario_com_desconto']:.2f}",
                    delta=f"-{desconto_slider:.1f}%"
                )
                st.caption(f"Equivale a: R$ {desconto_equivalente_reais:.2f} de desconto")
            
            with col6:
                st.markdown("**💰 Desconto em Valor (R$)**")
                
                desconto_maximo_reais = preco_unitario * 0.9
                
                manual_value = 0.0
                if st.session_state.sync_desconto == 'manual':
                    manual_value = st.session_state.get('last_manual_value', 0.0)
                
                desconto_manual_reais = st.number_input(
                    "Valor do Desconto (R$)",
                    min_value=0.0,
                    max_value=float(desconto_maximo_reais),
                    value=manual_value,
                    step=0.10,
                    format="%.2f",
                    key="desconto_manual_reais"
                )
                
                desconto_equivalente_percentual = converter_desconto_reais_para_percentual(desconto_manual_reais, preco_unitario)
                
                calculo_reais = calcular_preco_com_desconto_reais(preco_unitario, desconto_manual_reais, quantidade)
                
                st.metric(
                    "Preço com Desconto",
                    f"R$ {calculo_reais['preco_unitario_com_desconto']:.2f}",
                    delta=f"-R$ {desconto_manual_reais:.2f}"
                )
                st.caption(f"Equivale a: {desconto_equivalente_percentual:.1f}% de desconto")
            
            # Sincronizar campos
           col8:
                if st.button("🔄 Usar R$ em %", use_container_width=True):
                    st.session_state.sync_desconto = 'slider'
                    st.session_state.last_slider_value = min(desconto_equivalente_percentual, 50.0)
                    st.rerun()
            
            # Escolher tipo de desconto
            st.markdown("**🎯 Qual tipo de desconto usar na simulação?**")
            col9, col10 = st.columns(2)
            
            with col9:
                usar_desconto = st.radio(
                    "Selecione o tipo de desconto:",
                    ["Usar Porcentagem", "Usar Valor em R$"],
                    horizontal=True,
                    key="fonte_desconto"
                )
            
            with col10:
                if usar_desconto == "Usar Porcentagem":
                    desconto_final_percentual = desconto_slider
                    desconto_final_reais = desconto_equivalente_reais
                    tipo = "Porcentagem"
                    preco_final = calculo_slider['preco_unitario_com_desconto']
                    total_final = calculo_slider['total_com_desconto']
                    calculo_final = calculo_slider
                else:
                    desconto_final_percentual = desconto_equivalente_percentual
                    desconto_final_reais = desconto_manual_reais
                    tipo = "Reais"
                    preco_final = calculo_reais['preco_unitario_com_desconto']
                    total_final = calculo_reais['total_com_desconto']
                    calculo_final = calculo_reais
                
                st.info(f"**Desconto selecionado:**")
                st.info(f"**{desconto_final_percentual:.1f}%** | **R$ {desconto_final_reais:.2f}**")
                st.success(f"**Preço final:** R$ {preco_final:.2f}")
                st.success(f"**Total do item:** R$ {total_final:.2f}")
            
            # Botão para adicionar à simulação
            col11, col12, col13 = st.columns([1, 2, 1])
            
            with col12:
                if st.button("➕ Adicionar à Simulação", use_container_width=True, type="primary"):
                    novo_produto = {
                        'codigo': produto_info['Cod'],
                        'descricao': produto_info['Descrição'],
                        'tipo': tipo_venda,
                        'quantidade': quantidade,
                        'preco_base': preco_unitario,
                        'desconto_percentual': desconto_final_percentual,
                        'desconto_reais': desconto_final_reais,
                        'preco_com_desconto': calculo_final['preco_unitario_com_desconto'],
                        'total_com_desconto': calculo_final['total_com_desconto'],
                        'total_sem_desconto': calculo_final['total_sem_desconto'],
                        'desconto_total': calculo_final['desconto_total'],
                        'tipo_desconto': tipo
                    }
                    
                    st.session_state.produtos_selecionados.append(novo_produto)
                    st.success(f"✅ Produto adicionado! Desconto: {desconto_final_percentual:.1f}% (R$ {desconto_final_reais:.2f})")
                    st.rerun()
    else:
        st.warning("⚠️ Nenhum produto encontrado com os filtros aplicados.")
    
    # Seção da simulação
    if st.session_state.produtos_selecionados:
        st.subheader("🛒 Simulação Comercial")
        
        # Tabela de produtos na simulação
        dados_simulacao = []
        for i, produto in enumerate(st.session_state.produtos_selecionados):
            dados_simulacao.append({
                'Item': i + 1,
                'Código': produto['codigo'],
                'Descrição': produto['descricao'],
                'Tipo': produto['tipo'],
                'Qtd': produto['quantidade'],
                'Preço Base': f"R$ {produto['preco_base']:.2f}",
                'Desconto %': f"{produto['desconto_percentual']:.1f}%",
                'Desconto R$': f"R$ {produto['desconto_reais']:.2f}",
                'Tipo Desc.': produto['tipo_desconto'],
                'Preço c/ Desc': f"R$ {produto['preco_com_desconto']:.2f}",
                'Total': f"R$ {produto['total_com_desconto']:.2f}"
            })
        
        df_simulacao = pd.DataFrame(dados_simulacao)
        st.dataframe(df_simulacao, use_container_width=True)
        
        # Resumo financeiro
        st.subheader("📊 Resumo da Simulação")
        
        total_sem_desconto = sum(p['total_sem_desconto'] for p in st.session_state.produtos_selecionados)
        total_com_desconto = sum(p['total_com_desconto'] for p in st.session_state.produtos_selecionados)
        total_desconto = sum(p['desconto_total'] for p in st.session_state.produtos_selecionados)
        percentual_desconto_medio = (total_desconto / total_sem_desconto * 100) if total_sem_desconto > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total sem Desconto", f"R$ {total_sem_desconto:.2f}")
        with col2:
            st.metric("Total com Desconto", f"R$ {total_com_desconto:.2f}")
        with col3:
            st.metric("Desconto Total", f"R$ {total_desconto:.2f}")
        with col4:
            st.metric("Desconto Médio", f"{percentual_desconto_medio:.1f}%")
        
        # Botões de ação
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Limpar Simulação", use_container_width=True):
                st.session_state.produtos_selecionados = []
                st.session_state.sync_desconto = None
                st.rerun()
        
        with col2:
            # Criar DataFrame para exportação
            export_data = []
            for produto in st.session_state.produtos_selecionados:
                export_data.append({
                    'Código': produto['codigo'],
                    'Descrição': produto['descricao'],
                    'Tipo_Venda': produto['tipo'],
                    'Quantidade': produto['quantidade'],
                    'Preço_Base': produto['preco_base'],
                    'Desconto_Percentual': produto['desconto_percentual'],
                    'Desconto_Reais': produto['desconto_reais'],
                    'Tipo_Desconto': produto['tipo_desconto'],
                    'Preço_Com_Desconto': produto['preco_com_desconto'],
                    'Total_Com_Desconto': produto['total_com_desconto']
                })
            
            df_export = pd.DataFrame(export_data)
            csv = df_export.to_csv(index=False, decimal=',', sep=';')
            
            st.download_button(
                label="💾 Exportar Simulação",
                data=csv,
                file_name=f"simulacao_comercial_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )

else:
    # Tela inicial quando não há arquivo carregado
    st.info("👆 Por favor, carregue um arquivo CSV ou XLSX com a tabela de preços na sidebar para começar.")
    
    # Exemplo de estrutura esperada
    st.subheader("📋 Estrutura Esperada do Arquivo")
    
    exemplo_data = {
        'EAN': ['7898950000000', '7898950000000', '7898950000000'],
        'NCM': ['34029039', '34029039', '34029039'],
        'Cod': [9880, 9881, 9882],
        'Descrição': [
            'DETERGENTE LIMAO 500ML TANLUX | CX - 20/500ML',
            'DETERGENTE MACA 500ML TANLUX | CX - 20/500ML', 
            'DETERGENTE NEUTRO 500ML TANLUX | CX - 20/500ML'
        ],
        'QTD': [20.00, 20.00, 20.00],
        'X': ['X', 'X', 'X'],
        'Peso': [500, 500, 500],
        'Preco CX': [21.00, 21.00, 21.00],
        'Preco UN': [1.05, 1.05, 1.05],
        'Grupo': ['DETERGENTE', 'DETERGENTE', 'DETERGENTE'],
        'Peso CX': [10.8, 10.8, 10.8],
        'Ultima Venda': ['', '', ''],
        'Valor Ultima Venda': [0.00, 0.00, 0.00],
        'Cod Grupo': [10200100, 10200100, 10200100],
        'Marca': ['TANLUX', 'TANLUX', 'TANLUX'],
        'DUN': ['17899000000000', '17899000000000', '17899000000000']
    }
    
    df_exemplo = pd.DataFrame(exemplo_data)
    st.dataframe(df_exemplo, use_container_width=True)

# Rodapé
st.markdown("---")
st.markdown(
    "**Sadio | Simulador Comercial** - Para suporte, entre em contato com o administrador do sistema - Daniel Babo."

)


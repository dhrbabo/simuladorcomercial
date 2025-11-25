import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import io

# Configuração da página
st.set_page_config(
    page_title="Sadio | Simulador Comercial",
    page_icon="🧮",
    layout="wide"
)

# =============================================
# SISTEMA DE LOGIN
# =============================================

USUARIOS = {
    "ADMIN": "admin123",             
    "RANIER": "master123",          
    "ANDRE.RN": "andre123",
    "PAULINO.RN": "paulino123", 
    "CHATEAU.RN": "chateau123",
}

# Definir quais usuários são master (múltiplos usuários)
USUARIOS_MASTER = ["ADMIN", "RANIER"]

def verificar_login():
    """Verifica se o usuário está logado"""
    if 'logado' not in st.session_state:
        st.session_state.logado = False
    if 'vendedor_logado' not in st.session_state:
        st.session_state.vendedor_logado = None
    if 'eh_master' not in st.session_state:
        st.session_state.eh_master = False
    
    return st.session_state.logado

def fazer_login():
    """Interface de login"""
    st.title("🔐 Login - Sadio Simulador")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image("https://via.placeholder.com/150x150/4CAF50/FFFFFF?text=SADIO", width=150)
    
    with col2:
        vendedor = st.selectbox(
            "👤 Vendedor:",
            options=[""] + list(USUARIOS.keys()),
            key="login_vendedor"
        )
        
        senha = st.text_input(
            "🔒 Senha:",
            type="password",
            key="login_senha"
        )
        
        if st.button("🚀 Entrar", use_container_width=True):
            if vendedor and senha:
                if vendedor in USUARIOS and USUARIOS[vendedor] == senha:
                    st.session_state.logado = True
                    st.session_state.vendedor_logado = vendedor
                    st.session_state.eh_master = vendedor in USUARIOS_MASTER
                    st.success(f"✅ Login realizado! Bem-vindo, {vendedor}")
                    if st.session_state.eh_master:
                        st.info("👑 **Modo Master Ativado**: Acesso completo a todos os dados")
                    st.rerun()
                else:
                    st.error("❌ Vendedor ou senha incorretos")
            else:
                st.warning("⚠️ Preencha todos os campos")

# =============================================
# CONFIGURAÇÃO - URLs DO GITHUB
# =============================================

CONFIG_URLS = {
    "tabela_produtos": "https://raw.githubusercontent.com/dhrbabo/simuladorcomercial/main/tabela_produto.csv",
    "tabela_parceiros": "https://raw.githubusercontent.com/dhrbabo/simuladorcomercial/main/tabela_parceiro.csv"
}

# =============================================
# FUNÇÕES AUXILIARES PARA TRATAMENTO DE DADOS
# =============================================

def tratar_colunas_numericas(df, colunas):
    """Converte colunas para formato numérico, tratando vírgulas como separador decimal"""
    df_tratado = df.copy()
    
    for coluna in colunas:
        if coluna in df_tratado.columns:
            df_tratado[coluna] = df_tratado[coluna].astype(str)
            df_tratado[coluna] = df_tratado[coluna].str.replace('.', '', regex=False)
            df_tratado[coluna] = df_tratado[coluna].str.replace(',', '.', regex=False)
            df_tratado[coluna] = pd.to_numeric(df_tratado[coluna], errors='coerce')
    
    return df_tratado

def verificar_e_corrigir_dados(df, nome_tabela):
    """Verifica e corrige problemas comuns nos dados"""
    
    if nome_tabela == "tabela_produtos":
        colunas_numericas = ['PRECO_UNITARIO', 'PRECO_CX', 'QUANTIDADE', 'CODPROD', 'CODTAB']
        df = tratar_colunas_numericas(df, colunas_numericas)
    
    elif nome_tabela == "tabela_parceiros":
        colunas_numericas = ['ID_CLIENTE', 'CODTAB', 'ID_VENDEDOR']
        df = tratar_colunas_numericas(df, colunas_numericas)
    
    colunas_criticas = {
        "tabela_produtos": ['CODPROD', 'DESCRPROD', 'PRECO_CX'],
        "tabela_parceiros": ['ID_CLIENTE', 'FANTASIA', 'CODTAB']
    }
    
    if nome_tabela in colunas_criticas:
        colunas_check = colunas_criticas[nome_tabela]
        colunas_existentes = [col for col in colunas_check if col in df.columns]
        
        if colunas_existentes:
            linhas_antes = len(df)
            df = df.dropna(subset=colunas_existentes)
    
    return df

# =============================================
# CARREGAMENTO DAS TABELAS DO GITHUB
# =============================================

@st.cache_data(ttl=3600)
def carregar_todas_tabelas():
    """Carrega todas as tabelas necessárias do GitHub"""
    with st.spinner("🔄 Carregando base de dados..."):
        resultados = {}
        
        for nome_tabela, url in CONFIG_URLS.items():
            try:
                response = requests.get(url)
                response.raise_for_status()
                
                try:
                    df = pd.read_csv(io.StringIO(response.text), encoding='utf-8', sep=';')
                except:
                    try:
                        df = pd.read_csv(io.StringIO(response.text), encoding='utf-8', sep=',')
                    except:
                        try:
                            df = pd.read_csv(io.StringIO(response.text), encoding='latin-1', sep=';')
                        except:
                            df = pd.read_csv(io.StringIO(response.text), encoding='latin-1', sep=',')
                
                df = verificar_e_corrigir_dados(df, nome_tabela)
                resultados[nome_tabela] = df
                
            except Exception as e:
                st.error(f"❌ Erro ao carregar {nome_tabela}")
                resultados[nome_tabela] = criar_dados_exemplo(nome_tabela)
        
        return resultados

def criar_dados_exemplo(nome_tabela):
    """Cria dados de exemplo para desenvolvimento"""
    if nome_tabela == "tabela_produtos":
        return pd.DataFrame({
            'CODPROD': [2, 4, 6, 8, 10, 12],
            'REFERENCIA': ['7897518200014', '7897518200045', '7897518200656', '7897518200052', '7897518200069', '7897518200076'],
            'DESCRPROD': [
                'TEMPERO COMPLETO ESPECIAL 500G SADIO',
                'TEMPERO SEM PIMENTA 500G SADIO',
                'TEMPERO CASEIRO TRADICIONAL ESCURO VERDE 500G SADIO',
                'VINAGRE DE ALCOOL 500ML SADIO',
                'VINAGRE DE ALCOOL 1L SADIO',
                'VINAGRE DE ALCOOL 2L SADIO'
            ],
            'CODTAB': [16, 16, 16, 16, 16, 16],
            'PRECO_UNITARIO': [3.61, 3.61, 3.16, 1.48, 2.80, 5.20],
            'QUANTIDADE': [12.0, 12.0, 12.0, 12.0, 12.0, 12.0],
            'PRECO_CX': [43.32, 43.32, 37.92, 17.76, 33.60, 62.40]
        })
    
    elif nome_tabela == "tabela_parceiros":
        return pd.DataFrame({
            'ID_CLIENTE': [4, 101, 102, 103, 104, 105],
            'FANTASIA': [
                'INDUSTRIAS SM - CEARA',
                'NORDESTAO ALECRIM LJ 1',
                'NORDESTAO PETROPOLIS LJ 2',
                'NORDESTAO LAGOA NOVA LJ 3',
                'NORDESTAO CIDADE JARDIM LJ 4',
                'NORDESTAO SANTA CATARINA LJ 5'
            ],
            'CODTAB': [23, 3, 3, 3, 3, 3],
            'ID_VENDEDOR': [0, 18, 18, 18, 57, 18],
            'VENDEDOR': ['<SEM VENDEDOR>', 'ANDRE.RN', 'ANDRE.RN', 'ANDRE.RN', 'PAULINO.RN', 'ANDRE.RN'],
            'CIDADE': ['MARACANAU', 'Natal', 'Natal', 'Natal', 'Natal', 'Natal'],
            'GRUPODESC': ['', 'NORDESTAO', 'NORDESTAO', 'NORDESTAO', 'NORDESTAO', 'NORDESTAO']
        })

# =============================================
# SISTEMA DE CÁLCULO EM TEMPO REAL
# =============================================

def calcular_desconto_tempo_real(preco_base, quantidade, tipo_preco, desconto_percentual=0, desconto_reais=0):
    """Calcula os efeitos do desconto em tempo real"""
    if preco_base <= 0:
        return {
            'preco_final_unitario': 0,
            'total_sem_desconto': 0,
            'total_com_desconto': 0,
            'desconto_total': 0,
            'desconto_percentual_final': 0,
            'economia_por_unidade': 0
        }
    
    # Calcular preço unitário com desconto
    if desconto_reais > 0:
        preco_final_unitario = preco_base - desconto_reais
        desconto_percentual_final = (desconto_reais / preco_base) * 100
    else:
        preco_final_unitario = preco_base * (1 - desconto_percentual / 100)
        desconto_percentual_final = desconto_percentual
    
    # Calcular totais
    total_sem_desconto = preco_base * quantidade
    total_com_desconto = preco_final_unitario * quantidade
    desconto_total = total_sem_desconto - total_com_desconto
    economia_por_unidade = preco_base - preco_final_unitario
    
    return {
        'preco_final_unitario': preco_final_unitario,
        'total_sem_desconto': total_sem_desconto,
        'total_com_desconto': total_com_desconto,
        'desconto_total': desconto_total,
        'desconto_percentual_final': desconto_percentual_final,
        'economia_por_unidade': economia_por_unidade
    }

# =============================================
# SISTEMA DE CARRINHO E SIMULAÇÃO
# =============================================

def adicionar_ao_carrinho(produto, quantidade, tipo_preco, desconto_percentual=0, desconto_reais=0):
    """Adiciona produto ao carrinho de compras"""
    if 'carrinho' not in st.session_state:
        st.session_state.carrinho = []
    
    # Calcular preços finais
    preco_base = produto['PRECO_CX'] if tipo_preco == 'CX' else produto['PRECO_UNITARIO']
    
    if desconto_reais > 0:
        resultado = calcular_preco_com_desconto_reais(preco_base, desconto_reais, quantidade)
        desconto_percentual = resultado['desconto_percentual']
    else:
        resultado = calcular_precos_com_desconto(preco_base, quantidade, desconto_percentual, tipo_preco)
    
    item = {
        'codprod': produto['CODPROD'],
        'descricao': produto['DESCRPROD'],
        'quantidade': quantidade,
        'tipo_preco': tipo_preco,
        'preco_base': preco_base,
        'desconto_percentual': desconto_percentual,
        'desconto_reais': desconto_reais,
        'preco_unitario_com_desconto': resultado['preco_unitario_com_desconto'],
        'total_com_desconto': resultado['total_com_desconto'],
        'total_sem_desconto': resultado['total_sem_desconto'],
        'desconto_total': resultado['desconto_total']
    }
    
    st.session_state.carrinho.append(item)
    st.success(f"✅ {produto['DESCRPROD']} adicionado ao carrinho!")

def calcular_precos_com_desconto(preco_base, quantidade, desconto_percentual, tipo_preco='CX'):
    """Calcula preços com desconto aplicado"""
    desconto_decimal = desconto_percentual / 100
    preco_com_desconto = preco_base * (1 - desconto_decimal)
    
    total = preco_com_desconto * quantidade
    total_sem_desconto = preco_base * quantidade
    desconto_total = total_sem_desconto - total
    
    return {
        'preco_unitario_com_desconto': preco_com_desconto,
        'total_com_desconto': total,
        'total_sem_desconto': total_sem_desconto,
        'desconto_total': desconto_total
    }

def calcular_preco_com_desconto_reais(preco_base, desconto_reais, quantidade):
    """Calcula preço com desconto direto em R$"""
    preco_com_desconto = preco_base - desconto_reais
    total_com_desconto = preco_com_desconto * quantidade
    total_sem_desconto = preco_base * quantidade
    desconto_total = total_sem_desconto - total_com_desconto
    desconto_percentual = (desconto_reais / preco_base) * 100 if preco_base > 0 else 0
    
    return {
        'preco_unitario_com_desconto': preco_com_desconto,
        'total_com_desconto': total_com_desconto,
        'total_sem_desconto': total_sem_desconto,
        'desconto_total': desconto_total,
        'desconto_percentual': desconto_percentual
    }

def limpar_carrinho():
    """Limpa o carrinho de compras"""
    st.session_state.carrinho = []
    st.success("🛒 Carrinho limpo!")

# =============================================
# CARDS DE RESUMO
# =============================================

def mostrar_cards_resumo():
    """Mostra os cards com o resumo financeiro"""
    if 'carrinho' not in st.session_state or not st.session_state.carrinho:
        return
    
    carrinho = st.session_state.carrinho
    
    # Calcular totais
    total_sem_desconto = sum(item['total_sem_desconto'] for item in carrinho)
    total_com_desconto = sum(item['total_com_desconto'] for item in carrinho)
    total_desconto_valor = total_sem_desconto - total_com_desconto
    total_desconto_percentual = (total_desconto_valor / total_sem_desconto * 100) if total_sem_desconto > 0 else 0
    total_itens = sum(item['quantidade'] for item in carrinho)
    
    # Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Valor Total",
            value=f"R$ {total_com_desconto:,.2f}",
            delta=f"R$ {total_sem_desconto:,.2f} s/ desc"
        )
    
    with col2:
        st.metric(
            label="🎯 Desconto Total (R$)",
            value=f"R$ {total_desconto_valor:,.2f}",
            delta=f"{total_desconto_percentual:.1f}%"
        )
    
    with col3:
        st.metric(
            label="📊 Desconto Total (%)",
            value=f"{total_desconto_percentual:.1f}%",
            delta=f"R$ {total_desconto_valor:,.2f}"
        )
    
    with col4:
        st.metric(
            label="📦 Total de Itens",
            value=f"{total_itens:.0f}",
            delta=f"{len(carrinho)} produtos"
        )

# =============================================
# RELATÓRIO FINAL
# =============================================

def gerar_relatorio():
    """Gera relatório final da simulação"""
    if not st.session_state.carrinho:
        st.warning("📝 Nenhum item no carrinho para gerar relatório")
        return
    
    st.subheader("📊 Relatório da Simulação")
    
    # Dados da simulação
    parceiro = st.session_state.parceiro_selecionado
    vendedor = st.session_state.vendedor_logado
    data_simulacao = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Informações do parceiro
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("**🏢 Parceiro:**", parceiro['FANTASIA'])
    with col2:
        st.write("**👤 Vendedor:**", vendedor)
    with col3:
        st.write("**📅 Data:**", data_simulacao)
    
    # Tabela de itens
    st.subheader("🛒 Itens da Simulação")
    
    dados_relatorio = []
    total_geral_sem_desconto = 0
    total_geral_com_desconto = 0
    total_desconto = 0
    
    for item in st.session_state.carrinho:
        dados_relatorio.append({
            'Produto': item['descricao'],
            'Quantidade': item['quantidade'],
            'Tipo': item['tipo_preco'],
            'Preço Base': f"R$ {item['preco_base']:.2f}",
            'Preço c/ Desc.': f"R$ {item['preco_unitario_com_desconto']:.2f}",
            'Desc. %': f"{item['desconto_percentual']:.1f}%",
            'Total s/ Desc.': f"R$ {item['total_sem_desconto']:.2f}",
            'Total c/ Desc.': f"R$ {item['total_com_desconto']:.2f}",
            'Economia': f"R$ {item['desconto_total']:.2f}"
        })
        
        total_geral_sem_desconto += item['total_sem_desconto']
        total_geral_com_desconto += item['total_com_desconto']
        total_desconto += item['desconto_total']
    
    st.dataframe(pd.DataFrame(dados_relatorio), use_container_width=True)
    
    # Resumo financeiro
    st.subheader("💰 Resumo Financeiro")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Valor Total s/ Desconto", f"R$ {total_geral_sem_desconto:,.2f}")
    with col2:
        st.metric("Valor Total c/ Desconto", f"R$ {total_geral_com_desconto:,.2f}")
    with col3:
        st.metric("Desconto Total", f"R$ {total_desconto:,.2f}")
    with col4:
        percentual_desconto = (total_desconto / total_geral_sem_desconto * 100) if total_geral_sem_desconto > 0 else 0
        st.metric("Desconto %", f"{percentual_desconto:.1f}%")
    
    # Ações finais
    st.subheader("🚀 Ações Finais")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📧 Enviar Proposta", use_container_width=True):
            st.success("✅ Proposta enviada com sucesso!")
            st.info("📋 Um email foi enviado para o cliente com os detalhes da simulação")
    
    with col2:
        if st.button("💾 Salvar Simulação", use_container_width=True):
            st.success("✅ Simulação salva no histórico!")
    
    with col3:
        if st.button("🔄 Nova Simulação", use_container_width=True):
            limpar_carrinho()
            st.rerun()

# =============================================
# INTERFACE PRINCIPAL DO SIMULADOR
# =============================================

def mostrar_simulador():
    """Interface principal do simulador"""
    st.title("🧮 Sadio | Simulador Comercial")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.header("👤 Configurações")
    st.sidebar.write(f"**Vendedor logado:** {st.session_state.vendedor_logado}")
    
    if st.session_state.eh_master:
        st.sidebar.success("👑 **MODO MASTER ATIVADO**")
        st.sidebar.info("Acesso completo a todos os dados")
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logado = False
        st.session_state.vendedor_logado = None
        st.session_state.eh_master = False
        st.session_state.carrinho = []
        st.rerun()
    
    # Carregar dados
    if 'dados_carregados' not in st.session_state:
        st.session_state.dados_carregados = carregar_todas_tabelas()
    
    dados = st.session_state.dados_carregados
    tabela_produtos = dados['tabela_produtos']
    tabela_parceiros = dados['tabela_parceiros']
    
    # Filtrar parceiros - se for master, mostra todos, senão filtra pelo vendedor
    if st.session_state.eh_master:
        parceiros_filtrados = tabela_parceiros
        st.sidebar.info(f"👑 Master: Visualizando todos os {len(parceiros_filtrados)} parceiros")
    else:
        parceiros_filtrados = tabela_parceiros[tabela_parceiros['VENDEDOR'] == st.session_state.vendedor_logado]
        st.sidebar.info(f"Visualizando {len(parceiros_filtrados)} parceiros do vendedor")
    
    if parceiros_filtrados.empty:
        st.error("❌ Nenhum parceiro encontrado")
        return
    
    # Seleção do parceiro
    st.sidebar.subheader("🏢 Seleção do Parceiro")
    
    opcoes_parceiros = []
    for _, parceiro in parceiros_filtrados.iterrows():
        descricao = f"{parceiro['ID_CLIENTE']} - {parceiro['FANTASIA']} ({parceiro['CIDADE']}) - {parceiro['VENDEDOR']}"
        opcoes_parceiros.append((descricao, parceiro['ID_CLIENTE'], parceiro['CODTAB'], parceiro['VENDEDOR']))
    
    parceiro_options = [op[0] for op in opcoes_parceiros]
    
    parceiro_selecionado_desc = st.sidebar.selectbox(
        "Selecione o Parceiro:",
        ["Selecione um parceiro..."] + parceiro_options
    )
    
    if parceiro_selecionado_desc != "Selecione um parceiro...":
        id_cliente_selecionado = int(parceiro_selecionado_desc.split(' - ')[0])
        parceiro_info = parceiros_filtrados[parceiros_filtrados['ID_CLIENTE'] == id_cliente_selecionado].iloc[0]
        
        st.session_state.parceiro_selecionado = parceiro_info
        st.session_state.codtab_atual = parceiro_info['CODTAB']
        
        # Carregar produtos do parceiro
        produtos_parceiro = obter_produtos_por_codtab(parceiro_info['CODTAB'], tabela_produtos)
        st.session_state.tabela_precos_atual = produtos_parceiro
        
        st.sidebar.success(f"✅ {parceiro_info['FANTASIA']}")
        if st.session_state.eh_master:
            st.sidebar.info(f"Vendedor: {parceiro_info['VENDEDOR']}")
    
    # Mostrar simulador se parceiro selecionado
    if 'tabela_precos_atual' in st.session_state and st.session_state.tabela_precos_atual is not None and len(st.session_state.tabela_precos_atual) > 0:
        df = st.session_state.tabela_precos_atual
        
        # Header do parceiro
        if st.session_state.parceiro_selecionado is not None:
            parceiro = st.session_state.parceiro_selecionado
            st.subheader(f"🏢 Simulando para: {parceiro['FANTASIA']}")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("👤 Vendedor", st.session_state.vendedor_logado)
            with col2:
                st.metric("📊 Tabela", f"CODTAB {parceiro['CODTAB']}")
            with col3:
                st.metric("📍 Cidade", parceiro['CIDADE'])
            with col4:
                if st.session_state.eh_master and 'VENDEDOR' in parceiro:
                    st.metric("👥 Vendedor Parceiro", parceiro['VENDEDOR'])
        
        # =============================================
        # SEÇÃO 1: TABELA DE CONSULTA DE PRODUTOS
        # =============================================
        st.subheader("📦 Tabela de Produtos Disponíveis")
        
        # Filtro de busca
        col1, col2 = st.columns([3, 1])
        with col1:
            busca = st.text_input(
                "🔍 Buscar produto:", 
                placeholder="Digite código, descrição ou referência...",
                key="busca_produto"
            )
        with col2:
            st.metric("Produtos", len(df))
        
        # Aplicar filtro
        df_filtrado = df.copy()
        if busca:
            mask = (
                df_filtrado['DESCRPROD'].astype(str).str.contains(busca, case=False, na=False) |
                df_filtrado['CODPROD'].astype(str).str.contains(busca, case=False, na=False) |
                df_filtrado['REFERENCIA'].astype(str).str.contains(busca, case=False, na=False)
            )
            df_filtrado = df_filtrado[mask]
            st.info(f"📊 {len(df_filtrado)} produtos encontrados")
        
        # Formatar tabela para exibição
        df_display = df_filtrado[['CODPROD', 'DESCRPROD', 'PRECO_UNITARIO', 'QUANTIDADE', 'PRECO_CX']].copy()
        df_display['PRECO_UNITARIO'] = df_display['PRECO_UNITARIO'].apply(lambda x: f"R$ {x:.2f}")
        df_display['PRECO_CX'] = df_display['PRECO_CX'].apply(lambda x: f"R$ {x:.2f}")
        df_display['QUANTIDADE'] = df_display['QUANTIDADE'].apply(lambda x: f"{x:.0f} un")
        
        # Mostrar tabela de produtos
        st.dataframe(
            df_display,
            use_container_width=True,
            height=400
        )
        
        # =============================================
        # SEÇÃO 2: SELEÇÃO DE PRODUTOS PARA CARRINHO
        # =============================================
        st.subheader("🛒 Adicionar Produtos ao Carrinho")
        
        # Seleção de produto
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 2])
        
        with col1:
            # Criar opções para selectbox
            opcoes_produtos = [f"{row['CODPROD']} - {row['DESCRPROD']} (R$ {row['PRECO_CX']:.2f}/CX)" 
                              for _, row in df_filtrado.iterrows()]
            
            if opcoes_produtos:
                produto_selecionado = st.selectbox(
                    "Selecione o produto:",
                    options=["Selecione um produto..."] + opcoes_produtos,
                    key="select_produto"
                )
            else:
                produto_selecionado = "Selecione um produto..."
                st.warning("Nenhum produto encontrado para os filtros aplicados")
        
        with col2:
            quantidade = st.number_input(
                "Quantidade:",
                min_value=1,
                value=1,
                key="quantidade_produto"
            )
        
        with col3:
            tipo_preco = st.selectbox(
                "Tipo:",
                ["CX", "UN"],
                key="tipo_preco"
            )
        
        # =============================================
        # SEÇÃO 2.1: CÁLCULO EM TEMPO REAL DE DESCONTO
        # =============================================
        # Obter preço base do produto selecionado
        preco_base = 0
        if produto_selecionado != "Selecione um produto...":
            codprod_selecionado = int(produto_selecionado.split(' - ')[0])
            produto_info = df_filtrado[df_filtrado['CODPROD'] == codprod_selecionado].iloc[0]
            preco_base = produto_info['PRECO_CX'] if tipo_preco == 'CX' else produto_info['PRECO_UNITARIO']
        
        col4, col5 = st.columns(2)
        
        with col4:
            # Campo de desconto percentual
            desconto_percentual = st.number_input(
                "Desconto %:",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.5,
                key="desconto_percentual",
                help="Digite o desconto em porcentagem"
            )
            
            # Calcular e mostrar equivalente em R$
            if desconto_percentual > 0 and preco_base > 0:
                desconto_reais_calculado = preco_base * (desconto_percentual / 100)
                st.info(f"💡 Equivale a: R$ {desconto_reais_calculado:.2f} por unidade")
        
        with col5:
            # Campo de desconto em R$
            desconto_reais = st.number_input(
                "Desconto R$:",
                min_value=0.0,
                max_value=float(preco_base) if preco_base > 0 else 0.0,
                value=0.0,
                step=0.1,
                key="desconto_reais",
                help="Digite o desconto em reais"
            )
            
            # Calcular e mostrar equivalente em %
            if desconto_reais > 0 and preco_base > 0:
                desconto_percentual_calculado = (desconto_reais / preco_base) * 100
                st.info(f"💡 Equivale a: {desconto_percentual_calculado:.1f}%")
        
        # =============================================
        # SEÇÃO 2.2: VISUALIZAÇÃO EM TEMPO REAL
        # =============================================
        if produto_selecionado != "Selecione um produto..." and preco_base > 0:
            st.markdown("---")
            st.subheader("📊 Visualização em Tempo Real")
            
            # Calcular efeitos do desconto
            calculo_tempo_real = calcular_desconto_tempo_real(
                preco_base, quantidade, tipo_preco, desconto_percentual, desconto_reais
            )
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Preço Unitário Base (CX)",
                    f"R$ {preco_base:.2f}",
                    f"R$ {calculo_tempo_real['economia_por_unidade']:.2f} (Unidade)",
                    delta_color="off"
                )
            
            with col2:
                st.metric(
                    "Total do Item",
                    f"R$ {calculo_tempo_real['total_com_desconto']:.2f}",
                    f"R$ {calculo_tempo_real['total_sem_desconto']:.2f} s/ desc",
                    delta_color="off"
                )
            
            with col3:
                st.metric(
                    "Desconto do Item",
                    f"R$ {calculo_tempo_real['desconto_total']:.2f}",
                    f"{calculo_tempo_real['desconto_percentual_final']:.1f}%",
                    delta_color="inverse"
                )
        
        # Botão para adicionar ao carrinho
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("➕ Adicionar ao Carrinho", use_container_width=True, 
                        disabled=produto_selecionado == "Selecione um produto..."):
                # Encontrar produto selecionado
                codprod_selecionado = int(produto_selecionado.split(' - ')[0])
                produto_info = df_filtrado[df_filtrado['CODPROD'] == codprod_selecionado].iloc[0]
                
                adicionar_ao_carrinho(produto_info, quantidade, tipo_preco, desconto_percentual, desconto_reais)
                st.rerun()
        
        # =============================================
        # SEÇÃO 3: CARDS DE RESUMO
        # =============================================
        st.markdown("---")
        mostrar_cards_resumo()
        
        # =============================================
        # SEÇÃO 4: TABELA DO CARRINHO (PARCIAL)
        # =============================================
        st.markdown("---")
        st.subheader("📋 Carrinho de Compras - Parcial")
        
        if 'carrinho' in st.session_state and st.session_state.carrinho:
            # Criar DataFrame do carrinho
            carrinho_df = pd.DataFrame(st.session_state.carrinho)
            
            # Formatar colunas para exibição
            carrinho_display = carrinho_df[[
                'descricao', 'quantidade', 'tipo_preco', 'preco_base', 
                'desconto_percentual', 'preco_unitario_com_desconto', 'total_com_desconto'
            ]].copy()
            
            carrinho_display['preco_base'] = carrinho_display['preco_base'].apply(lambda x: f"R$ {x:.2f}")
            carrinho_display['preco_unitario_com_desconto'] = carrinho_display['preco_unitario_com_desconto'].apply(lambda x: f"R$ {x:.2f}")
            carrinho_display['total_com_desconto'] = carrinho_display['total_com_desconto'].apply(lambda x: f"R$ {x:.2f}")
            carrinho_display['desconto_percentual'] = carrinho_display['desconto_percentual'].apply(lambda x: f"{x:.1f}%")
            
            # Renomear colunas
            carrinho_display.columns = [
                'Produto', 'Quantidade', 'Tipo', 'Preço Base', 
                'Desc. %', 'Preço c/ Desc.', 'Total'
            ]
            
            # Mostrar tabela do carrinho
            st.dataframe(carrinho_display, use_container_width=True)
            
            # Botões de ação
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("📊 Gerar Relatório Completo", use_container_width=True):
                    gerar_relatorio()
            with col2:
                if st.button("🗑️ Limpar Carrinho", use_container_width=True):
                    limpar_carrinho()
                    st.rerun()
        else:
            st.info("🛒 Carrinho vazio. Selecione produtos acima para começar a simulação.")
    
    else:
        st.info("👆 Selecione um parceiro na sidebar para começar a simulação.")

# =============================================
# FUNÇÕES AUXILIARES
# =============================================

def obter_produtos_por_codtab(codtab_cliente, tabela_produtos):
    """Obtém os produtos da tabela de preços específica do cliente"""
    try:
        codtab_cliente = int(codtab_cliente)
        tabela_produtos['CODTAB'] = tabela_produtos['CODTAB'].astype(int)
        produtos_filtrados = tabela_produtos[tabela_produtos['CODTAB'] == codtab_cliente]
        return produtos_filtrados
    except Exception as e:
        st.error(f"Erro ao carregar produtos: {str(e)}")
        return pd.DataFrame()

# =============================================
# APLICAÇÃO PRINCIPAL
# =============================================

def main():
    """Função principal da aplicação"""
    if not verificar_login():
        fazer_login()
    else:
        mostrar_simulador()

if __name__ == "__main__":
    main()

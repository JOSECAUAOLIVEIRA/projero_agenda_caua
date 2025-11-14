import streamlit as st
import sqlite3
import datetime
import os

# Configuração da página
st.set_page_config(
    page_title="Agenda de Tarefas",
    page_icon="📅",
    layout="wide"
)

# =============================================
# BANCO DE DADOS - FUNÇÕES
# =============================================

def criar_conexao():
    """Cria conexão com o banco SQLite"""
    # Criar pasta database se não existir
    os.makedirs('database', exist_ok=True)
    
    conn = sqlite3.connect('database/agenda.db', check_same_thread=False)
    # Ativar chaves estrangeiras
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def criar_tabelas():
    """Cria todas as tabelas necessárias para SQLite"""
    conn = criar_conexao()
    cursor = conn.cursor()
    
    # Tabela de dias da semana
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dias_semana (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            ordem INTEGER NOT NULL
        )
    ''')
    
    # Tabela de tarefas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dia_semana_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            descricao TEXT,
            horario TEXT,
            prioridade TEXT DEFAULT 'media',
            concluida INTEGER DEFAULT 0,
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dia_semana_id) REFERENCES dias_semana (id)
        )
    ''')
    
    conn.commit()
    
    # Inserir dias da semana padrão
    dias_semana = [
        ('Segunda-feira', 1),
        ('Terça-feira', 2),
        ('Quarta-feira', 3),
        ('Quinta-feira', 4),
        ('Sexta-feira', 5),
        ('Sábado', 6),
        ('Domingo', 7)
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO dias_semana (nome, ordem) 
        VALUES (?, ?)
    ''', dias_semana)
    
    conn.commit()
    conn.close()

def adicionar_tarefa(dia_semana_id, titulo, descricao=None, horario=None, prioridade='media'):
    """Adiciona uma nova tarefa"""
    conn = criar_conexao()
    cursor = conn.cursor()
    
    # Validar prioridade
    prioridades_validas = ['baixa', 'media', 'alta']
    if prioridade not in prioridades_validas:
        prioridade = 'media'
    
    cursor.execute('''
        INSERT INTO tarefas (dia_semana_id, titulo, descricao, horario, prioridade)
        VALUES (?, ?, ?, ?, ?)
    ''', (dia_semana_id, titulo, descricao, horario, prioridade))
    
    conn.commit()
    conn.close()
    return cursor.lastrowid

def listar_tarefas_por_dia(dia_semana_id):
    """Lista todas as tarefas de um dia específico"""
    conn = criar_conexao()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.id, t.dia_semana_id, t.titulo, t.descricao, t.horario, 
               t.prioridade, t.concluida, t.data_criacao, ds.nome as dia_nome 
        FROM tarefas t 
        JOIN dias_semana ds ON t.dia_semana_id = ds.id 
        WHERE t.dia_semana_id = ? 
        ORDER BY 
            CASE 
                WHEN t.horario IS NULL THEN 1
                ELSE 0
            END,
            t.horario,
            CASE t.prioridade
                WHEN 'alta' THEN 1
                WHEN 'media' THEN 2
                WHEN 'baixa' THEN 3
                ELSE 4
            END
    ''', (dia_semana_id,))
    
    tarefas = cursor.fetchall()
    conn.close()
    return tarefas

def listar_todas_tarefas():
    """Lista todas as tarefas de todos os dias"""
    conn = criar_conexao()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.id, t.dia_semana_id, t.titulo, t.descricao, t.horario, 
               t.prioridade, t.concluida, t.data_criacao, 
               ds.nome as dia_nome, ds.ordem
        FROM tarefas t 
        JOIN dias_semana ds ON t.dia_semana_id = ds.id 
        ORDER BY ds.ordem, 
            CASE 
                WHEN t.horario IS NULL THEN 1
                ELSE 0
            END,
            t.horario,
            CASE t.prioridade
                WHEN 'alta' THEN 1
                WHEN 'media' THEN 2
                WHEN 'baixa' THEN 3
                ELSE 4
            END
    ''')
    
    tarefas = cursor.fetchall()
    conn.close()
    return tarefas

def listar_dias_semana():
    """Lista todos os dias da semana"""
    conn = criar_conexao()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, nome, ordem FROM dias_semana ORDER BY ordem')
    dias = cursor.fetchall()
    conn.close()
    return dias

def atualizar_tarefa(tarefa_id, **kwargs):
    """Atualiza uma tarefa existente"""
    conn = criar_conexao()
    cursor = conn.cursor()
    
    campos = []
    valores = []
    
    for campo, valor in kwargs.items():
        if campo == 'prioridade' and valor not in ['baixa', 'media', 'alta']:
            continue
        campos.append(f"{campo} = ?")
        valores.append(valor)
    
    valores.append(tarefa_id)
    
    query = f"UPDATE tarefas SET {', '.join(campos)} WHERE id = ?"
    cursor.execute(query, valores)
    
    conn.commit()
    conn.close()

def excluir_tarefa(tarefa_id):
    """Exclui uma tarefa"""
    conn = criar_conexao()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM tarefas WHERE id = ?', (tarefa_id,))
    
    conn.commit()
    conn.close()

def marcar_concluida(tarefa_id, concluida=True):
    """Marca uma tarefa como concluída ou não"""
    conn = criar_conexao()
    cursor = conn.cursor()
    
    concluida_int = 1 if concluida else 0
    cursor.execute('UPDATE tarefas SET concluida = ? WHERE id = ?', (concluida_int, tarefa_id))
    
    conn.commit()
    conn.close()

def buscar_tarefas(termo):
    """Busca tarefas por termo"""
    conn = criar_conexao()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.id, t.dia_semana_id, t.titulo, t.descricao, t.horario, 
               t.prioridade, t.concluida, t.data_criacao, ds.nome as dia_nome
        FROM tarefas t 
        JOIN dias_semana ds ON t.dia_semana_id = ds.id 
        WHERE t.titulo LIKE ? OR t.descricao LIKE ?
        ORDER BY ds.ordem, t.horario
    ''', (f'%{termo}%', f'%{termo}%'))
    
    tarefas = cursor.fetchall()
    conn.close()
    return tarefas

def contar_estatisticas():
    """Conta estatísticas das tarefas"""
    tarefas = listar_todas_tarefas()
    total = len(tarefas)
    concluidas = sum(1 for t in tarefas if t[6])  # índice 6 = concluida
    
    prioridades = {'alta': 0, 'media': 0, 'baixa': 0}
    for tarefa in tarefas:
        prioridade = tarefa[5]  # índice 5 = prioridade
        if prioridade in prioridades:
            prioridades[prioridade] += 1
    
    return {
        'total': total,
        'concluidas': concluidas,
        'prioridades': prioridades
    }

# =============================================
# INTERFACE STREAMLIT
# =============================================

def main():
    st.title("📅 Minha Agenda de Tarefas")
    
    # Inicializar banco de dados
    criar_tabelas()
    
    # Menu lateral
    menu = st.sidebar.selectbox(
        "Menu",
        ["🏠 Visão Semanal", "➕ Adicionar Tarefa", "📋 Todas as Tarefas", "🔍 Buscar", "📊 Estatísticas"]
    )
    
    # Mostrar estatísticas rápidas no sidebar
    mostrar_estatisticas_sidebar()
    
    # Navegação entre páginas
    if menu == "🏠 Visão Semanal":
        mostrar_visao_semanal()
    elif menu == "➕ Adicionar Tarefa":
        mostrar_adicionar_tarefa()
    elif menu == "📋 Todas as Tarefas":
        mostrar_todas_tarefas()
    elif menu == "🔍 Buscar":
        mostrar_buscar()
    elif menu == "📊 Estatísticas":
        mostrar_estatisticas_completas()

def mostrar_estatisticas_sidebar():
    """Mostra estatísticas rápidas na sidebar"""
    st.sidebar.divider()
    stats = contar_estatisticas()
    
    st.sidebar.write("**📊 Resumo:**")
    st.sidebar.write(f"Total: {stats['total']}")
    st.sidebar.write(f"Concluídas: {stats['concluidas']}")
    
    if stats['total'] > 0:
        porcentagem = (stats['concluidas'] / stats['total']) * 100
        st.sidebar.write(f"Progresso: {porcentagem:.1f}%")
        st.sidebar.progress(porcentagem / 100)

def mostrar_visao_semanal():
    st.header("📋 Visão Semanal")
    
    # Botão para adicionar tarefa rápido
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Adicionar Tarefa Rápida", use_container_width=True):
            st.session_state.show_quick_add = True
    
    # Formulário rápido para adicionar tarefa
    if st.session_state.get('show_quick_add', False):
        with st.form("quick_add_form"):
            st.subheader("Adicionar Tarefa Rápida")
            
            dias = listar_dias_semana()
            dias_dict = {nome: id for id, nome, ordem in dias}
            
            col1, col2 = st.columns(2)
            with col1:
                dia_selecionado = st.selectbox("Dia", options=list(dias_dict.keys()))
                titulo = st.text_input("Título*")
            with col2:
                prioridade = st.selectbox("Prioridade", options=["baixa", "media", "alta"], index=1)
                horario = st.text_input("Horário (HH:MM)", placeholder="09:00")
            
            descricao = st.text_area("Descrição (opcional)")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                submitted = st.form_submit_button("Adicionar Tarefa", use_container_width=True)
            with col3:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state.show_quick_add = False
                    st.rerun()
            
            if submitted:
                if titulo:
                    dia_id = dias_dict[dia_selecionado]
                    
                    if horario:
                        try:
                            datetime.datetime.strptime(horario, '%H:%M')
                        except ValueError:
                            st.error("❌ Formato de horário inválido! Use HH:MM")
                            st.stop()
                    
                    try:
                        adicionar_tarefa(dia_id, titulo, descricao, horario, prioridade)
                        st.success("✅ Tarefa adicionada com sucesso!")
                        st.session_state.show_quick_add = False
                        st.rerun()
                    except sqlite3.Error as e:
                        st.error(f"❌ Erro ao adicionar tarefa: {e}")
                else:
                    st.error("❌ Título é obrigatório!")
        
        st.divider()
    
    # Mostrar dias da semana
    dias = listar_dias_semana()
    
    for dia in dias:
        dia_id, nome, ordem = dia
        with st.expander(f"📅 {nome}", expanded=True):
            tarefas = listar_tarefas_por_dia(dia_id)
            
            if not tarefas:
                st.info("Nenhuma tarefa para este dia.")
                continue
            
            for tarefa in tarefas:
                exibir_tarefa(tarefa)

def mostrar_adicionar_tarefa():
    st.header("➕ Adicionar Nova Tarefa")
    
    with st.form("form_tarefa", clear_on_submit=True):
        dias = listar_dias_semana()
        dias_dict = {nome: id for id, nome, ordem in dias}
        
        col1, col2 = st.columns(2)
        
        with col1:
            dia_selecionado = st.selectbox(
                "Dia da Semana*",
                options=list(dias_dict.keys())
            )
            
            titulo = st.text_input("Título da Tarefa*")
            
            prioridade = st.selectbox(
                "Prioridade",
                options=["baixa", "media", "alta"],
                index=1
            )
        
        with col2:
            horario = st.text_input("Horário (HH:MM)", placeholder="Ex: 09:00, 14:30")
            
            descricao = st.text_area("Descrição", height=100)
        
        submitted = st.form_submit_button("Adicionar Tarefa", use_container_width=True)
        
        if submitted:
            if titulo and dia_selecionado:
                dia_id = dias_dict[dia_selecionado]
                
                # Validar formato do horário
                if horario:
                    try:
                        datetime.datetime.strptime(horario, '%H:%M')
                    except ValueError:
                        st.error("❌ Formato de horário inválido! Use HH:MM")
                        return
                
                try:
                    adicionar_tarefa(dia_id, titulo, descricao, horario, prioridade)
                    st.success("✅ Tarefa adicionada com sucesso!")
                    st.rerun()
                except sqlite3.Error as e:
                    st.error(f"❌ Erro ao adicionar tarefa: {e}")
            else:
                st.error("❌ Título e Dia da Semana são obrigatórios!")

def mostrar_todas_tarefas():
    st.header("📋 Todas as Tarefas")
    
    tarefas = listar_todas_tarefas()
    
    if not tarefas:
        st.info("📝 Nenhuma tarefa cadastrada. Comece adicionando uma tarefa!")
        return
    
    st.write(f"**Total:** {len(tarefas)} tarefas")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        filtrar_concluidas = st.selectbox("Status", ["Todas", "Pendentes", "Concluídas"])
    with col2:
        filtrar_prioridade = st.selectbox("Prioridade", ["Todas", "Alta", "Média", "Baixa"])
    with col3:
        filtrar_dia = st.selectbox("Dia", ["Todos"] + [nome for id, nome, ordem in listar_dias_semana()])
    
    # Aplicar filtros
    tarefas_filtradas = []
    for tarefa in tarefas:
        (id, dia_id, titulo, descricao, horario, prioridade, 
         concluida, data_criacao, dia_nome, ordem) = tarefa
        
        # Filtro de status
        if filtrar_concluidas == "Pendentes" and concluida:
            continue
        if filtrar_concluidas == "Concluídas" and not concluida:
            continue
        
        # Filtro de prioridade
        if filtrar_prioridade != "Todas" and prioridade.lower() != filtrar_prioridade.lower():
            continue
        
        # Filtro de dia
        if filtrar_dia != "Todos" and dia_nome != filtrar_dia:
            continue
        
        tarefas_filtradas.append(tarefa)
    
    st.write(f"**Mostrando:** {len(tarefas_filtradas)} tarefas")
    
    for tarefa in tarefas_filtradas:
        exibir_tarefa(tarefa)

def mostrar_buscar():
    st.header("🔍 Buscar Tarefas")
    
    termo = st.text_input("Digite o termo de busca (título ou descrição)")
    
    if termo:
        tarefas = buscar_tarefas(termo)
        
        if tarefas:
            st.write(f"**{len(tarefas)}** tarefa(s) encontrada(s):")
            for tarefa in tarefas:
                exibir_tarefa(tarefa)
        else:
            st.info("🔍 Nenhuma tarefa encontrada com esse termo.")
    else:
        st.info("🔍 Digite um termo para buscar nas tarefas.")

def mostrar_estatisticas_completas():
    st.header("📊 Estatísticas Detalhadas")
    
    stats = contar_estatisticas()
    total = stats['total']
    
    if total == 0:
        st.info("📝 Nenhuma tarefa para mostrar estatísticas.")
        return
    
    concluidas = stats['concluidas']
    porcentagem = (concluidas / total) * 100
    
    # Métricas principais
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Tarefas", total)
    with col2:
        st.metric("Tarefas Concluídas", concluidas)
    with col3:
        st.metric("Taxa de Conclusão", f"{porcentagem:.1f}%")
    
    # Progress bar
    st.progress(porcentagem / 100)
    
    # Estatísticas por prioridade
    st.subheader("📈 Distribuição por Prioridade")
    prioridades = stats['prioridades']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔴 Alta", prioridades['alta'])
    with col2:
        st.metric("🟡 Média", prioridades['media'])
    with col3:
        st.metric("🟢 Baixa", prioridades['baixa'])
    
    # Gráfico de pizza simples (usando texto)
    st.subheader("🍕 Distribuição Visual")
    
    if total > 0:
        cols = st.columns(3)
        labels = ['Concluídas', 'Pendentes']
        values = [concluidas, total - concluidas]
        
        with cols[0]:
            st.write("**Status**")
            for label, value in zip(labels, values):
                st.write(f"{label}: {value} ({value/total*100:.1f}%)")
        
        with cols[1]:
            st.write("**Prioridades**")
            for prioridade, valor in prioridades.items():
                if valor > 0:
                    st.write(f"{prioridade.title()}: {valor} ({valor/total*100:.1f}%)")
    
    # Tarefas recentes
    st.subheader("🕒 Tarefas Recentes")
    tarefas_recentes = listar_todas_tarefas()[:5]  # Últimas 5 tarefas
    if tarefas_recentes:
        for tarefa in tarefas_recentes:
            (id, dia_id, titulo, descricao, horario, prioridade, 
             concluida, data_criacao, dia_nome, ordem) = tarefa
            
            status = "✅" if concluida else "⏳"
            st.write(f"{status} **{titulo}** - {dia_nome} ({prioridade.title()})")
    else:
        st.info("Nenhuma tarefa recente.")

def exibir_tarefa(tarefa):
    """Exibe uma tarefa individualmente"""
    (id, dia_id, titulo, descricao, horario, prioridade, 
     concluida, data_criacao, dia_nome, *extra) = tarefa
    
    # Container para cada tarefa
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        
        with col1:
            # Status (concluída ou pendente) - riscado se concluído
            status = "✅" if concluida else "⏳"
            if concluida:
                st.write(f"{status} ~~{titulo}~~")
                st.caption("Concluída")
            else:
                st.write(f"{status} **{titulo}**")
            
            if descricao:
                st.caption(descricao)
        
        with col2:
            # Horário e dia
            if horario:
                st.write(f"🕒 {horario}")
            st.write(f"📅 {dia_nome}")
            
            # Data de criação
            if data_criacao:
                try:
                    data = datetime.datetime.strptime(data_criacao, '%Y-%m-%d %H:%M:%S')
                    st.caption(f"Criada: {data.strftime('%d/%m/%Y')}")
                except:
                    st.caption(f"Criada: {data_criacao}")
        
        with col3:
            # Prioridade com cores
            cores = {'alta': '🔴', 'media': '🟡', 'baixa': '🟢'}
            st.write(f"{cores.get(prioridade, '⚪')} {prioridade.title()}")
        
        with col4:
            # Botões de ação
            col_a, col_b = st.columns(2)
            
            with col_a:
                if concluida:
                    if st.button("↩️", key=f"desfazer_{id}", help="Desfazer conclusão"):
                        marcar_concluida(id, False)
                        st.rerun()
                else:
                    if st.button("✔️", key=f"concluir_{id}", help="Marcar como concluída"):
                        marcar_concluida(id, True)
                        st.rerun()
            
            with col_b:
                if st.button("🗑️", key=f"excluir_{id}", help="Excluir tarefa"):
                    excluir_tarefa(id)
                    st.success("🗑️ Tarefa excluída!")
                    st.rerun()
        
        st.divider()

# =============================================
# INICIALIZAÇÃO
# =============================================

if __name__ == "__main__":
    # Inicializar session state
    if 'show_quick_add' not in st.session_state:
        st.session_state.show_quick_add = False
    
    main()
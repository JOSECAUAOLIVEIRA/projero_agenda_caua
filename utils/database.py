import sqlite3
import streamlit as st
from datetime import datetime

def criar_conexao():
    """Cria conexão com o banco SQLite"""
    conn = sqlite3.connect('database/agenda.db', check_same_thread=False)
    # Ativar chaves estrangeiras
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def criar_tabelas():
    """Cria todas as tabelas necessárias para SQLite"""
    conn = criar_conexao()
    cursor = conn.cursor()
    
    # Tabela de dias da semana - CORRIGIDA
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dias_semana (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            ordem INTEGER NOT NULL
        )
    ''')
    
    # Tabela de tarefas - CORRIGIDA para SQLite
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dia_semana_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            descricao TEXT,
            horario TEXT,  -- Mudado para TEXT no SQLite
            prioridade TEXT DEFAULT 'media',
            concluida INTEGER DEFAULT 0,  -- INTEGER no lugar de BOOLEAN (0 = false, 1 = true)
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dia_semana_id) REFERENCES dias_semana (id)
        )
    ''')
    
    conn.commit()
    
    # Inserir dias da semana padrão
    inserir_dias_semana(cursor)
    
    conn.commit()
    conn.close()

def inserir_dias_semana(cursor):
    """Insere os dias da semana na tabela"""
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

# Operações CRUD para Tarefas - ATUALIZADAS
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
        # Validação específica para prioridade
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
    
    # Converter boolean para integer (SQLite)
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
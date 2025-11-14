import streamlit as st
from utils.database import criar_conexao, criar_tabelas
import sqlite3

# Configuração da página
st.set_page_config(
    page_title="Meu App",
    page_icon="🚀",
    layout="wide"
)

# Inicializar banco de dados
criar_tabelas()

def main():
    st.title("🚀 Meu Projeto Streamlit + SQLite")
    
    # Menu lateral
    menu = st.sidebar.selectbox(
        "Menu",
        ["Home", "Cadastrar", "Consultar", "Sobre"]
    )
    
    if menu == "Home":
        mostrar_home()
    elif menu == "Cadastrar":
        mostrar_cadastro()
    elif menu == "Consultar":
        mostrar_consulta()
    elif menu == "Sobre":
        mostrar_sobre()

def mostrar_home():
    st.header("Bem-vindo ao Sistema!")
    st.write("Use o menu lateral para navegar.")

def mostrar_cadastro():
    st.header("Cadastrar Novo Usuário")
    
    with st.form("form_cadastro"):
        nome = st.text_input("Nome")
        email = st.text_input("E-mail")
        
        if st.form_submit_button("Cadastrar"):
            if nome and email:
                cadastrar_usuario(nome, email)
                st.success("Usuário cadastrado com sucesso!")
            else:
                st.error("Preencha todos os campos!")

def mostrar_consulta():
    st.header("Consultar Usuários")
    usuarios = listar_usuarios()
    
    if usuarios:
        st.table(usuarios)
    else:
        st.info("Nenhum usuário cadastrado.")

def mostrar_sobre():
    st.header("Sobre o Projeto")
    st.write("Este é um projeto exemplo usando Streamlit e SQLite.")

def cadastrar_usuario(nome, email):
    """Cadastra um novo usuário no banco"""
    conn = criar_conexao()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO usuarios (nome, email) VALUES (?, ?)",
            (nome, email)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        st.error("E-mail já cadastrado!")
    finally:
        conn.close()

def listar_usuarios():
    """Lista todos os usuários do banco"""
    conn = criar_conexao()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()
    
    conn.close()
    return usuarios

if __name__ == "__main__":
    main()
import pyrebase
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridUpdateMode
from st_aggrid.grid_options_builder import GridOptionsBuilder

firebaseConfig = st.secrets['firebaseConfig']
          
# firebase authentication
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

# database
db = firebase.database()
storage = firebase.storage()

st.set_page_config(page_title="Steris Sellout", page_icon="🧊")
st.image("steris-logo-vector.png", width=200)

placeholder = st.empty()

# initialize state
if 'key' not in st.session_state:
  st.session_state.key = False

user = ''
if ~st.session_state.key:
  try:
    with placeholder.form(key="my-form"):
      options = st.selectbox('Entrar/Registrar', ['Entrar', 'Registrar'])
      email = st.text_input('Informar e-mail')
      password = st.text_input('Informar password', type='password')
      
      if options:
        submit = st.form_submit_button('Enviar')
        if submit:
          st.session_state.key = True
          if(options == 'Registrar'):
            #Signup 
            user = auth.create_user_with_email_and_password(email, password)
            st.success('Usuário criado com sucesso')
            st.balloons()
          else:
            # Login
            user = auth.sign_in_with_email_and_password(email, password)
            # db.child(user['localId']).child("Handle").set(email)
            # db.child(user['localId']).child("ID").set(user['localId'])
  except ValueError:
    st.error('Verifique os dados: email e senha', icon="⚠️")
    user = ''
    st.session_state.key = False
    placeholder.empty()
    
# download dataframe
@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(sep=';', encoding='latin1', header=True, decimal=',')

# editable table
@st.cache
def editable_df(df):
  gd = GridOptionsBuilder.from_dataframe(df)
  gd.configure_pagination(enabled=True)
  gd.configure_default_column(editable=True, groupable=True, headerCheckboxSelection=True)
  
  sel_mode = st.radio('Selecione o tipo', options=['single','multiple'])
  gd.configure_selection(selection_mode=sel_mode, use_checkbox=True)
  grid_options = gd.build()
  grid_table = AgGrid(df, try_to_convert_back_to_original_types=False, gridOptions=grid_options, update_mode= GridUpdateMode.SELECTION_CHANGED | GridUpdateMode.VALUE_CHANGED, allow_unsafe_jscode=True, height=500 )
  sel_row = grid_table['selected_rows']
  
  df_grid = pd.DataFrame(sel_row)
  
  csv = convert_df(df)
  st.download_button(
    label="Download tabela modificada como CSV",
    data=csv,
    file_name='dados_alterados.csv',
    mime='text/csv',  
  )
  st.subheader('Linhas atualizadas: ')
  st.table(data=df_grid)

@st.cache
def clean_transform_df(df):
    nan_value = float('NaN')
    csv = df.to_csv().encode('utf-8')
    df_updated = csv['NFE_NRONOTAFISCAL'].replace("", nan_value, inplace=True)
    df_updated = df_updated.dropna(subset='NFE_NRONOTAFISCAL', inplace=True)
    if df_updated['Dealer/Rep']:
        df_updated = df_updated[['Dealer/Rep','NFE_DATAEMISSAO','NFE_NRONOTAFISCAL', 'NFE_DEST_CNPJ','NFE_DEST_RAZAOSOCIAL','NFE_DEST_ESTADO','DEST_QTDEPRODUTO','DEST_CODIGOPRODUTO_STERIS', 'DEST_CODIGOCFOP']]
    if not df_updated['Dealer/Rep']:
        df_updated = df_updated[['NFE_DATAEMISSAO','NFE_NRONOTAFISCAL', 'NFE_DEST_CNPJ','NFE_DEST_RAZAOSOCIAL','NFE_DEST_ESTADO','DEST_QTDEPRODUTO','DEST_CODIGOPRODUTO_STERIS', 'DEST_CODIGOCFOP']]
    return df_updated
  
if st.session_state.key:
  placeholder.empty()
  c = st.container()
  # ---- MAINPAGE ----
  c.title("Arquivo em formato CSV - Steris")
  c.markdown("""---""")
  with open('produto.csv', 'rb') as file:
    c.download_button('Lista de Produtos Steris', data=file, file_name='Produtos.csv', mime='txt/csv')

  uploaded_file = c.file_uploader("Clique aqui para subir o seu arquivo TXT/CSV", type=["txt", "csv"], on_change=None, key="my-file", accept_multiple_files=False)

  if uploaded_file:
    df = pd.read_csv(uploaded_file, sep=";", encoding='latin1')
    df_changed = clean_transform_df(df)
    editable_df(df_changed)
    #out = df_changed.to_json(orient='records')[1:-1]
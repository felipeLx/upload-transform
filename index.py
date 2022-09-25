# from sharepoint import SharePoint
import pyrebase
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridUpdateMode, JsCode
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
@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(sep=';', encoding='latin1', header=True, decimal=',')

if st.session_state.key:
  _funct = st.sidebar.radio(label='Alterar ou Apagar linhas', options=['Alterar', 'Apagar'])

# editable table
# @st.cache(suppress_st_warning=True, allow_output_mutation=True)
def editable_df(df):
  dataframe = df
  gd = GridOptionsBuilder.from_dataframe(dataframe)
  gd.configure_pagination(enabled=True)
  gd.configure_default_column(editable=True, groupable=True)
  
  if _funct == 'Alterar':
    grid_options = gd.build()
    grid_table = AgGrid(dataframe, 
                try_to_convert_back_to_original_types=False, 
                gridOptions=grid_options, 
                update_mode= GridUpdateMode.SELECTION_CHANGED | GridUpdateMode.VALUE_CHANGED, allow_unsafe_jscode=True, 
                height=500, 
                width='100%',
                reload_data = False,
                theme='streamlit')
    sel_row = grid_table['data']
    df_grid = pd.DataFrame(sel_row)
    dataframe.update(df_grid)
  
  if _funct == 'Apagar':
    js = JsCode("""
    function(e) {
        let api = e.api;
        let sel = api.getSelectedRows();
        api.applyTransaction({remove: sel})    
    };
    """     
    )  
    
    gd.configure_selection(selection_mode= 'single')
    gd.configure_grid_options(onRowSelected = js,pre_selected_rows=[])
    gridOptions = gd.build()
    grid_table = AgGrid(dataframe, 
                try_to_convert_back_to_original_types=False,
                gridOptions = gridOptions, 
                height=500,
                width='100%',
                theme = "streamlit",
                update_mode = GridUpdateMode.SELECTION_CHANGED,
                reload_data = False,
                allow_unsafe_jscode=True,
                )
    sel_row = grid_table['data']
    df_grid = pd.DataFrame(sel_row)
    dataframe.update(df_grid)  
  
  csv = convert_df(dataframe)
  check_df(dataframe)
  st.download_button(
    label="Download tabela modificada como CSV",
    data=csv,
    file_name='dados_alterados.csv',
    mime='text/csv',  
  )

@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def transform_coluns(df):
  dataframe = df
  dataframe['NFE_DATAEMISSAO'] = dataframe['NFE_DATAEMISSAO'].str.replace("00:00", "")
  # dataframe['NFE_DATAEMISSAO'] = pd.to_datetime(dataframe['NFE_DATAEMISSAO'], format='%d/%m/%Y')
  dataframe['NFE_DEST_CNPJ'] = dataframe['NFE_DEST_CNPJ'].str.replace("[./-]", "")
  dataframe['DEST_CODIGOCFOP'] = dataframe['DEST_CODIGOCFOP'].str.replace("[.,]", "")
  dataframe['DEST_CODIGOCFOP'] = dataframe['DEST_CODIGOCFOP'].str[-4:]
  dataframe['NFE_DEST_RAZAOSOCIAL'] = dataframe['NFE_DEST_RAZAOSOCIAL'].str.replace("[.,-<>()/0123456789\t]", "")
  dataframe['DEST_CODIGOPRODUTO_STERIS'] = dataframe['DEST_CODIGOPRODUTO_STERIS'].str.strip()
  dataframe['NFE_DEST_RAZAOSOCIAL'] = dataframe['NFE_DEST_RAZAOSOCIAL'].str.replace("Ê", "E")
  dataframe['NFE_DEST_RAZAOSOCIAL'] = dataframe['NFE_DEST_RAZAOSOCIAL'].str.replace("Ã", "A")
  dataframe['NFE_DEST_RAZAOSOCIAL'] = dataframe['NFE_DEST_RAZAOSOCIAL'].str.replace("Õ", "O")
  dataframe['NFE_DEST_RAZAOSOCIAL'] = dataframe['NFE_DEST_RAZAOSOCIAL'].str.replace("Ç", "C")
  dataframe['DEST_QTDEPRODUTO'] = dataframe['DEST_QTDEPRODUTO'].str.replace(",", ".").astype(float)
  dataframe = dataframe.rename(columns={'NFE_DEST_RAZAOSOCIAL': 'RAZAO_SOCIAL'})
  return dataframe

# data clean and transformation
@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def clean_transform_df(df):
  dataframe = df
  nan_value = float('NaN')
  dataframe.replace("", nan_value, inplace=True)
  dataframe.dropna(subset='NFE_NRONOTAFISCAL', inplace=True)
  
  # df_updated = dataframe
  if 'Dealer/Rep' in dataframe.columns:
      df_updated = dataframe[['Dealer/Rep','NFE_DATAEMISSAO','NFE_NRONOTAFISCAL', 'NFE_DEST_CNPJ','NFE_DEST_RAZAOSOCIAL','NFE_DEST_ESTADO','DEST_QTDEPRODUTO','DEST_CODIGOPRODUTO_STERIS', 'DEST_CODIGOCFOP']]
      df_cleaned = transform_coluns(df_updated)
      return df_cleaned
  else:
      df_updated = dataframe[['NFE_DATAEMISSAO','NFE_NRONOTAFISCAL', 'NFE_DEST_CNPJ','NFE_DEST_RAZAOSOCIAL','NFE_DEST_ESTADO','DEST_QTDEPRODUTO','DEST_CODIGOPRODUTO_STERIS', 'DEST_CODIGOCFOP']]
      df_cleaned = transform_coluns(df_updated)
      return df_cleaned

# verify if some Product code not exist in the Steris list code
# @st.cache(suppress_st_warning=True, allow_output_mutation=True, show_spinner=True, persist=False)
def check_df(df):
  dataframe = df
  with open('produto.csv', 'rb') as file:
    df_prod = pd.read_csv(file, header=0, usecols=['Product Number'], encoding='latin1', sep=";")
    product_list = set(df_prod['Product Number'].tolist())
    df_errors = dataframe[~dataframe['DEST_CODIGOPRODUTO_STERIS'].isin(product_list)]
    df_errors = df_errors['DEST_CODIGOPRODUTO_STERIS']
    
    st.warning('Lista abaixo com a linha e código cujo Código de Produto Steris não foi encontrado. Baixe a lista de Produtos Steris', icon="⚠️")
    # print('list of errors', list_of_errors)
    st.subheader('Lista de Produtos não identificados: ')
    st.table(data=df_errors)


# start render front page if user exist
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
    df = pd.read_csv(uploaded_file, sep=";", encoding='latin1', dtype='str')
    #df['index'] = np.arange(len(df))+1
    #print(df.info())
    df_changed = clean_transform_df(df)
    checked_df = check_df(df_changed)
    editable_df(df_changed)
      
    
    #out = df_changed.to_json(orient='records')[1:-1]
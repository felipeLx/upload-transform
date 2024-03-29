# from sharepoint import SharePoint
import pyrebase
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridUpdateMode, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
# import csv

firebaseConfig = st.secrets['firebaseConfig']
emailConfig = st.secrets['emailConfig']

# convert dataframe to csv file
@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def convert_df_to_csv(df):
    csv_file = df.to_csv('sellout.csv', sep=';', encoding='utf-8', header=True, decimal=',')
    return csv_file
  
def send_email(user_input):
  # print(type(attached))
  email = user_input # st.text_input('Informar o email', 'exemplo@email.com')
  
  file = 'sellout.csv'# pd.read_csv(attached, index_col=[0], header=0, sep=';', dtype='str')
# print(file.head())
  recipients = ['felipe@beanalytic.com.br'] #, 'camila_menezes@steris.com'
  
  message = MIMEMultipart()
  message['Subject'] = f'Arquivo Sellout modificado por {email}'
  message['From'] = 'sistema@beanalytic.com.br'
  message['To'] = ', '.join(recipients)
  message['Bcc'] = 'felipe@beanalytic.com.br'
  message.attach(MIMEText('<h1 style="color: blue">Olá, </a><p>Segue em anexo o Sellout pronto para o Tableau Prep / Dashboard.</p>', 'html'))

  with open(file, 'rb') as attachment:
    payload = MIMEBase('application', 'octat-stream')
    payload.set_payload(attachment.read())
    
  encoders.encode_base64(payload) #encode the attachment
  #add payload header with filename
  payload.add_header('Content-Disposition', f'attachment; filename={file}')
  message.attach(payload)
  # start server
  # context = ssl.create_default_context()
  try:
    with smtplib.SMTP('smtp-legacy.office365.com', 587) as server:
      server.starttls()
      print('server on') 
      server.login(emailConfig.email, emailConfig.password)
      server.sendmail(
        emailConfig.email, 
        recipients, 
        message.as_string())

      attachment.close()
      server.quit()
      st.balloons()
      return True
  except Exception:
    st.warning('Não foi possível enviar o email para Steris, por favor entrar em contato com Steris para informar', icon="⚠️")
    
    
#if st.session_state.key:
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
    dataframe.update(df_grid, overwrite=True)
  
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
    dataframe.update(df_grid, overwrite=True)  
    dataframe.persist
  csv = convert_df_to_csv(dataframe)
  return csv

@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def transform_coluns(df):
  dataframe = df
  dataframe[dataframe.columns] = dataframe.apply(lambda x: x.str.strip())
  dataframe[dataframe.columns] = dataframe.apply(lambda x: x.str.replace("[/;-]", ""))
  dataframe['NFE_DATAEMISSAO'] = dataframe['NFE_DATAEMISSAO'].str.replace("00:00", "")
  dataframe['NFE_DEST_CNPJ'] = dataframe['NFE_DEST_CNPJ'].str.replace("[.,]", "")
  dataframe['DEST_CODIGOCFOP'] = dataframe['DEST_CODIGOCFOP'].str.replace("[.,]", "")
  dataframe['DEST_CODIGOCFOP'] = dataframe['DEST_CODIGOCFOP'].str[-4:]
  dataframe['NFE_DEST_RAZAOSOCIAL'] = dataframe['NFE_DEST_RAZAOSOCIAL'].str.replace("[.,-<>()/0123456789\t]]", "")
  #dataframe['DEST_CODIGOPRODUTO_STERIS'] = dataframe['DEST_CODIGOPRODUTO_STERIS'].str.replace("[.,-]", "")
  dataframe['NFE_DEST_RAZAOSOCIAL'] = dataframe['NFE_DEST_RAZAOSOCIAL'].str.replace("Ê", "E")
  dataframe['NFE_DEST_RAZAOSOCIAL'] = dataframe['NFE_DEST_RAZAOSOCIAL'].str.replace("Ã", "A")
  dataframe['NFE_DEST_RAZAOSOCIAL'] = dataframe['NFE_DEST_RAZAOSOCIAL'].str.replace("Õ", "O")
  dataframe['NFE_DEST_RAZAOSOCIAL'] = dataframe['NFE_DEST_RAZAOSOCIAL'].str.replace("Ç", "C")
  dataframe['DEST_QTDEPRODUTO'] = dataframe['DEST_QTDEPRODUTO'].str.replace(",", ".")
  #dataframe['DEST_QTDEPRODUTO'] = dataframe['DEST_QTDEPRODUTO'].astype(float)
  dataframe = dataframe.rename(columns={'NFE_DEST_RAZAOSOCIAL': 'RAZAO_SOCIAL'})
  cfop_list = ['51', '52', '53', '54', '61', '62', '63', '64', '', '0']
  dataframe['Matches'] = [any(w[0:2] in cfop_list for w in x.split()) for x in dataframe['DEST_CODIGOCFOP']]
  dataframe = dataframe[dataframe['Matches'] == True]
  dataframe = dataframe[['Dealer/Rep', 'NFE_DATAEMISSAO',	'NFE_NRONOTAFISCAL', 'NFE_DEST_CNPJ',	'RAZAO_SOCIAL','NFE_DEST_ESTADO', 'DEST_QTDEPRODUTO', 'DEST_CODIGOPRODUTO_STERIS', 'DEST_CODIGOCFOP']]
  #print(dataframe.info())
  return dataframe

# data clean and transformation
@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def clean_transform_df(df):
  dataframe = df
  nan_value = float('NaN')
  dataframe.replace("", nan_value, inplace=True)
  # dataframe.dropna(subset='NFE_NRONOTAFISCAL', inplace=True)
  
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
  #dataframe = dataframe.fillna(value=0, axis=0)
  with open('produto.csv', 'rb') as file:
    df_prod = pd.read_csv(file, header=0, usecols=['Product Number'], encoding='latin1', sep=";")
    product_list = set(df_prod['Product Number'].tolist())
    df_errors = dataframe[~dataframe['DEST_CODIGOPRODUTO_STERIS'].isin(product_list)]
    df_all_errors = pd.concat([df_errors, dataframe[dataframe['RAZAO_SOCIAL'].isnull()], dataframe[dataframe['DEST_QTDEPRODUTO'].isnull()], dataframe[dataframe['DEST_QTDEPRODUTO'] == 0]])
    # df_errors = df_errors['DEST_CODIGOPRODUTO_STERIS'] | dataframe[dataframe['RAZAO_SOCIAL'].isnull()]
    
    st.warning('Lista abaixo com a linha e código cujo Código de Produto Steris não foi encontrado. Baixe a lista de Produtos Steris', icon="⚠️")
    st.subheader('Lista de Produtos não identificados, ou coluna de quantidade ou razão social em branco: ')
    return st.table(data=df_all_errors)


# start render front page if user exist
# if st.session_state.key:
  # placeholder.empty()
c = st.container()
# ---- MAINPAGE ----
c.title("Arquivo em formato CSV - Steris")
c.markdown("""---""")
with open('produto.csv', 'rb') as file:
  c.download_button('Lista de Produtos Steris', data=file, file_name='Produtos.csv', mime='txt/csv')

uploaded_file = c.file_uploader("Clique aqui para subir o seu arquivo TXT/CSV", type=["txt", "csv"], on_change=None, key="my-file", accept_multiple_files=False)

if uploaded_file:
  df = pd.read_csv(uploaded_file, encoding='latin1', sep=";", dtype='str') #  
  df.to_csv('sellout.csv', sep=";")
  try:
    df_changed = clean_transform_df(df)
    check_df(df_changed)
    csv = editable_df(df_changed)        
  except ValueError as e:
    print('Value Error', e)
  except NameError:
    print('Something is going wrong', NameError)
  except TypeError:
    print("Type Error", TypeError)
  except RuntimeError:
    print("Runtime", RuntimeError)
  except Exception as e:
    print("none of above", e)
  
with st.form("my_form"):
  email = st.text_input('Informar o email', 'exemplo@email.com')
  submitted = st.form_submit_button("Enviar e-mail para Steris")
  st.write('Informar o email para o envio do arquivo para Steris')
  if submitted:
    email_sent = send_email(email)
    if email_sent:
      st.success('Email enviado com Sucesso!', icon="✅")
  
    #out = df_changed.to_json(orient='records')[1:-1]
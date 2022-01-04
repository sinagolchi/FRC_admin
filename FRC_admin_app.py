import streamlit as st
import psycopg2
import time
import pytz
import seaborn as sns
import pandas as pd

st.set_page_config(layout='wide') #set streamlit page to wide mode

phase_dict = {0: 'Adjusting tax rate (for government only)', 1: 'Taxes', 2: 'Bidding on features', 3: 'Transactions', 4: 'Flood and damage analysis', 5: 'Vote'}
phase_dict_inv = {v:k for k, v in phase_dict.items()}

def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])

conn = init_connection()

st.header('FRC Admin Tool')
st.caption('Developed by Sina Golchi with collaboration with FRC Team under creative commons license')

with st.sidebar:
    board = st.selectbox(label='FRC Board number', options=[1, 2, 3, 4, 5])

def get_sql(table):
    return pd.read_sql("SELECT * from " + table+";",conn)

st.header('Main Game properties')

df = get_sql('budget_lb1')
df.set_index('role',inplace=True)

df_m = get_sql('measures_lb1')
df_m.set_index('measure_id', inplace=True)

df_v = get_sql('frc_long_variables')
df_v.set_index('board',inplace=True)


st.header('Game phase')
sub_col1, sub_col2, sub_col3 = st.columns(3)
with sub_col1:
    st.text(phase_dict[int(df_v.loc[board, 'phase'])])
with sub_col2:
    set_phase = phase_dict_inv[st.selectbox(options=phase_dict.values(), label='Set phase to:')]
with sub_col3:
    phase_change = st.button(label='Submit changes to phase',help='Change the phase only when needed')

def change_phase(set_phase):
    curA = conn.cursor()
    curA.execute("UPDATE frc_long_variables SET phase=%s WHERE board=%s",(set_phase,board))
    conn.commit()
    st.success('Game phase changed successfully')
    time.sleep(2)
    st.experimental_rerun()

st.header('Game round')
sub_col1, sub_col2, sub_col3 = st.columns(3)
with sub_col1:
    st.metric(label='Current game round', value=int(df_v.loc[board,'round']))
with sub_col2:
    set_round = st.number_input(label='Set game round',min_value=1,value=1,max_value=3)
with sub_col3:
    round_change = st.button(label='Submit changes',help='Change the round only when needed')

def change_round(set_round):
    curA = conn.cursor()
    curA.execute("UPDATE frc_long_variables SET round=%s WHERE board=%s",((set_round,board)))
    conn.commit()
    st.success('Game round changed successfully')
    time.sleep(2)
    st.experimental_rerun()

if phase_change:
    change_phase(set_phase)

if round_change:
    change_round(set_round)

st.markdown("""___""")

st.header('Transaction management')
def transaction_management():
    with st.expander('Dev tools'):
        def clear_transaction_log():
            curA = conn.cursor()
            curA.execute("DELETE FROM payment")
            conn.commit()
            with st.spinner('clearing transaction log'):
                time.sleep(2)
            st.success('Transaction log cleared')
            time.sleep(2)
            st.experimental_rerun()
        col1, col2, col3 = st.columns(3)

        with col1:
            confirm_clear_log = st.button(label='Clear transaction log')
        if confirm_clear_log:
            clear_transaction_log()

        def reinitial_main_raster():
            curA = conn.cursor()
            curA.execute("UPDATE budget_lb1 SET cb=ib, delta=0, r1_tax=false, r2_tax=false, r3_tax=false, r1_vote=null, r2_vote=null, r3_vote=null, r1_insurance = false, r2_insurance = false, r3_insurance = false;")
            conn.commit()
            with st.spinner('Reinitializing the main raster'):
                time.sleep(2)
            st.success('Raster reinitialized')
            time.sleep(2)
            st.experimental_rerun()

        with col2:
            confirm_reinit_raster = st.button(label='Reinitialize main raster')

        if confirm_reinit_raster:
            reinitial_main_raster()

    def transaction_revert(id):
        revert_query_sender = ("UPDATE budget_lb1 SET cb=cb+%s WHERE role=%s;")
        revert_query_receiver = ("UPDATE budget_lb1 SET cb=cb-%s WHERE role=%s;")
        curA = conn.cursor()
        curA.execute(revert_query_sender, (int(df_payement.loc[id,'Transaction total']),df_payement.loc[id,'Sender']))
        curA.execute(revert_query_receiver, (int(df_payement.loc[id, 'Transaction total']), df_payement.loc[id, 'Receiving party']))
        curA.execute("UPDATE payment SET reverted=True WHERE id=%s;",[id])
        conn.commit()
        with st.spinner('Reverting transaction'):
            time.sleep(2)
        st.success('Transaction reverted')
        time.sleep(2)
        st.experimental_rerun()



    df_payement = get_sql('payment')
    est = pytz.timezone('EST')
    df_payement = df_payement.rename(
        columns={'datetime': 'Timestamp', 'from_user': 'Sender', 'amount': 'Transaction total',
                 'to_user': 'Receiving party'})
    if not df_payement.empty:
        df_payement['Timestamp'] = df_payement['Timestamp'].dt.tz_convert('EST').dt.strftime('%B %d, %Y, %r')
        df_payement.set_index('id',inplace=True)
        st.dataframe(df_payement)
    else:
        st.info('No transaction history')


    st.subheader('Transaction modification')
    st.markdown('Revert transaction')
    col1, col2 = st.columns(2)
    with col1:
        trans_id = st.number_input(value=0, min_value=0, label='Transction ID')
    with col2:
        confirm_revert = st.button(label='Revert transaction')

    if confirm_revert:
        transaction_revert(int(trans_id))

transaction_management()

st.markdown("""___""")

def voting_status():
    st.header('Voting management')
    st.dataframe(df[['r1_vote','r2_vote','r3_vote']])
    def end_current_session():
        print('end')
    end_vote_session = st.button(label='End current vote session and show results')


voting_status()
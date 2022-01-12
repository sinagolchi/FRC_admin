import streamlit as st
import psycopg2
import time
import pytz
import seaborn as sns
import pandas as pd
from random import randrange

st.set_page_config(layout='wide') #set streamlit page to wide mode

user_dict = {
    'M':'Mayor',
    'LEF':'Large Engineering Firm',
    'DP': 'District Planner',
    'EM': 'Emergency Manager',
    'ENGO': 'Environmental ENGO',
    'F': 'Farmer',
    'FP': 'Federal Government',
    'FN': 'First Nations',
    'I': 'Insurance Company',
    'J': 'Journalist',
    'LD': 'Land Developer',
    'LBO': 'Local Business',
    'PUC': 'Power Utility',
    'CRA-HV': 'Community Residence - High Value',
    'CRA-MHA': 'Community Residence - Mobile Home',
    'CRA-MV': ' Community Residence - Mediume value',
    'PH': 'Hydrologist',
    'PP': 'Provincial Politician',
    'TA': 'Transport Authority',
    'WW': 'Waste and Water Treatment Director'
}
user_dict_inv= {v:k for k,v in user_dict.items()}

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

        def reset_flood_event():
            cursor = conn.cursor()
            cursor.execute("UPDATE frc_long_variables SET floods='{NULL,NULL,NULL}' WHERE board=%s;",[board])
            conn.commit()
            with st.spinner('Resetting flood events'):
                time.sleep(2)
            st.success('Flood events cleared')


        with col3:
            reset_flood_confirm = st.button(label='Reset all flood events')

        if reset_flood_confirm:
            reset_flood_event()

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

#flood conttrol centre

damage_flood_dict = {'Ice jam winter flooding':{'light': ['ENGO', 'EM', 'F'], 'heavy':['CRA-MHA']}, 'Freshet flood':{'light':['EM','M','CRA-MV'],'heavy':['CRA-HV','CRA-MHA']},'Storm surge winter flooding':{'light':['M','WW','DP'],'heavy':['CRA-MHA','CRA-HV','LBO']},
                     'Convective summer storm':{'light':['EM','F','CRA-MHA','CRA-MV','CRA-HV','DP','LBO'],'heavy':['M']},'Minor localized flooding':{'light':['DP'],'heavy':['CRA-MV']},'Future sea level rise':{'light':['CRA-MHA','M','CRA-HV',],'heavy':['WW','LBO','DP']}}

qulified_for_DRP = ['CRA-HV','CRA-MV','CRA-MHA','ENGO','F']
def flood_centre():
    def flooding():
        flood_type = randrange(1,8)
        st.write(flood_dict[flood_type])
        curA = conn.cursor()
        dict_flood_round = {1:"{" + str(flood_dict[flood_type]) + ",NULL,NULL}", 2:"{"+str(df_v.loc[board,'floods'][0])+"," + str(flood_dict[flood_type]) + ",NULL}" , 3:"{"+str(df_v.loc[board,'floods'][0])+","+str(df_v.loc[board,'floods'][1])+"," + str(flood_dict[flood_type]) + "}"}
        curA.execute("UPDATE frc_long_variables SET floods=%s WHERE board=%s;",(dict_flood_round[int(df_v.loc[board,'round'])],int(board)))
        conn.commit()
        with st.spinner('Waiting for flood'):
            time.sleep(2)
        st.success(str(flood_dict[flood_type]) + ' in effect')

    st.markdown('''___''')
    st.header('Flood event')
    flood_dict = {1: 'Ice jam winter flooding' , 2: 'Freshet flood', 3: 'Storm surge winter flooding',4: 'Convective summer storm' , 5: 'Minor localized flooding', 6: 'Future sea level rise' , 7: 'No flooding'}
    if df_v.loc[board,'floods'][int(df_v.loc[board,'round'])-1] is None:
        generate_flood = st.button('Roll the dice')
        if generate_flood:
            flooding()
    else:
        st.info(df_v.loc[board,'floods'][int(df_v.loc[board,'round'])-1])

    st.markdown('''___''')
    st.subheader('Damage analysis')
    lightly_affected = []
    severity = []
    insured = []
    heavily_affected = []
    protected = []
    DRP_eligiblity = []

    if damage_flood_dict[df_v.loc[board,'floods'][int(df_v.loc[board,'round'])-1]] is not None:
        for user in damage_flood_dict[df_v.loc[board,'floods'][int(df_v.loc[board,'round'])-1]]['light']:
            lightly_affected.append(user)
            severity.append('light')
            if df.loc[user,'r'+str(df_v.loc[board,'round'])+'_insurance']:
                insured.append(True)
            else:
                insured.append((False))

        for user in damage_flood_dict[df_v.loc[board,'floods'][int(df_v.loc[board,'round'])-1]]['heavy']:
            heavily_affected.append(user)
            severity.append('heavy')
            if df.loc[user,'r'+str(df_v.loc[board,'round'])+'_insurance']:
                insured.append(True)
            else:
                insured.append(False)

        for user in damage_flood_dict[df_v.loc[board,'floods'][int(df_v.loc[board,'round'])-1]]['light']:
            if user in qulified_for_DRP:
                DRP_eligiblity.append(True)
            else:
                DRP_eligiblity.append(False)

        for user in damage_flood_dict[df_v.loc[board,'floods'][int(df_v.loc[board,'round'])-1]]['heavy']:
            if user in qulified_for_DRP:
                DRP_eligiblity.append(True)
            else:
                DRP_eligiblity.append(False)


    # st.markdown('lightly effected')
    # st.write(insured)
    # st.write(lightly_affected)
    # st.markdown('heavily effected')
    # st.write(heavily_affected)
    damage_amount = []
    insurance_rebate = []

    protected_roles = st.multiselect(label='Protected roles (Refer to board)', options=lightly_affected + heavily_affected)
    protected = [True if user in protected_roles else False for user in lightly_affected+heavily_affected]
    flood_damage = pd.DataFrame(zip(lightly_affected + heavily_affected, severity, insured, protected, DRP_eligiblity),
                                columns=['Roles', 'Severity', 'Insured', 'Protected by measures','Eligible for DRP - 3 units'])
    flood_damage.set_index('Roles', inplace=True)

    for user in flood_damage.index:
        if flood_damage.loc[user,'Severity'] == 'light':
            init_dmg = df.loc[user,'ib']/4
            if flood_damage.loc[user,'Insured']:
                i_r = init_dmg*(3/4)
                insurance_rebate.append(init_dmg*(3/4))
            else:
                insurance_rebate.append(0)
                i_r = 0
            damage_amount.append(init_dmg)
        else:
            init_dmg = df.loc[user,'ib'] / 2
            if flood_damage.loc[user, 'Insured']:
                i_r = init_dmg*(3/4)
                insurance_rebate.append(init_dmg*(3/4))
            else:
                insurance_rebate.append(0)
                i_r = 0
            damage_amount.append(init_dmg)

    flood_damage['Insurance rebate'] = insurance_rebate
    flood_damage['Payable damage'] = damage_amount

    st.dataframe(flood_damage)

    def submit_flood_details():
        for user in flood_damage.index:
            curA = conn.cursor()
            curA.execute("UPDATE budget_lb1 SET r%s_flood='{%s,%s,%s}' WHERE role=%s;",(int(df_v.loc[board,'round']),True,bool(flood_damage.loc[user,'Protected by measures']),float(flood_damage.loc[user,'Payable damage']),user))
            conn.commit()

    def submit_insurance():
        curA = conn.cursor()
        for user in flood_damage.index:
            if flood_damage.loc[user,'Insured']:

                curA.execute("UPDATE budget_lb1 SET cb=cb+%s WHERE role=%s",(int(flood_damage.loc[user,'Insurance rebate']),user))
                curA.execute("UPDATE budget_lb1 SET delta=%s WHERE role=%s",
                             (int(flood_damage.loc[user, 'Insurance rebate']), user))
        curA.execute("UPDATE budget_lb1 SET cb=cb-%s WHERE role=%s",(int(flood_damage['Insurance rebate'].sum()),'I'))
        curA.execute("UPDATE budget_lb1 SET delta=-%s WHERE role=%s",
                     (int(flood_damage['Insurance rebate'].sum()), 'I'))
        conn.commit()
        with st.spinner('Processing insurance claim'):
            time.sleep(2)
        st.success('Insurance claim went through')
        time.sleep(2)


    col1, col2, col3  = st.columns(3)
    with col1:
        flood_submit = st.button(label='Submit flood details')
    with col3:
        insurance_submit = st.button(label='Submit insurance claim')

    if flood_submit:
        submit_flood_details()

    if insurance_submit:
        submit_insurance()

    # def update_damage_analysis(users,severity,protected):










flood_centre()




#Voting section
st.markdown("""___""")

def voting_status():
    st.header('Voting management')
    st.dataframe(df[['r1_vote','r2_vote','r3_vote']])
    def end_current_session():
        print('end')
    end_vote_session = st.button(label='End current vote session and show results')


voting_status()


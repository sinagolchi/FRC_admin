import streamlit as st
import psycopg2
import time
import pytz
import seaborn as sns
import pandas as pd
from random import randrange
from pathlib import Path
import streamlit.components.v1 as components
import math

st.set_page_config(layout='wide') #set streamlit page to wide mode


def refresh():
    st.experimental_rerun()

def read_markdown_file(markdown_file):
    return Path(markdown_file).read_text()

def styler(val):
    color = 'red' if val == False else ('green' if val == True else 'gray')
    return 'color: %s' % color

with st.sidebar:
    game_type = st.radio(label='Game type', options=['Simplified','Full'], index=0)

if game_type == 'Full':
    def init_connection():
        return psycopg2.connect(**st.secrets["postgres"])
else:
    def init_connection():
        return psycopg2.connect(options='-c search_path=FRC_s',**st.secrets["postgres"])


if game_type == 'Full':
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
else:
    user_dict = {'M': "Mayor", 'P': 'Planner', 'EM': 'Emergency Manager', 'CSO': 'Community Service',
                 'WR': 'Waterfront Resident', 'F': 'Farmer', 'LD': 'Land Developer', 'LEF': 'Large Engineering Firm'}
user_dict_inv= {v:k for k,v in user_dict.items()}

#phase_dict = {2: 'Phase 1A: FRM Measure bidding',3: 'Phase 1B: Transactions',4: 'Phase 2: Flood and damage analysis',0: '(Pre Phase 3) Adjusting tax rate (for government only) ', 1: 'Phase 3: Updating Budget', 5: 'Phase 4: Vote'}
phase_dict = {1: 'Phase 1: FRM Measure bidding',2: 'Phase 2: Flood and damage analysis', 3: 'Phase 3: Updating Budget', 4: 'Phase 4: Vote'}
phase_dict_inv = {v:k for k, v in phase_dict.items()}


conn = init_connection()

st.header('FRC Admin Tool')
st.caption('Developed by Sina Golchi with collaboration with FRC Team under creative commons license')
def get_sql(table):
    return pd.read_sql("SELECT * from " + table+";",conn)
df_authen = get_sql('facilitators')
df_authen.set_index('user',inplace=True)
def authenticate(user,password):
    if user in df_authen.index:
        st.session_state['user'] = 'ok'
        if password == df_authen.loc[user,'pass']:
            st.session_state['pass'] = 'ok'
        else:
            st.error('Your password is incorrect')
            st.session_state['pass'] = 'wrong'
            st.stop()
    else:
        st.session_state['user'] = 'wrong'
        st.error('Your username is incorrect')
        st.stop()


with st.sidebar:
    with st.form(' Facilitator sign in'):
        username = st.text_input(label='username',placeholder='username')
        password = st.text_input(label='password',placeholder='password',type='password')
        submit_sign_in = st.form_submit_button(label='Sign in')
        if submit_sign_in:
            authenticate(username,password)

    @st.cache(suppress_st_warning=True)
    def check_user():
        if 'user' not in st.session_state and 'pass' not in st.session_state:
            st.warning('You are not signed in')
            st.stop()
        elif st.session_state['user'] == 'ok' and st.session_state['pass'] == 'ok':
            pass
        else:
            st.error('Your user name or password is incorrect, please try again')
            st.stop()

    check_user()

    if username != "":
        try:
            if df_authen.loc[username,'level'] == 3: # or username == 'evalyna' or username == 'shaieree':
                board = st.selectbox(label='FRC Board number', options=[1, 2, 3, 4, 5, 6, 7])
            else:
                board = int(df_authen.loc[username,'board'])
            st.success('Welcome ' + df_authen.loc[username, 'name'])
            st.success('You are facilitating board ' + str(board))
            confirm_rerun = st.button(label='Refresh Data')
            if confirm_rerun:
                refresh()
        except:
            st.error('your username is not registered')

    else:
        st.warning('Please log in with the provided username and password')
        st.stop()


df = get_sql('budget_lb' + str(board))
df.set_index('role',inplace=True)

df_m = get_sql('measures_lb1')
df_m.set_index('measure_id', inplace=True)

df_v = get_sql('frc_long_variables')
df_v.set_index('board',inplace=True)

if df_authen.loc[username,'level'] > 1:
    st.header('Main Game properties')
    st.header('Game phase')
    sub_col1, sub_col2, sub_col3 = st.columns(3)
    with sub_col1:
        st.markdown('<p style="font-size: 20px; color:rgb(58, 134, 255);">' + str(phase_dict[int(df_v.loc[board, 'phase'])]) + '</p>',unsafe_allow_html=True)
        #st.subheader(phase_dict[int(df_v.loc[board, 'phase'])])
    with sub_col2:
        set_phase = phase_dict_inv[st.selectbox(options=phase_dict.values(), label='Set phase to:')]
    with sub_col3:
        phase_change = st.button(label='Submit changes to phase',help='Change the phase only when needed')
        phase_change_all_boards = st.button(label='Submit changes to phase (All boards)',help='Change the phase only when needed')

    def change_phase(set_phase):
        curA = conn.cursor()
        curA.execute("UPDATE frc_long_variables SET phase=%s WHERE board=%s",(set_phase,board))
        conn.commit()
        st.success('Game phase changed successfully')
        time.sleep(2)
        st.experimental_rerun()

    def change_phase_all(set_phase):
        curA = conn.cursor()
        curA.execute("UPDATE frc_long_variables SET phase=%s;",[set_phase])
        conn.commit()
        st.success('Game phase changed successfully')
        time.sleep(2)
        st.experimental_rerun()

    st.header('Game round')
    sub_col1, sub_col2, sub_col3 = st.columns(3)
    with sub_col1:
        st.metric(label='Current game round', value=int(df_v.loc[board,'round']))
        g_round = df_v.loc[board, 'round']
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

    if phase_change_all_boards:
        change_phase_all(set_phase)

    if round_change:
        change_round(set_round)

else:
    st.caption('Game round')
    st.info('Your board is on round ' + str(df_v.loc[board,'round']))
    g_round = df_v.loc[board, 'round']
    st.caption('Game Phase')
    st.info('The current game phase is ' + phase_dict[int(df_v.loc[board, 'phase'])])


def budget_section():
    other_roles = [x for x in user_dict.keys()]
    with st.expander('Participants budgets'):
        metric_cols_1 = st.columns(7)
        metric_cols_2 = st.columns(7)
        metric_cols_3 = st.columns(7)
        metric_cols = metric_cols_1 + metric_cols_2 + metric_cols_3

        for col, role in zip(metric_cols, other_roles):
            with col:
                st.metric(label=user_dict[role], value='$' + str(df.loc[role, 'cb']), delta=int(df.loc[role, 'delta']))

def process_bid(measure,biders,amounts):
    try:
        curA = conn.cursor()
        curA.execute('INSERT INTO impl_measures%s VALUES (%s,%s,%s,%s);',(int(board),measure,biders,amounts,int(g_round)))
        curA.execute('UPDATE budget_lb%s SET r%s_measure = NULL, r%s_bid = NULL WHERE role=ANY(%s);',(int(board),int(g_round),int(g_round),biders))
        conn.commit()

        for role, amount in zip(biders,amounts):
            curA = conn.cursor()
            curA.execute('UPDATE budget_lb%s SET cb=cb-%s WHERE role = %s;', (int(board),amount,role))
            curA.execute('UPDATE budget_lb%s SET delta=-%s WHERE role = %s;', (int(board),amount,role))
            conn.commit()

        if (measure in df_m[df_m['type']=='Structural'].index):
            curA = conn.cursor()
            curA.execute('UPDATE budget_lb%s SET cb=cb+%s WHERE role = %s;', (int(board), int((sum(amounts)-2)/4), 'LEF'))
            curA.execute('UPDATE budget_lb%s SET cb=cb+%s WHERE role = %s;', (int(board), 2, 'ENGO'))
            conn.commit()
    except:
        st.error('Bid processing failed, try again')
        pass



    st.success('Bid processed')
    time.sleep(2)

def bidding_section():
    st.markdown('''___''')
    with st.expander('FRM measures bidding help'):
        st.markdown(read_markdown_file('checklists/FRM measures checklist.md'))
    st.subheader('Measures suggested')

    confirm_rerun = st.button(label='Refresh Data', key='bidding section')
    if confirm_rerun:
        refresh()
    for measure in df_m.index.values:
        if measure in df['r' + str(g_round) + '_measure'].to_list():
            if sum([int(i) for i in df[df['r' + str(g_round) + '_measure'] == measure][
                              'r' + str(g_round) + '_bid'].to_list()]) != int(df_m.loc[measure, 'cost']):

                col1, col2 = st.columns([1, 3])
                with col1:
                    st.metric(label=measure,
                              value=str(sum([int(i) for i in df[df['r' + str(g_round) + '_measure'] == measure][
                                  'r' + str(g_round) + '_bid'].to_list()])) + r"/" + str(int(df_m.loc[measure, 'cost'])))
                with col2:
                    biders = list(df[df['r' + str(g_round) + '_measure'] == measure].index)
                    amounts = df[df['r' + str(g_round) + '_measure'] == measure]['r' + str(g_round) + '_bid'].to_list()
                    st.caption('Bidders: ' + ',  '.join([user_dict[p] + ': \$' + str(b) for p, b in zip(biders, amounts)]))
                    try:
                        st.progress(int(sum([int(i) for i in df[df['r' + str(g_round) + '_measure'] == measure][
                            'r' + str(g_round) + '_bid'].to_list()]) / df_m.loc[measure, 'cost'] * 100))
                    except:
                        st.warning('The bid on this measure have exceeded the cost')

            else:
                #If bid has reached the level
                col1, col2, col3= st.columns([1, 2, 1])
                with col1:
                    st.metric(label=measure,
                              value=str(sum([int(i) for i in df[df['r' + str(g_round) + '_measure'] == measure][
                                  'r' + str(g_round) + '_bid'].to_list()])) + r"/" + str(
                                  int(df_m.loc[measure, 'cost'])))
                with col2:
                    biders = list(df[df['r' + str(g_round) + '_measure'] == measure].index)
                    amounts = df[df['r' + str(g_round) + '_measure'] == measure]['r' + str(g_round) + '_bid'].to_list()
                    st.caption(
                        'Bidders: ' + ',  '.join([user_dict[p] + ': \$' + str(b) for p, b in zip(biders, amounts)]))
                    try:
                        st.progress(int(sum([int(i) for i in df[df['r' + str(g_round) + '_measure'] == measure][
                            'r' + str(g_round) + '_bid'].to_list()]) / df_m.loc[measure, 'cost'] * 100))
                    except:
                        st.warning('The bid on this measure have exceeded the cost')

                with col3:
                    st.button(label='Process bid',key=measure,on_click=process_bid , args=(measure,biders,amounts))

    df_impl_measures = get_sql('impl_measures'+str(board))
    st.subheader('Implemented measures')
    for m_row in df_impl_measures.iterrows():
        m_row = m_row[1]
        if m_row['round'] == g_round:
            col1, col2,col3 = st.columns([1,3,1])
            with col1:
                st.metric(label=m_row['measure'],
                              value=str(sum(m_row['amounts'])) + r"/" + str(
                                  int(df_m.loc[m_row['measure'], 'cost'])))
            with col2:
                st.caption(
                    'Bidders: ' + ',  '.join([user_dict[p] + ': \$' + str(b) for p, b in zip(m_row['biders'], m_row['amounts'])]))

                st.progress(int(sum(m_row['amounts']) / df_m.loc[m_row['measure'], 'cost'] * 100))
            with col3:
                st.success('Implemented')


def transaction_management():
    #st.markdown("""___""")
    with st.expander('Transactions help'):
        st.markdown(read_markdown_file('checklists/transaction.md'))
    st.header('Transaction management')
    confirm_rerun = st.button(label='Refresh Data', key='transaction section')
    if confirm_rerun:
        refresh()

    def transaction_revert(id):
        revert_query_sender = ("UPDATE budget_lb%s SET cb=cb+%s WHERE role=%s;")
        revert_query_receiver = ("UPDATE budget_lb%s SET cb=cb-%s WHERE role=%s;")
        curA = conn.cursor()
        curA.execute(revert_query_sender, (int(board),int(df_payement.loc[id,'Transaction total']),df_payement.loc[id,'Sender']))
        curA.execute(revert_query_receiver, (int(board),int(df_payement.loc[id, 'Transaction total']), df_payement.loc[id, 'Receiving party']))
        curA.execute("UPDATE payment%s SET reverted=True WHERE id=%s;",(board,id))
        conn.commit()
        with st.spinner('Reverting transaction'):
            time.sleep(2)
        st.success('Transaction reverted')
        time.sleep(2)
        st.experimental_rerun()


    df_payement = get_sql('payment' + str(board))
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

    st.header('Summary')
    with st.expander("Bidding summary"):
        df_m_log = get_sql('measure_log' + str(board))
        est = pytz.timezone('EST')
        df_m_log = df_m_log.rename(
            columns={'datetime': 'Timestamp', 'bid_type': 'Type of bid', 'person_biding': 'Role of bidder',
                     'amount': 'Amount of bid', 'measure': 'Measure'})
        if not df_m_log.empty:
            df_m_log['Timestamp'] = df_m_log['Timestamp'].dt.tz_convert('EST').dt.strftime('%B %d, %Y, %r')
            st.dataframe(df_m_log)
        else:
            st.info('No bid to show')

    with st.expander("Transaction summary"):
        df_p_log = get_sql('payment' + str(board))
        est = pytz.timezone('EST')
        df_p_log = df_p_log.rename(
            columns={'datetime': 'Timestamp', 'from_user': 'Sender', 'amount': 'Transaction total',
                     'to_user': 'Receiving party'})
        df_p_log['id'] = [int(p) for p in df_p_log['id']]
        df_p_log.set_index('id', inplace=True)
        if not df_p_log.empty:
            df_p_log['Timestamp'] = df_p_log['Timestamp'].dt.tz_convert('EST').dt.strftime('%B %d, %Y, %r')
            st.dataframe(df_p_log)
        else:
            st.info('No transaction to show')


def secret_transaction_management():
    #st.markdown("""___""")
    st.header('Secret Transaction management')
    confirm_rerun = st.button(label='Refresh Data', key='transaction section')
    if confirm_rerun:
        refresh()

    def transaction_revert(id):
        revert_query_sender = ("UPDATE budget_lb%s SET cb=cb+%s WHERE role=%s;")
        revert_query_receiver = ("UPDATE budget_lb%s SET cb=cb-%s WHERE role=%s;")
        curA = conn.cursor()
        curA.execute(revert_query_sender, (int(board),int(df_payement.loc[id,'Transaction total']),df_payement.loc[id,'Sender']))
        curA.execute(revert_query_receiver, (int(board),int(df_payement.loc[id, 'Transaction total']), df_payement.loc[id, 'Receiving party']))
        curA.execute("UPDATE payment%s SET reverted=True WHERE id=%s;",(board,id))
        conn.commit()
        with st.spinner('Reverting transaction'):
            time.sleep(2)
        st.success('Transaction reverted')
        time.sleep(2)
        st.experimental_rerun()


    df_payement = get_sql('payment' + str(board))
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


#flood conttrol centre
if game_type == 'Full':
    damage_flood_dict = {'Ice jam winter flooding':{'light': ['ENGO', 'EM', 'F'], 'heavy':['CRA-MHA']}, 'Freshet flood':{'light':['EM','M','CRA-MV'],'heavy':['CRA-HV','CRA-MHA']},'Storm surge winter flooding':{'light':['M','WW','DP'],'heavy':['CRA-MHA','CRA-HV','LBO']},
                     'Convective summer storm':{'light':['EM','F','CRA-MHA','CRA-MV','CRA-HV','DP','LBO'],'heavy':['M']},'Minor localized flooding':{'light':['DP'],'heavy':['CRA-MV']},'Future sea level rise':{'light':['CRA-MHA','M','CRA-HV',],'heavy':['WW','LBO','DP']}}
    qulified_for_DRP = ['CRA-HV', 'CRA-MV', 'CRA-MHA', 'ENGO', 'F']
else:
    damage_flood_dict = {'Ice jam winter flooding':{'light': ['EM'], 'heavy':[]}, 'Freshet flood':{'light':['EM','M'],'heavy':['WR']},'Storm surge winter flooding':{'light':['P','M'],'heavy':['WR']},
                     'Convective summer storm':{'light':['EM','F'],'heavy':['M']},'Minor localized flooding':{'light':['CSO'],'heavy':[]},'Future sea level rise':{'light':['M'],'heavy':['P','WR']}}
    qulified_for_DRP = ['CSO','F','WR']
def flood_centre():
    def flooding_random():
        flood_type = randrange(1,8)
        st.write(flood_dict[flood_type])
        curA = conn.cursor()
        dict_flood_round = {1:"{" + str(flood_dict[flood_type]) + ",NULL,NULL}", 2:"{"+str(df_v.loc[board,'floods'][0])+"," + str(flood_dict[flood_type]) + ",NULL}" , 3:"{"+str(df_v.loc[board,'floods'][0])+","+str(df_v.loc[board,'floods'][1])+"," + str(flood_dict[flood_type]) + "}"}
        curA.execute("UPDATE frc_long_variables SET floods=%s WHERE board=%s;",(dict_flood_round[int(df_v.loc[board,'round'])],int(board)))
        conn.commit()
        with st.spinner('Waiting for flood'):
            time.sleep(2)
        st.success(str(flood_dict[flood_type]) + ' in effect')
        time.sleep(1)
        st.experimental_rerun()

    def flooding_manual(flood):
        st.write(flood)
        curA = conn.cursor()
        dict_flood_round = {1:"{" + flood + ",NULL,NULL}", 2:"{"+str(df_v.loc[board,'floods'][0])+"," + flood + ",NULL}" , 3:"{"+str(df_v.loc[board,'floods'][0])+","+str(df_v.loc[board,'floods'][1])+"," + flood + "}"}
        curA.execute("UPDATE frc_long_variables SET floods=%s WHERE board=%s;",(dict_flood_round[int(df_v.loc[board,'round'])],int(board)))
        conn.commit()
        with st.spinner('Waiting for flood'):
            time.sleep(2)
        st.success(flood + ' in effect')
        time.sleep(1)
        st.experimental_rerun()

    st.markdown('''___''')
    with st.expander('Flood Event checklist'):
        st.markdown(read_markdown_file('checklists/Flood.md'))
    st.header('Flood event')
    confirm_rerun = st.button(label='Refresh Data', key='flood section')
    if confirm_rerun:
        refresh()
    flood_dict = {1: 'Ice jam winter flooding' , 2: 'Freshet flood', 3: 'Storm surge winter flooding',4: 'Convective summer storm' , 5: 'Minor localized flooding', 6: 'Future sea level rise' , 7: 'No flooding'}
    if df_v.loc[board,'floods'][int(df_v.loc[board,'round'])-1] is None:
        gen_type = st.radio(label='Flood generation method',options=['Random','Manual'],index=0)
        if gen_type == 'Random':
            generate_flood = st.button('Roll the dice')
            if generate_flood:
                flooding_random()
        else:
            flood_type = st.selectbox(label='Type of flood to implement',options=flood_dict.values())
            generate_flood = st.button('Set the flood')
            if generate_flood:
                flooding_manual(flood_type)

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
    if df_v.loc[board,'floods'][int(df_v.loc[board,'round'])-1] is not None:
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

        protected_roles = [user_dict_inv[b] for b in st.multiselect(label='Protected roles (Refer to board)', options=[user_dict[x] for x in lightly_affected] + [user_dict[x] for x in heavily_affected])]
        print(protected_roles)
        protected = [True if user in protected_roles else False for user in lightly_affected+heavily_affected]
        flood_damage = pd.DataFrame(zip(lightly_affected + heavily_affected, severity, insured, protected, DRP_eligiblity),
                                    columns=['Roles', 'Severity', 'Insured', 'Protected by measures','Eligible for DRP (3 units)'])
        flood_damage.set_index('Roles', inplace=True)

        for user in flood_damage.index:
            if flood_damage.loc[user,'Severity'] == 'light':
                init_dmg = math.ceil(df.loc[user,'ib']/4)
                if flood_damage.loc[user,'Insured']:
                    i_r = math.ceil(init_dmg*(3/4))
                    insurance_rebate.append(math.ceil(init_dmg*(3/4)))
                else:
                    insurance_rebate.append(0)
                    i_r = 0
                damage_amount.append(init_dmg)
            else:
                init_dmg = math.ceil(df.loc[user,'ib'] / 2)
                if flood_damage.loc[user, 'Insured']:
                    i_r = math.ceil(init_dmg*(3/4))
                    insurance_rebate.append(math.ceil(init_dmg*(3/4)))
                else:
                    insurance_rebate.append(0)
                    i_r = 0
                damage_amount.append(init_dmg)

        flood_damage['Cost of damage'] = damage_amount
        flood_damage['Insurance rebate'] = insurance_rebate
        flood_d_rename = flood_damage.rename(index=user_dict, inplace=False)
        flood_d_rename_styled = flood_d_rename.style.applymap(styler)


        st.dataframe(flood_d_rename_styled)

        def submit_flood_details():

            for user in flood_damage.index:
                curA = conn.cursor()
                curA.execute("UPDATE budget_lb%s SET r%s_flood=ARRAY[%s,%s,%s] WHERE role=%s;",(int(board),int(df_v.loc[board,'round']),int(True),int(bool(flood_damage.loc[user,'Protected by measures'])),int(flood_damage.loc[user,'Cost of damage']),user))
                conn.commit()

            df = get_sql('budget_lb' + str(board))
            df.set_index('role', inplace=True)

            for user in flood_damage.index:

                if not df.loc[user, 'r'+str(g_round)+'_flood'][1]:
                    curA = conn.cursor()
                    curA.execute("UPDATE budget_lb%s SET ib=ib-%s, delta = -%s WHERE role=%s;", (
                    int(board),
                    int(df.loc[user, 'r'+str(g_round)+'_flood'][2]),int(df.loc[user, 'r'+str(g_round)+'_flood'][2]), user))
                    conn.commit()

            with st.spinner('Submitting flood details to players'):
                time.sleep(2)
            st.success('Flood details is updated')
            time.sleep(1)
            st.experimental_rerun()


        def submit_insurance():
            curA = conn.cursor()
            for user in flood_damage.index:
                if flood_damage.loc[user,'Insured']:

                    curA.execute("UPDATE budget_lb%s SET cb=cb+%s WHERE role=%s",(int(board),int(flood_damage.loc[user,'Insurance rebate']),user))
                    curA.execute("UPDATE budget_lb%s SET delta=%s WHERE role=%s",
                                 (int(board),int(flood_damage.loc[user, 'Insurance rebate']), user))
            curA.execute("UPDATE budget_lb%s SET cb=cb-%s WHERE role=%s",(int(board),int(flood_damage['Insurance rebate'].sum()),'I'))
            curA.execute("UPDATE budget_lb%s SET delta=-%s WHERE role=%s",
                         (int(board),int(flood_damage['Insurance rebate'].sum()), 'I'))

            total_DRP = 0
            for user in flood_damage.index:
                if flood_damage.loc[user,'Eligible for DRP (3 units)'] and not flood_damage.loc[user,'Insured']:
                    if int(flood_damage.loc[user,'Cost of damage']) < 3:
                        DRP_payment = int(flood_damage.loc[user,'Cost of damage'])
                    else:
                        DRP_payment = 3
                    curA.execute("UPDATE budget_lb%s SET cb=cb+%s WHERE role=%s",
                                 (int(board), DRP_payment, user))
                    curA.execute("UPDATE budget_lb%s SET delta=%s WHERE role=%s",
                                 (int(board), DRP_payment, user))
                    total_DRP += DRP_payment
            curA.execute("UPDATE budget_lb%s SET cb=cb-%s WHERE role=%s",
                         (int(board), int(total_DRP), 'PP'))
            curA.execute("UPDATE budget_lb%s SET delta=-%s WHERE role=%s",
                         (int(board), int(total_DRP), 'PP'))
            conn.commit()
            with st.spinner('Processing insurance/DRP claim'):
                time.sleep(2)
            st.success('Insurance/DRP claims went through')
            time.sleep(2)


        col1, col2, col3  = st.columns(3)
        with col1:
            flood_submit = st.button(label='Submit flood details')
        with col3:
            insurance_submit = st.button(label='Submit insurance/DRP claim')

        if flood_submit:
            submit_flood_details()

        if insurance_submit:
            submit_insurance()

    # def update_damage_analysis(users,severity,protected):

def dev_tools():
    st.markdown('''___''')
    with st.expander('Dev tools'):
        def clear_transaction_log():
            curA = conn.cursor()
            curA.execute("DELETE FROM payment%s",[int(board)])
            conn.commit()
            with st.spinner('Clearing transaction log'):
                time.sleep(1)
            st.success('Transaction log cleared')
            time.sleep(1)
            st.experimental_rerun()

        def clear_bidding_log():
            curA = conn.cursor()
            curA.execute("DELETE FROM measure_log%s", [int(board)])
            conn.commit()
            with st.spinner('Clearing bidding log'):
                time.sleep(1)
            st.success('Bidding log cleared')
            time.sleep(1)
            st.experimental_rerun()

        col1, col2, col3 = st.columns(3)

        with col1:
            confirm_clear_log = st.button(label='Clear transaction log')
            confirm_clear_bid_log = st.button(label='Clear bidding log')

        if confirm_clear_log:
            clear_transaction_log()

        if confirm_clear_bid_log:
            clear_bidding_log()

        def reinitial_main_raster():
            curA = conn.cursor()
            curA.execute("UPDATE budget_lb%s SET cb=ib, delta=0, r1_tax=false, r2_tax=false, r3_tax=false, r1_vote=null, r2_vote=null, r3_vote=null, r1_insurance = false, r2_insurance = false, r3_insurance = false, r1_m_payment = false, r2_m_payment= false, r3_m_payment = false, r1_measure = NULL, r2_measure = NULL, r3_measure = NULL, r1_bid = NULL, r2_bid = NULL, r3_bid = NULL;",[board])
            for user in ['DP','EM','FP','M','PH','TA','WW','PP']:
                curA.execute("UPDATE budget_lb%s SET r1_tax=NULL, r2_tax=NULL, r3_tax=NULL WHERE role=%s;",(int(board),user))

            curA.execute("UPDATE budget_lb%s SET r1_m_payment=NULL, r2_m_payment= NULL, r3_m_payment = NULL WHERE role='J' OR role= 'I';",(int(board),))
            curA.execute("UPDATE frc_long_variables SET municipal_tax = 1, provincial_tax = 1, federal_tax = 1, r1_vote_override = false, r2_vote_override = false, r3_vote_override = false, phase = 1, power_price = 1, r1_taxed=FALSE, r2_taxed=FALSE, r3_taxed=FALSE,prog_counter= 0, round=1 WHERE board = %s", [int(board)])
            curA.execute("DELETE FROM impl_measures%s", [int(board)])
            conn.commit()
            with st.spinner('Reinitializing the main database'):
                time.sleep(2)
            st.success('Database reinitialized')
            time.sleep(2)
            st.experimental_rerun()

        with col2:
            confirm_reinit_raster = st.button(label='Reinitialize main database')

        if confirm_reinit_raster:
            reinitial_main_raster()

        def reset_flood_event():
            cursor = conn.cursor()
            cursor.execute("UPDATE frc_long_variables SET floods=ARRAY[null,null,null] WHERE board=%s;",[board])
            cursor.execute("UPDATE budget_lb%s SET r1_flood =null,r2_flood =null,r3_flood =null",[int(board)])
            conn.commit()
            with st.spinner('Resetting flood events'):
                time.sleep(2)
            st.success('Flood events cleared')


        with col3:
            reset_flood_confirm = st.button(label='Reset all flood events')

        if reset_flood_confirm:
            reset_flood_event()

        query = st.text_area(label='Custom query on database (do not use this field unless you are given specific instructions)')
        param = st.text_input(label='Query parameters')
        def perform_query():
            cur = conn.cursor()
            cur.execute(query, [param])
            conn.commit()
            st.success('Query committed to DB')

        st.button(label='Perform query',help='Do not click on this unless you are given specific instructions', on_click=perform_query)
    with st.expander('Database table'):
        st.dataframe(df)

def tax_payment_status():
    st.markdown('''___''')
    with st.expander('Update budget checklist'):
        st.markdown(read_markdown_file('checklists/update budget.md'))
    st.header('Tax and mandatory payments')
    confirm_rerun = st.button(label='Refresh Data', key='Tax section')
    if confirm_rerun:
        refresh()
    col1, col2 = st.columns(2)

    with col1:
        st.subheader('Who paid tax')
        df_tax = df[['r'+str(df_v.loc[board,'round'])+'_tax']]
        df_tax.rename(index=user_dict, inplace=True)
        df_tax_styled = df_tax.style.applymap(styler)
        st.dataframe(df_tax_styled)

    with col2:
        st.subheader('Who paid mandatory costs')
        df_payment = df[['r' + str(df_v.loc[board, 'round']) + '_m_payment']]
        df_payment.rename(index=user_dict, inplace=True)
        df_payment_styled = df_payment.style.applymap(styler)
        st.dataframe(df_payment_styled)

def tax_auto_short():
    st.markdown('''___''')
    st.subheader('Process tax and payment')

    def process_all():
        role_tax = ['P','EM','CSO','M','WR','F','LEF','LD']
        role_uni_tax = [1,2,0,7,0,1,0,0]  # the total sum of money to be added or removed from the role during the tax section
        try:
            for role, tax in zip(role_tax, role_uni_tax):
                curA = conn.cursor()
                curA.execute('UPDATE budget_lb%s SET cb=cb+%s WHERE role=ANY(%s);', (int(board), tax, [role]))
                curA.execute('UPDATE budget_lb%s SET delta=%s WHERE role=ANY(%s);', (int(board), tax, [role]))
                conn.commit()

            curA = conn.cursor()
            curA.execute('UPDATE frc_long_variables SET r%s_taxed=%s WHERE board=%s', (int(g_round), True, int(board)))
            conn.commit()

            with st.success('All payments processed'):
                time.sleep(2)
        except:
            pass

    if df_v.loc[int(board), 'r' + str(g_round) + '_taxed']:
        st.success('Tax and mandatory payments are already processed for this round')
    else:
        st.info('Taxes are not processed yet!')

    st.button(label="Process tax and payment", disabled=df_v.loc[int(board), 'r' + str(g_round) + '_taxed'],
              on_click=process_all)


def tax_auto_long():
    st.markdown('''___''')
    st.subheader('Process tax and payment')


    def process_all():
        # curA = conn.cursor()
        # curA.execute('UPDATE budget_lb%s SET cb=cb+%s WHERE role=ANY(%s);',(int(board),2,['P','EM','CSO','F']))
        # curA.execute('UPDATE budget_lb%s SET cb=cb+%s WHERE role=ANY(%s);', (int(board), 1, ['WR','LD']))
        # curA.execute('UPDATE budget_lb%s SET cb=cb+%s WHERE role=ANY(%s);', (int(board), 3, ['M']))
        # curA.execute('UPDATE frc_long_variables SET r%s_taxed=%s WHERE board=%s',(int(g_round),True,int(board)))
        # conn.commit()

        role_tax = ['CRA-HV', 'CRA-MHA', 'CRA-MV', 'DP','EM','ENGO','F', 'FP','FN','I','J','LD','LEF','M','PUC','PH','PP','TA', 'WW']
        role_uni_tax = [2,0,1,1,1,1,-1,3,0,-1,0,0,-1,1,6,3,0,7,0,0] #the total sum of money to be added or removed from the role during the tax section

        try:
            for role, tax in zip(role_tax,role_uni_tax):
                curA = conn.cursor()
                curA.execute('UPDATE budget_lb%s SET cb=cb+%s WHERE role=ANY(%s);',(int(board), tax, [role]))
                curA.execute('UPDATE budget_lb%s SET delta=%s WHERE role=ANY(%s);', (int(board), tax, [role]))
                conn.commit()

            curA = conn.cursor()
            curA.execute('UPDATE frc_long_variables SET r%s_taxed=%s WHERE board=%s', (int(g_round), True, int(board)))
            conn.commit()
        except:
            pass



        with st.success('All payments processed'):
            time.sleep(2)

    if df_v.loc[int(board), 'r' + str(g_round) + '_taxed']:
        st.success('Tax and mandatory payments are already processed for this round')
    else:
        st.info('Taxes are not processed yet!')

    st.button(label="Process tax and payment",disabled=df_v.loc[int(board),'r'+str(g_round)+'_taxed'],on_click=process_all)

#Voting section


def voting_status():
    st.markdown("""___""")
    with st.expander('Vote status checklist'):
        st.markdown(read_markdown_file('checklists/Vote.md'))
    st.header('Voting management')
    confirm_rerun = st.button(label='Refresh Data', key='vote section')
    if confirm_rerun:
        refresh()
    df_vote = df[['r'+str(g_round)+'_vote']]
    #df_vote.set_index('role',inplace=True)
    df_vote.rename(index=user_dict, inplace=True)
    st.dataframe(df_vote, use_container_width=True)
    def end_current_session():
        try:
            curA = conn.cursor()
            curA.execute("UPDATE frc_long_variables SET r%s_vote_override=%s WHERE board=%s",(int(g_round),True,int(board)))
            conn.commit()
            with st.spinner('Revealing results of the voting session'):
                time.sleep(1)
            st.success('Voting results are now available')
            time.sleep(2)
        except:
            pass

    end_vote_session = st.button(label='End current vote session and show results',on_click=end_current_session)


    st.subheader('Vote results (preview)')
    try:
        vote = []
        vote_g_round = []
        official = []
        for r in range(1, 4):
            for v in df.loc[:, 'r' + str(r) + '_vote']:
                if v is not None:
                    if game_type == 'Full':
                        for i, o in zip(range(3), ['Mayor', 'Provincial politician', 'Federal politician']):
                            vote.append(v[i])
                            official.append(o)
                            vote_g_round.append(r)
                    else:
                        for i, o in zip(range(1), ['Mayor']):
                            vote.append(v[i])
                            official.append(o)
                            vote_g_round.append(r)
        df_vote_result = pd.DataFrame(zip(vote, official, vote_g_round), columns=['Votes', 'Official', 'Game round'])
        sns.set_theme(style='darkgrid', palette='colorblind')
        fig = sns.catplot(data=df_vote_result, x='Votes', col='Official', kind='count', row='Game round')
        st.pyplot(fig)
    except:
        st.info('No result to show yet, keep refreshing the data')
        pass

#main page start


with st.expander('Game progression help'):
    st.markdown(read_markdown_file("checklists/Intro.md"))
    st.image('checklists/flow chart.png')
    st.markdown('The round and phases will be set automatically by a game admin, and you can see the current round and phase in blue boxes (see image below):')
    st.image('checklists/current phase.JPG')
    st.markdown('but you can see the options ahead of time by selecting via the phase selector in the main page (see image below):')
    st.image('checklists/phase settings.JPG')

def progress_game(direction):
    prog_counter = int(df_v.loc[board, 'prog_counter'])
    dict_prog = {0: [1,1], 1: [1,2], 2: [1,3], 3: [1,4], 4: [2,1], 5: [2,2], 6: [2,3], 7: [2,4], 8: [3,1], 9: [3,2], 10: [3,3], 11: [3,4]}
    if direction == 'forward':
        prog_counter += 1
    else:
        prog_counter -= 1
    curA = conn.cursor()
    curA.execute("UPDATE frc_long_variables SET phase=%s WHERE board=%s", (dict_prog[prog_counter][1], board))
    curA.execute("UPDATE frc_long_variables SET round=%s WHERE board=%s", (dict_prog[prog_counter][0], board))
    conn.commit()
    curA = conn.cursor()
    curA.execute("UPDATE frc_long_variables SET prog_counter=%s WHERE board=%s",(prog_counter,board))
    conn.commit()
    st.success('We progressed to next phase!')


admin_phase_dict = {0:None,3:tax_auto_short,1:bidding_section,5:transaction_management,2:flood_centre, 4:voting_status}
if df_authen.loc[username,'level'] == 1:
    with st.sidebar:
        st.subheader('Phase progression setting')
        phase_progress_type = st.radio(label='Method of showing the phase settings', options=['Manual select','Progression mode','Follow the current phase'],index=1)

    if phase_progress_type == 'Manual select':
        st.subheader('Phase settings')
        st.caption('Does not change the phase, but setting are adjustable ahead of time')
        set_phase = phase_dict_inv[st.selectbox(options=phase_dict.values(), label='See settings for:')]
    elif phase_progress_type == 'Progression mode':
        set_phase = int(df_v.loc[board, 'phase'])
        prog_counter = int(df_v.loc[board,'prog_counter'])
        colu1, colu2 = st.columns(2)

        with colu1:
            st.button(label='Return',on_click=progress_game,kwargs={'direction':'return'},help='Click here to go back to the last stage',disabled=prog_counter==0)

        with colu2:
            st.button(label='Progress game',on_click=progress_game,kwargs={'direction':'forward'},help='Click here to progress to next stage',disabled=prog_counter==11)
    else:
        set_phase = int(df_v.loc[board, 'phase'])

budget_section()

with st.expander('Secret transaction management'):
    secret_transaction_management()

if admin_phase_dict[set_phase] is not None:
    admin_phase_dict[set_phase]()

st.markdown('''___''')
st.subheader('Miro board ' + str(int(board)))
miro_dict = {1:['https://miro.com/app/live-embed/uXjVP5Rnvd8=/?moveToViewport=-1278,-7444,8403,5935&embedId=143045527681&embedAutoplay=true','https://miro.com/app/board/uXjVP5Rnvd8=/?share_link_id=424657725671'],
             2:['https://miro.com/app/live-embed/uXjVP5RnvfU=/?moveToViewport=-1096,-7622,8193,6241&embedId=384110064484&embedAutoplay=true','https://miro.com/app/board/uXjVP5RnvfU=/?share_link_id=17892545068'],
             3:['https://miro.com/app/live-embed/uXjVPBmsTmg=/?moveToViewport=-10463,-6096,8785,4266&embedId=26206919528&embedAutoplay=true','https://miro.com/app/board/uXjVPBmsTmg=/?share_link_id=27320976313'],
             4:['https://miro.com/app/live-embed/uXjVOR_hQ8o=/?moveToViewport=-23351,-9416,27515,14305&embedAutoplay=true','https://miro.com/app/board/uXjVOR_hQ8o=/?invite_link_id=471512594109'],
             5:['https://miro.com/app/live-embed/uXjVOR_h058=/?moveToViewport=-23351,-9416,27515,14305&embedAutoplay=true','https://miro.com/app/board/uXjVOR_h058=/?invite_link_id=575464384272'],
             6:['https://miro.com/app/live-embed/uXjVOR_h1vw=/?moveToViewport=-23351,-9416,27515,14305&embedAutoplay=true','https://miro.com/app/board/uXjVOR_h1vw=/?invite_link_id=87971323805']}

with st.expander('Miro board', expanded=True):
    components.iframe(miro_dict[int(board)][0],height=740)
    st.write("Open board in a new tab [link]("+miro_dict[int(board)][1]+')')

if df_authen.loc[username,'level'] == 3:
    dev_tools()
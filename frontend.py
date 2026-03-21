import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import google.generativeai as genai

# set up page
st.set_page_config(page_title='Patient DB Explorer', layout='wide')
st.title('Patient DB Explorer')
st.markdown('Real-time patient data from PostgreSQL DB')

# connect to PostgreSQL
@st.cache_resource
def init_connection():
    return create_engine('postgresql://test_user:password123@localhost:5432/patient_db')

engine = init_connection()

# display live feed
st.subheader('Live Patient Feed')
df = pd.read_sql("SELECT * FROM patients;", engine)
st.dataframe(df, use_container_width=True)

st.divider()

# display LLM interface
st.subheader('Ask AI about patient data (generate and run SQL query)')

with st.form("sql_builder_form"):
    inp = st.text_input('Your query:', placeholder='e.g., How many male patients are there?')
    submitted = st.form_submit_button("Submit")

if inp and submitted:
    # config gemini
    genai.configure(api_key=st.secrets['GEMINI_API_KEY'])
    
    # schema for gatekeeper (evaluates legitimacy of user input)
    gatekeeper_context = f"""
    You are a strict data validation assistant.
    I have a database with a 'patients' table containing only these columns:
    - patient_id (VARCHAR)
    - first_name (VARCHAR)
    - last_name (VARCHAR)
    - dob (DATE)
    - gender (VARCHAR - values are 'male', 'female', 'other', 'unknown')
    - processed_at (TIMESTAMP)

    The user asked: "{inp}"

    Can this question be answered using the data in this table?
    If yes, reply with the exact word: YES
    If no, or if the user input is unrelated to the table, reply with the exact word: NO
    """
    
    gatekeeper_model = genai.GenerativeModel('gemini-3-flash-preview')
    gatekeeper_response = gatekeeper_model.generate_content(gatekeeper_context, generation_config=genai.types.GenerationConfig(temperature=0.0))
    
    decision = gatekeeper_response.text.strip().upper()

    if "YES" not in decision:
        st.warning("This question or input cannot be answered using the data in the table. Please try again.")
        st.stop()

    # schema for SQL-generating LLM
    context = """
    You are a SQL expert. I have a PostgreSQL database with a table named 'patients'.
    The 'patients' table has the following columns:
    - patient_id (VARCHAR)
    - first_name (VARCHAR)
    - last_name (VARCHAR)
    - dob (DATE)
    - gender (VARCHAR - values are 'male', 'female', 'other', 'unknown')
    - processed_at (TIMESTAMP)

    Write ONLY a valid PostgreSQL query to answer the user's question. Do not include any markdown formatting or explanations.
    Just include the raw SQL string.
    """

    st.info(f"Generating SQL based on your input...")

    try:
        # init gemini model
        model = genai.GenerativeModel(model_name = 'gemini-3-flash-preview', system_instruction=context)

        # generate SQL
        response = model.generate_content(inp, generation_config=genai.types.GenerationConfig(temperature=0.0))

        # clean response
        out = response.text
        generated_sql = out.replace("```sql","").replace("```","").strip() # remove markdown ticks

        st.success("SQL Generated!")
        st.code(generated_sql, language='sql')

        # execute SQL
        result_df = pd.read_sql(generated_sql, engine)
        st.write("### Query Results")
        st.dataframe(result_df)

        # generate natural summary
        st.info("Analyzing results...")
        result_model = genai.GenerativeModel(model_name='gemini-3-flash-preview')
        data_string = result_df.to_markdown(index=False)
        answer_prompt = f"""
        The user asked the following question: "{inp}"

        Here is the raw data returned from the SQL database:
        {data_string}
        
        Based ONLY on this data, write a clear, conversational, and brief answer to the user's question.
        """

        # generate answer with slightly more creative writing
        text_response = result_model.generate_content(answer_prompt, generation_config=genai.types.GenerationConfig(temperature=0.3))

        # display answer
        st.write("### AI Answer")
        st.success(text_response.text)

    except Exception as e:
        st.error(f"Error executing query: {e}")
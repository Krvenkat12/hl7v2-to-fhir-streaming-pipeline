from confluent_kafka import Consumer
import hl7
import json
import requests
import psycopg2

# configure consumer
conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'fhir-converter-group',
    'auto.offset.reset': 'earliest'
}

fhir_server_url = "http://localhost:8080/fhir/Patient"

# create consumer
c = Consumer(conf)

#subscribe to topic
topic_name = 'hl7-admissions'
c.subscribe([topic_name])

print(f'Listening to topic: {topic_name}')

# mapping function
def map_pid_to_fhir(pid_segment):
    """
    Convert HL7 PID segment to FHIR Patient resource.
    """
    
    # extract raw fields
    patient_id = str(pid_segment[3])
    name = str(pid_segment[5]).split('^')
    last_name = name[0]
    first_name = name[1] if len(name) > 1 else ""
    raw_dob = str(pid_segment[7])
    raw_gender = str(pid_segment[8])

    # convert dob to FHIR format
    fhir_dob = f"{raw_dob[:4]}-{raw_dob[4:6]}-{raw_dob[6:]}" if len(raw_dob) == 8 else raw_dob
    
    #convert gender codes to lowercase
    gender_map = {
        "M": "male",
        "F": "female",
        "O": "other",
        "U": "unknown"
    }
    fhir_gender = gender_map.get(raw_gender, "unknown")

    # construct FHIR JSON schema
    fhir_patient = {
        "resourceType": "Patient",
        "identifier": [
            {
                'system': 'http://mockhospital.com/patient-ids',
                'value': patient_id
            }
        ],
        'name': [
            {
                'use': 'official',
                'family': last_name,
                'given': [first_name]
            }
        ],
        'gender': fhir_gender,
        'birthDate': fhir_dob
    }

    return fhir_patient

# SQL database setup
print('Connecting to PostgreSQL...')
conn = psycopg2.connect(
    host='localhost',
    database='patient_db',
    user='test_user',
    password='password123'
)

# create cursor
cur = conn.cursor()

# create table
cur.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        patient_id VARCHAR(255) PRIMARY KEY,
        first_name VARCHAR(255),
        last_name VARCHAR(255),
        dob DATE,
        gender VARCHAR(50),
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

conn.commit()
print("PostgreSQL connection established and table created")

# create listening loop
try:
    while True:
        msg = c.poll(1.0) # poll queue every 1s
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
        # extract message
        raw_hl7 = msg.value().decode('utf-8')
        parsed_msg = hl7.parse(raw_hl7)
        pid_segment = parsed_msg.segment('PID')
        
        # transform to FHIR
        fhir_json_dict = map_pid_to_fhir(pid_segment)
        
        # load
        headers = {'Content-Type': 'application/fhir+json'}

        # POST to HAPI FHIR server
        response = requests.post(
            fhir_server_url,
            json=fhir_json_dict,
            headers=headers
        )

        # sink to SQL DB
        id = fhir_json_dict['identifier'][0]['value']
        f_name = fhir_json_dict['name'][0]['given'][0]
        l_name = fhir_json_dict['name'][0]['family']
        dob = fhir_json_dict['birthDate']
        gender = fhir_json_dict['gender']

        cur.execute("""
            INSERT INTO patients (patient_id, first_name, last_name, dob, gender)
            VALUES (%s, %s, %s, %s, %s)
            """, (id, f_name, l_name, dob, gender))
        conn.commit()
        
        # print result
        print('\n')
        if response.status_code == 201: # created
            print(f"Successfully loaded Patient: {fhir_json_dict['name'][0]['family']}")
            print(f'Server response: {response.json().get('id', 'Unknown ID')}')
        else:
            print(f"Failed to load Patient. Status: {response.status_code}")
            print(f'Error details: {response.text}')
except KeyboardInterrupt:
    print("\nStopping consumer...")
finally:
    cur.close()
    conn.close()
    c.close()
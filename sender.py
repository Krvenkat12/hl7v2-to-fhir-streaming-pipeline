import pandas as pd
from datetime import datetime
from confluent_kafka import Producer
import time

# Kafka producer configuration
conf = {
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'hl7-mock-producer'
}

# create producer
p = Producer(conf)

# confirm message delivery
def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

patients_df = pd.read_csv("./output/csv/patients.csv")

# iterate through csv records to build HL7 messages and stream

topic_name = 'hl7-admissions'
print(f"Sending messages to topic: {topic_name}...")

for index, row in patients_df.iterrows():
    patient_id = row['Id']
    first_name = row['FIRST']
    last_name = row['LAST']
    gender = row['GENDER']
    dob = str(row['BIRTHDATE']).replace('-', '')

    # construct message header
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    msh_segment = f"MSH|^~\\&|Synthea|LegacyHospital|FHIRConverter|DataTeam|{timestamp}||ADT^A01|msg_{index}|P|2.3"

    # construct PID segment
    pid_segment = f"PID|1||{patient_id}||{last_name}^{first_name}||{dob}|{gender}"

    # combine with carriage return
    hl7_message = f"{msh_segment}\r{pid_segment}"
    
    # produce message to kafka
    p.produce(topic_name, value=hl7_message.encode('utf-8'), callback=delivery_report)

    # poll to ensure delivery/callbacks and sleep to stagger message stream
    p.poll(0)
    time.sleep(1)

# flush remaining messages
p.flush()
print("All messages sent successfully.")
    

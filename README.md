# HL7v2 to FHIR Streaming Pipeline
The goal of this project is to convert patient messages from HL7v2 format, which is still the dominant healthcare data exchange framework in the United States despite releasing in 1989, to the modern HL7 FHIR framework using an ETL pipeline solution. Although moving off of old infrastructure can be timely and costly, FHIR comes with an array of fruitful benefits for both health-tech developers and doctors.

<img width="1835" height="722" alt="image" src="https://github.com/user-attachments/assets/41476a64-3b0e-4d0d-b605-cf0e47b7bd1f" />


## How does it work?
- First, synthetic patient records (CSV, non-FHIR) are generated using [Synthea](https://github.com/synthetichealth/synthea). A set of a little over 100 records are provided in this repo, but if you would like to generate your own, copy the patients.csv file from Synthea's output to the root of this project.
- Several Docker containers are initialized, such as Kafka for message streaming, HAPI-FHIR to use as a mock FHIR server, and Postgres to send the results to an SQL database. **Docker Desktop must be running for the code to work so that these containers can be created.**
- As an aside, Apache Kafka is used to simulate real healthcare systems where data is constantly being sent to multiple receivers in real-time. For example, if the data were to scale significantly, the code in this build can easily be adjusted to add new receivers (e.g., a data lake).
- As a preliminary step for the data, each row is transformed into a pipe-delineated string that adheres to the HL7v2 format. This is done because Synthea does not natively support outputting data in HL7v2 but does support formats such as CSV and FHIR.
- Each string is then streamed to Kafka. On the receiving end, as each message is received, the string is broken down into its individual components and transformed into a JSON/dictionary format that adheres to FHIR.
- Each converted message is then posted to the HAPI FHIR server and subsequently inserted into the Postgres database using SQL. The FHIR server will display the patient data in JSON format. Each page will display about 20 patients, and each subsequent page can be navigated to by finding, on the page, the URL associated with the "next" relation.
- The program will open both the FHIR server as well as a web application which will display the Postgres DB. These pages can be refreshed as the data is continuously being streamed.
- The web application has been made using Streamlit, which is a framework that provides developers with intuitive tools for showcasing and analyzing data. The app features an AI chatbot that can generate and run SQL queries on the database based on your input. The generative AI model under the hood is Gemini 3 Flash, which was chosen based on its performance of generating SQL code as well as the availability of a free tier with access to more-than-capable models.

## Usage
- Clone this repo.
- In the root of the project, open a terminal and type and enter ```.\run.bat``` (or ```sh run.sh``` on Mac/Linux) to begin the program. This batch script prompts the user for their Gemini API key, which can be generateed for free [here](https://aistudio.google.com/), installs dependencies, starts the Docker containers, opens the FHIR server, and runs each Python script concurrently.
- To terminate the Docker containers, in a terminal, type and enter ```.\stop.bat``` (or ```sh stop.sh``` on Mac/Linux).

## Data Sources & Acknowledgement
The mock patient data used to simulate the streaming environment in this project was generated using **[Synthea™](https://github.com/synthetichealth/synthea)**, an open-source, synthetic patient population simulator.

**Citation:**
> Walonoski J, Kramer M, Nichols J, Quina A, Moesel C, Hall D, Duffett C, Dube K, Gallagher T, McLachlan S. *Synthea: An approach, method, and software mechanism for generating synthetic patients and the synthetic electronic health care record.* Journal of the American Medical Informatics Association. 2018 Aug 1;25(8):230-8. [https://doi.org/10.1093/jamia/ocx079](https://doi.org/10.1093/jamia/ocx079)

# Comp-Project-1

## AI Nurse assistant 
1. verify the patient Name and ID 
2. Ask symptoms
3. Follow ups to know more
4. record all symptoms in pdf and json
5. Record chat history in pdf and json
6. Classify patient's symptoms to cardiological or diabetes related
7. Refer and direct chat to another LLM (cardioLLM or diabetesLLM based on classification for deeper and specialized analysis along wth sensor data)
8. Keep updating the data

   PDF - for human reference (doctor, specialist, non IT person)


   Json - for LLM training and retraining purposes to improve the model and to pass all the information to another specialized LLM
   
## Technologies used 
1. Python
2. Streamlit
3. FPDF
4. Json

## Future Directions :
1. CrewAI integration for delegation or routing to another LLM (cardioLLM or DiabetesLLM)
2. WhatsApp integration for conversation on the Go
3. Vector Database for memory based on the previous convesation (after name and ID verification)
4. SerpAPI integration for web browse 

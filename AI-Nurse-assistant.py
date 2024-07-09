import streamlit as st
from openai import OpenAI
from fpdf import FPDF
import os
import json
import base64
from datetime import datetime

# Set up OpenAI API key
client = OpenAI(api_key="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")

MIN_QUESTIONS = 10
MAX_RETRIES = 3

def get_ai_response(messages, retries=0):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        if retries < MAX_RETRIES:
            st.warning(f"An error occurred. Retrying... ({retries + 1}/{MAX_RETRIES})")
            return get_ai_response(messages, retries + 1)
        else:
            st.error(f"Failed to get AI response after {MAX_RETRIES} attempts. Please try again later.")
            return None

def create_pdf_with_chat_history(messages):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for message in messages:
        role = "User" if message["role"] == "user" else "AI"
        pdf.multi_cell(0, 10, f"{role}: {message['content']}")
    pdf_output = "chat_history.pdf"
    pdf.output(pdf_output)
    return pdf_output

def create_pdf_user_info(patient_info):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Patient Information", ln=1, align='C')
    
    for key, value in patient_info.items():
        pdf.cell(200, 10, txt=f"{key.capitalize()}: {value}", ln=1)
    
    pdf_output = "patient_info.pdf"
    pdf.output(pdf_output)
    return pdf_output

def create_json_with_chat_history(messages):
    json_output = "chat_history.json"
    with open(json_output, "w") as json_file:
        json.dump(messages, json_file, indent=4)
    return json_output

def create_json_with_patient_info(patient_info):
    json_output = "patient_info.json"
    with open(json_output, "w") as json_file:
        json.dump(patient_info, json_file, indent=4)
    return json_output

def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}" id="{file_label}">{file_label}</a>'
    return href

def parse_ai_response(response):
    patient_info = {}
    lines = response.split('\n')
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            if key in ['name', 'id', 'symptoms', 'onset', 'duration', 'severity', 'associated factors', 'category']:
                if key == 'symptoms' and 'symptoms' in patient_info:
                    patient_info[key] += ", " + value
                else:
                    patient_info[key] = value
    return patient_info

def initialize_session():
    st.session_state.messages = [
        {"role": "system", "content": "You are an AI Nurse assistant conducting a professional medical interview. Always start by greeting the patient and asking for their name and ID for verification. Then collect detailed patient information including symptoms, onset, duration, severity (1-10), associated factors, and category (cardiology or diabetes). Ask relevant, non-repetitive questions. Maintain a compassionate and professional tone."}
    ]
    st.session_state.patient_info = {}
    st.session_state.question_count = 0
    st.session_state.conversation_ended = False
    st.session_state.current_question = "Hello! I'm your AI Nurse Assistant. Before we begin, could you please provide your name and ID number for verification?"

def main():
    st.title("AI Nurse Assistant")

    if "messages" not in st.session_state:
        initialize_session()

    if not st.session_state.messages[1:]:
        with st.chat_message("assistant"):
            st.markdown(st.session_state.current_question)
        st.session_state.messages.append({"role": "assistant", "content": st.session_state.current_question})

    for message in st.session_state.messages[1:]:  # Skip the system message
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if not st.session_state.conversation_ended:
        if prompt := st.chat_input("Your response:"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            ai_prompt = f"""
            Current question: {st.session_state.current_question}
            User's response: {prompt}
            Current patient info: {st.session_state.patient_info}

            Based on the user's response, update the appropriate field in the patient information.
            If the user confirms new symptoms, add them to the existing symptoms list.
            Ensure that severity is between 1-10 if provided.
            Classify symptoms as either cardiology or diabetes related when possible.
            Always include onset, duration, and associated factors in your response.
            Respond with the updated patient info and the next question to ask.
            Use this format for your response, but only return the 'Next question' part to the user:
            Name: [name]
            ID: [id]
            Symptoms: [all symptoms, including newly confirmed ones]
            Onset: [onset]
            Duration: [duration]
            Severity: [severity]
            Associated factors: [associated factors]
            Category: [category]
            Next question: [next question to ask]
            """

            ai_response = get_ai_response(st.session_state.messages + [{"role": "user", "content": ai_prompt}])
            if ai_response:
                # Parse the AI response to update patient info
                new_info = parse_ai_response(ai_response)
                st.session_state.patient_info.update(new_info)

                # Extract just the question to display to the user
                next_question = ai_response.split("Next question:")[-1].strip()
                
                # Display only the question to the user
                with st.chat_message("assistant"):
                    st.markdown(next_question)

                # Update the session state
                st.session_state.messages.append({"role": "assistant", "content": next_question})
                st.session_state.current_question = next_question

                st.session_state.question_count += 1

                if st.session_state.question_count >= MIN_QUESTIONS or "anything else" in ai_response.lower():
                    # Final summary and referral
                    summary_prompt = f"""
                    Please provide a final summary of the patient's information:
                    {st.session_state.patient_info}
                    
                    Summarize this information concisely and determine whether to refer to a Cardio LLM or Diabetes LLM based on the symptoms and category.
                    """
                    summary_response = get_ai_response(st.session_state.messages + [{"role": "user", "content": summary_prompt}])
                    
                    with st.chat_message("assistant"):
                        st.markdown(summary_response)
                    
                    st.session_state.messages.append({"role": "assistant", "content": summary_response})
                    
                    # Determine referral based on category
                    category = st.session_state.patient_info.get('category', '').lower()
                    if 'diabetes' in category:
                        referral_message = "I have recorded all the relevant data and now referring you to our expert AI diabetes specialist for further analysis."
                    else:  # Default to cardiology if not specifically diabetes
                        referral_message = "I have recorded all the relevant data and now referring you to our expert AI cardiologist for further analysis."
                    
                    with st.chat_message("assistant"):
                        st.markdown(referral_message)
                    
                    st.session_state.messages.append({"role": "assistant", "content": referral_message})
                    st.session_state.conversation_ended = True

            st.rerun()

    if st.session_state.conversation_ended:
        st.write("Thank you for providing your information. Here's a summary of what we've gathered:")
        
        for key, value in st.session_state.patient_info.items():
            st.write(f"{key.capitalize()}: {value}")

        # Generate and display download links
        pdf_chat_file = create_pdf_with_chat_history(st.session_state.messages)
        pdf_info_file = create_pdf_user_info(st.session_state.patient_info)
        json_chat_file = create_json_with_chat_history(st.session_state.messages)
        json_info_file = create_json_with_patient_info(st.session_state.patient_info)
        
        pdf_chat_link = get_binary_file_downloader_html(pdf_chat_file, 'Download Chat History PDF')
        pdf_info_link = get_binary_file_downloader_html(pdf_info_file, 'Download Patient Info PDF')
        json_chat_link = get_binary_file_downloader_html(json_chat_file, 'Download Chat History JSON')
        json_info_link = get_binary_file_downloader_html(json_info_file, 'Download Patient Info JSON')
        
        st.markdown(pdf_chat_link, unsafe_allow_html=True)
        st.markdown(pdf_info_link, unsafe_allow_html=True)
        st.markdown(json_chat_link, unsafe_allow_html=True)
        st.markdown(json_info_link, unsafe_allow_html=True)

        st.success("Your information summary has been prepared as PDF and JSON files. Please click the links above to download them.")

        if st.button("Start New Consultation"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
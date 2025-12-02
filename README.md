
# MAT496 Capstone Project

## Medical Symptom Analyzer  
By Karthik Raj R (2210110344)  
  
Video link for the project summary and demo run: https://drive.google.com/file/d/1qT7MJ6WkwDdzurSyH5mxPSiLaLuPIRPy/view?usp=drive_link  
    
Note: Video length is slightly over 5 minutes due the the execution time being more.
(Both jupyter notebook and the langgraph website graph)    
  
## Overview

The project takes in medical symptoms from the patient. Then a certain number of doctors from various specializations (which can be chosen by the user based on their area of interest, experience and university) offer their insights for the situation. After this, the doctors provide a treatment plan for the patient from their expertise. (For example, if the symptom is back pain, an orthopedist and a physical therapist can have differing treatment plans). Finally, all the information from all doctors is summarized into a clean, easy to understand diagnosis for the patient(user), who can choose their treatment plan accordingly.

## Reason for picking up this project:

Getting perspective from multiple doctors is a very practical scenario. With the power of AI, getting data from all these perspectives is effective and simple. Furthermore, this use-case ensures a lot of the concepts learnt during the course can be applied. And most important of all, a model like this can be used by a layman in a day-to-day manner. 

The above reasons are why I have decided to try to make an application which diagnoses a symptom from various specialized perspectives.

## Plan:

Here is a step by step plan for completion of the project

[DONE] Step-1: Create a template for a doctor (with qualifications, specialization, experience etc)  
[DONE] Step-2: Make a simple graph which incorporates human feedback to choose doctors according to the user's preference.    
[DONE] Step-2.5: Testing out human feedback to modify the list of doctors obtained.   
[DONE] Step-3: Get the doctors to analyze the patient's symptom (Big step, divide into substeps)  
[DONE] Step-3.1: Decide on method of generating information (decided on debate between experts)    
[DONE] Step-3.2: Add web search capabilities (Tavily) and integrate parallelization        
[DONE] Step-4: Combine information from all doctors and give the patient a comprehensive and simple to understand diagnosis from various perspectives.(Possibly offer the patient mulitple "treatment plans" with its positives and negatives and they can choose accordingly)    
[DONE] Step-5: Integrate all the above steps into a working graph, which can take symptom from user and returns the final diagnosis.    
[DONE] Step-6: Make a .py file to get the same in langgraph and observe if similar results can be obtained.  

## Conclusion:  
The project has been completed successfully. The initial goal to get multiple doctors to analyze a patient's symptom and give treatments from their specialization point of view was successful. Geting the three doctors to have a conversation amongst themselves was successful.   
  
However a few things which were not satisfactory and can be improved in the future. 
-> Unable to integrate human feedback in creation of doctors in the final graph. (Integrating both graphs and maintaining the format got messy since I had made a separate debate graph in between.)  
-> A few places still hardcoded with 3 doctors in assumption.    
  
To summarize the overall project was a success with being able to acheive the initial goal. A few improvements can be done down the line, but it is a pretty good graph. The most important part ofcourse is that designing this project has helped in refreshing all concepts learnt throughout the course and improve understanding of them since I had to write it from scratch with the course as reference.  





  
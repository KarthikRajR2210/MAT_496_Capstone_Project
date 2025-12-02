import operator
from pydantic import BaseModel, Field
from typing import Annotated, List
from typing_extensions import TypedDict

from langchain_community.document_loaders import WikipediaLoader
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, get_buffer_string
from langchain_openai import ChatOpenAI

from langgraph.constants import Send
from langgraph.graph import END, MessagesState, START, StateGraph

### LLM

llm = ChatOpenAI(model="gpt-5", temperature=0) 

class Doctor(BaseModel):
    name: str = Field(
        description="Name of the doctor."
    )
    qualifications: str = Field(
        description="Qualifications of the doctor",
    )
    specialization: str = Field(
        description="Specialization of the dcotor i.e., cardiologist, dermatologist, orthopedist, etc.",
    )
    experience: int = Field(
        description="Number of years of work experience of the doctor"
    )
    description: str = Field(
        description="Description of the doctor's place of work, achievements, etc.",
    )
    @property
    def persona(self) -> str:
        return f"Name: {self.name}\nQualifications: {self.qualifications}\nSpecialization: {self.specialization}\nExperience: {self.experience}\nDescription: {self.description}\n"

class Perspectives(BaseModel):
    doctors: List[Doctor] = Field(
        description="Comprehensive list of doctors with their specializations, place of work and qualifications.",
    )

class GenerateDoctorsState(TypedDict):
    symptom: str 
    max_doctors: int 
    human_feedback: str 
    doctors: List[Doctor]

class DebateState(MessagesState):
    max_num_turns: int 
    context: Annotated[list, operator.add] 
    doctors: list
    debate: str 
    sections: list 

class SearchQuery(BaseModel):
    search_query: str = Field(None, description="Search query for retrieval.")

from dataclasses import dataclass, field
@dataclass
class FinalState:
    symptom: str 
    max_doctors: int  
    doctors: List[Doctor]
    max_num_turns: int 
    context: Annotated[list, operator.add] 
    debate: str 
    sections: list

doctor_instructions="""You are tasked with creating a set of Doctors. Follow these instructions carefully:

1. First, take a look at the symptom: {symptom}
        
2. Examine any feedback that has been optionally provided to guide creation of the doctor personas: 
        
{human_feedback}
    
3. Determine the most suitable specialists who can diagnose the symptom {symptom}.
                    
4. Pick the top {max_doctors} specialists most suited for the symptom {symptom}.

5. Assign one doctor for each specialization."""

def create_doctors(state: GenerateDoctorsState):
    
    """ Create doctors """
    
    symptom=state['symptom']
    max_doctors=state['max_doctors']
    human_feedback=state.get('human_feedback', '')
        
    structured_llm = llm.with_structured_output(Perspectives)

    system_message = doctor_instructions.format(symptom=symptom,
                                                            human_feedback=human_feedback, 
                                                            max_doctors=max_doctors)
 
    doctors = structured_llm.invoke([SystemMessage(content=system_message)]+[HumanMessage(content="Generate the list of doctors.")])


    return {"doctors": doctors.doctors}

debate_instructions = """You are to initiate a discussion between multiple doctors to diagnose the given symptom. 

Your goal is to get all of them to justify their approach and try to convince the other doctors why their way is the best. Be open to all ideas and decide the best way.

1. Take turns: Have a back and forth with the other specialists on how to diagnose and treat the symptom.
        
2. Specific: Insights that avoid generalities and include specific knowledge from each induviduals field.

Here is your topic of focus and set of goals for each doctor: {goals}
        
Begin by introducing yourself using a name that fits your persona, and then make your case.

Continue to ask questions to drill down and refine your treatment plan for the patient.

You are to make judgments based on just the symptoms of the patient, if there is any uncertainty (i.e. gender, age, history), you are to provide answers for all cases to be as all-encompassing as possible
        
When you are satisfied with your plan, complete the debate with: "Thank you!"

Remember to stay in character throughout your response, reflecting the persona and goals provided to you."""

def generate_discussion(state: DebateState):
    """ Node to generate a discussion """

    doctors = state["doctors"]
    messages = state["messages"]
 
    system_message = debate_instructions.format(goals={doctors[0].persona,doctors[1].persona,doctors[2].persona})
    sentence = llm.invoke([SystemMessage(content=system_message)]+messages)
        
    return {"messages": [sentence]}

search_instructions = SystemMessage(content=f"""You will be given a conversation between medical experts diagnosing a symptom. 

Your goal is to generate a well-structured query for use in retrieval and / or web-search related to the conversation.
        
First, analyze the full conversation.

Pay particular attention to the treatment plan posed by each doctor.

Verify this final plan using a well-structured web search query""")

def search_web(state: DebateState):

    structured_llm = llm.with_structured_output(SearchQuery)
    search_query = structured_llm.invoke([search_instructions] + state['messages'])
    tavily_search = TavilySearchResults(max_results=2)
    search_docs = tavily_search.invoke(search_query.search_query)

    if isinstance(search_docs, dict) and "results" in search_docs:
        search_docs = search_docs["results"]

    formatted = []

    for doc in search_docs:
        if isinstance(doc, dict):
            url = doc.get("url", "unknown")
            content = doc.get("content", str(doc))
            formatted.append(
                f'<Document href="{url}">\n{content}\n</Document>'
            )
        else:
            formatted.append(
                f'<Document>\n{str(doc)}\n</Document>'
            )

    return {"context": ["\n\n---\n\n".join(formatted)]}


def search_wikipedia(state: DebateState):
    
    """ Retrieve docs from wikipedia """

    structured_llm = llm.with_structured_output(SearchQuery)
    search_query = structured_llm.invoke([search_instructions]+state['messages'])
    
    search_docs = WikipediaLoader(query=search_query.search_query, 
                                  load_max_docs=3).load()

    formatted_search_docs = "\n\n---\n\n".join(
        [
            f'<Document source="{doc.metadata["source"]}" page="{doc.metadata.get("page", "")}"/>\n{doc.page_content}\n</Document>'
            for doc in search_docs
        ]
    )

    return {"context": [formatted_search_docs]} 

def merge_search_results(state: DebateState):
    merged = "\n\n".join(state["context"])
    return {"context": [merged]}

def generate_treatment_plan(state: DebateState):
    """
    Node that merges:
    - all debate conversation
    - web + wikipedia search context
    and generates a final, unified medical treatment plan.
    """

    messages = state["messages"]            
    context_list = state.get("context", []) 
    debate_topic = state.get("debate", "")  
    
    context_text = "\n\n".join(context_list) if context_list else "No external context available."
    
    system_message = """You are a panel lead physician tasked with producing the *final medical treatment plan based on:

    1. The entire debate between specialists.
    2. The combined search context (clinical guidelines, web results, wikipedia summaries).
    3. The patient’s main complaint: {debate_topic}

    Your output must be:

    - Structured
    - Evidence-based
    - Reflective of the discussion points raised by all specialists
    - Clear and clinically actionable

    DO NOT repeat the debate.
    DO NOT repeat the search results.
    Synthesize everything into a **single, authoritative treatment plan**.

    Include:
    - Primary diagnosis or differential
    - Recommended diagnostic tests with justification
    - Initial treatment
    - Follow-up considerations
    - Any red flags or escalation scenarios

Finish with: “Final plan complete.”
"""

    final_response = llm.invoke([SystemMessage(content=system_message)] + messages)
    final_response.name = "treatment_plan"

    return {"messages": [final_response]}

def bridge(state: FinalState):
    return state

full_builder = StateGraph(FinalState)
full_builder.add_node("create_doctors", create_doctors)
#full_builder.add_node("human_feedback", human_feedback)

full_builder.add_node("bridge",bridge)

full_builder.add_node("debate_step", generate_discussion)
full_builder.add_node("search_web", search_web)
full_builder.add_node("search_wikipedia", search_wikipedia)
full_builder.add_node("merge_search_results", merge_search_results)
full_builder.add_node("generate_treatment_plan", generate_treatment_plan)

# Flow
full_builder.add_edge(START, "create_doctors")
full_builder.add_edge("create_doctors", "bridge")
#full_builder.add_conditional_edges("human_feedback", should_continue, ["create_doctors", "bridge"])



full_builder.add_edge("bridge", "debate_step")
full_builder.add_edge("debate_step", "search_web")
full_builder.add_edge("debate_step", "search_wikipedia")
full_builder.add_edge("search_web", "merge_search_results")
full_builder.add_edge("search_wikipedia", "merge_search_results")
full_builder.add_edge("merge_search_results", "generate_treatment_plan")
full_builder.add_edge("generate_treatment_plan", END)

graph = full_builder.compile()


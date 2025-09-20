import os
import json
from crewai import LLM
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (VisionTool)
from po_invoice_discrepancy_analyzer.tools.textract_tool import TextractTool


from crewai_tools import CrewaiEnterpriseTools
from pydantic import BaseModel
from jambo import SchemaConverter

@CrewBase
class PoInvoiceDiscrepancyAnalyzerCrew:
    """PoInvoiceDiscrepancyAnalyzer crew"""

    
    @agent
    def document_ocr_processor(self) -> Agent:

        
        return Agent(
            config=self.agents_config["document_ocr_processor"],
            
            
            tools=[
                TextractTool()
            ],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            max_execution_time=None,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
            
        )
    
    @agent
    def po_data_extractor(self) -> Agent:

        
        return Agent(
            config=self.agents_config["po_data_extractor"],
            
            
            tools=[

            ],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            max_execution_time=None,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
            
        )
    
    @agent
    def invoice_data_extractor(self) -> Agent:

        
        return Agent(
            config=self.agents_config["invoice_data_extractor"],
            
            
            tools=[

            ],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            max_execution_time=None,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
            
        )
    
    @agent
    def document_discrepancy_analyst(self) -> Agent:

        
        return Agent(
            config=self.agents_config["document_discrepancy_analyst"],
            
            
            tools=[

            ],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            max_execution_time=None,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
            
        )
    
    @agent
    def email_reporter(self) -> Agent:
        enterprise_actions_tool = CrewaiEnterpriseTools(
            enterprise_token=os.getenv("ENTERPRISE_TOKEN"),
            actions_list=[
                
                "gmail_send_email",
                
            ],
        )

        
        return Agent(
            config=self.agents_config["email_reporter"],
            
            
            tools=[
				*enterprise_actions_tool
            ],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            max_execution_time=None,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
            
        )
    

    
    @task
    def extract_documents_text(self) -> Task:
        return Task(
            config=self.tasks_config["extract_documents_text"],
            markdown=False,
        )
    
    @task
    def parse_po_data(self) -> Task:
        return Task(
            config=self.tasks_config["parse_po_data"],
            markdown=False,
            
        )
    
    @task
    def parse_invoice_data(self) -> Task:
        return Task(
            config=self.tasks_config["parse_invoice_data"],
            markdown=False,
            
        )
    
    @task
    def analyze_discrepancies(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_discrepancies"],
            markdown=False,
            
        )
    
    @task
    def send_email_report(self) -> Task:
        return Task(
            config=self.tasks_config["send_email_report"],
            markdown=False,
            
        )
    

    @crew
    def crew(self) -> Crew:
        """Creates the PoInvoiceDiscrepancyAnalyzer crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )

    def _load_response_format(self, name):
        with open(os.path.join(self.base_directory, "config", f"{name}.json")) as f:
            json_schema = json.loads(f.read())

        return SchemaConverter.build(json_schema)
